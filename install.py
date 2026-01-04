#!/usr/bin/env python3
"""
Fyntora Linux Installer - Main entry point
"""

import sys
import os

# Add src directory to path so we can import modules
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, src_dir)

# Now import our modules
from src.installer import main

if __name__ == "__main__":
    # Pass through all command line arguments
    sys.exit(main())
