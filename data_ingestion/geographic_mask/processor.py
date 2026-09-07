"""
Pipeline processor for SCAR ADD geographic mask.
Coordinates downloading, geometry validation, normalization, and saving of processed
geospatial artifacts with comprehensive provenance metadata.
"""

import json
from pathlib import Path
from typing import Optional, Union, Dict, Any
from datetime import datetime, timezone
import geopandas as gpd
from core.logging import get_logger
from data_ingestion.geographic_mask.metadata import ADDDatasetMetadata
from data_ingestion.geographic_mask.downloader import ADDDownloader
from data_ingestion.geographic_mask.reader import ADDReader
from data_ingestion.geographic_mask.validator import ADDGeometryValidator

logger = get_logger("data_ingestion.geographic_mask.processor")


class ADDProcessor:
    """Processes SCAR ADD high-resolution vector coastline dataset."""

    def __init__(
        self,
        raw_dir: Optional[Union[str, Path]] = None,
        processed_dir: Optional[Union[str, Path]] = None,
        metadata: Optional[ADDDatasetMetadata] = None,
    ):
        self.raw_dir = Path(raw_dir or "data/raw/geographic_mask")
        self.processed_dir = Path(processed_dir or "data/processed/geographic_mask")
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.metadata = metadata or ADDDatasetMetadata()
        self.downloader = ADDDownloader(raw_data_dir=self.raw_dir, metadata=self.metadata)
        self.reader = ADDReader(expected_crs=self.metadata.native_crs)
        self.validator = ADDGeometryValidator(expected_crs=self.metadata.native_crs)

    def process_pipeline(
        self,
        mode: str = "auto",
        manual_path: Optional[Union[str, Path]] = None,
        force_redownload: bool = False,
    ) -> Path:
        """
        Executes end-to-end ingestion and processing pipeline.
        
        Returns:
            Path to processed GeoPackage file.
        """
        logger.info("Starting SCAR ADD geographic mask processing pipeline")
        
        # 1. Download or retrieve raw file
        raw_filepath = self.downloader.download_or_get(
            mode=mode,
            manual_path=manual_path,
            force_redownload=force_redownload,
        )
        
        # 2. Read dataset
        raw_gdf = self.reader.read_dataset(raw_filepath)
        
        # 3. Validate and repair geometries
        self.validator.validate_crs(raw_gdf)
        cleaned_gdf, val_summary = self.validator.validate_and_repair_geometries(raw_gdf)
        
        # 4. Standardize columns
        keep_cols = ["surface", "geometry"]
        for extra in ["surface_id", "source", "name", "id"]:
            if extra in cleaned_gdf.columns:
                keep_cols.append(extra)
        available_cols = [c for c in keep_cols if c in cleaned_gdf.columns]
        processed_gdf = cleaned_gdf[available_cols].copy()
        
        # 5. Save processed GeoPackage
        processed_path = self.processed_dir / "antarctic_geographic_mask.gpkg"
        logger.info("Writing processed GeoPackage", destination=str(processed_path))
        processed_gdf.to_file(str(processed_path), driver="GPKG")
        
        # 6. Save structured provenance metadata
        provenance = {
            "dataset_name": self.metadata.dataset_name,
            "edition": self.metadata.edition,
            "doi": self.metadata.doi,
            "publisher": self.metadata.publisher,
            "publication_date": self.metadata.publication_date,
            "catalogue_url": self.metadata.catalogue_url,
            "source_download_url": self.metadata.direct_gpkg_url,
            "raw_filepath": str(raw_filepath.resolve()),
            "processed_filepath": str(processed_path.resolve()),
            "native_crs": self.metadata.native_crs,
            "coverage_boundary_latitude": self.metadata.coverage_boundary_lat,
            "total_features": len(processed_gdf),
            "surface_distribution": val_summary["surface_counts"],
            "validation_metrics": val_summary,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "pipeline_version": "1.0.0",
        }
        provenance_path = self.processed_dir / "provenance.json"
        with open(provenance_path, "w", encoding="utf-8") as f:
            json.dump(provenance, f, indent=2)
        logger.info("Saved provenance metadata", provenance_path=str(provenance_path))
        
        return processed_path
