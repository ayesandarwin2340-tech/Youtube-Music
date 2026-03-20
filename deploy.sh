#!/bin/bash

# Music Bot Deployment Script
echo "🎵 Music Bot Ultimate - Deployment Script"
echo "=========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env file with your credentials"
    exit 1
fi

# Load environment variables
source .env

# Validate required variables
if [ -z "$API_ID" ] || [ -z "$API_HASH" ] || [ -z "$BOT_TOKEN" ]; then
    echo "❌ Missing required environment variables!"
    echo "Please set API_ID, API_HASH, and BOT_TOKEN in .env file"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data downloads logs
chmod 755 data downloads logs

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed!"
    echo "Please install docker-compose first"
    exit 1
fi

# Build and run
echo "🐳 Building Docker image..."
docker-compose build

echo "🚀 Starting bot..."
docker-compose up -d

# Check if bot is running
sleep 5
if docker-compose ps | grep -q "Up"; then
    echo "✅ Bot started successfully!"
    echo "📊 View logs: make logs or docker-compose logs -f"
    echo "🛑 Stop bot: make stop or docker-compose down"
else
    echo "❌ Bot failed to start!"
    echo "Check logs: docker-compose logs"
    exit 1
fi
