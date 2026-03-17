#!/bin/bash
# Start the OpenClaw MVP backend (native, no Docker)

set -euo pipefail

VENV_PATH="$HOME/venvs/ai-dev"
BACKEND_MODULE="backend.main:app"
SERVER_HOST="127.0.0.1"
SERVER_PORT="8000"

# Activate venv
if [[ -d "$VENV_PATH" ]]; then
  echo "Activating virtualenv at $VENV_PATH"
  source "$VENV_PATH/bin/activate"
else
  echo "WARNING: Virtualenv not found at $VENV_PATH. You can activate manually: source $VENV_PATH/bin/activate"
fi

# Run uvicorn
echo "Starting OpenClaw MVP backend at http://$SERVER_HOST:$SERVER_PORT"
exec uvicorn "$BACKEND_MODULE" --host "$SERVER_HOST" --port "$SERVER_PORT" --reload
