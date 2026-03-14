# utils/download.py

from dataclasses import dataclass
from typing import Optional
import requests


@dataclass
class DownloadResponse:
    status: int
    raw_response: Optional[requests.Response]


def download(url: str, config, logger) -> DownloadResponse:
    """
    Simple HTTP downloader used by crawler worker.
    Returns a response object compatible with scraper expectations.
    """
    headers = {"User-Agent": getattr(config, "user_agent", "MusicMatcherBot/1.0")}
    timeout = getattr(config, "request_timeout", 15)

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        return DownloadResponse(status=resp.status_code, raw_response=resp)
    except Exception as exc:
        logger.warning(f"Download failed for {url}: {exc}")
        return DownloadResponse(status=0, raw_response=None)
