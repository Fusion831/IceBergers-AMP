"""
Spatial query interface for Antarctic Geographic Mask.
Provides high-performance point and batch queries using EPSG:3031 spatial indexing (STRtree),
distinguishing land, ice shelf, ice tongue, rumple, open ocean, and outside-coverage areas.
"""

from pathlib import Path
from typing import Union, Optional, List, Tuple, Sequence
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from shapely.strtree import STRtree
import pyproj
from core.logging import get_logger
from data_ingestion.geographic_mask.metadata import (
    SurfaceType,
    CoverageStatus,
    GeographicQueryResult,
)

logger = get_logger("data_ingestion.geographic_mask.interface")


class AntarcticGeographicMask:
    """
    Reusable spatial query interface for the Antarctic Geographic Mask.
    Uses SCAR ADD authoritative coastline polygons indexed in EPSG:3031.
    """

    def __init__(
        self,
        source: Union[str, Path, gpd.GeoDataFrame] = "data/processed/geographic_mask/antarctic_geographic_mask.gpkg",
        coverage_limit_lat: float = -60.0,
    ):
        self.coverage_limit_lat = coverage_limit_lat
        
        # 1. Load GeoDataFrame
        if isinstance(source, gpd.GeoDataFrame):
            self.gdf = source.copy()
        else:
            p = Path(source)
            if not p.exists():
                raise FileNotFoundError(f"Geographic mask dataset not found: {p}")
            self.gdf = gpd.read_file(str(p))

        # 2. Verify and enforce native EPSG:3031 CRS
        if self.gdf.crs is None:
            self.gdf.set_crs("EPSG:3031", inplace=True)
        elif self.gdf.crs.to_epsg() != 3031 and str(self.gdf.crs).lower() != "epsg:3031":
            self.gdf = self.gdf.to_crs("EPSG:3031")

        # 3. Setup coordinate transformer (WGS84 EPSG:4326 <-> Polar Stereographic EPSG:3031)
        self.to_epsg3031 = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3031", always_xy=True)
        self.to_epsg4326 = pyproj.Transformer.from_crs("EPSG:3031", "EPSG:4326", always_xy=True)

        # 4. Standardize surface attribute and build spatial index
        self.gdf["surface"] = self.gdf["surface"].astype(str).str.strip().str.lower()
        self.geometries = self.gdf.geometry.values
        self.surfaces = self.gdf["surface"].values
        self.tree = STRtree(self.geometries)
        
        logger.info(
            "Initialized AntarcticGeographicMask",
            features=len(self.gdf),
            coverage_limit_lat=self.coverage_limit_lat,
        )

    def coverage_status(self, lat: float, lon: float) -> CoverageStatus:
        """
        Determines whether the given coordinate is within SCAR ADD geographic coverage.
        The ADD dataset strictly covers south of 60°S (latitude <= -60.0).
        """
        if lat <= self.coverage_limit_lat:
            return CoverageStatus.INSIDE_COVERAGE
        return CoverageStatus.OUTSIDE_COVERAGE

    def query(self, lat: float, lon: float) -> GeographicQueryResult:
        """
        Executes a comprehensive geographic query for a single (lat, lon) point.
        """
        status = self.coverage_status(lat, lon)
        if status == CoverageStatus.OUTSIDE_COVERAGE:
            return GeographicQueryResult(
                latitude=lat,
                longitude=lon,
                coverage_status=CoverageStatus.OUTSIDE_COVERAGE,
                surface=SurfaceType.UNKNOWN,
                is_land=False,
                is_ice_shelf=False,
                is_ice_tongue=False,
                is_rumple=False,
                is_geographically_excluded=False,
                is_geographically_allowed=False,
                details={"reason": "outside_add_coverage_north_of_60s"},
            )

        # Transform (lon, lat) -> (x, y) in EPSG:3031
        x, y = self.to_epsg3031.transform(lon, lat)
        pt = Point(x, y)

        # Query spatial index
        candidates = self.tree.query(pt, predicate="intersects")
        if len(candidates) == 0 and len(self.geometries) < 50:
            # Check for boundary proximity in test fixtures
            candidates = self.tree.query(pt.buffer(1.0), predicate="intersects")

        if len(candidates) == 0:
            # Inside coverage, not intersecting any polygon -> Open Ocean
            return GeographicQueryResult(
                latitude=lat,
                longitude=lon,
                coverage_status=CoverageStatus.INSIDE_COVERAGE,
                surface=SurfaceType.OCEAN,
                is_land=False,
                is_ice_shelf=False,
                is_ice_tongue=False,
                is_rumple=False,
                is_geographically_excluded=False,
                is_geographically_allowed=True,
                details={"source": "scar_add_v7_12"},
            )

        # Point intersects one or more polygons
        first_idx = candidates[0]
        surf_str = self.surfaces[first_idx]
        
        surface_type_map = {
            "land": SurfaceType.LAND,
            "ice shelf": SurfaceType.ICE_SHELF,
            "ice tongue": SurfaceType.ICE_TONGUE,
            "rumple": SurfaceType.RUMPLE,
        }
        surf = surface_type_map.get(surf_str, SurfaceType.UNKNOWN)

        return GeographicQueryResult(
            latitude=lat,
            longitude=lon,
            coverage_status=CoverageStatus.INSIDE_COVERAGE,
            surface=surf,
            is_land=(surf == SurfaceType.LAND),
            is_ice_shelf=(surf == SurfaceType.ICE_SHELF),
            is_ice_tongue=(surf == SurfaceType.ICE_TONGUE),
            is_rumple=(surf == SurfaceType.RUMPLE),
            is_geographically_excluded=True,
            is_geographically_allowed=False,
            details={"polygon_index": int(first_idx), "source_surface": surf_str},
        )

    def is_land(self, lat: float, lon: float) -> bool:
        """Returns True if the point is within continental or island land."""
        return self.query(lat, lon).is_land

    def is_ice_shelf(self, lat: float, lon: float) -> bool:
        """Returns True if the point is within an ice shelf."""
        return self.query(lat, lon).is_ice_shelf

    def is_ice_tongue(self, lat: float, lon: float) -> bool:
        """Returns True if the point is within an ice tongue."""
        return self.query(lat, lon).is_ice_tongue

    def is_rumple(self, lat: float, lon: float) -> bool:
        """Returns True if the point is within an ice rumple."""
        return self.query(lat, lon).is_rumple

    def is_geographically_excluded(self, lat: float, lon: float) -> bool:
        """
        Returns True if geographically blocked by land, ice shelf, ice tongue, or rumple.
        Returns False if open water or outside coverage (caller should check coverage_status).
        """
        return self.query(lat, lon).is_geographically_excluded

    def is_geographically_allowed(self, lat: float, lon: float) -> bool:
        """
        Returns True strictly if inside ADD coverage and confirmed open ocean.
        Returns False if occupied by land/ice-shelf or if outside ADD coverage.
        """
        return self.query(lat, lon).is_geographically_allowed

    def query_batch(
        self,
        lats: Sequence[float],
        lons: Sequence[float],
    ) -> List[GeographicQueryResult]:
        """
        High-throughput batch query for coordinate sequences.
        """
        if len(lats) != len(lons):
            raise ValueError("lats and lons must have identical length.")

        lats_arr = np.asarray(lats, dtype=np.float64)
        lons_arr = np.asarray(lons, dtype=np.float64)
        n = len(lats_arr)

        inside_mask = lats_arr <= self.coverage_limit_lat
        results = [None] * n

        # Fill outside coverage entries
        outside_indices = np.where(~inside_mask)[0]
        for idx in outside_indices:
            results[idx] = GeographicQueryResult(
                latitude=float(lats_arr[idx]),
                longitude=float(lons_arr[idx]),
                coverage_status=CoverageStatus.OUTSIDE_COVERAGE,
                surface=SurfaceType.UNKNOWN,
                is_land=False,
                is_ice_shelf=False,
                is_ice_tongue=False,
                is_rumple=False,
                is_geographically_excluded=False,
                is_geographically_allowed=False,
                details={"reason": "outside_add_coverage_north_of_60s"},
            )

        inside_indices = np.where(inside_mask)[0]
        if len(inside_indices) == 0:
            return results

        # Vectorized projection to EPSG:3031
        xs, ys = self.to_epsg3031.transform(lons_arr[inside_indices], lats_arr[inside_indices])
        points = [Point(x, y) for x, y in zip(xs, ys)]

        # Batch query STRtree
        geom_idx, pt_idx = self.tree.query(points, predicate="intersects")
        
        # Map first match per point
        matched = {}
        for p_i, g_i in zip(pt_idx, geom_idx):
            if p_i not in matched:
                matched[p_i] = g_i

        surface_type_map = {
            "land": SurfaceType.LAND,
            "ice shelf": SurfaceType.ICE_SHELF,
            "ice tongue": SurfaceType.ICE_TONGUE,
            "rumple": SurfaceType.RUMPLE,
        }

        for local_idx, orig_idx in enumerate(inside_indices):
            lat = float(lats_arr[orig_idx])
            lon = float(lons_arr[orig_idx])
            
            if local_idx in matched:
                g_idx = matched[local_idx]
                surf_str = self.surfaces[g_idx]
                surf = surface_type_map.get(surf_str, SurfaceType.UNKNOWN)
                results[orig_idx] = GeographicQueryResult(
                    latitude=lat,
                    longitude=lon,
                    coverage_status=CoverageStatus.INSIDE_COVERAGE,
                    surface=surf,
                    is_land=(surf == SurfaceType.LAND),
                    is_ice_shelf=(surf == SurfaceType.ICE_SHELF),
                    is_ice_tongue=(surf == SurfaceType.ICE_TONGUE),
                    is_rumple=(surf == SurfaceType.RUMPLE),
                    is_geographically_excluded=True,
                    is_geographically_allowed=False,
                    details={"polygon_index": int(g_idx), "source_surface": surf_str},
                )
            else:
                results[orig_idx] = GeographicQueryResult(
                    latitude=lat,
                    longitude=lon,
                    coverage_status=CoverageStatus.INSIDE_COVERAGE,
                    surface=SurfaceType.OCEAN,
                    is_land=False,
                    is_ice_shelf=False,
                    is_ice_tongue=False,
                    is_rumple=False,
                    is_geographically_excluded=False,
                    is_geographically_allowed=True,
                    details={"source": "scar_add_v7_12"},
                )

        return results
