"""
Data models and constants for SCAR Antarctic Digital Database (ADD) Geographic Mask.
Provides strong type definitions for surface classification, coverage tracking,
provenance metadata, and H3 aggregation.
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class SurfaceType(str, Enum):
    """Authoritative surface types from SCAR ADD coastline polygons."""
    LAND = "land"
    ICE_SHELF = "ice shelf"
    ICE_TONGUE = "ice tongue"
    RUMPLE = "rumple"
    OCEAN = "ocean"
    UNKNOWN = "unknown"


class CoverageStatus(str, Enum):
    """Geographic source coverage status relative to ADD dataset domain."""
    INSIDE_COVERAGE = "inside_coverage"
    OUTSIDE_COVERAGE = "outside_coverage"


class GeographicQueryResult(BaseModel):
    """Result of a point or batch query against the geographic mask."""
    latitude: float
    longitude: float
    coverage_status: CoverageStatus
    surface: SurfaceType
    is_land: bool
    is_ice_shelf: bool
    is_ice_tongue: bool
    is_rumple: bool
    is_geographically_excluded: bool
    is_geographically_allowed: bool
    details: Dict[str, Any] = Field(default_factory=dict)


class H3GeographicCell(BaseModel):
    """H3 Cell aggregated geographic attributes from polygon intersection."""
    h3_index: str
    resolution: int
    centroid_lat: float
    centroid_lon: float
    coverage_status: CoverageStatus
    land_fraction: float = 0.0
    ice_shelf_fraction: float = 0.0
    ice_tongue_fraction: float = 0.0
    rumple_fraction: float = 0.0
    open_water_fraction: float = 1.0
    geographically_blocked: bool = False
    blocking_threshold: float = 0.5


class ADDDatasetMetadata(BaseModel):
    """Authoritative provenance and catalog information for SCAR ADD dataset."""
    dataset_name: str = "High resolution vector polygons of the Antarctic coastline"
    dataset_id: str = "13c4d2f1-8903-4d7f-8977-592121975554"
    edition: str = "7.12"
    publication_date: str = "12 May 2026"
    doi: str = "10.5285/13c4d2f1-8903-4d7f-8977-592121975554"
    publisher: str = "British Antarctic Survey / UK Polar Data Centre / SCAR ADD"
    native_crs: str = "EPSG:3031"
    coverage_boundary_lat: float = -60.0
    catalogue_url: str = "https://data.bas.ac.uk/items/13c4d2f1-8903-4d7f-8977-592121975554/"
    direct_gpkg_url: str = (
        "https://ramadda.data.bas.ac.uk/repository/entry/get/"
        "add_coastline_high_res_polygon_v7_12.gpkg?"
        "entryid=synth%3A13c4d2f1-8903-4d7f-8977-592121975554%3AL2FkZF9jb2FzdGxpbmVfaGlnaF9yZXNfcG9seWdvbl92N18xMi5ncGtn"
    )
    direct_shp_zip_url: str = (
        "https://ramadda.data.bas.ac.uk/repository/entry/get/"
        "add_coastline_high_res_polygon_v7_12.shp.zip?"
        "entryid=synth%3A13c4d2f1-8903-4d7f-8977-592121975554%3AL2FkZF9jb2FzdGxpbmVfaGlnaF9yZXNfcG9seWdvbl92N18xMi5zaHAuemlw"
    )
    download_format: str = "GeoPackage"
    download_timestamp: Optional[datetime] = None
    file_size_bytes: Optional[int] = None
    sha256_checksum: Optional[str] = None
    total_features: Optional[int] = None
    surface_counts: Dict[str, int] = Field(default_factory=dict)
    repaired_features: int = 0
