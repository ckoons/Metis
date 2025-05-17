"""
Configuration module for Metis

This module manages the configuration for Metis, including
environment variables, default settings, and component integration.
"""

import os
from typing import Dict, Any

# Default configuration
DEFAULT_CONFIG = {
    # Service configuration
    "SERVICE_NAME": "Metis",
    "SERVICE_DESCRIPTION": "Task Management System for Tekton",
    "SERVICE_VERSION": "0.1.0",
    
    # Port configuration
    "METIS_PORT": 8011,
    "HERMES_PORT": 8001,
    "TELOS_PORT": 8008,
    "PROMETHEUS_PORT": 8006,
    
    # Database configuration
    "DB_URL": "sqlite:///metis.db",
    
    # API configuration
    "API_PREFIX": "/api/v1",
    "WEBSOCKET_PATH": "/ws",
    "EVENTS_PATH": "/events",
    
    # Component URLs (constructed at runtime)
    "HERMES_URL": None,
    "TELOS_URL": None,
    "PROMETHEUS_URL": None,
}

def get_config() -> Dict[str, Any]:
    """
    Get the configuration for Metis.
    
    Returns:
        Dict[str, Any]: Configuration dictionary with all settings
    """
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables
    for key in config.keys():
        if key in os.environ:
            # Convert to appropriate type
            if isinstance(config[key], int):
                config[key] = int(os.environ[key])
            elif isinstance(config[key], bool):
                config[key] = os.environ[key].lower() in ("true", "1", "yes")
            else:
                config[key] = os.environ[key]
    
    # Construct component URLs
    config["HERMES_URL"] = f"http://localhost:{config['HERMES_PORT']}"
    config["TELOS_URL"] = f"http://localhost:{config['TELOS_PORT']}"
    config["PROMETHEUS_URL"] = f"http://localhost:{config['PROMETHEUS_PORT']}"
    
    return config

# Global config instance for import
config = get_config()