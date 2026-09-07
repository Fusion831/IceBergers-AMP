"""
Programmatic HTTPS Downloader for NOAA@NSIDC G02202 v6 Sea-Ice Concentration.
Follows current NOAA@NSIDC HTTPS directory structure with robust retry logic,
streaming downloads, and non-destructive caching.
"""

from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Optional, Union
import re
import time
import httpx
from core.logging import get_logger

logger = get_logger("data_ingestion.nsidc.downloader")

NSIDC_NOAA_HTTPS_BASE = "https://noaadata.apps.nsidc.org/NOAA/G02202_V6"
ANCILLARY_FILENAME = "G02202-ancillary-pss25-v06r00.nc"

# Default satellite sensors by historical epoch
def get_default_sensor_for_year(year: int) -> str:
    if year >= 2008:
        return "F17"
    elif year >= 1995:
        return "F13"
    elif year >= 1991:
        return "F11"
    elif year >= 1987:
        return "F08"
    else:
        return "N07"


class NSIDCDownloader:
    """
    Downloads NOAA/NSIDC Climate Data Record v6 Sea Ice Concentration files
    via HTTPS from the official NOAA@NSIDC data repository.
    """

    def __init__(
        self,
        base_url: str = NSIDC_NOAA_HTTPS_BASE,
        raw_data_dir: Optional[Union[str, Path]] = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.raw_data_dir = Path(raw_data_dir or "data/raw/nsidc/g02202")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.client = httpx.Client(
            timeout=self.timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": "AMIP-Antarctic-Mission-Intelligence/0.1.0"},
        )

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_ancillary_url(self) -> str:
        """Returns the HTTPS URL for the 25km Southern Hemisphere ancillary file."""
        return f"{self.base_url}/ancillary/{ANCILLARY_FILENAME}"

    def get_daily_url(self, target_date: date, sensor: Optional[str] = None) -> str:
        """Returns the HTTPS URL for a specific daily G02202 Southern Hemisphere file."""
        sensor = sensor or get_default_sensor_for_year(target_date.year)
        date_str = target_date.strftime("%Y%m%d")
        filename = f"sic_pss25_{date_str}_{sensor}_v06r00.nc"
        return f"{self.base_url}/south/daily/{target_date.year}/{filename}"

    def download_file(
        self,
        url: str,
        destination_path: Path,
        force_redownload: bool = False,
    ) -> Path:
        """
        Download a file with exponential backoff retries and integrity validation.
        Preserves existing files unless force_redownload is True.
        """
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        if destination_path.exists() and destination_path.stat().st_size > 0 and not force_redownload:
            logger.info("File already exists, skipping download", path=str(destination_path))
            return destination_path

        temp_path = destination_path.with_suffix(destination_path.suffix + ".tmp")
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info("Downloading file from NSIDC", url=url, attempt=attempt)
                with self.client.stream("GET", url) as response:
                    if response.status_code == 404:
                        raise FileNotFoundError(f"File not found on NSIDC server (404): {url}")
                    response.raise_for_status()

                    content_length = int(response.headers.get("content-length", 0))
                    bytes_received = 0

                    with open(temp_path, "wb") as f:
                        for chunk in response.iter_bytes(chunk_size=65536):
                            f.write(chunk)
                            bytes_received += len(chunk)

                if bytes_received == 0:
                    raise ValueError(f"Downloaded empty file from {url}")

                if content_length > 0 and bytes_received != content_length:
                    raise IOError(
                        f"Incomplete download: expected {content_length} bytes, got {bytes_received}"
                    )

                # Move temp file to final destination atomically
                if destination_path.exists():
                    destination_path.unlink()
                temp_path.rename(destination_path)
                logger.info("Download completed successfully", path=str(destination_path), size=bytes_received)
                return destination_path

            except Exception as e:
                last_error = e
                logger.warning("Download attempt failed", attempt=attempt, error=str(e), url=url)
                if temp_path.exists():
                    temp_path.unlink(missing_ok=True)
                if attempt < self.max_retries:
                    sleep_time = 2.0 ** attempt
                    time.sleep(sleep_time)

        raise IOError(f"Failed to download {url} after {self.max_retries} attempts: {last_error}")

    def download_ancillary(self, force_redownload: bool = False) -> Path:
        """Download the official NSIDC 25km Southern Hemisphere ancillary reference file."""
        url = self.get_ancillary_url()
        dest = self.raw_data_dir / "ancillary" / ANCILLARY_FILENAME
        return self.download_file(url, dest, force_redownload=force_redownload)

    def download_daily(
        self,
        target_date: Union[date, datetime],
        sensor: Optional[str] = None,
        force_redownload: bool = False,
    ) -> Path:
        """Download a single daily Antarctic G02202 file."""
        d = target_date.date() if isinstance(target_date, datetime) else target_date
        url = self.get_daily_url(d, sensor=sensor)
        filename = Path(url).name
        dest = self.raw_data_dir / str(d.year) / filename
        return self.download_file(url, dest, force_redownload=force_redownload)

    def download_date_range(
        self,
        start_date: Union[date, datetime],
        end_date: Union[date, datetime],
        sensor: Optional[str] = None,
        force_redownload: bool = False,
    ) -> List[Path]:
        """
        Download daily Antarctic G02202 files for a given date range (inclusive).
        """
        d_start = start_date.date() if isinstance(start_date, datetime) else start_date
        d_end = end_date.date() if isinstance(end_date, datetime) else end_date

        if d_end < d_start:
            raise ValueError(f"end_date ({d_end}) must be >= start_date ({d_start})")

        downloaded_paths = []
        curr = d_start
        while curr <= d_end:
            try:
                path = self.download_daily(curr, sensor=sensor, force_redownload=force_redownload)
                downloaded_paths.append(path)
            except FileNotFoundError as e:
                logger.warning("Daily file unavailable on server", date=str(curr), error=str(e))
            curr += timedelta(days=1)

        return downloaded_paths


def download_nsidc(
    dataset: str = "G02202",
    start_date: Union[str, date, datetime] = "2024-01-01",
    end_date: Union[str, date, datetime] = "2024-01-07",
    destination: Optional[Union[str, Path]] = None,
) -> List[Path]:
    """
    Convenience function matching the conceptual download_nsidc interface:
    download_nsidc(dataset="G02202", start_date=..., end_date=..., destination=...)
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    with NSIDCDownloader(raw_data_dir=destination) as downloader:
        # Also ensure ancillary file is present
        downloader.download_ancillary()
        return downloader.download_date_range(start_date, end_date)
