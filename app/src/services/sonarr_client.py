"""Sonarr API client service."""
import logging
import urllib.parse
from typing import Dict, List, Optional, Any

import requests

from models import Series, Episode


logger = logging.getLogger(__name__)


class SonarrAPIError(Exception):
    """Raised when Sonarr API errors occur."""
    pass


class SonarrClient:
    """Client for interacting with Sonarr API."""

    def __init__(self, host: str, port: int, api_key: str,
                 ssl: bool = False, api_base_path: str = "api/v3"):
        """Initialize the Sonarr client.

        Args:
            host: Sonarr host address.
            port: Sonarr port number.
            api_key: Sonarr API key.
            ssl: Whether to use HTTPS.
            api_base_path: API base path.
        """
        self.host = host
        self.port = port
        self.api_key = api_key
        self.ssl = ssl
        self.api_base_path = api_base_path.strip('/')

        scheme = "https" if ssl else "http"
        self.base_url = f"{scheme}://{host}:{port}"
        self.api_url = f"{self.base_url}/{self.api_base_path}"

        logger.info("Sonarr client initialized for %s", self.base_url)

    def _make_request(self, method: str, endpoint: str,
                     params: Optional[Dict[str, Any]] = None,
                     json_data: Optional[Dict[str, Any]] = None) -> requests.Response:
        """Make a request to the Sonarr API.

        Args:
            method: HTTP method (GET, POST, PUT, etc.).
            endpoint: API endpoint (without leading slash).
            params: Query parameters.
            json_data: JSON data for POST/PUT requests.

        Returns:
            Response object.

        Raises:
            SonarrAPIError: If the request fails.
        """
        url = f"{self.api_url}/{endpoint}"

        # Add API key to parameters
        if params is None:
            params = {}
        params['apikey'] = self.api_key

        headers = {}
        if json_data is not None:
            headers['Content-Type'] = 'application/json'

        try:
            logger.debug("Making %s request to %s", method, url)
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            logger.error("Sonarr API request failed: %s", e)
            raise SonarrAPIError(f"Sonarr API request failed: {e}") from e

    def get_series(self) -> List[Series]:
        """Get all series from Sonarr.

        Returns:
            List of Series objects.
        """
        logger.debug("Fetching all series from Sonarr")
        response = self._make_request('GET', 'series')

        series_list = []
        for series_data in response.json():
            series = Series.from_sonarr_data(series_data)
            series_list.append(series)

        logger.info("Retrieved %d series from Sonarr", len(series_list))
        return series_list

    def get_series_by_id(self, series_id: int) -> Series:
        """Get a specific series by ID.

        Args:
            series_id: The series ID.

        Returns:
            Series object.
        """
        logger.debug("Fetching series %d from Sonarr", series_id)
        response = self._make_request('GET', f'series/{series_id}')
        return Series.from_sonarr_data(response.json())

    def get_episodes_by_series_id(self, series_id: int) -> List[Episode]:
        """Get all episodes for a specific series.

        Args:
            series_id: The series ID.

        Returns:
            List of Episode objects.
        """
        logger.debug("Fetching episodes for series %d", series_id)
        response = self._make_request('GET', 'episode', {'seriesId': series_id})

        episodes = []
        for episode_data in response.json():
            episode = Episode.from_sonarr_data(episode_data)
            episodes.append(episode)

        logger.debug("Retrieved %d episodes for series %d", len(episodes), series_id)
        return episodes

    def get_episode_files_by_series_id(self, series_id: int) -> List[Dict[str, Any]]:
        """Get all episode files for a specific series.

        Args:
            series_id: The series ID.

        Returns:
            List of episode file data.
        """
        logger.debug("Fetching episode files for series %d", series_id)
        response = self._make_request('GET', f'episodefile?seriesId={series_id}')
        return response.json()

    def rescan_series(self, series_id: int) -> Dict[str, Any]:
        """Trigger a rescan of a series.

        Args:
            series_id: The series ID.

        Returns:
            Command response data.
        """
        logger.debug("Triggering rescan for series %d", series_id)
        command_data = {
            "name": "RescanSeries",
            "seriesId": str(series_id)
        }

        response = self._make_request('POST', 'command', json_data=command_data)
        logger.info("Rescan triggered for series %d", series_id)
        return response.json()
