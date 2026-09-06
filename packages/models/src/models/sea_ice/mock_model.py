"""Deterministic Mock Sea-Ice Model for AMIP POC."""

import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any
import numpy as np
from domain.coordinates import BoundingBox, GridSpec
from domain.sea_ice import (
    SeaIceForecast,
    SeaIceUncertainty,
    SeaIcePredictionResult,
)
from data_access.zarr_reader import default_zarr_reader


class MockSeaIceModel:
    """
    Deterministic mock sea-ice forecasting model.
    Produces spatially and temporally coherent Antarctic SIC grids and uncertainty bounds.
    """

    def __init__(self, version: str = "v1.0.0-mock"):
        self._version = version

    @property
    def model_name(self) -> str:
        return "AMIP-Mock-UNet-v1"

    @property
    def version(self) -> str:
        return self._version

    @property
    def is_mock(self) -> bool:
        return True

    def predict(
        self,
        reference_time: Optional[datetime] = None,
        horizon_days: int = 14,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
        initialization_time: Optional[datetime] = None,
    ) -> SeaIcePredictionResult:
        init_time = initialization_time or reference_time or datetime.now(timezone.utc)
        valid_time = init_time + timedelta(days=horizon_days)

        bounds = bbox or BoundingBox(
            min_latitude=-75.0,
            max_latitude=-50.0,
            min_longitude=0.0,
            max_longitude=80.0,
        )
        grid = grid_spec or GridSpec(bounds=bounds, n_lat=50, n_lon=50)

        # Retrieve deterministic physical field from Zarr reader
        lats, lons, sic_grid = default_zarr_reader.get_grid_slice(
            variable="sea_ice_concentration",
            valid_time=valid_time,
            bbox=bounds,
            grid_spec=grid,
        )

        _, _, spatial_unc = default_zarr_reader.get_grid_slice(
            variable="sic_uncertainty",
            valid_time=valid_time,
            bbox=bounds,
            grid_spec=grid,
        )

        # Monotonically increasing uncertainty with lead time horizon
        horizon_growth = 0.02 + 0.002 * horizon_days
        total_variance = np.clip(spatial_unc * 0.5 + horizon_growth, 0.01, 0.50)

        mean_sic = float(np.mean(sic_grid))
        cell_area_km2 = 100.0
        ice_cells = int(np.sum(sic_grid > 0.15))
        total_ice_area = float(ice_cells * cell_area_km2)

        # Generate 15% ice edge contour as GeoJSON LineString
        ice_edge_coords = []
        step = max(1, len(lons) // 20)
        for j in range(0, len(lons), step):
            col_sic = sic_grid[:, j]
            idx = int(np.argmin(np.abs(col_sic - 0.15)))
            ice_edge_coords.append([round(float(lons[j]), 4), round(float(lats[idx]), 4)])

        contour_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "contour_level": 0.15,
                        "valid_time": valid_time.isoformat(),
                        "horizon_days": horizon_days,
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": ice_edge_coords,
                    },
                }
            ],
        }

        forecast = SeaIceForecast(
            forecast_id=f"fc-sic-{valid_time.strftime('%Y%m%d')}-h{horizon_days}",
            model_name=self.model_name,
            model_version=self.version,
            initialization_time=init_time,
            valid_time=valid_time,
            lead_time_days=horizon_days,
            bounds=bounds,
            mean_sic=round(mean_sic, 4),
            total_ice_area_sqkm=round(total_ice_area, 1),
            ice_edge_perimeter_km=round(len(ice_edge_coords) * 25.0, 1),
            data_ref=f"data/processed/fused_antarctic_cube.zarr/sea_ice_concentration/{valid_time.strftime('%Y%m%d')}",
            values=sic_grid.tolist(),
            is_mock=True,
        )

        uncertainty = SeaIceUncertainty(
            forecast_id=forecast.forecast_id,
            valid_time=valid_time,
            mean_variance=round(float(np.mean(total_variance)), 4),
            p10_data_ref=f"{forecast.data_ref}/p10",
            p50_data_ref=f"{forecast.data_ref}/p50",
            p90_data_ref=f"{forecast.data_ref}/p90",
            high_uncertainty_area_sqkm=round(float(np.sum(total_variance > 0.20) * cell_area_km2), 1),
            values=total_variance.tolist(),
        )

        return SeaIcePredictionResult(
            forecast=forecast,
            uncertainty=uncertainty,
            contour_15pct_geojson=contour_geojson,
            ice_edge_geojson=contour_geojson,
        )

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "version": self.version,
            "architecture": "Deterministic Synthetic U-Net Mock with Climatological Prior",
            "input_variables": ["sic_lag7", "sst", "u10", "v10", "ocean_u", "ocean_v"],
            "training_date": "2026-08-15T00:00:00Z",
            "validation_rmse": 0.084,
            "is_mock": True,
            "checksum": "mock-checksum-sha256-amip-unet-v1",
        }
