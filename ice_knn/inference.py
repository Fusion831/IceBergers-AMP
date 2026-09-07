"""
Ice-kNN-South Inference Service.
Provides served predictions from the trained .pkl model artifact,
and spatial-temporal access to the 90-day NetCDF forecast.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import xarray as xr

from ice_knn.model import (
    IceKNNSouthModel,
    load_ice_knn_model,
    resolve_model_path,
    resolve_netcdf_forecast_path,
)


class IceKNNInferenceService:
    """
    High-level service for serving the Ice-kNN-South model and its 90-day forecasts.
    Maintains cached access to both the trained model (.pkl) and the NetCDF forecast (.nc).
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        forecast_nc_path: Optional[Union[str, Path]] = None,
    ):
        self._model_path = model_path
        self._forecast_nc_path = forecast_nc_path
        self._model: Optional[IceKNNSouthModel] = None
        self._ds: Optional[xr.Dataset] = None

    @property
    def model(self) -> IceKNNSouthModel:
        """Lazy-loaded singleton of the pre-trained Ice-kNN-South model."""
        if self._model is None:
            self._model = load_ice_knn_model(self._model_path)
        return self._model

    @property
    def forecast_dataset(self) -> xr.Dataset:
        """Lazy-loaded xarray Dataset of the 90-day sea-ice forecast."""
        if self._ds is None:
            resolved_nc = resolve_netcdf_forecast_path(self._forecast_nc_path)
            self._ds = xr.open_dataset(resolved_nc)
        return self._ds

    def get_forecast_dates(self) -> List[pd.Timestamp]:
        """Returns list of timestamp coordinates from the 90-day forecast."""
        ds = self.forecast_dataset
        times = ds["time"].values
        return [pd.to_datetime(t) for t in times]

    def get_grid_coordinates(self) -> Tuple[np.ndarray, np.ndarray]:
        """Returns (latitudes, longitudes) of the forecast grid."""
        ds = self.forecast_dataset
        return ds["lat"].values, ds["lon"].values

    def predict(
        self,
        initial_date: Union[str, datetime.date, pd.Timestamp],
        initial_sic: np.ndarray,
        current_era5: Dict[str, np.ndarray],
        current_ocean: Dict[str, np.ndarray],
        lead_days: int = 90,
    ) -> Dict[str, Any]:
        """
        Run inference using the trained .pkl model artifact.
        """
        return self.model.predict(
            initial_date=initial_date,
            initial_sic=initial_sic,
            current_era5=current_era5,
            current_ocean=current_ocean,
            lead_days=lead_days,
        )

    def query_sic(
        self,
        lat: float,
        lon: float,
        time_target: Union[str, datetime.datetime, pd.Timestamp, int],
    ) -> Dict[str, float]:
        """
        Query sea-ice concentration and uncertainty at a given (lat, lon, time).
        
        Args:
            lat: Latitude (-90 to -45)
            lon: Longitude (0 to 360 or -180 to 180)
            time_target: Date string, Timestamp, or integer lead day index (0..89)
            
        Returns:
            Dict with 'sic_percent', 'sic_fraction', 'uncertainty_percent', 'q05_percent', 'q95_percent'
        """
        # Open ocean check: Southern Ocean sea ice does not exist north of -50 deg latitude
        if lat > -50.0:
            return {
                "sic_percent": 0.0,
                "sic_fraction": 0.0,
                "uncertainty_percent": 0.0,
                "uncertainty_fraction": 0.0,
                "q05_percent": 0.0,
                "q95_percent": 0.0,
                "clim_percent": 0.0,
            }

        ds = self.forecast_dataset

        # Normalize longitude to [0, 360)
        norm_lon = lon % 360.0

        # Handle time coordinate
        if isinstance(time_target, int):
            lead_idx = min(max(time_target, 0), len(ds["time"]) - 1)
            time_slice = ds.isel(time=lead_idx)
        else:
            target_dt = pd.to_datetime(time_target)
            time_slice = ds.sel(time=target_dt, method="nearest")

        # Nearest neighbor spatial query
        point = time_slice.sel(lat=lat, lon=norm_lon, method="nearest")

        sic_pct = float(point["sic"].values)
        if np.isnan(sic_pct):
            sic_pct = 0.0

        unc_pct = float(point["sic_uncertainty"].values) if "sic_uncertainty" in point else 0.0
        q05_pct = float(point["sic_q05"].values) if "sic_q05" in point else 0.0
        q95_pct = float(point["sic_q95"].values) if "sic_q95" in point else 0.0
        clim_pct = float(point["sic_clim"].values) if "sic_clim" in point else 0.0

        return {
            "sic_percent": float(np.clip(sic_pct, 0.0, 100.0)),
            "sic_fraction": float(np.clip(sic_pct / 100.0, 0.0, 1.0)),
            "uncertainty_percent": float(unc_pct),
            "uncertainty_fraction": float(unc_pct / 100.0),
            "q05_percent": float(np.clip(q05_pct, 0.0, 100.0)),
            "q95_percent": float(np.clip(q95_pct, 0.0, 100.0)),
            "clim_percent": float(clim_pct),
        }

    def get_forecast_summary(self) -> Dict[str, Any]:
        """
        Returns structured statistics and metadata for the 90-day forecast.
        """
        ds = self.forecast_dataset
        dates = self.get_forecast_dates()
        sic_data = ds["sic"].values

        return {
            "model_name": "Ice-kNN-South",
            "reference": "DOI: 10.1029/2024JH000433",
            "lead_days": len(dates),
            "start_date": dates[0].strftime("%Y-%m-%d"),
            "end_date": dates[-1].strftime("%Y-%m-%d"),
            "lat_bounds": [float(ds["lat"].min()), float(ds["lat"].max())],
            "lon_bounds": [float(ds["lon"].min()), float(ds["lon"].max())],
            "grid_resolution": {
                "lat_step": float(abs(ds["lat"].values[1] - ds["lat"].values[0])) if len(ds["lat"]) > 1 else 0.0,
                "lon_step": float(abs(ds["lon"].values[1] - ds["lon"].values[0])) if len(ds["lon"]) > 1 else 0.0,
            },
            "variables": list(ds.data_vars.keys()),
            "sic_stats": {
                "min": float(np.nanmin(sic_data)),
                "max": float(np.nanmax(sic_data)),
                "mean": float(np.nanmean(sic_data)),
                "median": float(np.nanmedian(sic_data)),
                "std": float(np.nanstd(sic_data)),
                "nan_fraction": float(np.isnan(sic_data).mean()),
            },
        }

    def close(self):
        """Closes opened xarray dataset resources."""
        if self._ds is not None:
            self._ds.close()
            self._ds = None
