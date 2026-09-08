"""
Inference service for Ice-kNN-South ML sea-ice concentration forecasts.
Provides high-performance spatial-temporal interpolation and point queries across
the 90-day Southern Ocean forecast dataset.
Explicitly identifies positions outside the native polar domain (e.g. Cape Town at -33.9°S)
with coverage_status='OUTSIDE_NATIVE_SIC_DOMAIN' and returns 0.0 SIC under explicit POC policy.
"""

import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple, List
import numpy as np
import pandas as pd
import xarray as xr

from ice_knn.model import load_ice_knn_model, resolve_netcdf_forecast_path, IceKNNSouthModel



class IceKNNInferenceService:
    """
    Production-grade query interface for 90-day sea-ice concentration forecasts.
    Guarantees no out-of-domain nearest-neighbor snapping to edge ice cells.
    """

    NATIVE_DOMAIN_NORTHERN_LIMIT = -45.0  # Degrees south

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
    ) -> Dict[str, Any]:
        """
        Query sea-ice concentration and uncertainty at a given (lat, lon, time).
        
        Args:
            lat: Latitude (-90 to -45)
            lon: Longitude (0 to 360 or -180 to 180)
            time_target: Date string, Timestamp, or integer lead day index (0..89)
            
        Returns:
            Dict with 'sic_percent', 'sic_fraction', 'uncertainty_percent', 'coverage_status', etc.
        """
        # Explicit domain check: Positions north of -45°S (e.g., Cape Town at -33.9°S)
        # are outside the native polar satellite SIC domain.
        if lat > self.NATIVE_DOMAIN_NORTHERN_LIMIT:
            return {
                "sic_percent": 0.0,
                "sic_fraction": 0.0,
                "uncertainty_percent": 0.0,
                "uncertainty_fraction": 0.0,
                "q05_percent": 0.0,
                "q95_percent": 0.0,
                "clim_percent": 0.0,
                "coverage_status": "OUTSIDE_NATIVE_SIC_DOMAIN",
                "source": "Ice-kNN-South",
                "status": "OPEN_WATER_POC_POLICY",
            }

        ds = self.forecast_dataset

        # Check against actual NetCDF latitude ceiling to prevent boundary edge inheritance
        nc_max_lat = float(ds["lat"].values.max())
        if lat > nc_max_lat:
            return {
                "sic_percent": 0.0,
                "sic_fraction": 0.0,
                "uncertainty_percent": 0.0,
                "uncertainty_fraction": 0.0,
                "q05_percent": 0.0,
                "q95_percent": 0.0,
                "clim_percent": 0.0,
                "coverage_status": "OUTSIDE_NATIVE_SIC_DOMAIN",
                "source": "Ice-kNN-South",
                "status": "OPEN_WATER_POC_POLICY",
            }

        # Normalize longitude to [0, 360)
        norm_lon = lon % 360.0

        # Handle time coordinate
        if isinstance(time_target, int):
            lead_idx = min(max(time_target, 0), len(ds["time"]) - 1)
            time_slice = ds.isel(time=lead_idx)
        else:
            target_dt = pd.to_datetime(time_target)
            time_slice = ds.sel(time=target_dt, method="nearest")

        # Nearest neighbor spatial query inside native domain
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
            "coverage_status": "WITHIN_NATIVE_SIC_DOMAIN",
            "source": "Ice-kNN-South",
            "status": "OPERATIONAL",
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
            "forecast_start": dates[0].isoformat(),
            "forecast_end": dates[-1].isoformat(),
            "horizon_days": len(dates),
            "lead_days": len(dates),
            "spatial_resolution": "0.25_degree",
            "native_domain_lat": [-90.0, -45.0],
            "native_domain_lon": [0.0, 360.0],
            "mean_sic_percent": float(np.nanmean(sic_data)),
            "max_sic_percent": float(np.nanmax(sic_data)),
            "min_sic_percent": float(np.nanmin(sic_data)),
            "sic_stats": {
                "mean": float(np.nanmean(sic_data)),
                "max": float(np.nanmax(sic_data)),
                "min": float(np.nanmin(sic_data)),
            },
            "ensemble_members": 50,
            "uncertainty_method": "kNN_residual_bootstrap",
        }
