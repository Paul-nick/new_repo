#!/usr/bin/env python3
"""
Build script to convert send_emails_gui.py to a Windows .EXE file.

This script uses PyInstaller to create a standalone executable that can be
distributed and run on Windows without Python installed.

Requirements:
    pip install pyinstaller

Usage:
    python build_exe.py

Output:
    dist/EmailSender.exe  (main executable)
"""

import os
import sys
import subprocess
from pathlib import Path

def build_exe():
    """Build the GUI application into a Windows EXE."""
    
    print("=" * 60)
    print("Building Jade Agency Email Sender EXE")
    print("=" * 60)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✓ PyInstaller found")
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Check if required files exist
    if not os.path.exists("send_emails_gui.py"):
        print("✗ send_emails_gui.py not found in current directory")
        sys.exit(1)
    
    print("✓ send_emails_gui.py found")
    
    # Create build command
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",                          # Single EXE file
        "--windowed",                         # No console window
        "--name", "EmailSender",              # Output filename
        "--icon", "NONE",                     # Can add icon later
        "--add-data", "credentials.json:.",   # Include credentials template
        "send_emails_gui.py"
    ]
    
    print("\nBuilding executable...")
    print("Command:", " ".join(cmd))
    print()
    
    try:
        result = subprocess.run(cmd, check=True)
        
        print("\n" + "=" * 60)
        print("✓ Build successful!")
        print("=" * 60)
        print("\nYour EXE file is located at:")
        print("  → dist/EmailSender.exe")
        print("\nBefore running:")
        print("  1. Download credentials.json from Google Cloud Console")
        print("  2. Place it in the same folder as EmailSender.exe")
        print("  3. Create a contacts.csv file with 'name' and 'email' columns")
        print("  4. Run EmailSender.exe")
        print("\nOn first run, you'll be prompted to log in with your Google account.")
        print("=" * 60)
        
    except subprocess.CalledProcessError as e:
        print("\n✗ Build failed!")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
