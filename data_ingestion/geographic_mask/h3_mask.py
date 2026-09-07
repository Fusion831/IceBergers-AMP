"""
H3 Polygon Intersection and Area Fraction Aggregator for Antarctic Geographic Mask.
Calculates precise fractional coverage (land, ice shelf, ice tongue, rumple, open water)
per H3 cell using spatial polygon intersections in native EPSG:3031 projection.
"""

from typing import List, Dict, Any, Optional, Union, Sequence
import h3
import pyproj
from shapely.geometry import Polygon
from shapely.ops import unary_union
import geopandas as gpd
from core.logging import get_logger
from data_ingestion.geographic_mask.metadata import (
    H3GeographicCell,
    CoverageStatus,
)
from data_ingestion.geographic_mask.interface import AntarcticGeographicMask

logger = get_logger("data_ingestion.geographic_mask.h3_mask")


class H3GeographicMaskAggregator:
    """
    Computes H3-cell geographic attributes from SCAR ADD polygon intersections.
    Configurable by H3 resolution, domain, and blocking threshold.
    """

    def __init__(
        self,
        mask: AntarcticGeographicMask,
        default_blocking_threshold: float = 0.5,
    ):
        self.mask = mask
        self.default_blocking_threshold = default_blocking_threshold
        self.to_epsg3031 = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3031", always_xy=True)

    def h3_to_polygon_3031(self, cell_id: str) -> Polygon:
        """
        Converts an H3 cell index to a Shapely Polygon projected in EPSG:3031 coordinates.
        """
        # h3 v4 returns tuple of (lat, lng) pairs
        boundary_lat_lng = h3.cell_to_boundary(cell_id)
        # Transform (lng, lat) -> (x, y) in EPSG:3031
        coords_3031 = [
            self.to_epsg3031.transform(lng, lat)
            for lat, lng in boundary_lat_lng
        ]
        return Polygon(coords_3031)

    def compute_cell_attributes(
        self,
        cell_id: str,
        blocking_threshold: Optional[float] = None,
    ) -> H3GeographicCell:
        """
        Calculates exact fractional coverage for a single H3 cell via polygon intersection.
        """
        threshold = blocking_threshold if blocking_threshold is not None else self.default_blocking_threshold
        centroid_lat, centroid_lon = h3.cell_to_latlng(cell_id)
        resolution = h3.get_resolution(cell_id)
        cov_status = self.mask.coverage_status(centroid_lat, centroid_lon)

        # If centroid is north of 60°S, mark OUTSIDE_COVERAGE
        if cov_status == CoverageStatus.OUTSIDE_COVERAGE:
            return H3GeographicCell(
                h3_index=cell_id,
                resolution=resolution,
                centroid_lat=centroid_lat,
                centroid_lon=centroid_lon,
                coverage_status=CoverageStatus.OUTSIDE_COVERAGE,
                land_fraction=0.0,
                ice_shelf_fraction=0.0,
                ice_tongue_fraction=0.0,
                rumple_fraction=0.0,
                open_water_fraction=1.0,
                geographically_blocked=False,
                blocking_threshold=threshold,
            )

        cell_poly = self.h3_to_polygon_3031(cell_id)
        cell_area = cell_poly.area
        if cell_area <= 0:
            return H3GeographicCell(
                h3_index=cell_id,
                resolution=resolution,
                centroid_lat=centroid_lat,
                centroid_lon=centroid_lon,
                coverage_status=CoverageStatus.INSIDE_COVERAGE,
                land_fraction=0.0,
                ice_shelf_fraction=0.0,
                ice_tongue_fraction=0.0,
                rumple_fraction=0.0,
                open_water_fraction=1.0,
                geographically_blocked=False,
                blocking_threshold=threshold,
            )

        # Query candidate polygons intersecting cell bounding box
        candidate_indices = self.mask.tree.query(cell_poly, predicate="intersects")
        if len(candidate_indices) == 0:
            # Entirely open water
            return H3GeographicCell(
                h3_index=cell_id,
                resolution=resolution,
                centroid_lat=centroid_lat,
                centroid_lon=centroid_lon,
                coverage_status=CoverageStatus.INSIDE_COVERAGE,
                land_fraction=0.0,
                ice_shelf_fraction=0.0,
                ice_tongue_fraction=0.0,
                rumple_fraction=0.0,
                open_water_fraction=1.0,
                geographically_blocked=False,
                blocking_threshold=threshold,
            )

        # Group intersections by surface category
        surface_areas = {"land": 0.0, "ice shelf": 0.0, "ice tongue": 0.0, "rumple": 0.0}

        for idx in candidate_indices:
            poly = self.mask.geometries[idx]
            surf_str = self.mask.surfaces[idx]
            if surf_str in surface_areas:
                inter = cell_poly.intersection(poly)
                if not inter.is_empty:
                    surface_areas[surf_str] += inter.area

        land_f = min(1.0, max(0.0, surface_areas["land"] / cell_area))
        ice_shelf_f = min(1.0, max(0.0, surface_areas["ice shelf"] / cell_area))
        ice_tongue_f = min(1.0, max(0.0, surface_areas["ice tongue"] / cell_area))
        rumple_f = min(1.0, max(0.0, surface_areas["rumple"] / cell_area))
        
        total_blocked_fraction = min(1.0, land_f + ice_shelf_f + ice_tongue_f + rumple_f)
        open_water_f = max(0.0, 1.0 - total_blocked_fraction)
        
        is_blocked = total_blocked_fraction >= threshold

        return H3GeographicCell(
            h3_index=cell_id,
            resolution=resolution,
            centroid_lat=centroid_lat,
            centroid_lon=centroid_lon,
            coverage_status=CoverageStatus.INSIDE_COVERAGE,
            land_fraction=round(land_f, 4),
            ice_shelf_fraction=round(ice_shelf_f, 4),
            ice_tongue_fraction=round(ice_tongue_f, 4),
            rumple_fraction=round(rumple_f, 4),
            open_water_fraction=round(open_water_f, 4),
            geographically_blocked=is_blocked,
            blocking_threshold=threshold,
        )

    def aggregate_cells(
        self,
        cell_ids: Sequence[str],
        blocking_threshold: Optional[float] = None,
    ) -> List[H3GeographicCell]:
        """
        Batch aggregates geographic attributes across multiple H3 cells.
        """
        results = []
        for cell_id in cell_ids:
            results.append(self.compute_cell_attributes(cell_id, blocking_threshold))
        return results
