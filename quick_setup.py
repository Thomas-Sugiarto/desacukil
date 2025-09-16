#!/usr/bin/env python3
"""
Quick setup script for Portal Desa Digital
This script installs dependencies and initializes the database.
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description.lower()}:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def main():
    print("Portal Desa Digital - Quick Setup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists('run.py'):
        print("❌ Error: run.py not found. Make sure you're in the project root directory.")
        sys.exit(1)
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        print("❌ Failed to install dependencies. Please check your Python environment.")
        sys.exit(1)
    
    # Initialize database
    if not run_command("python init_db.py", "Initializing database"):
        print("❌ Failed to initialize database.")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n🚀 To start the application, run:")
    print("   python run.py")
    print("\n🔐 Admin login credentials:")
    print("   Username: admin")
    print("   Password: Admin123!")
    print("   URL: http://localhost:5000/auth/login")

if __name__ == '__main__':
    main()