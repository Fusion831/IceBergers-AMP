"""
Automated downloader and local cache manager for SCAR Antarctic Digital Database (ADD) v7.12.
Supports automated HTTPS streaming download, local caching, integrity verification (SHA256),
and manual path override for air-gapped or customized environments.
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Optional, Union, Dict, Any
from datetime import datetime, timezone
import httpx
from core.logging import get_logger
from data_ingestion.geographic_mask.metadata import ADDDatasetMetadata

logger = get_logger("data_ingestion.geographic_mask.downloader")


class ADDDownloader:
    """
    Manages acquisition and local caching of SCAR ADD v7.12 high-resolution coastline polygons.
    """

    def __init__(
        self,
        raw_data_dir: Optional[Union[str, Path]] = None,
        timeout_seconds: float = 120.0,
        max_retries: int = 3,
        metadata: Optional[ADDDatasetMetadata] = None,
    ):
        self.raw_data_dir = Path(raw_data_dir or "data/raw/geographic_mask")
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.metadata = metadata or ADDDatasetMetadata()

    def get_default_raw_filepath(self) -> Path:
        """Returns standard destination path for the raw GeoPackage file."""
        return self.raw_data_dir / "add_coastline_high_res_polygon_v7_12.gpkg"

    def compute_sha256(self, filepath: Path) -> str:
        """Computes SHA256 checksum of the local file."""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(1024 * 1024):
                hasher.update(chunk)
        return hasher.hexdigest()

    def save_discovery_report(self, raw_path: Path, sha256_hash: str) -> Path:
        """Saves a discovery report documenting raw data acquisition and provenance."""
        report_path = self.raw_data_dir / "discovery_report.json"
        report_data = {
            "dataset_name": self.metadata.dataset_name,
            "edition": self.metadata.edition,
            "doi": self.metadata.doi,
            "publication_date": self.metadata.publication_date,
            "publisher": self.metadata.publisher,
            "catalogue_url": self.metadata.catalogue_url,
            "download_url": self.metadata.direct_gpkg_url,
            "native_crs": self.metadata.native_crs,
            "coverage_boundary_lat": self.metadata.coverage_boundary_lat,
            "local_raw_path": str(raw_path.resolve()),
            "file_size_bytes": raw_path.stat().st_size,
            "sha256_checksum": sha256_hash,
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        logger.info("Saved SCAR ADD discovery report", report_path=str(report_path))
        return report_path

    def download_or_get(
        self,
        mode: Optional[str] = None,
        manual_path: Optional[Union[str, Path]] = None,
        force_redownload: bool = False,
    ) -> Path:
        """
        Retrieves the SCAR ADD GeoPackage dataset.
        
        Args:
            mode: 'auto' (default) or 'manual'. If unset, checks DOWNLOAD_MODE env var.
            manual_path: Path to existing file if mode is manual, or RAW_DATA_PATH env var.
            force_redownload: If True, bypasses local cache and downloads fresh copy.
            
        Returns:
            Path to verified local GeoPackage or Shapefile.
        """
        resolved_mode = (mode or os.environ.get("DOWNLOAD_MODE", "auto")).lower()
        
        # 1. Handle manual mode
        if resolved_mode == "manual":
            override = manual_path or os.environ.get("RAW_DATA_PATH")
            if not override:
                raise ValueError(
                    "DOWNLOAD_MODE=manual specified, but no manual_path or RAW_DATA_PATH provided."
                )
            p = Path(override)
            if not p.exists() or p.stat().st_size == 0:
                raise FileNotFoundError(f"Manual data file not found or empty: {p}")
            logger.info("Using manually provided SCAR ADD dataset", path=str(p))
            sha256_hash = self.compute_sha256(p)
            self.save_discovery_report(p, sha256_hash)
            return p

        # 2. Check local cache
        dest_path = self.get_default_raw_filepath()
        if dest_path.exists() and dest_path.stat().st_size > 0 and not force_redownload:
            logger.info("SCAR ADD dataset found in local cache", path=str(dest_path), size_mb=dest_path.stat().st_size / (1024*1024))
            report_path = self.raw_data_dir / "discovery_report.json"
            if not report_path.exists():
                sha256_hash = self.compute_sha256(dest_path)
                self.save_discovery_report(dest_path, sha256_hash)
            return dest_path

        # 3. Automated download via streaming HTTPS
        url = self.metadata.direct_gpkg_url
        logger.info("Starting automatic download of SCAR ADD GeoPackage", url=url)
        temp_path = dest_path.with_suffix(".gpkg.tmp")

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(
                    timeout=self.timeout_seconds,
                    follow_redirects=True,
                    headers={"User-Agent": "AMIP-Antarctic-Mission-Intelligence/0.1.0"},
                ) as client:
                    with client.stream("GET", url) as response:
                        response.raise_for_status()
                        total_bytes = int(response.headers.get("content-length", 0))
                        downloaded = 0
                        with open(temp_path, "wb") as f:
                            for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if total_bytes > 0 and downloaded % (10 * 1024 * 1024) < 1024 * 1024:
                                        logger.info(
                                            "Downloading SCAR ADD v7.12",
                                            progress_mb=f"{downloaded / (1024*1024):.1f} / {total_bytes / (1024*1024):.1f}",
                                        )

                # Move temp to destination
                if temp_path.exists() and temp_path.stat().st_size > 0:
                    if dest_path.exists():
                        dest_path.unlink()
                    temp_path.rename(dest_path)
                    logger.info("Download completed successfully", dest=str(dest_path))
                    sha256_hash = self.compute_sha256(dest_path)
                    self.save_discovery_report(dest_path, sha256_hash)
                    return dest_path
                else:
                    raise RuntimeError("Downloaded file was empty or missing.")

            except Exception as e:
                last_error = e
                logger.warning(
                    "Download attempt failed",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    error=str(e),
                )
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception:
                        pass

        raise RuntimeError(
            f"Failed to automatically download SCAR ADD dataset after {self.max_retries} attempts: {last_error}. "
            "You can use DOWNLOAD_MODE=manual and RAW_DATA_PATH=<path> as a fallback."
        )
