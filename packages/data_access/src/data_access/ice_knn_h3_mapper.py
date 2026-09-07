"""
H3 Sea-Ice Mapper for Ice-kNN-South NetCDF Forecasts.
Projects the 90-day gridded NetCDF sea-ice predictions onto the canonical
AMIP H3 resolution 5 cells, respecting land masks and bathymetric boundaries.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import xarray as xr

from ice_knn.inference import IceKNNInferenceService
from ice_knn.model import resolve_netcdf_forecast_path


class IceKNNH3Mapper:
    """
    Maps 90-day Ice-kNN-South regular lat-lon predictions onto canonical AMIP H3 cells.
    """

    def __init__(
        self,
        grid_cells_parquet: str = "data/antarctica/grid/cells.parquet",
        forecast_nc_path: Optional[str] = None,
    ):
        self.grid_cells_path = Path(grid_cells_parquet)
        self.forecast_nc_path = forecast_nc_path
        self._grid_df: Optional[pd.DataFrame] = None
        self._forecast_ds: Optional[xr.Dataset] = None

    @property
    def grid_df(self) -> pd.DataFrame:
        if self._grid_df is None:
            if not self.grid_cells_path.is_file():
                # Fallback to environment_cells.parquet if grid/cells.parquet not found
                alt_path = Path("data/antarctica/environment/environment_cells.parquet")
                if alt_path.is_file():
                    self._grid_df = pd.read_parquet(alt_path)
                else:
                    raise FileNotFoundError(f"Canonical cells parquet not found at {self.grid_cells_path} or {alt_path}")
            else:
                self._grid_df = pd.read_parquet(self.grid_cells_path)
        return self._grid_df

    @property
    def forecast_ds(self) -> xr.Dataset:
        if self._forecast_ds is None:
            nc_path = resolve_netcdf_forecast_path(self.forecast_nc_path)
            self._forecast_ds = xr.open_dataset(nc_path)
        return self._forecast_ds

    def build_h3_forecast_dataframe(self) -> pd.DataFrame:
        """
        Builds a multi-temporal DataFrame mapping (cell_id, lead_day) -> SIC forecast metrics.
        Returns columns:
            [cell_id, lead_day, valid_time, centroid_lat, centroid_lon,
             sea_ice_concentration, sea_ice_percent, sea_ice_uncertainty,
             uncertainty_percent, sic_q05, sic_q95, sic_clim, is_blocked, provenance]
        """
        grid = self.grid_df
        ds = self.forecast_ds

        cell_ids = grid["cell_id"].values
        lats = grid["centroid_lat"].values
        lons = grid["centroid_lon"].values
        is_blocked = grid["is_blocked"].values if "is_blocked" in grid.columns else np.zeros(len(grid), dtype=bool)

        times = [pd.to_datetime(t) for t in ds["time"].values]
        num_leads = len(times)
        num_cells = len(cell_ids)

        forecast_lats = ds["lat"].values
        forecast_lons = ds["lon"].values
        sic_grid = ds["sic"].values             # (lead, lat, lon)
        unc_grid = ds["sic_uncertainty"].values # (lead, lat, lon)
        q05_grid = ds["sic_q05"].values
        q95_grid = ds["sic_q95"].values
        clim_grid = ds["sic_clim"].values

        # Pre-compute nearest spatial indices for all H3 cells
        lat_indices = np.zeros(num_cells, dtype=int)
        lon_indices = np.zeros(num_cells, dtype=int)
        in_antarctic_domain = np.zeros(num_cells, dtype=bool)

        for i in range(num_cells):
            c_lat = lats[i]
            c_lon = lons[i] % 360.0
            if c_lat <= forecast_lats.max():
                in_antarctic_domain[i] = True
                lat_indices[i] = int(np.argmin(np.abs(forecast_lats - c_lat)))
                lon_indices[i] = int(np.argmin(np.abs(forecast_lons - c_lon)))

        records = []
        for lead_idx in range(num_leads):
            lead_time = times[lead_idx]
            lead_day_sic = sic_grid[lead_idx]
            lead_day_unc = unc_grid[lead_idx]
            lead_day_q05 = q05_grid[lead_idx]
            lead_day_q95 = q95_grid[lead_idx]
            lead_day_clim = clim_grid[lead_idx]

            for i in range(num_cells):
                cid = cell_ids[i]
                c_lat = float(lats[i])
                c_lon = float(lons[i])
                blocked = bool(is_blocked[i])

                if not in_antarctic_domain[i]:
                    # North of Antarctic ice zone (-45 deg): open water
                    sic_pct = 0.0
                    unc_pct = 0.0
                    q05_pct = 0.0
                    q95_pct = 0.0
                    clim_pct = 0.0
                else:
                    l_idx = lat_indices[i]
                    o_idx = lon_indices[i]
                    sic_pct = float(lead_day_sic[l_idx, o_idx])
                    unc_pct = float(lead_day_unc[l_idx, o_idx])
                    q05_pct = float(lead_day_q05[l_idx, o_idx])
                    q95_pct = float(lead_day_q95[l_idx, o_idx])
                    clim_pct = float(lead_day_clim[l_idx, o_idx])

                # Handle NaNs and bounds
                sic_pct = float(np.clip(np.nan_to_num(sic_pct, nan=0.0), 0.0, 100.0))
                unc_pct = float(np.clip(np.nan_to_num(unc_pct, nan=0.0), 0.0, 100.0))
                q05_pct = float(np.clip(np.nan_to_num(q05_pct, nan=0.0), 0.0, 100.0))
                q95_pct = float(np.clip(np.nan_to_num(q95_pct, nan=0.0), 0.0, 100.0))
                clim_pct = float(np.clip(np.nan_to_num(clim_pct, nan=0.0), 0.0, 100.0))

                records.append({
                    "cell_id": cid,
                    "lead_day": lead_idx,
                    "valid_time": lead_time,
                    "centroid_lat": c_lat,
                    "centroid_lon": c_lon,
                    "sea_ice_concentration": round(sic_pct / 100.0, 4),
                    "sea_ice_percent": round(sic_pct, 2),
                    "sea_ice_uncertainty": round(unc_pct / 100.0, 4),
                    "uncertainty_percent": round(unc_pct, 2),
                    "sic_q05": round(q05_pct / 100.0, 4),
                    "sic_q95": round(q95_pct / 100.0, 4),
                    "sic_clim": round(clim_pct / 100.0, 4),
                    "is_blocked": blocked,
                    "provenance": "Ice-kNN-South+NetCDF4",
                })

        return pd.DataFrame.from_records(records)

    def export_h3_forecast_parquet(
        self,
        output_parquet_path: str = "data/processed/ice_knn/h3_sic_forecast_90d.parquet",
    ) -> Path:
        """
        Builds and saves the canonical H3 sea-ice forecast parquet dataset.
        """
        out_p = Path(output_parquet_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df = self.build_h3_forecast_dataframe()
        df.to_parquet(out_p, index=False, compression="snappy")
        print(f"H3 90-day sea-ice forecast saved to {out_p} ({len(df):,} rows)")
        return out_p
