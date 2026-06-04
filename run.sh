#!/bin/bash
# Start the Badminton Matchmaking Platform

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Create venv if not exists
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies..."
pip install -q -r backend/requirements.txt

echo "Starting server at http://localhost:8000"
PYTHONPATH="$SCRIPT_DIR" uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
