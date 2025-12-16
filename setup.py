#!/usr/bin/env python3
"""
Setup script for Enterprise RAG System.
Automates initial setup and verification.
"""

import os
import subprocess
import sys
from pathlib import Path


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def check_command(command: str) -> bool:
    """Check if a command exists."""
    try:
        subprocess.run(
            [command, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        return True
    except FileNotFoundError:
        return False


def main() -> None:
    """Main setup function."""
    print_header("🚀 Enterprise RAG System - Setup Script")
    
    # Check prerequisites
    print("1️⃣ Checking prerequisites...")
    
    prerequisites = {
        "python": "Python 3.11+",
        "docker": "Docker",
        "docker-compose": "Docker Compose",
    }
    
    missing = []
    for cmd, name in prerequisites.items():
        if check_command(cmd):
            print(f"   ✅ {name} found")
        else:
            print(f"   ❌ {name} NOT found")
            missing.append(name)
    
    if missing:
        print(f"\n⚠️  Missing prerequisites: {', '.join(missing)}")
        print("   Please install them before continuing.")
        sys.exit(1)
    
    # Check for uv
    print("\n2️⃣ Checking for uv package manager...")
    if check_command("uv"):
        print("   ✅ uv found")
    else:
        print("   ❌ uv not found")
        print("   Installing uv...")
        try:
            subprocess.run(
                "curl -LsSf https://astral.sh/uv/install.sh | sh",
                shell=True,
                check=True,
            )
            print("   ✅ uv installed successfully")
        except subprocess.CalledProcessError:
            print("   ❌ Failed to install uv")
            print("   Please install manually: https://astral.sh/uv")
            sys.exit(1)
    
    # Create .env file
    print("\n3️⃣ Setting up environment configuration...")
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("   ⚠️  .env file already exists, skipping...")
    elif env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
        print("   ✅ Created .env from .env.example")
        print("   ⚠️  Please edit .env and add your API keys!")
    else:
        print("   ❌ .env.example not found")
    
    # Install dependencies
    print("\n4️⃣ Installing Python dependencies...")
    try:
        subprocess.run(["uv", "pip", "install", "-e", "."], check=True)
        print("   ✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("   ❌ Failed to install dependencies")
        sys.exit(1)
    
    # Create data directories
    print("\n5️⃣ Creating data directories...")
    dirs = ["data/uploads", "logs"]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created {dir_path}/")
    
    # Start Docker services
    print("\n6️⃣ Starting Docker services...")
    response = input("   Start Docker services now? (y/n): ")
    if response.lower() == 'y':
        try:
            subprocess.run(["docker-compose", "up", "-d"], check=True)
            print("   ✅ Docker services started")
            print("   ⏳ Waiting for services to be ready...")
            import time
            time.sleep(10)
        except subprocess.CalledProcessError:
            print("   ❌ Failed to start Docker services")
            print("   You can start them manually with: docker-compose up -d")
    else:
        print("   ⏭️  Skipped Docker setup")
        print("   Start manually with: docker-compose up -d")
    
    # Final instructions
    print_header("✅ Setup Complete!")
    
    print("📋 Next Steps:\n")
    print("1. Edit .env file and add your API keys:")
    print("   - OPENAI_API_KEY (if using OpenAI)")
    print("   - Or configure Ollama for local LLM\n")
    
    print("2. Start the application:")
    print("   uv run uvicorn src.main:app --reload\n")
    
    print("3. Access the API:")
    print("   - Swagger UI: http://localhost:8000/docs")
    print("   - ReDoc: http://localhost:8000/redoc")
    print("   - Health: http://localhost:8000/health\n")
    
    print("4. Upload and query documents:")
    print("   - See QUICKSTART.md for examples\n")
    
    print("📚 Documentation:")
    print("   - README.md - Project overview")
    print("   - QUICKSTART.md - Quick start guide")
    print("   - ARCHITECTURE.md - Architecture details")
    print("   - PROJECT_SUMMARY.md - Implementation summary\n")
    
    print("🎉 Happy coding!\n")


if __name__ == "__main__":
    main()
