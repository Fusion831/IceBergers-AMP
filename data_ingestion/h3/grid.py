"""
Canonical AMIP H3 Grid Generator for the Antarctic Operating Domain.
Generates all H3 cells covering Antarctica, the Southern Ocean, and the Cape Town navigation corridor.
Provides spatial scaling diagnostics, memory profiling, and configurable resolutions.
"""

import time
import sys
from typing import List, Set, Dict, Any, Optional
import h3
import pandas as pd
from core.logging import get_logger
from data_ingestion.h3.config import H3Config, default_h3_config
from data_ingestion.h3.geometry import H3GeometryEngine

logger = get_logger("data_ingestion.h3.grid")


class AntarcticH3GridGenerator:
    """
    Generates canonical H3 cells for the Antarctic operational domain:
    - Southern Ocean: -80°S to -40°S (all longitudes)
    - Cape Town to Antarctica Navigation Corridor: -40°S to -33.5°S (15°E to 25°E)
    """

    def __init__(self, config: Optional[H3Config] = None):
        self.config = config or default_h3_config
        self.geom = H3GeometryEngine()

    def generate_domain_cells(self, resolution: Optional[int] = None) -> List[str]:
        """
        Generates unique H3 cell indexes covering the Antarctic domain at specified resolution.
        """
        res = resolution if resolution is not None else self.config.resolution
        t0 = time.time()
        cells: Set[str] = set()

        # Split circum-Antarctic Southern Ocean into 4 quadrant polygons to avoid longitude wrap-around
        quadrants = [
            (self.config.primary_domain_lon_min, -90.0),
            (-90.0, 0.0),
            (0.0, 90.0),
            (90.0, self.config.primary_domain_lon_max),
        ]

        lat_min = self.config.primary_domain_lat_min
        lat_max = self.config.primary_domain_lat_max

        for q_min_lon, q_max_lon in quadrants:
            poly = h3.LatLngPoly([
                (lat_min, q_min_lon),
                (lat_max, q_min_lon),
                (lat_max, q_max_lon),
                (lat_min, q_max_lon),
            ])
            cells.update(h3.geo_to_cells(poly, res))

        # Add Cape Town Navigation Corridor (-40.0°S to -33.5°S, 15.0°E to 25.0°E)
        corridor_poly = h3.LatLngPoly([
            (self.config.corridor_lat_min, self.config.corridor_lon_min),
            (self.config.corridor_lat_max, self.config.corridor_lon_min),
            (self.config.corridor_lat_max, self.config.corridor_lon_max),
            (self.config.corridor_lat_min, self.config.corridor_lon_max),
        ])
        cells.update(h3.geo_to_cells(corridor_poly, res))

        sorted_cells = sorted(list(cells))
        t1 = time.time()

        logger.info(
            "Generated Antarctic domain H3 grid",
            resolution=res,
            total_cells=len(sorted_cells),
            generation_time_sec=round(t1 - t0, 3),
            approx_cell_area_km2=self.geom.get_approx_cell_area_km2(res),
            approx_cell_edge_km=self.geom.get_approx_cell_edge_km(res),
        )
        return sorted_cells

    def get_grid_diagnostics(self, cell_count: int, resolution: Optional[int] = None) -> Dict[str, Any]:
        """
        Emits spatial scaling and memory diagnostics for the configured grid.
        """
        res = resolution if resolution is not None else self.config.resolution
        approx_area_km2 = self.geom.get_approx_cell_area_km2(res)
        approx_edge_km = self.geom.get_approx_cell_edge_km(res)
        total_covered_area_km2 = round(cell_count * approx_area_km2, 2)

        # Estimated memory for cell table in bytes (approx 120 bytes per cell in memory)
        est_mem_bytes = cell_count * 120
        est_mem_mb = round(est_mem_bytes / (1024 * 1024), 2)

        return {
            "h3_resolution": res,
            "total_cells": cell_count,
            "approx_cell_edge_km": approx_edge_km,
            "approx_cell_area_km2": approx_area_km2,
            "total_domain_area_km2": total_covered_area_km2,
            "estimated_memory_mb": est_mem_mb,
            "domain_bounds": {
                "southern_ocean": {
                    "lat": [self.config.primary_domain_lat_min, self.config.primary_domain_lat_max],
                    "lon": [self.config.primary_domain_lon_min, self.config.primary_domain_lon_max],
                },
                "capetown_corridor": {
                    "lat": [self.config.corridor_lat_min, self.config.corridor_lat_max],
                    "lon": [self.config.corridor_lon_min, self.config.corridor_lon_max],
                },
            },
        }
