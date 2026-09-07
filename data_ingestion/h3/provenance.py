"""
Provenance tracking and metadata schemas for H3 integration.
Maintains granular source attribution, versions, and aggregation methods.
"""

from typing import Dict, Any


CANONICAL_DATASET_PROVENANCE = {
    "nsidc": {
        "dataset_name": "NSIDC NOAA/NSIDC Climate Data Record of Passive Microwave Sea Ice Concentration",
        "dataset_id": "NSIDC_G02202_v6",
        "version": "v06r00",
        "native_grid": "25km Polar Stereographic South (EPSG:3412)",
        "spatial_aggregation": "Valid-pixel area mean (excluding land/coast/missing flags)",
        "temporal_alignment": "Daily observation persisted over 24h cycle",
    },
    "cmems_currents": {
        "dataset_name": "Copernicus Marine Global Ocean Physics Analysis and Forecast",
        "dataset_id": "CMEMS_GLOBAL_ANALYSISFORECAST_PHY_001_024",
        "version": "PHY-001-024",
        "native_grid": "0.083° x 0.083° Geographic Regular Lat/Lon",
        "spatial_aggregation": "Direct vector component mean: mean(u), mean(v)",
        "temporal_alignment": "Native 6-hourly direct alignment",
    },
    "cmems_waves": {
        "dataset_name": "Copernicus Marine Global Ocean Waves Analysis and Forecast",
        "dataset_id": "CMEMS_GLOBAL_ANALYSISFORECAST_WAV_001_027",
        "version": "WAV-001-027",
        "native_grid": "0.083° x 0.083° Geographic Regular Lat/Lon",
        "spatial_aggregation": "Scalar mean for Hs/Tp; circular vector averaging for wave direction",
        "temporal_alignment": "3-hourly sampled at 6h stride",
    },
    "ecmwf": {
        "dataset_name": "ECMWF Open Data High-Resolution Atmospheric Forecast",
        "dataset_id": "ECMWF_Open_Data",
        "version": "IFS 0.4°/0.25°",
        "native_grid": "0.4° Gaussian / Regular Lat/Lon",
        "spatial_aggregation": "Direct vector component mean: mean(10u), mean(10v)",
        "temporal_alignment": "0-48h NWP forecast aligned to valid timestamps",
    },
    "gebco": {
        "dataset_name": "GEBCO 2026 Sub-Ice Topography and Bathymetry Grid",
        "dataset_id": "GEBCO_2026",
        "version": "2026 Release (BODC / CEDA)",
        "native_grid": "15 arc-second Global Grid",
        "spatial_aggregation": "Multi-point depth sampling (mean, min, p10, p50, p90)",
        "sign_convention": "Positive water depth (depth_m > 0)",
        "temporal_alignment": "Static",
    },
    "scar_add": {
        "dataset_name": "SCAR Antarctic Digital Database High-Resolution Coastline",
        "dataset_id": "SCAR_ADD_v7.12",
        "version": "v7.12 (2024 Release)",
        "native_grid": "Native Vector Polygons in EPSG:3031",
        "spatial_aggregation": "Exact polygon intersection area weighting in EPSG:3031",
        "temporal_alignment": "Static",
    },
    "byu_icebergs": {
        "dataset_name": "BYU Antarctic Iceberg Tracking Database",
        "dataset_id": "BYU",
        "version": "Historical 1978-2026 (42,431 records, 40 icebergs)",
        "geometry": "Exact point coordinates (preserved)",
        "spatial_indexing": "Discrete H3 cell index",
    },
    "usnic_icebergs": {
        "dataset_name": "U.S. National Ice Center Operational Antarctic Iceberg Positions",
        "dataset_id": "USNIC",
        "version": "Operational September 2026 (33 records, 33 icebergs)",
        "geometry": "Exact point coordinates (preserved)",
        "spatial_indexing": "Discrete H3 cell index",
    },
}


def get_source_provenance(source_key: str) -> Dict[str, Any]:
    """Returns provenance metadata dictionary for a specific dataset source."""
    return CANONICAL_DATASET_PROVENANCE.get(source_key, {"dataset_id": source_key, "provenance": "AMIP_CUSTOM"})
