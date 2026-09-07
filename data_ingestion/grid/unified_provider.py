"""
Unified Environmental Data Provider for AMIP.
Implements EnvironmentalDataProviderInterface, supplying real NSIDC Sea Ice observations
alongside physical hydrodynamics and bathymetry fields.
"""

from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import numpy as np
from domain.coordinates import GeoPoint, BoundingBox, GridSpec
from data_access.environment_provider import EnvironmentalDataProviderInterface, default_environment_provider
from data_ingestion.nsidc.interface import NSIDCSeaIceInterface
from data_ingestion.grid.amip_grid import AMIPGrid
from data_ingestion.grid.environment_cell import EnvironmentCell
from core.logging import get_logger

logger = get_logger("data_ingestion.grid.unified_provider")


class AMIPUnifiedEnvironmentalProvider(EnvironmentalDataProviderInterface):
    """
    Environmental data provider uniting real satellite/reanalysis datasets
    with the AMIP canonical computational grid.
    """

    def __init__(
        self,
        nsidc_interface: Optional[NSIDCSeaIceInterface] = None,
        fallback_provider: Optional[EnvironmentalDataProviderInterface] = None,
    ):
        self.nsidc = nsidc_interface or NSIDCSeaIceInterface()
        self.fallback = fallback_provider or default_environment_provider
        self.grid = AMIPGrid()

    def get_point_environment(
        self,
        point: GeoPoint,
        valid_time: datetime,
    ) -> Dict[str, float]:
        """
        Query physical state at a specific coordinate and time.
        Uses real NSIDC SIC if available, falling back to physical base provider.
        """
        # Baseline physical state from fallback
        env = self.fallback.get_point_environment(point, valid_time)

        # Attempt to inject real NSIDC SIC
        real_sic = self.nsidc.get_sic_point(point, valid_time)
        if real_sic is not None:
            # Normalize % to [0.0, 1.0] for the provider interface
            env["sea_ice_concentration"] = round(real_sic / 100.0, 4)
            env["sic_source"] = "NSIDC_G02202_v6"
        else:
            env["sic_source"] = "synthetic_fallback"

        return env

    def get_environment_cell(
        self,
        point: GeoPoint,
        valid_time: datetime,
    ) -> Optional[EnvironmentCell]:
        """
        Returns a populated canonical EnvironmentCell for the grid cell containing point.
        """
        cell = self.grid.find_cell(point.latitude, point.longitude)
        if not cell:
            return None

        env = self.get_point_environment(point, valid_time)

        return EnvironmentCell(
            cell_id=cell.cell_id,
            valid_time=valid_time,
            latitude=cell.centroid_lat,
            longitude=cell.centroid_lon,
            lat_min=cell.lat_min,
            lat_max=cell.lat_max,
            lon_min=cell.lon_min,
            lon_max=cell.lon_max,
            sea_ice_concentration=round(env["sea_ice_concentration"] * 100.0, 2),
            current_u_ms=env.get("current_u_ms"),
            current_v_ms=env.get("current_v_ms"),
            wind_speed_ms=env.get("wind_speed_ms"),
            wave_height_m=env.get("wave_height_m"),
            bathymetry_depth_m=env.get("bathymetry_depth_m"),
            is_land=bool(env.get("is_land", 0.0) == 1.0),
            is_navigable=bool(env.get("is_land", 0.0) == 0.0 and env.get("sea_ice_concentration", 0.0) <= 0.85),
            provenance={"sic_source": env.get("sic_source", "unknown")},
        )

    def get_grid_slice(
        self,
        variable: str,
        valid_time: datetime,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Retrieve 2D spatial grid slice [lats, lons, values]."""
        return self.fallback.get_grid_slice(variable, valid_time, bbox, grid_spec)
