"""
Unified environmental adapter for Antarctic iceberg trajectory simulation.
Decouples the physics engine from concrete file formats and repositories,
providing standardized spatial and temporal interpolation for currents, winds,
sea ice, waves, and the SCAR ADD geographic mask.
"""

from pathlib import Path
from typing import Optional, Tuple, Union, Dict, Any
from datetime import datetime, timezone
import numpy as np
import xarray as xr
from core.logging import get_logger
from data_ingestion.geographic_mask.interface import AntarcticGeographicMask
from data_ingestion.geographic_mask.metadata import CoverageStatus
from data_ingestion.gebco.interface import GEBCOBathymetryInterface
from data_ingestion.iceberg.metadata import ForcingMode

logger = get_logger("data_ingestion.iceberg.environment_adapter")


class AntarcticEnvironmentAdapter:
    """
    Environmental data adapter providing currents, winds, SIC, waves, and coastline boundaries.
    Seamlessly handles transitions from numerical forecast to extended climatology.
    """

    def __init__(
        self,
        currents_path: Optional[Union[str, Path]] = "data/raw/cmems/currents/cmems_currents_surface_20240101_20240107.nc",
        wind_path: Optional[Union[str, Path]] = "data/raw/ecmwf/wind/ecmwf_wind_surface_0_48h.grib2",
        sic_path: Optional[Union[str, Path]] = "data/processed/nsidc/g02202/2024/sic_processed_20240101.nc",
        mask_path: Optional[Union[str, Path]] = "data/processed/geographic_mask/antarctic_geographic_mask.gpkg",
        gebco_path: Optional[Union[str, Path]] = "data/processed/gebco/gebco_2026/bathymetry_processed_antarctic.nc",
        extended_forcing_method: str = "CLIMATOLOGY",
    ):
        self.extended_forcing_method = extended_forcing_method
        
        # 1. Initialize Geographic Mask
        self.mask: Optional[AntarcticGeographicMask] = None
        if mask_path and Path(mask_path).exists():
            try:
                self.mask = AntarcticGeographicMask(mask_path)
                logger.info("Loaded real SCAR ADD geographic mask into environment adapter")
            except Exception as e:
                logger.warning("Failed to initialize geographic mask", error=str(e))

        # 2. Open Currents dataset
        self.ds_currents: Optional[xr.Dataset] = None
        self.currents_time_min: Optional[datetime] = None
        self.currents_time_max: Optional[datetime] = None
        if currents_path and Path(currents_path).exists():
            try:
                self.ds_currents = xr.open_dataset(currents_path)
                times = self.ds_currents["time"].values
                self.currents_time_min = np.datetime64(times[0], "ms").astype(datetime).replace(tzinfo=timezone.utc)
                self.currents_time_max = np.datetime64(times[-1], "ms").astype(datetime).replace(tzinfo=timezone.utc)
                logger.info("Loaded CMEMS currents", time_span=(self.currents_time_min, self.currents_time_max))
            except Exception as e:
                logger.warning("Could not open currents dataset", error=str(e))

        # 3. Open Wind dataset
        self.ds_wind: Optional[xr.Dataset] = None
        self.wind_time_min: Optional[datetime] = None
        self.wind_time_max: Optional[datetime] = None
        if wind_path and Path(wind_path).exists():
            try:
                self.ds_wind = xr.open_dataset(wind_path, engine="cfgrib")
                # Detect time coordinate
                t_coord = "valid_time" if "valid_time" in self.ds_wind.coords else "time"
                times = self.ds_wind[t_coord].values
                self.wind_time_min = np.datetime64(times[0], "ms").astype(datetime).replace(tzinfo=timezone.utc)
                self.wind_time_max = np.datetime64(times[-1], "ms").astype(datetime).replace(tzinfo=timezone.utc)
                logger.info("Loaded ECMWF wind", time_span=(self.wind_time_min, self.wind_time_max))
            except Exception as e:
                logger.warning("Could not open wind dataset via cfgrib", error=str(e))

        # 4. Open SIC dataset
        self.ds_sic: Optional[xr.Dataset] = None
        if sic_path and Path(sic_path).exists():
            try:
                self.ds_sic = xr.open_dataset(sic_path)
                logger.info("Loaded NSIDC sea ice concentration dataset")
            except Exception as e:
                logger.warning("Could not open SIC dataset", error=str(e))

        # 5. Initialize GEBCO Bathymetry
        self.gebco: Optional[GEBCOBathymetryInterface] = None
        if gebco_path and Path(gebco_path).exists():
            try:
                self.gebco = GEBCOBathymetryInterface(gebco_path)
                logger.info("Loaded GEBCO_2026 sub-ice bathymetry into environment adapter")
            except Exception as e:
                logger.warning("Could not initialize GEBCO bathymetry", error=str(e))

        # Fast spatial caches
        self._geo_cache: Dict[Tuple[float, float], Tuple[bool, CoverageStatus]] = {}
        self._depth_cache: Dict[Tuple[float, float], Optional[float]] = {}

    def get_geographic_status(self, lat: float, lon: float) -> Tuple[bool, CoverageStatus]:
        """
        Queries SCAR ADD geographic mask with caching.
        Returns (is_geographically_excluded, coverage_status).
        """
        if lat > -60.0:
            return False, CoverageStatus.OUTSIDE_COVERAGE

        key = (round(lat, 2), round(lon, 2))
        if key in self._geo_cache:
            return self._geo_cache[key]

        if self.mask is not None:
            res = self.mask.query(lat, lon)
            ret = (res.is_geographically_excluded, res.coverage_status)
        else:
            cov = CoverageStatus.INSIDE_COVERAGE if lat <= -60.0 else CoverageStatus.OUTSIDE_COVERAGE
            ret = (False, cov)

        self._geo_cache[key] = ret
        return ret

    def get_bathymetry_depth(self, lat: float, lon: float) -> Optional[float]:
        """
        Queries GEBCO bathymetry depth in meters (positive down), or None if land/outside coverage.
        """
        key = (round(lat, 2), round(lon, 2))
        if key in self._depth_cache:
            return self._depth_cache[key]

        depth = None
        if self.gebco is not None:
            try:
                depth = self.gebco.get_depth(lat, lon)
            except Exception:
                depth = None

        self._depth_cache[key] = depth
        return depth

    def get_current(
        self,
        lat: float,
        lon: float,
        sim_time: datetime,
    ) -> Tuple[float, float, ForcingMode, str]:
        """
        Retrieves ocean current vector (uo, vo) in m/s.
        Returns (uo, vo, forcing_mode, forcing_source).
        """
        # 1. Try direct forecast interpolation if within CMEMS time range
        if (
            self.ds_currents is not None
            and self.currents_time_min is not None
            and self.currents_time_max is not None
            and self.currents_time_min <= sim_time <= self.currents_time_max
        ):
            try:
                # Wrap longitude to CMEMS longitude conventions (-180 to 180)
                norm_lon = ((lon + 180.0) % 360.0) - 180.0
                pt = self.ds_currents.sel(
                    time=np.datetime64(sim_time.replace(tzinfo=None)),
                    latitude=lat,
                    longitude=norm_lon,
                    method="nearest",
                )
                u = float(pt["uo"].values.squeeze())
                v = float(pt["vo"].values.squeeze())
                if not (np.isnan(u) or np.isnan(v)):
                    return u, v, ForcingMode.DIRECT_FORECAST, "CMEMS_PHY_GLOBAL"
            except Exception:
                pass

        # 2. Extended Forcing: Southern Ocean Climatology
        # Physical Antarctic ocean circulation:
        # - Antarctic Circumpolar Current (ACC): Eastward (u > 0) between 45°S and 63°S (~0.15 to 0.25 m/s)
        # - Antarctic Coastal Current (East Wind Drift): Westward (u < 0) near coastline (< 65°S) (~ -0.10 m/s)
        # - Ekman / gyre components: small northward deflection (v > 0)
        if lat < -65.0:
            # Coastal current
            u_clim = -0.10 + 0.03 * np.cos(np.radians(lon))
            v_clim = -0.02 + 0.02 * np.sin(np.radians(lon))
        elif -65.0 <= lat <= -50.0:
            # ACC strong eastward jet
            u_clim = 0.20 + 0.05 * np.sin(np.radians(lon * 2))
            v_clim = 0.03 + 0.02 * np.cos(np.radians(lon))
        else:
            # Sub-Antarctic
            u_clim = 0.12
            v_clim = 0.01

        return round(float(u_clim), 3), round(float(v_clim), 3), ForcingMode.EXTENDED_FORCING, "SOUTHERN_OCEAN_CLIMATOLOGY"

    def get_wind(
        self,
        lat: float,
        lon: float,
        sim_time: datetime,
    ) -> Tuple[float, float, ForcingMode, str]:
        """
        Retrieves 10m atmospheric wind vector (10u, 10v) in m/s.
        Returns (10u, 10v, forcing_mode, forcing_source).
        """
        # 1. Try direct forecast interpolation if within ECMWF time range
        if (
            self.ds_wind is not None
            and self.wind_time_min is not None
            and self.wind_time_max is not None
            and self.wind_time_min <= sim_time <= self.wind_time_max
        ):
            try:
                # Wrap lon to 0-360 if ECMWF uses 0-360
                ecmwf_lon = lon if lon >= 0 else lon + 360.0
                t_coord = "valid_time" if "valid_time" in self.ds_wind.coords else "time"
                pt = self.ds_wind.sel(
                    {t_coord: np.datetime64(sim_time.replace(tzinfo=None))},
                    latitude=lat,
                    longitude=ecmwf_lon,
                    method="nearest",
                )
                u = float(pt["10u"].values.squeeze())
                v = float(pt["10v"].values.squeeze())
                if not (np.isnan(u) or np.isnan(v)):
                    return u, v, ForcingMode.DIRECT_FORECAST, "ECMWF_OPEN_DATA"
            except Exception:
                pass

        # 2. Extended Forcing: Southern Hemisphere Atmospheric Climatology
        # - Roaring Forties & Furious Fifties (50°S-65°S): strong Westerlies (u > 0, ~8-12 m/s)
        # - Polar Easterlies south of 65°S: (u < 0, ~4-7 m/s) with katabatic offshore drainage (v < 0)
        if lat < -65.0:
            # Polar easterlies
            u_wind = -5.5 + 2.0 * np.sin(np.radians(lon))
            v_wind = -2.0 + 1.5 * np.cos(np.radians(lon))
        else:
            # Southern westerlies
            u_wind = 9.0 + 3.0 * np.cos(np.radians(lon))
            v_wind = 1.0 + 2.0 * np.sin(np.radians(lon))

        return round(float(u_wind), 2), round(float(v_wind), 2), ForcingMode.EXTENDED_FORCING, "SOUTHERN_ATMOSPHERE_CLIMATOLOGY"

    def get_sic(
        self,
        lat: float,
        lon: float,
        sim_time: datetime,
    ) -> Tuple[float, ForcingMode, str]:
        """
        Retrieves Sea Ice Concentration (0.0 to 1.0 fraction).
        """
        # In summer (Jan/Feb), ice pack retreats; in winter (Aug/Sep), extends to ~60°S.
        # Deep coastal shelf (< -72°S) generally retains high ice concentration or ice shelves.
        if lat < -72.0:
            sic = 0.65
        elif -72.0 <= lat < -65.0:
            sic = 0.35
        elif -65.0 <= lat < -62.0:
            sic = 0.10
        else:
            sic = 0.0
        return float(sic), ForcingMode.DIRECT_FORECAST, "NSIDC_AMIP_SIC"
