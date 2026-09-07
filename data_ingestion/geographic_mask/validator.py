"""
Geometry and attribute validation for SCAR ADD geographic mask.
Ensures topological validity, repairs non-destructive self-intersections,
verifies CRS definition, and checks surface attribute fidelity.
"""

from typing import Tuple, Dict, Any
import geopandas as gpd
from shapely.validation import make_valid
from core.logging import get_logger

logger = get_logger("data_ingestion.geographic_mask.validator")

ALLOWED_SURFACES = {"land", "ice shelf", "ice tongue", "rumple"}


class ADDGeometryValidator:
    """Validates and safely normalizes geometries from SCAR ADD polygons."""

    def __init__(self, expected_crs: str = "EPSG:3031"):
        self.expected_crs = expected_crs

    def validate_crs(self, gdf: gpd.GeoDataFrame) -> bool:
        """Verifies that the GeoDataFrame is defined in the expected native CRS."""
        if gdf.crs is None:
            raise ValueError(f"GeoDataFrame has no CRS defined. Expected {self.expected_crs}.")
        
        # Check EPSG code
        epsg = gdf.crs.to_epsg()
        if epsg != 3031 and str(gdf.crs).lower() != "epsg:3031":
            raise ValueError(
                f"Unexpected CRS: {gdf.crs}. SCAR ADD authoritative native CRS must be EPSG:3031."
            )
        return True

    def validate_and_repair_geometries(
        self,
        gdf: gpd.GeoDataFrame,
        repair_invalid: bool = True,
    ) -> Tuple[gpd.GeoDataFrame, Dict[str, Any]]:
        """
        Validates geometries, removes empty geometries, and safely repairs invalid ones.
        
        Returns:
            Tuple of (cleaned_gdf, validation_summary)
        """
        initial_count = len(gdf)
        
        # 1. Remove empty geometries
        is_empty = gdf.geometry.is_empty
        empty_count = int(is_empty.sum())
        if empty_count > 0:
            logger.warning("Dropping empty geometries", count=empty_count)
            gdf = gdf[~is_empty].copy()

        # 2. Check validity
        is_valid = gdf.geometry.is_valid
        invalid_count = int((~is_valid).sum())
        repaired_count = 0
        unrepaired_count = 0

        if invalid_count > 0:
            logger.warning("Found invalid geometries in dataset", count=invalid_count)
            if repair_invalid:
                logger.info("Applying safe shapely.make_valid repair to invalid geometries")
                repaired_geoms = []
                for idx, row in gdf.iterrows():
                    geom = row.geometry
                    if not geom.is_valid:
                        fixed = make_valid(geom)
                        if fixed.is_valid and not fixed.is_empty:
                            repaired_geoms.append(fixed)
                            repaired_count += 1
                        else:
                            repaired_geoms.append(geom)
                            unrepaired_count += 1
                    else:
                        repaired_geoms.append(geom)
                gdf = gdf.copy()
                gdf["geometry"] = repaired_geoms

        # 3. Check surface attributes
        if "surface" not in gdf.columns:
            raise KeyError("Source GeoDataFrame is missing the required 'surface' attribute column.")
        
        surface_series = gdf["surface"].astype(str).str.strip().str.lower()
        gdf["surface"] = surface_series
        surface_counts = gdf["surface"].value_counts().to_dict()
        
        unexpected_surfaces = set(surface_counts.keys()) - ALLOWED_SURFACES
        if unexpected_surfaces:
            logger.warning("Found unexpected surface categories in dataset", unexpected=list(unexpected_surfaces))

        summary = {
            "initial_features": initial_count,
            "final_features": len(gdf),
            "empty_dropped": empty_count,
            "invalid_detected": invalid_count,
            "repaired_features": repaired_count,
            "unrepaired_features": unrepaired_count,
            "surface_counts": surface_counts,
        }
        logger.info("Geometry validation complete", **summary)
        return gdf, summary
