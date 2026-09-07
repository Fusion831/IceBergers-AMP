"""
Ice-kNN-South Model Loader and Definition.
Wraps the trained Ice-kNN-South model without retraining.
"""

from __future__ import annotations

import datetime
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
import xarray as xr


class IceKNNSouthModel:
    """
    Trained Ice-kNN-South model for Antarctic Sea Ice Concentration forecasts.
    Maintains compatibility with the serialized model artifact.
    """

    def __init__(self, k_neighbors: int = 30, n_components: int = 10, search_window_days: int = 30):
        self.k_neighbors = k_neighbors
        self.n_components = n_components
        self.search_window_days = search_window_days
        self.climatology: Dict[str, np.ndarray] = {}
        self.pcas: Dict[str, Dict[str, Any]] = {}
        self.historical_features: Optional[np.ndarray] = None
        self.historical_targets: Optional[np.ndarray] = None
        self.historical_dates: Optional[pd.DatetimeIndex] = None
        self.lat: Optional[np.ndarray] = None
        self.lon: Optional[np.ndarray] = None
        self.is_fitted: bool = False

    def _compute_dayofyear(self, dates: pd.DatetimeIndex) -> np.ndarray:
        doy = dates.dayofyear
        return np.where(doy == 366, 365, doy)

    def _drift_ice_correction(self, predicted_sic: np.ndarray, predicted_sica: np.ndarray, sst: Optional[np.ndarray] = None):
        if sst is not None:
            mask = (sst > -1.0) & (predicted_sic < 15.0)
            predicted_sic[mask] = 0.0
            predicted_sica[mask] = 0.0
        return predicted_sic, predicted_sica

    def predict(
        self,
        initial_date: Union[str, datetime.date, pd.Timestamp],
        initial_sic: np.ndarray,
        current_era5: Dict[str, np.ndarray],
        current_ocean: Dict[str, np.ndarray],
        lead_days: int = 90,
    ) -> Dict[str, Any]:
        """
        Run inference over a given lead time (default 90 days).
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction.")

        initial_date = pd.to_datetime(initial_date)
        doy = self._compute_dayofyear(pd.DatetimeIndex([initial_date]))[0]

        variables = {"sic": initial_sic}
        variables.update(current_era5)
        variables.update(current_ocean)

        current_features_list = []
        for v, data in variables.items():
            anom = data - self.climatology[v][doy]
            flattened = np.nan_to_num(anom.reshape(1, -1), nan=0.0)
            scores = self.pcas[v]["model"].transform(flattened)
            scores = scores / self.pcas[v]["std"]
            current_features_list.append(scores)

        current_features = np.hstack(current_features_list)

        hist_doy = self._compute_dayofyear(self.historical_dates)
        diff = np.abs(hist_doy - doy)
        diff = np.minimum(diff, 365 - diff)
        valid_indices = np.where(diff <= self.search_window_days)[0]
        max_idx = len(self.historical_dates) - lead_days - 1
        valid_indices = valid_indices[valid_indices <= max_idx]

        search_features = self.historical_features[valid_indices]
        knn = NearestNeighbors(n_neighbors=self.k_neighbors, metric="euclidean")
        knn.fit(search_features)
        distances, indices = knn.kneighbors(current_features)
        analog_indices = valid_indices[indices[0]]

        weights = 1.0 / (distances[0] + 1e-6)
        weights /= np.sum(weights)

        forecast_dates = [initial_date + pd.Timedelta(days=d) for d in range(1, lead_days + 1)]
        forecast_doy = self._compute_dayofyear(pd.DatetimeIndex(forecast_dates))

        forecast_sic = np.zeros((lead_days, len(self.lat), len(self.lon)))
        forecast_sica = np.zeros_like(forecast_sic)
        forecast_uncertainty = np.zeros_like(forecast_sic)
        forecast_q05 = np.zeros_like(forecast_sic)
        forecast_q95 = np.zeros_like(forecast_sic)
        forecast_clim = np.zeros_like(forecast_sic)

        for i, tau in enumerate(range(1, lead_days + 1)):
            target_indices = analog_indices + tau
            ensemble_sica = self.historical_targets[target_indices]

            pred_sica = np.average(ensemble_sica, axis=0, weights=weights)
            variance = np.average((ensemble_sica - pred_sica) ** 2, axis=0, weights=weights)
            pred_unc = np.sqrt(variance)
            pred_q05 = np.percentile(ensemble_sica, 5, axis=0)
            pred_q95 = np.percentile(ensemble_sica, 95, axis=0)

            c_doy = forecast_doy[i]
            clim_sic = self.climatology["sic"][c_doy]
            pred_sic = np.clip(clim_sic + pred_sica, 0.0, 100.0)

            pred_sic, pred_sica = self._drift_ice_correction(pred_sic, pred_sica, None)

            forecast_sic[i] = pred_sic
            forecast_sica[i] = pred_sica
            forecast_uncertainty[i] = pred_unc
            forecast_q05[i] = np.clip(clim_sic + pred_q05, 0.0, 100.0)
            forecast_q95[i] = np.clip(clim_sic + pred_q95, 0.0, 100.0)
            forecast_clim[i] = clim_sic

        return {
            "dates": forecast_dates,
            "sic": forecast_sic,
            "sica": forecast_sica,
            "sic_uncertainty": forecast_uncertainty,
            "sic_q05": forecast_q05,
            "sic_q95": forecast_q95,
            "sic_clim": forecast_clim,
        }

    def export_amip_netcdf(self, forecast: Dict[str, Any], output_path: Union[str, Path], model_name: str = "Ice-kNN-South"):
        times = pd.DatetimeIndex(forecast["dates"])
        lat_bnds = np.zeros((len(self.lat), 2))
        lat_bnds[:, 0] = self.lat - 0.25
        lat_bnds[:, 1] = self.lat + 0.25
        lon_bnds = np.zeros((len(self.lon), 2))
        lon_bnds[:, 0] = self.lon - 0.25
        lon_bnds[:, 1] = self.lon + 0.25

        ds = xr.Dataset(
            data_vars=dict(
                sic=(["time", "lat", "lon"], forecast["sic"], {"standard_name": "sea_ice_area_fraction", "units": "%", "_FillValue": 1.0e20, "long_name": "Sea Ice Concentration"}),
                sica=(["time", "lat", "lon"], forecast["sica"], {"standard_name": "sea_ice_area_fraction_anomaly", "units": "%", "_FillValue": 1.0e20, "long_name": "Sea Ice Concentration Anomaly"}),
                sic_uncertainty=(["time", "lat", "lon"], forecast["sic_uncertainty"], {"units": "%", "_FillValue": 1.0e20, "long_name": "Ensemble Standard Deviation"}),
                sic_q05=(["time", "lat", "lon"], forecast["sic_q05"], {"units": "%", "_FillValue": 1.0e20, "long_name": "5th Percentile"}),
                sic_q95=(["time", "lat", "lon"], forecast["sic_q95"], {"units": "%", "_FillValue": 1.0e20, "long_name": "95th Percentile"}),
                sic_clim=(["time", "lat", "lon"], forecast["sic_clim"], {"units": "%", "_FillValue": 1.0e20, "long_name": "Climatological SIC"}),
            ),
            coords=dict(
                time=(["time"], times, {"standard_name": "time", "axis": "T"}),
                lat=(["lat"], self.lat, {"standard_name": "latitude", "units": "degrees_north", "axis": "Y", "bounds": "lat_bnds"}),
                lon=(["lon"], self.lon, {"standard_name": "longitude", "units": "degrees_east", "axis": "X", "bounds": "lon_bnds"}),
            ),
            attrs=dict(
                title=f"{model_name} Sea Ice Forecast",
                institution="National Centre for Polar and Ocean Research (NCPOR) / AMIP",
                source="Ice-kNN-South (Lin et al. 2024/2025)",
                references="DOI: 10.1029/2024JH000433",
                conventions="CF-1.7, AMIP",
                history=f"Generated on {datetime.datetime.now().isoformat()}",
            ),
        )
        ds["lat_bnds"] = (["lat", "bnds"], lat_bnds)
        ds["lon_bnds"] = (["lon", "bnds"], lon_bnds)
        ds.to_netcdf(output_path, format="NETCDF4")

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "IceKNNSouthModel":
        return load_ice_knn_model(filepath)


def resolve_model_path(model_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Finds the ice_knn_south_model.pkl path across common repository locations.
    """
    if model_path is not None:
        p = Path(model_path)
        if p.is_file():
            return p

    candidates = [
        Path("model/ice_knn_south/models/ice_knn_south_model.pkl"),
        Path("ice_knn/models/ice_knn_south_model.pkl"),
        Path("models/ice_knn_south_model.pkl"),
        Path(__file__).resolve().parent.parent / "model" / "ice_knn_south" / "models" / "ice_knn_south_model.pkl",
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()
    raise FileNotFoundError(f"Trained Ice-kNN-South model .pkl not found. Checked: {[str(c) for c in candidates]}")


def resolve_netcdf_forecast_path(nc_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Finds the 90-day NetCDF forecast file across common repository locations.
    """
    if nc_path is not None:
        p = Path(nc_path)
        if p.is_file():
            return p

    candidates = [
        Path("model/ice_knn_south/models/amip_forecast_sample.nc"),
        Path("data/processed/ice_knn/amip_forecast_90d.nc"),
        Path("ice_knn/models/amip_forecast_sample.nc"),
        Path(__file__).resolve().parent.parent / "model" / "ice_knn_south" / "models" / "amip_forecast_sample.nc",
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()
    raise FileNotFoundError(f"NetCDF forecast not found. Checked: {[str(c) for c in candidates]}")


def load_ice_knn_model(model_path: Optional[Union[str, Path]] = None) -> IceKNNSouthModel:
    """
    Safely load the pre-trained Ice-kNN-South model from .pkl.
    Ensures __main__.IceKNNSouthModel resolves correctly to prevent unpickling errors.
    """
    resolved_path = resolve_model_path(model_path)
    
    # Register class alias in __main__ and sys.modules to satisfy pickle deserialization
    sys.modules.setdefault("__main__", sys.modules[__name__])
    setattr(sys.modules["__main__"], "IceKNNSouthModel", IceKNNSouthModel)
    
    loaded = joblib.load(resolved_path)
    return loaded
