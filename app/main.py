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
    # Set up basic logging first to catch initialization errors
    logger = setup_logging(console_logging=True, file_logging=False, debug=True)
    logger.info("Starting Sonarr YT-DLP application...")

    # Check for configuration file
    config_path = os.environ.get('CONFIGPATH', '/config/config.yml')
    config_file = Path(config_path)

    if not config_file.exists():
        logger.critical("Configuration file not found: %s", config_path)
        logger.critical("Please create a config.yml file using config.yml.template as an example")
        logger.critical("Expected config file location: %s", config_path)

        # Show template location if it exists
        template_path = Path('/app/config.yml.template')
        if template_path.exists():
            logger.info("Template file available at: %s", template_path)
            logger.info("Copy it to: %s", config_path)

        sys.exit(1)

    logger.info("Found configuration file: %s", config_path)

    try:
        # Initialize and run the application
        logger.info("Initializing application...")
        app = SonarrYTDLPApp()
        logger.info("Starting scheduler...")
        app.run_scheduler()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
