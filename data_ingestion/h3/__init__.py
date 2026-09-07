"""
AMIP Canonical H3 Spatial Backbone & Temporal Integration.
"""

from data_ingestion.h3.config import H3Config, default_h3_config
from data_ingestion.h3.geometry import H3GeometryEngine
from data_ingestion.h3.grid import AntarcticH3GridGenerator
from data_ingestion.h3.schema import (
    StaticH3Cell,
    DynamicH3State,
    UnifiedEnvironmentCell,
    TemporalQualityStatus,
    H3GeographicStatus,
)
from data_ingestion.h3.static_layers import H3StaticLayerMapper
from data_ingestion.h3.environmental_layers import H3EnvironmentalAggregator, circular_mean_degrees, vector_mean_components
from data_ingestion.h3.iceberg import H3IcebergIndexer
from data_ingestion.h3.hazard import H3HazardMapper
from data_ingestion.h3.ml_interface import SeaIceForecastCell, MockSeaIceMLProvider
from data_ingestion.h3.temporal import H3TemporalAligner
from data_ingestion.h3.lookup import H3CellLookupService
from data_ingestion.h3.package import H3PackageBuilder
from data_ingestion.h3.validator import H3Validator
from data_ingestion.h3.provenance import CANONICAL_DATASET_PROVENANCE, get_source_provenance

__all__ = [
    "H3Config",
    "default_h3_config",
    "H3GeometryEngine",
    "AntarcticH3GridGenerator",
    "StaticH3Cell",
    "DynamicH3State",
    "UnifiedEnvironmentCell",
    "TemporalQualityStatus",
    "H3GeographicStatus",
    "H3StaticLayerMapper",
    "H3EnvironmentalAggregator",
    "circular_mean_degrees",
    "vector_mean_components",
    "H3IcebergIndexer",
    "H3HazardMapper",
    "SeaIceForecastCell",
    "MockSeaIceMLProvider",
    "H3TemporalAligner",
    "H3CellLookupService",
    "H3PackageBuilder",
    "H3Validator",
    "CANONICAL_DATASET_PROVENANCE",
    "get_source_provenance",
]
