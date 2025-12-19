#!/bin/bash

echo "Setting up AI-Powered Shopify Analytics App..."
echo ""

# Setup Rails API
echo "=== Setting up Rails API ==="
cd rails_api

if [ ! -f "Gemfile.lock" ]; then
    echo "Installing Ruby dependencies..."
    bundle install
fi

if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit rails_api/.env with your Shopify credentials"
fi

cd ..

# Setup Python Service
echo ""
echo "=== Setting up Python Service ==="
cd python_service

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit python_service/.env with your OpenAI API key"
fi

deactivate
cd ..

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit rails_api/.env with your Shopify API credentials"
echo "2. Edit python_service/.env with your OpenAI API key"
echo "3. Start Rails API: cd rails_api && rails server"
echo "4. Start Python Service: cd python_service && source venv/bin/activate && uvicorn main:app --reload"
echo ""

