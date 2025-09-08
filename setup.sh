#!/bin/bash

# Development setup script for Algebra Integral DEX Screener Adapter

echo "Setting up Algebra Integral DEX Screener Adapter..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

echo "Setup complete!"
echo "To run the adapter:"
echo "1. Edit .env file with your Infura API key and other settings"
echo "2. Run: python main.py"
