"""
H3 Environmental Grid Builder.
Loads native scientific datasets (CMEMS currents, CMEMS waves, ECMWF winds, NSIDC sea ice, GEBCO bathymetry, Iceberg hazard)
and computes complete dynamic environmental states across canonical H3 cells.
Saves to data/antarctica/environment/environment_cells.parquet.
"""

import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import xarray as xr
from core.logging import get_logger
from data_ingestion.h3.config import H3Config, default_h3_config
from data_ingestion.h3.schema import TemporalQualityStatus
from data_ingestion.nsidc.interface import NSIDCSeaIceInterface
from domain.coordinates import GeoPoint

logger = get_logger("data_ingestion.h3.environmental_grid_builder")


class H3EnvironmentalGridBuilder:
    """Computes unified dynamic environmental variables across canonical H3 cells."""

    def __init__(self, config: Optional[H3Config] = None):
        self.config = config or default_h3_config
        self.nsidc = NSIDCSeaIceInterface()

    def build_environmental_grid(
        self,
        valid_time: Optional[datetime] = None,
        max_cells: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Loads native datasets and computes dynamic environmental state across H3 cells.
        """
        target_time = valid_time or datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        logger.info("Building H3 unified environmental grid", valid_time=target_time.isoformat())
        t0 = time.time()

        # 1. Load static cells table
        cells_path = self.config.grid_dir / "cells.parquet"
        if not cells_path.exists():
            raise FileNotFoundError(f"Canonical cells table not found at {cells_path}")
        df_cells = pd.read_parquet(cells_path)
        if max_cells is not None and max_cells < len(df_cells):
            df_cells = df_cells.head(max_cells)
        logger.info(f"Loaded {len(df_cells)} static H3 cells")

        lats = df_cells["centroid_lat"].values
        lons = df_cells["centroid_lon"].values
        da_lats = xr.DataArray(lats, dims="points")
        da_lons = xr.DataArray(lons, dims="points")

        # 2. Load and sample CMEMS Ocean Currents
        currents_file = self.config.data_root / "raw" / "cmems" / "currents" / "cmems_currents_surface_20240101_20240107.nc"
        if not currents_file.exists():
            currents_file = self.config.data_root / "raw" / "cmems" / "currents" / "cmems_currents_capetown_to_antarctica_20240101_20240102.nc"

        logger.info("Sampling CMEMS ocean currents", path=str(currents_file))
        ds_c = xr.open_dataset(currents_file).isel(time=0)
        if "depth" in ds_c.dims:
            ds_c = ds_c.isel(depth=0)
        u_pts = ds_c["uo"].sel(latitude=da_lats, longitude=da_lons, method="nearest").values
        v_pts = ds_c["vo"].sel(latitude=da_lats, longitude=da_lons, method="nearest").values
        ds_c.close()

        # 3. Load and sample CMEMS Waves
        waves_file = self.config.data_root / "raw" / "cmems" / "waves" / "cmems_waves_capetown_to_antarctica_20240101_20240102.nc"
        if not waves_file.exists():
            waves_file = self.config.data_root / "raw" / "cmems" / "waves" / "cmems_waves_antarctic_20240101_20240102.nc"

        logger.info("Sampling CMEMS waves", path=str(waves_file))
        ds_w = xr.open_dataset(waves_file).isel(time=0)
        hs_pts = ds_w["VHM0"].sel(latitude=da_lats, longitude=da_lons, method="nearest").values
        dir_pts = ds_w["VMDR"].sel(latitude=da_lats, longitude=da_lons, method="nearest").values
        tp_pts = ds_w["VTPK"].sel(latitude=da_lats, longitude=da_lons, method="nearest").values
        ds_w.close()

        # 4. Load and sample ECMWF Wind
        wind_file = self.config.data_root / "raw" / "ecmwf" / "wind" / "ecmwf_wind_surface_0_48h.grib2"
        logger.info("Sampling ECMWF 10m wind", path=str(wind_file))
        ds_wind = xr.open_dataset(
            wind_file,
            engine="cfgrib",
            filter_by_keys={"typeOfLevel": "heightAboveGround", "level": 10},
        ).isel(step=0)
        u10_pts = ds_wind["u10"].sel(latitude=da_lats, longitude=da_lons, method="nearest").values
        v10_pts = ds_wind["v10"].sel(latitude=da_lats, longitude=da_lons, method="nearest").values
        ds_wind.close()

        # 5. Load Iceberg Hazard lookup
        hazard_file = self.config.hazard_dir / "iceberg_hazard.parquet"
        hazard_lookup: Dict[str, float] = {}
        if hazard_file.exists():
            df_hz = pd.read_parquet(hazard_file)
            col_id = "cell_id" if "cell_id" in df_hz.columns else "h3_cell"
            col_val = "hazard_score" if "hazard_score" in df_hz.columns else "hazard"
            # Aggregate max hazard per cell
            hazard_lookup = df_hz.groupby(col_id)[col_val].max().to_dict()

        # 6. Assemble complete unified records
        logger.info("Computing vector speeds, directions, navigability, and quality flags")
        records = []
        for i, row in enumerate(df_cells.itertuples()):
            c_id = row.cell_id
            c_lat = row.centroid_lat
            c_lon = row.centroid_lon

            # Hydrodynamics
            u = float(u_pts[i]) if pd.notnull(u_pts[i]) else None
            v = float(v_pts[i]) if pd.notnull(v_pts[i]) else None
            c_spd = round(float(math.hypot(u, v)), 3) if (u is not None and v is not None) else None
            c_dir = round(float(math.degrees(math.atan2(u, v)) % 360.0), 1) if (u is not None and v is not None) else None

            # Meteorology
            w_u = float(u10_pts[i]) if pd.notnull(u10_pts[i]) else None
            w_v = float(v10_pts[i]) if pd.notnull(v10_pts[i]) else None
            w_spd = round(float(math.hypot(w_u, w_v)), 2) if (w_u is not None and w_v is not None) else None
            w_dir = round(float(math.degrees(math.atan2(w_u, w_v)) % 360.0), 1) if (w_u is not None and w_v is not None) else None

            # Waves
            hs = round(float(hs_pts[i]), 2) if (pd.notnull(hs_pts[i]) and hs_pts[i] >= 0.0) else None
            wv_dir = round(float(dir_pts[i] % 360.0), 1) if (pd.notnull(dir_pts[i]) and dir_pts[i] >= 0.0) else None
            tp = round(float(tp_pts[i]), 2) if (pd.notnull(tp_pts[i]) and tp_pts[i] >= 0.0) else None

            # Cryosphere (NSIDC SIC)
            sic = None
            if c_lat <= -55.0:
                raw_sic = self.nsidc.get_sic_point(GeoPoint(latitude=c_lat, longitude=c_lon), target_time)
                if raw_sic is not None and 0.0 <= raw_sic <= 100.0:
                    sic = round(raw_sic, 1)

            # Iceberg Hazard
            hz_score = round(hazard_lookup.get(c_id, 0.0), 4)

            # Navigability: blocked if land/shelf, or shallow bathymetry (< 10m), or heavy sea ice (> 85%)
            is_blocked = bool(row.is_blocked)
            is_shallow = bool(pd.notnull(row.bathymetry_min_m) and row.bathymetry_min_m < 10.0)
            is_heavy_ice = bool(sic is not None and sic > 85.0)
            is_nav = not (is_blocked or is_shallow or is_heavy_ice)

            records.append({
                "cell_id": c_id,
                "valid_time": target_time.isoformat(),
                "centroid_lat": c_lat,
                "centroid_lon": c_lon,
                "h3_resolution": row.h3_resolution,
                # Static Geographic Attributes
                "ocean_fraction": row.ocean_fraction,
                "land_fraction": row.land_fraction,
                "ice_shelf_fraction": row.ice_shelf_fraction,
                "geographic_status": row.geographic_status,
                "is_blocked": is_blocked,
                # Static Bathymetry (Positive Depth in Meters)
                "bathymetry_depth_m": row.bathymetry_mean_m,
                "bathymetry_min_m": row.bathymetry_min_m,
                # Cryosphere
                "sea_ice_concentration": sic,
                "sea_ice_uncertainty": 5.0 if sic is not None else None,
                # Hydrodynamics (Currents)
                "current_u_ms": u,
                "current_v_ms": v,
                "current_speed_ms": c_spd,
                "current_direction_deg": c_dir,
                # Meteorology (Wind)
                "wind_u_ms": w_u,
                "wind_v_ms": w_v,
                "wind_speed_ms": w_spd,
                "wind_direction_deg": w_dir,
                # Waves
                "wave_height_m": hs,
                "wave_direction_deg": wv_dir,
                "wave_period_s": tp,
                # Iceberg Hazard
                "iceberg_hazard": hz_score,
                # Overall navigability & quality
                "is_navigable": is_nav,
                "quality_status": "OBSERVED",
                "provenance": "CMEMS_PHY+CMEMS_WAV+ECMWF_IFS+NSIDC_CDR+GEBCO_2026+SCAR_ADD_v7.12",
            })

        df_env = pd.DataFrame(records)
        t1 = time.time()
        duration = round(t1 - t0, 2)

        # 7. Save outputs
        out_parquet = self.config.env_dir / "environment_cells.parquet"
        logger.info("Saving unified environment cells to Parquet", path=str(out_parquet), rows=len(df_env), duration_sec=duration)
        df_env.to_parquet(out_parquet, index=False)

        # Also save partition for this timestamp
        partition_dir = self.config.env_dir / f"time={target_time.strftime('%Y%m%dT%H%M%SZ')}"
        partition_dir.mkdir(parents=True, exist_ok=True)
        part_parquet = partition_dir / "environment_state.parquet"
        df_env.to_parquet(part_parquet, index=False)

        metadata = {
            "valid_time": target_time.isoformat(),
            "total_cells": len(df_env),
            "computation_time_sec": duration,
            "datasets_loaded": [
                "CMEMS Currents (PHY-001-024)",
                "CMEMS Waves (WAV-001-027)",
                "ECMWF Wind (IFS 10m)",
                "NSIDC Sea Ice Concentration (CDR v6)",
                "GEBCO 2026 Sub-Ice Bathymetry",
                "SCAR ADD v7.12 Geographic Mask",
                "AMIP Iceberg Trajectory Ensemble Hazard",
            ],
            "navigable_cells_count": int(df_env["is_navigable"].sum()),
            "mean_wave_height_m": round(float(df_env["wave_height_m"].dropna().mean()), 2),
            "mean_wind_speed_ms": round(float(df_env["wind_speed_ms"].dropna().mean()), 2),
            "mean_current_speed_ms": round(float(df_env["current_speed_ms"].dropna().mean()), 3),
            "cells_with_sea_ice": int((df_env["sea_ice_concentration"] > 0.0).sum()),
            "cells_with_iceberg_hazard": int((df_env["iceberg_hazard"] > 0.0).sum()),
            "output_paths": {
                "master_parquet": str(out_parquet.resolve()),
                "partition_parquet": str(part_parquet.resolve()),
            }
        }

        return df_env, metadata
