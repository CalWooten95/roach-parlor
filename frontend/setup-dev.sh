#!/bin/bash

# Development setup script for Roach Parlor Frontend

echo "🚀 Setting up Roach Parlor Frontend development environment..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ is required. Current version: $(node --version)"
    exit 1
fi

echo "✅ Node.js $(node --version) detected"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please review and update as needed."
else
    echo "ℹ️  .env file already exists"
fi

# Run type check
echo "🔍 Running TypeScript type check..."
npm run type-check

if [ $? -ne 0 ]; then
    echo "❌ TypeScript type check failed"
    exit 1
fi

echo "✅ TypeScript type check passed"

# Run linting
echo "🧹 Running ESLint..."
npm run lint

if [ $? -ne 0 ]; then
    echo "⚠️  ESLint found issues. Run 'npm run lint:fix' to auto-fix some issues."
else
    echo "✅ ESLint check passed"
fi

echo ""
echo "🎉 Setup complete! You can now start development with:"
echo "   npm run dev"
echo ""
echo "📚 Available commands:"
echo "   npm run dev          - Start development server"
echo "   npm run build        - Build for production"
echo "   npm run lint         - Run ESLint"
echo "   npm run lint:fix     - Fix ESLint issues"
echo "   npm run format       - Format code with Prettier"
echo "   npm run type-check   - Run TypeScript type check"