"""
AMIP Antarctic Geographic Mask Package.
Ingestion, validation, spatial indexing, H3 aggregation, and visualization
for SCAR Antarctic Digital Database (ADD) v7.12 coastline polygons.
"""

from data_ingestion.geographic_mask.metadata import (
    SurfaceType,
    CoverageStatus,
    GeographicQueryResult,
    H3GeographicCell,
    ADDDatasetMetadata,
)
from data_ingestion.geographic_mask.downloader import ADDDownloader
from data_ingestion.geographic_mask.reader import ADDReader
from data_ingestion.geographic_mask.validator import ADDGeometryValidator
from data_ingestion.geographic_mask.processor import ADDProcessor
from data_ingestion.geographic_mask.interface import AntarcticGeographicMask
from data_ingestion.geographic_mask.h3_mask import H3GeographicMaskAggregator
from data_ingestion.geographic_mask.visualizer import GeographicMaskVisualizer

__all__ = [
    "SurfaceType",
    "CoverageStatus",
    "GeographicQueryResult",
    "H3GeographicCell",
    "ADDDatasetMetadata",
    "ADDDownloader",
    "ADDReader",
    "ADDGeometryValidator",
    "ADDProcessor",
    "AntarcticGeographicMask",
    "H3GeographicMaskAggregator",
    "GeographicMaskVisualizer",
]
