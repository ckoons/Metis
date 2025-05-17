"""
Entry point for Metis

This module serves as the entry point for running Metis as a standalone application.
It starts the API server using uvicorn.
"""

import os
import sys
import uvicorn
from metis.config import config

def main():
    """
    Main entry point for running Metis.
    
    Starts the API server using uvicorn.
    """
    print(f"Starting Metis API on port {config['METIS_PORT']}...")
    
    # Start the API server
    uvicorn.run(
        "metis.api.app:app", 
        host="0.0.0.0", 
        port=config["METIS_PORT"],
        reload=True
    )

if __name__ == "__main__":
    main()