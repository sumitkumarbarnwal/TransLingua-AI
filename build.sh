#!/bin/bash
# Render build script for TransLingua

echo "=========================================="
echo "TransLingua - Render Build Script"
echo "=========================================="

# Install Python dependencies
echo "Installing dependencies..."
pip install --no-cache-dir -r backend/requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p uploads/
mkdir -p feedback/
mkdir -p models/nepali
mkdir -p models/sinhalese

echo "Build complete!"
