"""
Automated downloader and local cache manager for BYU and USNIC Antarctic iceberg datasets.
Supports streaming downloads, SHA256 verification, zip extraction, and manual override paths.
"""

import os
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Optional, Union, Dict, Any, Tuple
from datetime import datetime, timezone
import httpx
from core.logging import get_logger

logger = get_logger("data_ingestion.iceberg.downloader")

BYU_CONSOLIDATED_ZIP_URL = "https://www.scp.byu.edu/iceberg/consolidated_database_v8.0.zip"
USNIC_CURRENT_CSV_URL = "https://usicecenter.gov/File/DownloadCurrent?pId=134"
USNIC_CURRENT_SHP_URL = "https://usicecenter.gov/File/DownloadCurrent?pId=228"


class IcebergDownloader:
    """Manages acquisition and local caching of Antarctic iceberg datasets."""

    def __init__(
        self,
        base_raw_dir: Optional[Union[str, Path]] = None,
        timeout_seconds: float = 60.0,
    ):
        self.base_raw_dir = Path(base_raw_dir or "data/raw/iceberg")
        self.byu_raw_dir = self.base_raw_dir / "byu"
        self.usnic_raw_dir = self.base_raw_dir / "usnic"
        self.byu_raw_dir.mkdir(parents=True, exist_ok=True)
        self.usnic_raw_dir.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = timeout_seconds

    def compute_sha256(self, filepath: Path) -> str:
        """Computes SHA256 hash of a file."""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(1024 * 1024):
                hasher.update(chunk)
        return hasher.hexdigest()

    def download_byu_historical(
        self,
        mode: str = "auto",
        manual_path: Optional[Union[str, Path]] = None,
        force_redownload: bool = False,
    ) -> Path:
        """
        Downloads and unpacks BYU consolidated database v8.0.
        Returns the path to the directory containing individual iceberg CSV files.
        """
        resolved_mode = (mode or os.environ.get("DOWNLOAD_MODE", "auto")).lower()
        if resolved_mode == "manual":
            override = manual_path or os.environ.get("BYU_RAW_DATA_PATH")
            if not override:
                raise ValueError("DOWNLOAD_MODE=manual specified but no BYU path provided.")
            p = Path(override)
            if not p.exists():
                raise FileNotFoundError(f"Manual BYU file not found: {p}")
            return p

        zip_dest = self.byu_raw_dir / "consolidated_database_v8.0.zip"
        extract_dir = self.byu_raw_dir / "extracted"

        # Check local cache
        if zip_dest.exists() and zip_dest.stat().st_size > 0 and extract_dir.exists() and not force_redownload:
            logger.info("BYU database found in local cache", path=str(zip_dest))
            return extract_dir

        logger.info("Downloading BYU consolidated database", url=BYU_CONSOLIDATED_ZIP_URL)
        temp_zip = zip_dest.with_suffix(".tmp")
        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
            resp = client.get(BYU_CONSOLIDATED_ZIP_URL)
            resp.raise_for_status()
            with open(temp_zip, "wb") as f:
                f.write(resp.content)

        if temp_zip.exists():
            if zip_dest.exists():
                zip_dest.unlink()
            temp_zip.rename(zip_dest)

        sha256_hash = self.compute_sha256(zip_dest)
        logger.info("Extracting BYU consolidated database", dest=str(extract_dir))
        with zipfile.ZipFile(zip_dest, "r") as z:
            z.extractall(extract_dir)

        # Write discovery report
        report = {
            "source": "BYU MERS Antarctic Iceberg Tracking Database",
            "version": "v8.0",
            "source_url": BYU_CONSOLIDATED_ZIP_URL,
            "download_timestamp": datetime.now(timezone.utc).isoformat(),
            "file_size_bytes": zip_dest.stat().st_size,
            "sha256": sha256_hash,
            "local_zip_path": str(zip_dest.resolve()),
            "extracted_path": str(extract_dir.resolve()),
        }
        with open(self.byu_raw_dir / "discovery_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return extract_dir

    def download_usnic_operational(
        self,
        mode: str = "auto",
        manual_path: Optional[Union[str, Path]] = None,
        force_redownload: bool = False,
    ) -> Path:
        """
        Downloads current USNIC operational Antarctic iceberg CSV.
        Returns the path to the local CSV file.
        """
        resolved_mode = (mode or os.environ.get("DOWNLOAD_MODE", "auto")).lower()
        if resolved_mode == "manual":
            override = manual_path or os.environ.get("USNIC_RAW_DATA_PATH")
            if not override:
                raise ValueError("DOWNLOAD_MODE=manual specified but no USNIC path provided.")
            p = Path(override)
            if not p.exists():
                raise FileNotFoundError(f"Manual USNIC file not found: {p}")
            return p

        # Check existing CSVs in usnic dir
        existing_csvs = list(self.usnic_raw_dir.glob("AntarcticIcebergs_*.csv"))
        if existing_csvs and not force_redownload:
            logger.info("USNIC operational CSV found in local cache", path=str(existing_csvs[0]))
            return existing_csvs[0]

        logger.info("Downloading USNIC operational Antarctic icebergs CSV", url=USNIC_CURRENT_CSV_URL)
        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True, verify=False) as client:
            resp = client.get(USNIC_CURRENT_CSV_URL)
            resp.raise_for_status()

            # Parse filename from content-disposition header if available
            cd = resp.headers.get("Content-Disposition", "")
            filename = "AntarcticIcebergs_current.csv"
            if "filename=" in cd:
                parts = cd.split("filename=")
                filename = parts[1].split(";")[0].strip("\"' ")

            dest = self.usnic_raw_dir / filename
            with open(dest, "wb") as f:
                f.write(resp.content)

        sha256_hash = self.compute_sha256(dest)
        report = {
            "source": "U.S. National Ice Center (USNIC)",
            "product": "Antarctic Iceberg Observations",
            "source_url": USNIC_CURRENT_CSV_URL,
            "filename": filename,
            "download_timestamp": datetime.now(timezone.utc).isoformat(),
            "file_size_bytes": dest.stat().st_size,
            "sha256": sha256_hash,
            "local_path": str(dest.resolve()),
        }
        with open(self.usnic_raw_dir / "discovery_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return dest
