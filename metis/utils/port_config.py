"""
Port configuration utility for Metis

This module manages port configuration and provides functions for constructing
URLs to other Tekton components.
"""

import os
from typing import Dict, Optional

def get_port(service_name: str, default_port: int) -> int:
    """
    Get the port for a service from environment variables or use the default.
    
    Args:
        service_name: Name of the service (e.g., "METIS", "HERMES")
        default_port: Default port to use if not specified in environment
        
    Returns:
        int: Port number for the service
    """
    env_var = f"{service_name.upper()}_PORT"
    return int(os.environ.get(env_var, default_port))

def get_service_url(service_name: str, default_port: int, protocol: str = "http") -> str:
    """
    Get the URL for a service.
    
    Args:
        service_name: Name of the service (e.g., "METIS", "HERMES")
        default_port: Default port to use if not specified in environment
        protocol: Protocol to use (http or ws)
        
    Returns:
        str: URL for the service
    """
    port = get_port(service_name, default_port)
    return f"{protocol}://localhost:{port}"

def get_service_endpoints() -> Dict[str, str]:
    """
    Get the endpoints for all services.
    
    Returns:
        Dict[str, str]: Dictionary of service URLs
    """
    return {
        "metis": get_service_url("METIS", 8011),
        "hermes": get_service_url("HERMES", 8001),
        "telos": get_service_url("TELOS", 8008),
        "prometheus": get_service_url("PROMETHEUS", 8006),
    }

def construct_api_url(service_name: str, default_port: int, endpoint: str) -> str:
    """
    Construct an API URL for a service.
    
    Args:
        service_name: Name of the service (e.g., "METIS", "HERMES")
        default_port: Default port to use if not specified in environment
        endpoint: API endpoint path
        
    Returns:
        str: Complete API URL
    """
    base_url = get_service_url(service_name, default_port)
    endpoint = endpoint.lstrip("/")
    return f"{base_url}/api/v1/{endpoint}"

def construct_ws_url(service_name: str, default_port: int, path: Optional[str] = None) -> str:
    """
    Construct a WebSocket URL for a service.
    
    Args:
        service_name: Name of the service (e.g., "METIS", "HERMES")
        default_port: Default port to use if not specified in environment
        path: Additional path for the WebSocket
        
    Returns:
        str: Complete WebSocket URL
    """
    base_url = get_service_url(service_name, default_port, protocol="ws")
    if path:
        path = path.lstrip("/")
        return f"{base_url}/ws/{path}"
    return f"{base_url}/ws"