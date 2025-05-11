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

# Create data directory if it doesn't exist
DATA_DIR="$APP_DIR/data"
mkdir -p "$DATA_DIR"

# Set ownership to www-data:ubuntu
chown -R www-data:ubuntu "$DATA_DIR"

# Set permissions to allow both www-data user and ubuntu group to write
chmod -R 775 "$DATA_DIR"

echo "Database directory permissions set up successfully at $DATA_DIR"
echo "The www-data user and ubuntu group now have write access to this directory."
