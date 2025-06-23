"""Main application orchestrator."""
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

import schedule

from config import ConfigManager
from models import Series, Episode
from services.sonarr_client import SonarrClient, SonarrAPIError
from services.ytdlp_service import YTDLPService
from utils.logging_utils import setup_logging
from utils.date_utils import apply_time_offset
from utils.text_utils import apply_regex_transformation


logger = logging.getLogger(__name__)


class SonarrYTDLPApp:
    """Main application class for Sonarr YT-DLP integration."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the application.

        Args:
            config_path: Path to configuration file.
        """
        print("DEBUG: Starting SonarrYTDLPApp.__init__")
        logger.info("Loading configuration...")
        # Load configuration
        print("DEBUG: About to create ConfigManager")
        self.config_manager = ConfigManager(config_path)
        print("DEBUG: About to load config")
        self.config = self.config_manager.load_config()
        print("DEBUG: Config loaded successfully")
        logger.info("Configuration loaded successfully")

        # Set up logging
        print("DEBUG: About to set up logging")
        logger.info("Setting up logging...")
        debug_mode = self._get_debug_mode()
        print(f"DEBUG: Debug mode: {debug_mode}")
        self.logger = setup_logging(debug=debug_mode)
        print("DEBUG: Logging configured")
        logger.info("Logging configured (debug=%s)", debug_mode)

        # Initialize services
        print("DEBUG: About to initialize services")
        logger.info("Initializing services...")
        self._initialize_services()
        print("DEBUG: Services initialized")
        logger.info("Services initialized successfully")

        # Set scan interval
        print("DEBUG: About to set scan interval")
        self.scan_interval = self.config_manager.get_value('sonarrytdl', 'scan_interval', 60)
        print(f"DEBUG: Scan interval set to {self.scan_interval} minutes")
        logger.info("Scan interval set to %d minutes", self.scan_interval)
        print("DEBUG: SonarrYTDLPApp.__init__ completed")

    def _get_debug_mode(self) -> bool:
        """Get debug mode from configuration."""
        debug_value = self.config_manager.get_value('sonarrytdl', 'debug', False)
        if isinstance(debug_value, str):
            return debug_value.lower() in ['true', '1', 'yes', 'on']
        return bool(debug_value)

    def _initialize_services(self) -> None:
        """Initialize external services."""
        print("DEBUG: Initializing Sonarr client...")
        logger.info("Initializing Sonarr client...")
        # Initialize Sonarr client
        sonarr_config = self.config_manager.get_section('sonarr')
        print(f"DEBUG: Sonarr config: {sonarr_config}")
        self.sonarr_client = SonarrClient(
            host=sonarr_config['host'],
            port=int(sonarr_config['port']),
            api_key=sonarr_config['apikey'],
            ssl=sonarr_config.get('ssl', False),
            api_base_path=sonarr_config.get('apiBasePath', 'api/v3')
        )
        print("DEBUG: Sonarr client created")
        logger.info("Sonarr client initialized")

        print("DEBUG: Initializing YT-DLP service...")
        logger.info("Initializing YT-DLP service...")
        # Initialize YT-DLP service
        ytdl_config = self.config_manager.get_section('ytdl')
        print(f"DEBUG: YT-DLP config: {ytdl_config}")
        self.ytdlp_service = YTDLPService(
            default_format=ytdl_config['default_format'],
            config_dir=self.config_manager.config_dir,
            debug=self._get_debug_mode()
        )
        print("DEBUG: YT-DLP service created")
        logger.info("YT-DLP service initialized")

    def filter_configured_series(self) -> List[Series]:
        """Filter series from Sonarr that are configured for download.

        Returns:
            List of configured Series objects.
        """
        print("DEBUG: Entered filter_configured_series")
        try:
            print("DEBUG: About to call sonarr_client.get_series()")
            all_series = self.sonarr_client.get_series()
            print(f"DEBUG: Got {len(all_series)} series from Sonarr")
        except SonarrAPIError as e:
            print(f"DEBUG: SonarrAPIError: {e}")
            logger.error("Failed to get series from Sonarr: %s", e)
            return []
        except Exception as e:
            print(f"DEBUG: Unexpected error getting series: {e}")
            logger.error("Unexpected error getting series from Sonarr: %s", e)
            return []

        print("DEBUG: About to get series configs from config manager")
        configured_series = []
        series_configs = self.config_manager.get_section('series')
        print(f"DEBUG: Got {len(series_configs)} series configs")

        for series in all_series:
            # Find matching configuration
            matching_config = None
            for config in series_configs:
                if isinstance(config, dict) and config.get('title') == series.title:
                    matching_config = config
                    break

            if matching_config:
                # Apply configuration to series
                series.apply_config(matching_config)
                configured_series.append(series)

                if not series.monitored:
                    logger.warning("Series '%s' is configured but not monitored in Sonarr",
                                 series.title)
            else:
                logger.debug("Series '%s' not configured for download", series.title)

        logger.info("Found %d configured series out of %d total",
                   len(configured_series), len(all_series))
        print(f"DEBUG: Returning {len(configured_series)} configured series")
        return configured_series

    def get_missing_episodes(self, series_list: List[Series]) -> List[Episode]:
        """Get episodes that need to be downloaded.

        Args:
            series_list: List of Series objects.

        Returns:
            List of Episode objects that need downloading.
        """
        missing_episodes = []
        current_time = datetime.now()

        for series in series_list[:]:  # Use slice copy to allow modification
            try:
                episodes = self.sonarr_client.get_episodes_by_series_id(series.id)
            except SonarrAPIError as e:
                logger.error("Failed to get episodes for series %s: %s", series.title, e)
                continue

            series_missing = []

            for episode in episodes:
                # Skip if not monitored
                if not episode.monitored:
                    continue

                # Skip if already has file
                if episode.has_file:
                    continue

                # Check air date
                episode_air_date = episode.air_date_utc
                if episode_air_date:
                    # Apply time offset if configured
                    if series.offset:
                        episode_air_date = apply_time_offset(episode_air_date, series.offset)

                    # Skip if hasn't aired yet
                    if episode_air_date > current_time:
                        continue

                # Apply title regex transformation if configured
                if series.sonarr_regex_match and series.sonarr_regex_replace:
                    episode.title = apply_regex_transformation(
                        episode.title,
                        series.sonarr_regex_match,
                        series.sonarr_regex_replace
                    )

                series_missing.append(episode)
                missing_episodes.append(episode)

            if series_missing:
                logger.info("Series '%s' missing %d episodes",
                           series.title, len(series_missing))
                for i, episode in enumerate(series_missing, 1):
                    logger.info("  %d: %s - %s", i, series.title, episode.title)
            else:
                logger.info("Series '%s' has no missing episodes", series.title)
                # Remove series with no missing episodes
                if series in series_list:
                    series_list.remove(series)

        return missing_episodes

    def download_episodes(self, series_list: List[Series], episodes: List[Episode]) -> Dict[str, Any]:
        """Download missing episodes.

        Args:
            series_list: List of Series objects.
            episodes: List of Episode objects to download.

        Returns:
            Dictionary with download statistics.
        """
        if not series_list:
            logger.info("No series to process")
            return {'total': 0, 'success': 0, 'failed': 0}

        stats = {'total': 0, 'success': 0, 'failed': 0}

        logger.info("Processing downloads for %d series", len(series_list))

        for series in series_list:
            logger.info("Processing series: %s", series.title)

            # Get episodes for this series
            series_episodes = [ep for ep in episodes if ep.series_id == series.id]

            for episode in series_episodes:
                stats['total'] += 1

                # Search for the episode
                found, video_url = self.ytdlp_service.search_for_episode(series, episode)

                if found:
                    logger.info("Found episode: %s - %s", series.title, episode.title)

                    # Download the episode
                    result = self.ytdlp_service.download_episode(series, episode, video_url)

                    if result.success:
                        stats['success'] += 1
                        logger.info("Successfully downloaded: %s - %s",
                                   series.title, episode.title)

                        # Trigger Sonarr rescan
                        try:
                            self.sonarr_client.rescan_series(series.id)
                        except SonarrAPIError as e:
                            logger.error("Failed to trigger rescan for series %s: %s",
                                       series.title, e)
                    else:
                        stats['failed'] += 1
                        logger.error("Failed to download: %s - %s",
                                   series.title, episode.title)
                else:
                    stats['failed'] += 1
                    logger.info("Episode not found: %s - %s", series.title, episode.title)

        return stats

    def run_scan(self) -> None:
        """Run a single scan cycle."""
        print("DEBUG: Entered run_scan")
        logger.info("Starting scan cycle")
        print("DEBUG: Logged 'Starting scan cycle'")
        start_time = time.time()

        try:
            # Get configured series
            print("DEBUG: About to get configured series")
            series_list = self.filter_configured_series()
            print(f"DEBUG: Got {len(series_list) if series_list else 0} configured series")

            if not series_list:
                logger.info("No configured series found")
                print("DEBUG: No configured series found, returning")
                return

            # Get missing episodes
            print("DEBUG: About to get missing episodes")
            episodes = self.get_missing_episodes(series_list)
            print(f"DEBUG: Got {len(episodes) if episodes else 0} missing episodes")

            if not episodes:
                logger.info("No missing episodes found")
                print("DEBUG: No missing episodes found, returning")
                return

            # Download episodes
            print("DEBUG: About to download episodes")
            stats = self.download_episodes(series_list, episodes)
            print(f"DEBUG: Download stats: {stats}")

            # Log summary
            duration = time.time() - start_time
            logger.info("Scan completed in %.2f seconds. "
                       "Total: %d, Success: %d, Failed: %d",
                       duration, stats['total'], stats['success'], stats['failed'])
            print("DEBUG: Scan completed successfully")

        except Exception as e:
            print(f"DEBUG: Exception in run_scan: {e}")
            logger.error("Error during scan cycle: %s", e, exc_info=True)

    def run_scheduler(self) -> None:
        """Run the application with scheduled scans."""
        print("DEBUG: Entered run_scheduler")
        logger.info("Starting Sonarr YT-DLP application")
        print("DEBUG: Logged 'Starting Sonarr YT-DLP application'")

        # Run initial scan
        print("DEBUG: About to run initial scan")
        logger.info("Running initial scan")
        print("DEBUG: About to call self.run_scan()")
        self.run_scan()
        print("DEBUG: Initial scan completed")

        # Schedule periodic scans
        print("DEBUG: About to schedule periodic scans")
        schedule.every(self.scan_interval).minutes.do(self.run_scan)
        logger.info("Scheduled scans every %d minutes", self.scan_interval)
        print("DEBUG: Scheduled scans configured")

        # Main loop
        print("DEBUG: Entering main loop")
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Application stopped by user")
        except Exception as e:
            logger.error("Unexpected error in main loop: %s", e, exc_info=True)
            raise
