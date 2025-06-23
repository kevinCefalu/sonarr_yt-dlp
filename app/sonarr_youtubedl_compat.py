#!/usr/bin/env python3
"""
Compatibility wrapper for the legacy sonarr_youtubedl.py script.

This wrapper provides backward compatibility while using the new modular codebase.
"""
import sys
import os
import warnings
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

# Issue deprecation warning
warnings.warn(
    "sonarr_youtubedl.py is deprecated. Please use main.py instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import and run the new application
from src.app import SonarrYTDLPApp


def main():
    """Main entry point for legacy compatibility."""
    try:
        print("Starting legacy compatibility mode...")
        print("Note: This script is deprecated. Please use main.py instead.")

        # Initialize and run the application
        app = SonarrYTDLPApp()
        app.run_scheduler()

    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
