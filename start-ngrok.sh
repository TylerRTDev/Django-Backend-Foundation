#!/bin/bash
# start-ngrok.sh - Start Django app with ngrok tunnel
set -e

cd "$(dirname "$0")"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please create one from .env.example."
    exit 1
fi

# Load .env variables (simple)
export $(grep -v '^#' .env | xargs)

# Check if NGROK_AUTHTOKEN is set
if [ -z "$NGROK_AUTHTOKEN" ] || [ "$NGROK_AUTHTOKEN" = "your_auth_token_here" ]; then
    echo "ERROR: NGROK_AUTHTOKEN is not set in .env file."
    echo "Please sign up at https://ngrok.com, get your authtoken, and add it to .env:"
    echo "NGROK_AUTHTOKEN=your_actual_token"
    exit 1
fi

# Ensure USE_NGROK is set to True
if [ "$USE_NGROK" != "True" ]; then
    echo "WARNING: USE_NGROK is not set to True in .env. Setting it temporarily for this run."
    export USE_NGROK=True
fi

# Ensure media directory exists for local storage when using ngrok
mkdir -p media

# Run docker compose with ngrok profile
echo "Starting Docker Compose with ngrok profile..."
docker compose --profile ngrok up

# Note: To stop, press Ctrl+C and run: docker-compose down