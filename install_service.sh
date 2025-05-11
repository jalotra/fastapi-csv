#!/bin/bash

# Exit on error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

# Get the absolute path of the application directory
APP_DIR=$(cd "$(dirname "$0")" && pwd)

# Create a Python virtual environment if it doesn't exist
if [ ! -d "$APP_DIR/venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv "$APP_DIR/venv"
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source "$APP_DIR/venv/bin/activate"
pip install -r "$APP_DIR/requirements.txt"
deactivate

# Update the service file with the correct paths
echo "Configuring service file..."
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$APP_DIR|g" "$APP_DIR/fastapi-csv.service"

# Verify app.py exists
if [ ! -f "$APP_DIR/app.py" ]; then
  echo "Error: app.py not found in $APP_DIR"
  exit 1
fi

# Copy service file to systemd directory
echo "Installing systemd service..."
cp "$APP_DIR/fastapi-csv.service" /etc/systemd/system/

# Reload systemd, enable and start the service
echo "Starting service..."
systemctl daemon-reload
systemctl enable fastapi-csv.service
systemctl start fastapi-csv.service

echo "Service installed and started successfully!"
echo "Check status with: systemctl status fastapi-csv.service"
