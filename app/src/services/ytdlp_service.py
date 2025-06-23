"""YT-DLP service for downloading videos."""
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import yt_dlp

from models import Series, Episode, DownloadResult
from utils.text_utils import escape_title_for_search


logger = logging.getLogger(__name__)


class YTDLPError(Exception):
    """Raised when YT-DLP errors occur."""
    pass


class YTDLPLogger:
    """Custom logger for YT-DLP."""

    def __init__(self):
        self.logger = logging.getLogger('yt-dlp')

    def info(self, msg: str) -> None:
        self.logger.info(msg)

    def debug(self, msg: str) -> None:
        self.logger.debug(msg)

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        self.logger.error(msg)


def ytdl_progress_hook(d: Dict[str, Any]) -> None:
    """Progress hook for YT-DLP downloads."""
    if d['status'] == 'finished':
        filename = os.path.basename(d['filename'])
        logger.info("Downloaded: %s", filename)
    elif d['status'] == 'downloading':
        if 'filename' in d and '_percent_str' in d:
            progress = f"{d['filename']} - {d['_percent_str']}"
            if '_eta_str' in d:
                progress += f" - ETA: {d['_eta_str']}"
            logger.debug(progress)


def ytdl_debug_hook(d: Dict[str, Any]) -> None:
    """Debug progress hook for YT-DLP downloads."""
    if d['status'] == 'finished':
        filename = os.path.basename(d['filename'])
        logger.info("Finished downloading: %s", filename)
    elif d['status'] == 'downloading':
        if all(key in d for key in ['filename', '_percent_str', '_eta_str']):
            logger.debug("Downloading %s - %s - %s",
                        d['filename'], d['_percent_str'], d['_eta_str'])


class YTDLPService:
    """Service for downloading videos using YT-DLP."""

    def __init__(self, default_format: str, config_dir: Path, debug: bool = False):
        """Initialize the YT-DLP service.

        Args:
            default_format: Default video format string.
            config_dir: Configuration directory for cookies files.
            debug: Enable debug logging.
        """
        self.default_format = default_format
        self.config_dir = config_dir
        self.debug = debug

        logger.info("YT-DLP service initialized with format: %s", default_format)

    def _get_search_options(self, title: str, playlist_reverse: bool = True,
                           cookies_file: Optional[str] = None) -> Dict[str, Any]:
        """Get YT-DLP options for searching videos.

        Args:
            title: Episode title to search for.
            playlist_reverse: Whether to reverse playlist order.
            cookies_file: Optional cookies file.

        Returns:
            YT-DLP options dictionary.
        """
        escaped_title = escape_title_for_search(title)

        options = {
            'ignoreerrors': True,
            'playlistreverse': playlist_reverse,
            'matchtitle': escaped_title,
            'quiet': not self.debug,
            'no_warnings': not self.debug,
        }

        if self.debug:
            options.update({
                'logger': YTDLPLogger(),
                'progress_hooks': [ytdl_debug_hook],
            })

        if cookies_file:
            cookie_path = self.config_dir / cookies_file
            if cookie_path.exists():
                options['cookiefile'] = str(cookie_path)
                logger.debug("Using cookies file: %s", cookie_path)
            else:
                logger.warning("Cookies file not found: %s", cookie_path)

        return options

    def _get_download_options(self, series: Series, episode: Episode,
                             cookies_file: Optional[str] = None) -> Dict[str, Any]:
        """Get YT-DLP options for downloading videos.

        Args:
            series: Series object.
            episode: Episode object.
            cookies_file: Optional cookies file.

        Returns:
            YT-DLP options dictionary.
        """
        # Use series-specific format or default
        video_format = series.format or self.default_format

        # Generate output filename
        output_template = (
            f'/sonarr_root{series.path}/Season {episode.season_number}/'
            f'{series.title} - S{episode.season_number:02d}E{episode.episode_number:02d} - '
            f'{episode.title} WEBDL.%(ext)s'
        )

        options = {
            'format': video_format,
            'quiet': not self.debug,
            'merge_output_format': 'mkv',
            'remux_video': 'mkv',
            'outtmpl': output_template,
            'progress_hooks': [ytdl_progress_hook if not self.debug else ytdl_debug_hook],
            'noplaylist': True,
        }

        # Add cookies if specified
        if cookies_file:
            cookie_path = self.config_dir / cookies_file
            if cookie_path.exists():
                options['cookiefile'] = str(cookie_path)

        # Add subtitle options if enabled
        if series.subtitles_enabled:
            postprocessors = [
                {
                    'key': 'FFmpegSubtitlesConvertor',
                    'format': 'srt',
                },
                {
                    'key': 'FFmpegEmbedSubtitle',
                }
            ]

            options.update({
                'writesubtitles': True,
                'allsubtitles': True,
                'writeautomaticsub': series.subtitles_autogenerated,
                'subtitleslangs': series.subtitles_languages,
                'postprocessors': postprocessors,
            })

        if self.debug:
            options.update({
                'logger': YTDLPLogger(),
            })

        return options

    def search_for_episode(self, series: Series, episode: Episode) -> Tuple[bool, str]:
        """Search for an episode video URL.

        Args:
            series: Series object.
            episode: Episode object.

        Returns:
            Tuple of (found, video_url).
        """
        if not series.url:
            logger.error("No URL configured for series: %s", series.title)
            return False, ""

        options = self._get_search_options(
            episode.title,
            series.playlist_reverse,
            series.cookies_file
        )

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                logger.debug("Searching for episode: %s - %s", series.title, episode.title)
                result = ydl.extract_info(series.url, download=False)

                if not result:
                    logger.debug("No results found for: %s", episode.title)
                    return False, ""

                video_url = None
                if 'entries' in result and result['entries']:
                    # Playlist result
                    video_url = result['entries'][0].get('webpage_url')
                else:
                    # Single video result
                    video_url = result.get('webpage_url')

                if video_url and video_url != series.url:
                    logger.debug("Found video for %s: %s", episode.title, video_url)
                    return True, video_url
                else:
                    logger.debug("No matching video found for: %s", episode.title)
                    return False, ""

        except Exception as e:
            logger.error("Error searching for episode %s: %s", episode.title, e)
            return False, ""

    def download_episode(self, series: Series, episode: Episode, video_url: str) -> DownloadResult:
        """Download an episode video.

        Args:
            series: Series object.
            episode: Episode object.
            video_url: URL of the video to download.

        Returns:
            DownloadResult object.
        """
        options = self._get_download_options(series, episode, series.cookies_file)

        try:
            logger.info("Downloading: %s - %s", series.title, episode.title)

            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([video_url])

            logger.info("Successfully downloaded: %s - %s", series.title, episode.title)
            return DownloadResult(
                success=True,
                episode=episode,
                series=series,
                video_url=video_url
            )

        except Exception as e:
            error_msg = f"Failed to download {episode.title}: {e}"
            logger.error(error_msg)
            return DownloadResult(
                success=False,
                episode=episode,
                series=series,
                video_url=video_url,
                error_message=error_msg
            )
