#!/usr/bin/env python3
"""
Sonarr YT-DLP Integration Application

A modernized version of the sonarr_youtubedl application that integrates
Sonarr with YT-DLP for downloading web series from various video platforms.
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

from src.app import SonarrYTDLPApp
from src.utils.logging_utils import setup_logging


def main():
    """Main entry point for the application."""
    try:
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
