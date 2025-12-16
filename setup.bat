@echo off
REM Windows setup script for Enterprise RAG System

echo ========================================
echo   Enterprise RAG System Setup
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11+
    exit /b 1
)
echo [OK] Python found

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found. Please install Docker Desktop
    exit /b 1
)
echo [OK] Docker found

REM Create .env file
if not exist .env (
    if exist .env.example (
        copy .env.example .env
        echo [OK] Created .env file
        echo [WARNING] Please edit .env and add your API keys!
    )
)

REM Install dependencies
echo.
echo Installing dependencies...
uv pip install -e .
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)
echo [OK] Dependencies installed

REM Create directories
if not exist data\uploads mkdir data\uploads
if not exist logs mkdir logs
echo [OK] Created data directories

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Start Docker: docker-compose up -d
echo 3. Run app: uv run uvicorn src.main:app --reload
echo 4. Visit: http://localhost:8000/docs
echo.
echo See QUICKSTART.md for more details.
echo.

pause
