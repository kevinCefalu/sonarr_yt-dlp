"""Configuration management for the application."""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import yaml


logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when configuration errors occur."""
    pass


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file.
                        If None, uses CONFIGPATH environment variable.
        """
        self.config_path = self._get_config_path(config_path)
        self.config_dir = self.config_path.parent
        self.template_path = self.config_path.with_suffix('.yml.template')
        self._config: Optional[Dict[str, Any]] = None

    def _get_config_path(self, config_path: Optional[str]) -> Path:
        """Get the configuration file path."""
        if config_path:
            return Path(config_path)

        env_path = os.environ.get('CONFIGPATH')
        if not env_path:
            raise ConfigError("CONFIGPATH environment variable not set")

        return Path(env_path)

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file.

        Returns:
            Configuration dictionary.

        Raises:
            ConfigError: If configuration cannot be loaded.
        """
        if self._config is not None:
            assert self._config is not None  # Explicit assertion for type checker
            return self._config

        if not self.config_path.exists():
            self._handle_missing_config()  # This will exit if config doesn't exist

        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config = yaml.load(file, Loader=yaml.SafeLoader)

            self._validate_config()
            logger.info("Configuration loaded successfully from %s", self.config_path)
            return self._config

        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}") from e
        except IOError as e:
            raise ConfigError(f"Cannot read config file: {e}") from e

    def _handle_missing_config(self) -> None:
        """Handle missing configuration file."""
        logger.critical("Configuration file not found: %s", self.config_path)

        if self.template_path.exists():
            logger.info("Template found at %s", self.template_path)
        else:
            # Try to find template in app directory
            app_template = Path('/app/config.yml.template')
            if app_template.exists():
                try:
                    import shutil
                    shutil.copy2(app_template, self.template_path)
                    logger.info("Template copied to %s", self.template_path)
                except Exception as e:
                    logger.error("Failed to copy template: %s", e)

        logger.critical("Create a config.yml using config.yml.template as an example.")
        sys.exit(1)

    def _validate_config(self) -> None:
        """Validate the loaded configuration."""
        if not self._config:
            raise ConfigError("Configuration is empty")

        required_sections = ['sonarr', 'ytdl', 'series']
        for section in required_sections:
            if section not in self._config:
                raise ConfigError(f"Missing required configuration section: {section}")

        # Validate Sonarr configuration
        sonarr_config = self._config['sonarr']
        required_sonarr_keys = ['host', 'port', 'apikey']
        for key in required_sonarr_keys:
            if key not in sonarr_config:
                raise ConfigError(f"Missing required Sonarr configuration: {key}")

        # Validate series configuration
        if not isinstance(self._config['series'], list):
            raise ConfigError("Series configuration must be a list")

        for i, series in enumerate(self._config['series']):
            if not isinstance(series, dict):
                raise ConfigError(f"Series {i} must be a dictionary")
            if 'title' not in series or 'url' not in series:
                raise ConfigError(f"Series {i} must have 'title' and 'url' fields")

    def get_config(self) -> Dict[str, Any]:
        """Get the loaded configuration."""
        if self._config is None:
            return self.load_config()
        return self._config

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get a specific configuration section.

        Args:
            section: The configuration section name.

        Returns:
            The configuration section.

        Raises:
            ConfigError: If section doesn't exist.
        """
        config = self.get_config()
        if section not in config:
            raise ConfigError(f"Configuration section '{section}' not found")
        return config[section]

    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """Get a specific configuration value.

        Args:
            section: The configuration section name.
            key: The configuration key.
            default: Default value if key doesn't exist.

        Returns:
            The configuration value or default.
        """
        try:
            section_config = self.get_section(section)
            return section_config.get(key, default)
        except ConfigError:
            return default
