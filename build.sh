#!/usr/bin/env bash
# Build script for Render deployment
# Installs Python deps + builds the React frontend

set -o errexit  # exit on error

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "📦 Installing frontend dependencies..."
cd frontend
npm install

echo "🔨 Building React frontend..."
npm run build

echo "✅ Build complete!"
