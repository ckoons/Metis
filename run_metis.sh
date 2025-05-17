#!/bin/bash

# Run script for Metis component
# This script starts the Metis API server

# Default port (can be overridden by environment variable)
export METIS_PORT=${METIS_PORT:-8011}

# Ensure we're in the right directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR" || exit 1

echo "Starting Metis on port $METIS_PORT..."

# Start the Metis service using uvicorn
python -m uvicorn metis.api.app:app --host 0.0.0.0 --port "$METIS_PORT" --reload