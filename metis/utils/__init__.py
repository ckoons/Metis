# Utility functions for Metis

# from tekton.utils.port_config import (
#     get_component_port as get_port,
#     get_component_url as get_service_url
# )

# Placeholder functions for compatibility
def get_port(component_name: str) -> int:
    """Get component port - placeholder"""
    port_map = {
        'metis': 8011,
        'telos': 8008,
        'hermes': 8001
    }
    return port_map.get(component_name, 8000)

def get_service_url(component_name: str) -> str:
    """Get service URL - placeholder"""
    port = get_port(component_name)
    return f"http://localhost:{port}"
from metis.utils.hermes_helper import HermesClient, hermes_client

__all__ = [
    # Port configuration
    'get_port',
    'get_service_url',
    
    # Hermes integration
    'HermesClient',
    'hermes_client',
]