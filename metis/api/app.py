"""
Metis API Application

This module defines the FastAPI application for the Metis task management service.
It follows Tekton's Single Port Architecture pattern, exposing HTTP, WebSocket,
and Event endpoints through path-based routing.
"""

import os
import sys
import json
import asyncio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Set, Any, Optional
from uuid import UUID

# Import Hermes registration utility
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "shared", "utils"))
from hermes_registration import HermesRegistration, heartbeat_loop

from metis.config import config
from metis.api.routes import router as api_router
from metis.api.routes import task_manager  # Reuse the TaskManager instance from routes
from metis.api.schemas import WebSocketMessage, WebSocketRegistration
from metis.api.fastmcp_endpoints import mcp_router, fastmcp_server


# Create FastAPI application
app = FastAPI(
    title="Metis API",
    description="Task Management System for Tekton",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get port from environment variable or use default
PORT = int(os.environ.get("METIS_PORT", 8011))

# Include API routers
app.include_router(api_router)
app.include_router(mcp_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint for Metis API."""
    return {
        "name": "Metis",
        "description": "Task Management System for Tekton",
        "version": "0.1.0",
        "status": "running",
    }


# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint following Tekton standards."""
    # from tekton.utils.port_config import get_metis_port
    def get_metis_port(): return 8011
    port = get_metis_port()
    
    return {
        "status": "healthy",
        "component": "metis",
        "version": "0.1.0",
        "port": port,
        "message": "Metis is running normally"
    }


# WebSocket connection manager
class ConnectionManager:
    """Manager for WebSocket connections."""
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        Connect a new WebSocket client.
        
        Args:
            websocket: WebSocket connection
            client_id: Client ID
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()
    
    def disconnect(self, client_id: str) -> None:
        """
        Disconnect a WebSocket client.
        
        Args:
            client_id: Client ID
        """
        self.active_connections.pop(client_id, None)
        self.subscriptions.pop(client_id, None)
    
    def subscribe(self, client_id: str, event_types: List[str]) -> None:
        """
        Subscribe a client to event types.
        
        Args:
            client_id: Client ID
            event_types: List of event types to subscribe to
        """
        if client_id in self.subscriptions:
            self.subscriptions[client_id].update(event_types)
    
    def unsubscribe(self, client_id: str, event_types: List[str]) -> None:
        """
        Unsubscribe a client from event types.
        
        Args:
            client_id: Client ID
            event_types: List of event types to unsubscribe from
        """
        if client_id in self.subscriptions:
            for event_type in event_types:
                self.subscriptions[client_id].discard(event_type)
    
    async def broadcast(self, event_type: str, data: Any) -> None:
        """
        Broadcast an event to all subscribed clients.
        
        Args:
            event_type: Event type
            data: Event data
        """
        message = {
            "type": event_type,
            "data": data
        }
        
        # Convert to JSON once
        message_json = json.dumps(message)
        
        # Send to each subscribed client
        for client_id, subscriptions in self.subscriptions.items():
            if event_type in subscriptions:
                websocket = self.active_connections.get(client_id)
                if websocket:
                    try:
                        await websocket.send_text(message_json)
                    except Exception:
                        # If sending fails, disconnect the client
                        self.disconnect(client_id)


# Create connection manager
manager = ConnectionManager()


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    client_id = str(UUID)  # Generate a random client ID
    
    # Accept the connection
    await manager.connect(websocket, client_id)
    
    try:
        # Wait for registration message
        registration_text = await websocket.receive_text()
        registration_data = json.loads(registration_text)
        
        # Validate registration
        try:
            registration = WebSocketRegistration(**registration_data)
            client_id = registration.client_id  # Use client-provided ID if available
            
            # Subscribe to event types
            manager.subscribe(client_id, registration.subscribe_to)
            
            # Send confirmation
            await websocket.send_json({
                "type": "registration_success",
                "data": {
                    "client_id": client_id,
                    "subscriptions": list(manager.subscriptions[client_id])
                }
            })
            
            # Register event handlers with task manager
            for event_type in registration.subscribe_to:
                task_manager.register_event_handler(
                    event_type,
                    lambda event_type, data: asyncio.create_task(
                        manager.broadcast(event_type, data)
                    )
                )
            
            # Keep connection alive and handle messages
            while True:
                message_text = await websocket.receive_text()
                message_data = json.loads(message_text)
                
                # Handle different message types
                message_type = message_data.get("type")
                
                if message_type == "ping":
                    # Respond to ping
                    await websocket.send_json({"type": "pong", "data": {}})
                
                elif message_type == "subscribe":
                    # Subscribe to event types
                    event_types = message_data.get("data", {}).get("event_types", [])
                    manager.subscribe(client_id, event_types)
                
                elif message_type == "unsubscribe":
                    # Unsubscribe from event types
                    event_types = message_data.get("data", {}).get("event_types", [])
                    manager.unsubscribe(client_id, event_types)
                
        except Exception as e:
            # Invalid registration
            await websocket.send_json({
                "type": "registration_error",
                "data": {
                    "error": str(e)
                }
            })
            await websocket.close()
    
    except WebSocketDisconnect:
        # Client disconnected
        manager.disconnect(client_id)
    
    except Exception as e:
        # Other error
        try:
            await websocket.send_json({
                "type": "error",
                "data": {
                    "error": str(e)
                }
            })
        except:
            pass
        manager.disconnect(client_id)


# Register with Hermes on startup
@app.on_event("startup")
async def startup_event():
    """Startup event handler for Metis API.
    
    Initializes FastMCP server and registers the service with Hermes for service discovery.
    """
    # Initialize FastMCP server
    try:
        await fastmcp_server.startup()
        print("FastMCP server initialized successfully")
    except Exception as e:
        print(f"Warning: FastMCP server initialization failed: {e}")
    
    # Register with Hermes using standard utility
    # from tekton.utils.port_config import get_metis_port
    def get_metis_port(): return 8011
    port = get_metis_port()
    
    hermes_registration = HermesRegistration()
    await hermes_registration.register_component(
        component_name="metis",
        port=port,
        version="0.1.0",
        capabilities=[
            "task_management",
            "dependency_management", 
            "task_tracking",
            "websocket_updates"
        ],
        metadata={
            "description": "Task breakdown and management",
            "category": "planning"
        }
    )
    app.state.hermes_registration = hermes_registration
    
    # Start heartbeat task
    if hermes_registration.is_registered:
        asyncio.create_task(heartbeat_loop(hermes_registration, "metis"))
    
    print(f"Metis API starting on port {port}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler for Metis API.
    
    Shuts down FastMCP server and unregisters the service from Hermes.
    """
    # Shutdown FastMCP server
    try:
        await fastmcp_server.shutdown()
        print("FastMCP server shut down successfully")
    except Exception as e:
        print(f"Warning: FastMCP server shutdown failed: {e}")
    
    # Deregister from Hermes
    if hasattr(app.state, "hermes_registration") and app.state.hermes_registration:
        await app.state.hermes_registration.deregister("metis")
    
    print("Metis API shutting down")


# Custom exception handler for HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom handler for HTTPException to provide consistent response format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Generic exception handler to catch all unhandled exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": f"An unexpected error occurred: {str(exc)}",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    )