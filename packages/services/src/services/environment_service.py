"""Environment Service coordinating data access, time-slider slicing, and point queries."""

from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any
import numpy as np
from core.config import settings
from domain.coordinates import BoundingBox, GridSpec, GeoPoint
from domain.environment import GridSlice, PointEnvironment
from data_access.zarr_reader import default_zarr_reader


class EnvironmentService:
    """Provides unified access to time-varying gridded environmental fields."""

    def __init__(self, zarr_reader=None):
        self.reader = zarr_reader or default_zarr_reader

    def get_slice(
        self,
        valid_time: datetime,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
        variable: Optional[str] = None,
    ) -> GridSlice:
        """Retrieves a 2D slice of environmental layers for map/slider rendering."""
        bounds = bbox or BoundingBox(
            min_latitude=-75.0,
            max_latitude=-50.0,
            min_longitude=0.0,
            max_longitude=80.0,
        )
        grid = grid_spec or GridSpec(bounds=bounds, n_lat=50, n_lon=50)

        # Synthesize multiple key physical layers
        _, _, sst = self.reader.get_grid_slice("sst", valid_time, bounds, grid)
        _, _, sic = self.reader.get_grid_slice("sea_ice_concentration", valid_time, bounds, grid)
        _, _, wind_u = self.reader.get_grid_slice("wind_u", valid_time, bounds, grid)
        _, _, wind_v = self.reader.get_grid_slice("wind_v", valid_time, bounds, grid)
        _, _, curr_u = self.reader.get_grid_slice("ocean_u", valid_time, bounds, grid)
        _, _, curr_v = self.reader.get_grid_slice("ocean_v", valid_time, bounds, grid)
        _, _, wave_hs = self.reader.get_grid_slice("significant_wave_height", valid_time, bounds, grid)
        _, _, depth = self.reader.get_grid_slice("bathymetry", valid_time, bounds, grid)

        wind_spd = np.sqrt(wind_u ** 2 + wind_v ** 2) * 1.94384
        curr_spd = np.sqrt(curr_u ** 2 + curr_v ** 2) * 1.94384

        layers = {
            "sea_surface_temperature_c": sst.tolist(),
            "sea_ice_concentration": sic.tolist(),
            "wind_speed_knots": wind_spd.tolist(),
            "ocean_current_speed_knots": curr_spd.tolist(),
            "significant_wave_height_m": wave_hs.tolist(),
            "bathymetry_m": depth.tolist(),
        }

        # Calculate lead time in days
        now = datetime.now(timezone.utc)
        lead_days = max(0, (valid_time.date() - now.date()).days)

        return GridSlice(
            variable=variable or "multi-layer",
            units="physical",
            valid_time=valid_time,
            lead_time_days=lead_days,
            bounds=bounds,
            bbox=bounds,
            grid_shape=list(sst.shape),
            min_value=float(np.min(sic)),
            max_value=float(np.max(sic)),
            mean_value=float(np.mean(sic)),
            values=sic.tolist(),
            layers=layers,
            data_ref=f"zarr://antarctic_cube/{valid_time.strftime('%Y%m%d')}",
        )

    def get_layer_slice(
        self,
        variable: str,
        valid_time: datetime,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
    ) -> GridSlice:
        return self.get_slice(valid_time, bbox, grid_spec, variable)

    def get_point(
        self,
        point: GeoPoint,
        valid_time: datetime,
    ) -> PointEnvironment:
        """Inspects all environmental variables at a specific point coordinate and time."""
        lat = point.latitude
        lon = point.longitude

        # Synthesize point conditions
        _, _, sic_grid = self.reader.get_grid_slice("sea_ice_concentration", valid_time)
        _, _, sst_grid = self.reader.get_grid_slice("sst", valid_time)
        _, _, wind_u = self.reader.get_grid_slice("wind_u", valid_time)
        _, _, wind_v = self.reader.get_grid_slice("wind_v", valid_time)
        _, _, curr_u = self.reader.get_grid_slice("ocean_u", valid_time)
        _, _, curr_v = self.reader.get_grid_slice("ocean_v", valid_time)
        _, _, wave_hs = self.reader.get_grid_slice("significant_wave_height", valid_time)
        _, _, wave_tp = self.reader.get_grid_slice("wave_peak_period", valid_time)
        _, _, depth_grid = self.reader.get_grid_slice("bathymetry", valid_time)

        i = int(np.clip((lat + 80.0) / 50.0 * (sic_grid.shape[0] - 1), 0, sic_grid.shape[0] - 1))
        j = int(np.clip((lon + 20.0) / 120.0 * (sic_grid.shape[1] - 1), 0, sic_grid.shape[1] - 1))

        sic_val = float(sic_grid[i, j])
        w_speed = float(np.sqrt(wind_u[i, j] ** 2 + wind_v[i, j] ** 2) * 1.94384)
        c_speed = float(np.sqrt(curr_u[i, j] ** 2 + curr_v[i, j] ** 2) * 1.94384)
        depth_val = float(depth_grid[i, j])

        return PointEnvironment(
            position=point,
            point=point,
            timestamp=valid_time,
            valid_time=valid_time,
            sea_ice_concentration=round(sic_val, 3),
            ice_thickness_m=round(sic_val * 1.4, 2),
            sea_surface_temp_c=round(float(sst_grid[i, j]), 1),
            sst_c=round(float(sst_grid[i, j]), 1),
            wind_speed_knots=round(w_speed, 1),
            wind_speed=round(w_speed, 1),
            wind_direction_deg=275.0,
            ocean_current_speed_knots=round(c_speed, 2),
            ocean_current_direction_deg=90.0,
            significant_wave_height_m=round(float(wave_hs[i, j]), 1),
            wave_height_m=round(float(wave_hs[i, j]), 1),
            wave_peak_period_s=round(float(wave_tp[i, j]), 1),
            water_depth_m=round(depth_val, 1),
            depth_m=round(depth_val, 1),
            is_land=depth_val <= 0.0,
        )

    def get_point_environment(self, point: GeoPoint, timestamp: datetime) -> PointEnvironment:
        return self.get_point(point, timestamp)


default_environment_service = EnvironmentService()
