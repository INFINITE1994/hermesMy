"""CleanMaster entry point."""
import sys
import os

# Add parent directory to path for development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CleanMaster.ui.main_window import main

if __name__ == "__main__":
    main()
