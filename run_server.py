#!/usr/bin/env python3
"""
Proper server startup script that handles imports correctly
"""

import os
import sys
from pathlib import Path

# Add server directory to Python path
server_dir = Path(__file__).parent / "server"
sys.path.insert(0, str(server_dir))

# Change to server directory for relative imports to work
os.chdir(server_dir)

if __name__ == "__main__":
    try:
        import uvicorn
        from main import app

        print("🚀 Starting Ninaivalaigal server...")
        print("✅ All imports successful")

        # Run with uvicorn
        uvicorn.run(
            "main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
        )
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running from the project root directory")
        sys.exit(1)
