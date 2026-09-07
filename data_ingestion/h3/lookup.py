"""
Common Spatial Key and Unified Cell Lookup API for AMIP.
Provides single-point spatial-temporal queries for Routing Engine, Risk Engine, and Frontend.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import pandas as pd
from shapely.geometry import Polygon, box
from core.logging import get_logger
from data_ingestion.h3.config import H3Config, default_h3_config
from data_ingestion.h3.geometry import H3GeometryEngine
from data_ingestion.h3.schema import StaticH3Cell, DynamicH3State, UnifiedEnvironmentCell, H3GeographicStatus

logger = get_logger("data_ingestion.h3.lookup")


class H3CellLookupService:
    """
    Unified spatial-temporal query service for the AMIP canonical grid.
    Abstracts underlying Parquet partitions and geospatial operations.
    """

    def __init__(
        self,
        config: Optional[H3Config] = None,
        cells_df: Optional[pd.DataFrame] = None,
    ):
        self.config = config or default_h3_config
        self.geom = H3GeometryEngine()
        self._cells_df: Optional[pd.DataFrame] = cells_df
        self._cell_dict: Dict[str, StaticH3Cell] = {}

        if self._cells_df is not None:
            self._build_index()

    def _ensure_loaded(self) -> None:
        """Loads static cells table if not already in memory."""
        if self._cells_df is None:
            parquet_path = self.config.grid_dir / "cells.parquet"
            if not parquet_path.exists():
                raise FileNotFoundError(
                    f"Canonical cells table not found at {parquet_path}. Run static layer mapper first."
                )
            self._cells_df = pd.read_parquet(parquet_path)
            self._build_index()

    def _build_index(self) -> None:
        """Builds in-memory dictionary for O(1) cell lookup."""
        for _, row in self._cells_df.iterrows():
            c_id = str(row["cell_id"])
            self._cell_dict[c_id] = StaticH3Cell(
                cell_id=c_id,
                h3_resolution=int(row["h3_resolution"]),
                centroid_lat=float(row["centroid_lat"]),
                centroid_lon=float(row["centroid_lon"]),
                geometry_wkt=str(row.get("geometry_wkt", "")),
                ocean_fraction=float(row["ocean_fraction"]),
                land_fraction=float(row["land_fraction"]),
                ice_shelf_fraction=float(row["ice_shelf_fraction"]),
                ice_tongue_fraction=float(row["ice_tongue_fraction"]),
                rumple_fraction=float(row["rumple_fraction"]),
                geographic_status=H3GeographicStatus(row["geographic_status"]),
                is_blocked=bool(row["is_blocked"]),
                bathymetry_valid_fraction=float(row.get("bathymetry_valid_fraction", 1.0)),
                bathymetry_mean_m=float(row["bathymetry_mean_m"]) if pd.notnull(row.get("bathymetry_mean_m")) else None,
                bathymetry_min_m=float(row["bathymetry_min_m"]) if pd.notnull(row.get("bathymetry_min_m")) else None,
                bathymetry_p10_m=float(row["bathymetry_p10_m"]) if pd.notnull(row.get("bathymetry_p10_m")) else None,
                bathymetry_p50_m=float(row["bathymetry_p50_m"]) if pd.notnull(row.get("bathymetry_p50_m")) else None,
                bathymetry_p90_m=float(row["bathymetry_p90_m"]) if pd.notnull(row.get("bathymetry_p90_m")) else None,
            )

    def latlon_to_cell(self, lat: float, lon: float, resolution: Optional[int] = None) -> str:
        """Converts geographic point to canonical H3 cell index."""
        res = resolution if resolution is not None else self.config.resolution
        return self.geom.latlng_to_cell(lat, lon, res)

    def cell_to_geometry(self, cell_id: str) -> Polygon:
        """Returns cell polygon boundary in EPSG:4326."""
        return self.geom.cell_to_polygon_4326(cell_id)

    def get_cell(self, cell_id: str) -> Optional[StaticH3Cell]:
        """O(1) lookup of static cell attributes."""
        self._ensure_loaded()
        return self._cell_dict.get(cell_id)

    def neighboring_cells(self, cell_id: str, ring_size: int = 1) -> List[str]:
        """Returns neighbor cell indices for routing graph expansion."""
        neighbors = self.geom.neighboring_cells(cell_id, k=ring_size)
        # Exclude origin
        neighbors.discard(cell_id)
        return sorted(list(neighbors))

    def cells_in_bbox(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
    ) -> List[str]:
        """Queries all canonical cells intersecting bounding box."""
        self._ensure_loaded()
        sub = self._cells_df[
            (self._cells_df["centroid_lat"] >= min_lat) &
            (self._cells_df["centroid_lat"] <= max_lat) &
            (self._cells_df["centroid_lon"] >= min_lon) &
            (self._cells_df["centroid_lon"] <= max_lon)
        ]
        return sub["cell_id"].tolist()

    def is_navigable(self, cell_id: str, min_draft_clearance_m: float = 5.0) -> bool:
        """
        Evaluates physical navigability considering SCAR ADD land/shelf masks and GEBCO minimum depth.
        """
        c = self.get_cell(cell_id)
        if c is None:
            return False
        if c.is_blocked:
            return False
        if c.bathymetry_min_m is not None and c.bathymetry_min_m < min_draft_clearance_m:
            return False
        return True

    def get_environment(
        self,
        cell_id: str,
        valid_time: datetime,
    ) -> Dict[str, Any]:
        """
        Unified environmental query returning dictionary format for routing and risk engine.
        """
        static = self.get_cell(cell_id)
        if not static:
            # Generate static attributes on-the-fly if not in pre-computed table
            c_lat, c_lon = self.geom.cell_to_latlng(cell_id)
            return {
                "cell_id": cell_id,
                "valid_time": valid_time.isoformat(),
                "centroid_lat": c_lat,
                "centroid_lon": c_lon,
                "geographic_status": "OPEN_OCEAN",
                "is_navigable": True,
                "sea_ice_concentration": 0.0,
                "iceberg_hazard": 0.0,
            }

        return {
            "cell_id": cell_id,
            "valid_time": valid_time.isoformat(),
            "centroid_lat": static.centroid_lat,
            "centroid_lon": static.centroid_lon,
            "geographic_status": static.geographic_status.value,
            "ocean_fraction": static.ocean_fraction,
            "land_fraction": static.land_fraction,
            "ice_shelf_fraction": static.ice_shelf_fraction,
            "is_blocked": static.is_blocked,
            "is_navigable": self.is_navigable(cell_id),
            "bathymetry_depth_m": static.bathymetry_mean_m,
            "bathymetry_min_m": static.bathymetry_min_m,
            "sea_ice_concentration": 0.0,
            "iceberg_hazard": 0.0,
        }
