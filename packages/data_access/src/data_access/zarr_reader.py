"""Zarr / Multidimensional Environmental Cube Reader and Deterministic Mock Generator."""
import math
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from core.config import settings
from core.logging import get_logger
from domain.coordinates import BoundingBox, GridSpec

logger = get_logger("data_access.zarr_reader")


class ZarrReader:
    """
    Reads 2D and 3D scientific raster variables from consolidated Zarr arrays.
    In MOCK_MODE, deterministically synthesizes coherent Antarctic physical fields.
    """

    def __init__(self, zarr_base_path: Optional[str] = None):
        self.base_path = zarr_base_path or str(settings.DATA_DIR / "processed")

    def get_grid_slice(
        self,
        variable: str,
        valid_time: datetime,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Retrieves a 2D grid slice for variable at valid_time.
        Returns:
            lats (1D array), lons (1D array), values (2D array [n_lat, n_lon])
        """
        if bbox is None:
            bbox = BoundingBox(
                min_latitude=-80.0,
                min_longitude=-20.0,
                max_latitude=-30.0,
                max_longitude=100.0,
            )

        n_lat = grid_spec.n_lat if grid_spec else 60
        n_lon = grid_spec.n_lon if grid_spec else 120

        lats = np.linspace(bbox.min_latitude, bbox.max_latitude, n_lat)
        lons = np.linspace(bbox.min_longitude, bbox.max_longitude, n_lon)

        # In Mock Mode, synthesize deterministic physical fields
        values = self._synthesize_mock_field(variable, valid_time, lats, lons)
        return lats, lons, values

    def _synthesize_mock_field(
        self,
        variable: str,
        valid_time: datetime,
        lats: np.ndarray,
        lons: np.ndarray,
    ) -> np.ndarray:
        """
        Synthesizes deterministic, physically plausible fields for the Southern Ocean transect.
        Uses time day-of-year to simulate realistic seasonal cycles.
        """
        lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")
        day_of_year = valid_time.timetuple().tm_yday

        # Seasonal phase factor (summer minimum in Feb around day 45-60, winter maximum in Sept day 260)
        seasonal_phase = math.cos(2.0 * math.pi * (day_of_year - 260) / 365.25)
        # Ice edge latitude varies between ~ -60 (winter) and -66 (summer)
        ice_edge_lat = -66.0 + (seasonal_phase * 6.0)

        if variable == "sea_ice_concentration":
            # 0.0 north of ice edge, transitions to high concentration (up to 0.95) south
            delta = ice_edge_lat - lat_grid
            sic = 1.0 / (1.0 + np.exp(-0.8 * delta))
            # Smooth mask north of ice edge
            sic[lat_grid > ice_edge_lat] = 0.0
            # Add subtle deterministic spatial perturbation
            perturb = 0.05 * np.sin(np.radians(lon_grid * 4.0)) * np.cos(np.radians(lat_grid * 2.0))
            sic = np.clip(sic + perturb, 0.0, 1.0)
            return sic

        elif variable == "sic_uncertainty":
            # Uncertainty peaks at the dynamic ice edge zone
            dist_to_edge = np.abs(lat_grid - ice_edge_lat)
            unc = 0.25 * np.exp(-0.5 * (dist_to_edge / 2.0) ** 2)
            # Modulate with lead time if simulated
            return np.clip(unc, 0.01, 0.50)

        elif variable == "bathymetry":
            # Deep ocean (> 3500m) in Southern Ocean, shoaling near continental shelf south of -68
            depth = 3800.0 + 800.0 * np.sin(np.radians(lon_grid))
            # Continental slope shelf shoaling
            shelf_factor = 1.0 / (1.0 + np.exp(0.5 * (lat_grid + 67.0)))
            depth = depth * (1.0 - 0.9 * shelf_factor)
            # Land mask south of -72
            depth[lat_grid < -72.0] = -50.0  # Land / ice shelf elevation above sea level
            return depth

        elif variable in ("wind_u", "u10", "wind_u10"):
            # Strong westerly winds between -40S and -60S (Roaring Forties)
            peak_westerly = 14.0 + 4.0 * seasonal_phase
            return peak_westerly * np.exp(-0.5 * ((lat_grid + 50.0) / 8.0) ** 2)

        elif variable in ("wind_v", "v10", "wind_v10"):
            # Meridional wind component with cyclonic perturbations
            return 3.0 * np.sin(np.radians(lon_grid * 3.0))

        elif variable in ("ocean_u", "uC", "ocean_current_u"):
            # Antarctic Circumpolar Current (ACC) flowing east (~0.3 to 0.5 m/s) at -50S
            acc = 0.45 * np.exp(-0.5 * ((lat_grid + 52.0) / 6.0) ** 2)
            # Coastal current flowing west (-0.15 m/s) near -68S
            coastal = -0.20 * np.exp(-0.5 * ((lat_grid + 68.0) / 2.0) ** 2)
            return acc + coastal

        elif variable in ("ocean_v", "vC", "ocean_current_v"):
            return 0.05 * np.cos(np.radians(lon_grid * 2.0))

        elif variable in ("significant_wave_height", "wave_hs", "wave_height"):
            # Wave height peaks in the Southern Ocean belt
            return 3.5 + 2.0 * np.exp(-0.5 * ((lat_grid + 52.0) / 7.0) ** 2)

        elif variable in ("wave_peak_period", "wave_tp"):
            return 11.0 + 3.0 * np.exp(-0.5 * ((lat_grid + 52.0) / 8.0) ** 2)

        elif variable == "sst":
            # Sea Surface Temperature: ~18C near Cape Town (-34S), dropping to -1.8C near sea-ice edge
            temp = 18.0 - (19.8 / (1.0 + np.exp(-0.15 * (lat_grid + 50.0))))
            return np.clip(temp, -1.8, 25.0)

        else:
            # Generic normalized scalar
            return np.zeros_like(lat_grid)


default_zarr_reader = ZarrReader()
