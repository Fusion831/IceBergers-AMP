"""
Environmental Data Provider Interface and Synthetic Mock Implementation.
Clean interface designed to allow future real Copernicus/ECMWF/NSIDC/GEBCO integration.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import numpy as np

from domain.coordinates import BoundingBox, GridSpec, GeoPoint
from data_access.zarr_reader import default_zarr_reader


class EnvironmentalDataProviderInterface(ABC):
    """
    Abstract interface for retrieving marine and atmospheric environmental conditions.
    Decouples routing, risk, and mission planning from the underlying data source
    (whether synthetic physics mock or real Copernicus Marine / ECMWF feeds).
    """

    @abstractmethod
    def get_point_environment(
        self,
        point: GeoPoint,
        valid_time: datetime,
    ) -> Dict[str, float]:
        """
        Query physical state at a specific coordinate and time.
        Returns:
            dict with:
                - sea_ice_concentration (0.0 to 1.0)
                - bathymetry_depth_m (positive depth in meters)
                - wave_height_m (significant wave height H_s)
                - wind_speed_ms (10m surface wind magnitude)
                - current_u_ms (eastward ocean current)
                - current_v_ms (northward ocean current)
                - is_land (1.0 if land/ice-shelf, 0.0 otherwise)
        """
        pass

    @abstractmethod
    def get_grid_slice(
        self,
        variable: str,
        valid_time: datetime,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Retrieve 2D spatial grid slice [lats, lons, values]."""
        pass


class SyntheticEnvironmentalDataProvider(EnvironmentalDataProviderInterface):
    """
    Deterministic synthetic implementation for testing, demonstration, and MOCK_MODE.
    Synthesizes physically coherent Antarctic fields without external API dependencies.
    """

    def __init__(self, reader=None):
        self.reader = reader or default_zarr_reader

    def get_point_environment(
        self,
        point: GeoPoint,
        valid_time: datetime,
    ) -> Dict[str, float]:
        # Sample directly from the deterministic synthesizer
        lats = np.array([point.latitude])
        lons = np.array([point.longitude])

        sic = float(self.reader._synthesize_mock_field("sea_ice_concentration", valid_time, lats, lons)[0, 0])
        depth = float(self.reader._synthesize_mock_field("bathymetry", valid_time, lats, lons)[0, 0])
        waves = float(self.reader._synthesize_mock_field("wave_height", valid_time, lats, lons)[0, 0])
        current_u = float(self.reader._synthesize_mock_field("ocean_current_u", valid_time, lats, lons)[0, 0])
        current_v = float(self.reader._synthesize_mock_field("ocean_current_v", valid_time, lats, lons)[0, 0])
        wind_u = float(self.reader._synthesize_mock_field("wind_u10", valid_time, lats, lons)[0, 0])
        wind_v = float(self.reader._synthesize_mock_field("wind_v10", valid_time, lats, lons)[0, 0])
        wind_speed = float(np.sqrt(wind_u**2 + wind_v**2))
        is_land = 1.0 if depth <= 0.0 or point.latitude < -78.0 else 0.0

        return {
            "sea_ice_concentration": round(sic, 4),
            "bathymetry_depth_m": round(depth, 1),
            "wave_height_m": round(waves, 2),
            "wind_speed_ms": round(wind_speed, 2),
            "current_u_ms": round(current_u, 3),
            "current_v_ms": round(current_v, 3),
            "is_land": is_land,
        }

    def get_grid_slice(
        self,
        variable: str,
        valid_time: datetime,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        return self.reader.get_grid_slice(variable, valid_time, bbox, grid_spec)


class CoupledEnvironmentalDataProvider(EnvironmentalDataProviderInterface):
    """
    Unified environmental data provider coupling physical marine fields (currents, waves,
    wind, bathymetry) with the Ice-kNN-South Sea-Ice Concentration model.
    """

    def __init__(self, reader=None, sea_ice_provider=None):
        self.reader = reader or default_zarr_reader
        from data_access.sea_ice_provider import get_sea_ice_provider
        import os
        default_src = os.environ.get("AMIP_SIC_PROVIDER", "synthetic_trend")
        default_scenario = os.environ.get("AMIP_SIC_SCENARIO", "historical_trend_normal")
        self.sea_ice_provider = sea_ice_provider or get_sea_ice_provider(source=default_src, scenario=default_scenario)

    def get_point_environment(
        self,
        point: GeoPoint,
        valid_time: datetime,
        cell_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        lats = np.array([point.latitude])
        lons = np.array([point.longitude])

        depth = float(self.reader._synthesize_mock_field("bathymetry", valid_time, lats, lons)[0, 0])
        waves = float(self.reader._synthesize_mock_field("wave_height", valid_time, lats, lons)[0, 0])
        current_u = float(self.reader._synthesize_mock_field("ocean_current_u", valid_time, lats, lons)[0, 0])
        current_v = float(self.reader._synthesize_mock_field("ocean_current_v", valid_time, lats, lons)[0, 0])
        wind_u = float(self.reader._synthesize_mock_field("wind_u10", valid_time, lats, lons)[0, 0])
        wind_v = float(self.reader._synthesize_mock_field("wind_v10", valid_time, lats, lons)[0, 0])
        wind_speed = float(np.sqrt(wind_u**2 + wind_v**2))
        is_land = 1.0 if depth <= 0.0 or point.latitude < -78.0 else 0.0

        # Query active sea-ice provider
        sic_info = self.sea_ice_provider.get_sea_ice_at(
            cell_id=cell_id or "",
            valid_time=valid_time,
            lat=point.latitude,
            lon=point.longitude,
        )

        return {
            "sea_ice_concentration": sic_info["sea_ice_concentration"],
            "sea_ice_percent": sic_info.get("sea_ice_percent", sic_info["sea_ice_concentration"] * 100.0),
            "sea_ice_uncertainty": sic_info.get("sea_ice_uncertainty", 0.0),
            "sic_q05": sic_info.get("sic_q05", 0.0),
            "sic_q95": sic_info.get("sic_q95", 0.0),
            "sic_clim": sic_info.get("sic_clim", 0.0),
            "is_mock_sic": sic_info.get("is_mock", False),
            "sic_source": sic_info.get("source", self.sea_ice_provider.source_name),
            "bathymetry_depth_m": round(depth, 1),
            "wave_height_m": round(waves, 2),
            "wind_speed_ms": round(wind_speed, 2),
            "current_u_ms": round(current_u, 3),
            "current_v_ms": round(current_v, 3),
            "is_land": is_land,
        }

    def get_grid_slice(
        self,
        variable: str,
        valid_time: datetime,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        return self.reader.get_grid_slice(variable, valid_time, bbox, grid_spec)


default_environment_provider = CoupledEnvironmentalDataProvider()

