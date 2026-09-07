"""
Static Layer Mapping for Canonical H3 Grid:
- SCAR ADD v7.12 Geographic Mask (Area-weighted polygon intersection in EPSG:3031)
- GEBCO 2026 Sub-Ice Bathymetry (Depth statistics & percentiles, positive water depth convention)
Generates the canonical static cell table: cells.parquet, geometry.geojson, and metadata.json.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import h3
from shapely.geometry import mapping
from core.logging import get_logger
from data_ingestion.h3.config import H3Config, default_h3_config
from data_ingestion.h3.geometry import H3GeometryEngine
from data_ingestion.h3.schema import StaticH3Cell, H3GeographicStatus
from data_ingestion.geographic_mask.interface import AntarcticGeographicMask
from data_ingestion.geographic_mask.h3_mask import H3GeographicMaskAggregator
from data_ingestion.gebco.interface import GEBCOBathymetryInterface

logger = get_logger("data_ingestion.h3.static_layers")


class H3StaticLayerMapper:
    """Maps SCAR ADD geographic boundaries and GEBCO bathymetry onto the canonical H3 grid."""

    def __init__(
        self,
        config: Optional[H3Config] = None,
        geographic_mask: Optional[AntarcticGeographicMask] = None,
        gebco_interface: Optional[GEBCOBathymetryInterface] = None,
    ):
        self.config = config or default_h3_config
        self.geom = H3GeometryEngine()
        
        # SCAR ADD Mask
        try:
            self.mask = geographic_mask or AntarcticGeographicMask()
            self.scar_aggregator = H3GeographicMaskAggregator(
                mask=self.mask,
                default_blocking_threshold=self.config.default_blocking_threshold,
            )
        except Exception as e:
            logger.warning("Could not initialize SCAR ADD geographic mask, using open ocean fallback", error=str(e))
            self.mask = None
            self.scar_aggregator = None

        # GEBCO Bathymetry Interface
        try:
            self.gebco = gebco_interface or GEBCOBathymetryInterface()
            self.gebco._ensure_loaded()
        except Exception as e:
            logger.warning("Could not initialize GEBCO interface, depths will be None", error=str(e))
            self.gebco = None

    def map_cell(self, cell_id: str) -> StaticH3Cell:
        """
        Maps static geographic fractions and bathymetric statistics for a single H3 cell.
        """
        c_lat, c_lon = h3.cell_to_latlng(cell_id)
        res = h3.get_resolution(cell_id)
        poly = self.geom.cell_to_polygon_4326(cell_id)

        # 1. SCAR ADD Geographic Fractions
        ocean_f = 1.0
        land_f = 0.0
        shelf_f = 0.0
        tongue_f = 0.0
        rumple_f = 0.0
        status = H3GeographicStatus.OPEN_OCEAN
        is_blocked = False

        if c_lat > -60.0:
            # North of 60°S is open ocean outside SCAR ADD Antarctic boundary
            ocean_f = 1.0
            status = H3GeographicStatus.OPEN_OCEAN
            is_blocked = False
        elif self.scar_aggregator is not None:
            try:
                attr = self.scar_aggregator.compute_cell_attributes(cell_id)
                ocean_f = float(attr.open_water_fraction)
                land_f = float(attr.land_fraction)
                shelf_f = float(attr.ice_shelf_fraction)
                tongue_f = float(attr.ice_tongue_fraction)
                rumple_f = float(attr.rumple_fraction)
                is_blocked = bool(attr.geographically_blocked)

                # Classify status
                if land_f >= 0.5:
                    status = H3GeographicStatus.LAND
                elif shelf_f >= 0.5:
                    status = H3GeographicStatus.ICE_SHELF
                elif tongue_f >= 0.5:
                    status = H3GeographicStatus.ICE_TONGUE
                elif rumple_f >= 0.5:
                    status = H3GeographicStatus.RUMPLE
                elif (land_f + shelf_f + tongue_f + rumple_f) > 0.0:
                    status = H3GeographicStatus.MIXED
                else:
                    status = H3GeographicStatus.OPEN_OCEAN
            except Exception as e:
                logger.debug("Error aggregating SCAR ADD for cell", cell_id=cell_id, error=str(e))

        # 2. GEBCO 2026 Bathymetry Statistics
        depth_stats = self._compute_gebco_stats(cell_id, c_lat, c_lon)

        return StaticH3Cell(
            cell_id=cell_id,
            h3_resolution=res,
            centroid_lat=round(c_lat, 5),
            centroid_lon=round(c_lon, 5),
            geometry_wkt=poly.wkt,
            ocean_fraction=round(ocean_f, 4),
            land_fraction=round(land_f, 4),
            ice_shelf_fraction=round(shelf_f, 4),
            ice_tongue_fraction=round(tongue_f, 4),
            rumple_fraction=round(rumple_f, 4),
            geographic_status=status,
            is_blocked=is_blocked,
            bathymetry_valid_fraction=depth_stats["valid_fraction"],
            bathymetry_mean_m=depth_stats["mean_m"],
            bathymetry_min_m=depth_stats["min_m"],
            bathymetry_p10_m=depth_stats["p10_m"],
            bathymetry_p50_m=depth_stats["p50_m"],
            bathymetry_p90_m=depth_stats["p90_m"],
        )

    def _compute_gebco_stats(self, cell_id: str, c_lat: float, c_lon: float) -> Dict[str, Any]:
        """
        Samples GEBCO depths across centroid and boundary vertices to derive percentiles and valid fraction.
        """
        if self.gebco is None or self.gebco._depth_m is None:
            return {
                "valid_fraction": 0.0,
                "mean_m": None,
                "min_m": None,
                "p10_m": None,
                "p50_m": None,
                "p90_m": None,
            }

        # Sample points: centroid + 6 vertices
        boundary = h3.cell_to_boundary(cell_id)
        sample_pts = [(c_lat, c_lon)] + [(lat, lng) for lat, lng in boundary]

        depths = []
        for lat, lon in sample_pts:
            d = self.gebco.get_depth(lat, lon)
            if d is not None and d > 0.0:
                depths.append(d)

        if not depths:
            # Check if centroid is classified as land
            is_land = self.gebco.is_land(c_lat, c_lon)
            return {
                "valid_fraction": 0.0 if not is_land else 1.0,
                "mean_m": None,
                "min_m": None,
                "p10_m": None,
                "p50_m": None,
                "p90_m": None,
            }

        arr = np.array(depths, dtype=float)
        return {
            "valid_fraction": round(len(depths) / float(len(sample_pts)), 3),
            "mean_m": round(float(np.mean(arr)), 1),
            "min_m": round(float(np.min(arr)), 1),
            "p10_m": round(float(np.percentile(arr, 10)), 1),
            "p50_m": round(float(np.percentile(arr, 50)), 1),
            "p90_m": round(float(np.percentile(arr, 90)), 1),
        }

    def generate_static_grid_table(self, cells: List[str]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Processes all H3 cells into the static canonical table.
        """
        t0 = time.time()
        logger.info("Starting static layer mapping across H3 cells", total_cells=len(cells))

        records = []
        for idx, cell_id in enumerate(cells):
            st_cell = self.map_cell(cell_id)
            records.append({
                "cell_id": st_cell.cell_id,
                "h3_resolution": st_cell.h3_resolution,
                "centroid_lat": st_cell.centroid_lat,
                "centroid_lon": st_cell.centroid_lon,
                "ocean_fraction": st_cell.ocean_fraction,
                "land_fraction": st_cell.land_fraction,
                "ice_shelf_fraction": st_cell.ice_shelf_fraction,
                "ice_tongue_fraction": st_cell.ice_tongue_fraction,
                "rumple_fraction": st_cell.rumple_fraction,
                "geographic_status": st_cell.geographic_status.value,
                "is_blocked": st_cell.is_blocked,
                "bathymetry_valid_fraction": st_cell.bathymetry_valid_fraction,
                "bathymetry_mean_m": st_cell.bathymetry_mean_m,
                "bathymetry_min_m": st_cell.bathymetry_min_m,
                "bathymetry_p10_m": st_cell.bathymetry_p10_m,
                "bathymetry_p50_m": st_cell.bathymetry_p50_m,
                "bathymetry_p90_m": st_cell.bathymetry_p90_m,
                "geometry_wkt": st_cell.geometry_wkt,
            })

            if (idx + 1) % 200 == 0 or (idx + 1) == len(cells):
                logger.info(f"Mapped {idx + 1}/{len(cells)} cells ({round((idx + 1)/len(cells)*100, 1)}%)")

        df = pd.DataFrame(records)
        t1 = time.time()

        metadata = {
            "h3_resolution": self.config.resolution,
            "total_cells": len(df),
            "mapping_duration_sec": round(t1 - t0, 2),
            "scar_add_release": "SCAR ADD v7.12",
            "gebco_release": "GEBCO_2026 Sub-Ice Antarctic Bathymetry",
            "bathymetry_convention": "positive water depth (depth_m > 0)",
            "geographic_blocking_threshold": self.config.default_blocking_threshold,
            "status_distribution": df["geographic_status"].value_counts().to_dict(),
            "blocked_cells_count": int(df["is_blocked"].sum()),
            "ocean_cells_count": int((df["geographic_status"] == "OPEN_OCEAN").sum()),
        }

        return df, metadata

    def save_static_grid(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> Tuple[Path, Path, Path]:
        """
        Saves static layers to cells.parquet, geometry.geojson, and metadata.json.
        """
        self.config.ensure_directories()
        parquet_path = self.config.grid_dir / "cells.parquet"
        geojson_path = self.config.grid_dir / "geometry.geojson"
        meta_path = self.config.grid_dir / "metadata.json"

        logger.info("Writing static cells table to Parquet", path=str(parquet_path))
        df.to_parquet(parquet_path, index=False)

        logger.info("Writing static metadata", path=str(meta_path))
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Generate lightweight representative GeoJSON (e.g. sample or coastal/blocked/corridor features)
        # To keep browser fast, include up to 5,000 key cells (all blocked/mixed + corridor sample)
        logger.info("Generating representative GeoJSON for UI map", path=str(geojson_path))
        non_ocean = df[df["geographic_status"] != "OPEN_OCEAN"]
        corridor = df[(df["centroid_lat"] > -40.0) & (df["centroid_lon"] >= 15.0) & (df["centroid_lon"] <= 25.0)]
        ocean_df = df[df["geographic_status"] == "OPEN_OCEAN"]
        sampled_ocean = ocean_df.sample(n=min(2000, len(ocean_df)), random_state=42) if not ocean_df.empty else pd.DataFrame()
        geojson_df = pd.concat([non_ocean, corridor, sampled_ocean]).drop_duplicates(subset=["cell_id"])

        features = []
        for _, row in geojson_df.iterrows():
            poly = self.geom.cell_to_polygon_4326(row["cell_id"])
            features.append({
                "type": "Feature",
                "id": row["cell_id"],
                "geometry": mapping(poly),
                "properties": {
                    "cell_id": row["cell_id"],
                    "status": row["geographic_status"],
                    "is_blocked": bool(row["is_blocked"]),
                    "depth_m": row["bathymetry_mean_m"],
                    "land_f": row["land_fraction"],
                    "shelf_f": row["ice_shelf_fraction"],
                }
            })

        fc = {"type": "FeatureCollection", "features": features}
        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(fc, f)

        return parquet_path, geojson_path, meta_path
