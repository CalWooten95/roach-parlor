@echo off
REM Development setup script for Roach Parlor Frontend (Windows)

echo 🚀 Setting up Roach Parlor Frontend development environment...

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 18+ first.
    echo    Visit: https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ Node.js detected

REM Install dependencies
echo 📦 Installing dependencies...
npm install

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully

REM Copy environment file if it doesn't exist
if not exist ".env" (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ✅ .env file created. Please review and update as needed.
) else (
    echo ℹ️  .env file already exists
)

REM Run type check
echo 🔍 Running TypeScript type check...
npm run type-check

if %errorlevel% neq 0 (
    echo ❌ TypeScript type check failed
    pause
    exit /b 1
)

echo ✅ TypeScript type check passed

REM Run linting
echo 🧹 Running ESLint...
npm run lint

if %errorlevel% neq 0 (
    echo ⚠️  ESLint found issues. Run 'npm run lint:fix' to auto-fix some issues.
) else (
    echo ✅ ESLint check passed
)

echo.
echo 🎉 Setup complete! You can now start development with:
echo    npm run dev
echo.
echo 📚 Available commands:
echo    npm run dev          - Start development server
echo    npm run build        - Build for production
echo    npm run lint         - Run ESLint
echo    npm run lint:fix     - Fix ESLint issues
echo    npm run format       - Format code with Prettier
echo    npm run type-check   - Run TypeScript type check

pause