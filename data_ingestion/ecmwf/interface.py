from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import numpy as np
import xarray as xr
from .reader import open_ecmwf_wind_dataset


@dataclass(frozen=True)
class WindState:
    u10: float
    v10: float
    wind_speed: float
    wind_direction: float
    t2m_c: Optional[float] = None
    icing_risk: Optional[bool] = None


class ECMWFWindProvider:
    """Provides spatial-temporal querying and interpolation of ECMWF Open Data wind and temperature fields."""

    def __init__(self, grib_path: str):
        self.grib_path = grib_path
        self.ds = open_ecmwf_wind_dataset(grib_path)

    def get_wind(self, latitude: float, longitude: float, step_index: int = 0) -> WindState:
        """Query wind and temperature at a specific coordinate and forecast step index."""
        # Ensure longitude is in [-180, 180]
        if longitude > 180.0:
            longitude -= 360.0

        sub = self.ds.isel(step=step_index).sel(
            latitude=latitude,
            longitude=longitude,
            method="nearest"
        )

        u = float(sub["u10"].values)
        v = float(sub["v10"].values)
        speed = float(sub["wind_speed"].values)
        direction = float(sub["wind_direction"].values)
        t_c = float(sub["t2m_c"].values) if "t2m_c" in sub else None
        icing = bool(sub["icing_risk"].values) if "icing_risk" in sub else None

        return WindState(
            u10=round(u, 2),
            v10=round(v, 2),
            wind_speed=round(speed, 2),
            wind_direction=round(direction, 1),
            t2m_c=round(t_c, 2) if t_c is not None else None,
            icing_risk=icing
        )
