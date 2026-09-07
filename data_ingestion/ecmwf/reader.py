import os
import xarray as xr
import numpy as np


def open_ecmwf_wind_dataset(grib_path: str) -> xr.Dataset:
    """Open an ECMWF Open Data GRIB2 file containing 10u, 10v, and 2t.

    Merges heightAboveGround=10 and heightAboveGround=2 levels cleanly and
    adds derived variables:
      - wind_speed (m/s)
      - wind_direction (degrees true, meteorological 'from' convention)
      - t2m_c (Celsius)
      - icing_risk (Boolean / float potential index)
    """
    if not os.path.exists(grib_path):
        raise FileNotFoundError(f"ECMWF GRIB2 file not found: {grib_path}")

    ds_wind = xr.open_dataset(
        grib_path,
        engine="cfgrib",
        filter_by_keys={"typeOfLevel": "heightAboveGround", "level": 10}
    ).drop_vars("heightAboveGround", errors="ignore")

    try:
        ds_temp = xr.open_dataset(
            grib_path,
            engine="cfgrib",
            filter_by_keys={"typeOfLevel": "heightAboveGround", "level": 2}
        ).drop_vars("heightAboveGround", errors="ignore")
        ds = xr.merge([ds_wind[["u10", "v10"]], ds_temp[["t2m"]]], compat="override")
    except Exception:
        # If t2m wasn't retrieved, fall back to wind only
        ds = ds_wind[["u10", "v10"]]

    # Derive wind speed magnitude
    ds["wind_speed"] = np.sqrt(ds["u10"] ** 2 + ds["v10"] ** 2)
    ds["wind_speed"].attrs = {"units": "m s**-1", "long_name": "10 metre wind speed magnitude"}

    # Derive meteorological wind direction (from direction, clockwise from North)
    wind_dir = (np.rad2deg(np.arctan2(-ds["u10"], -ds["v10"]))) % 360.0
    ds["wind_direction"] = wind_dir
    ds["wind_direction"].attrs = {"units": "degree", "long_name": "10 metre wind from direction (degrees true)"}

    if "t2m" in ds:
        ds["t2m_c"] = ds["t2m"] - 273.15
        ds["t2m_c"].attrs = {"units": "degC", "long_name": "2 metre temperature in Celsius"}

        # Superstructure icing potential (IMO Polar Code criterion: wind >= 10 m/s and air temp <= -2 C)
        ds["icing_risk"] = (ds["wind_speed"] >= 10.0) & (ds["t2m_c"] <= -2.0)
        ds["icing_risk"].attrs = {"description": "True where wind >= 10 m/s and air temp <= -2 degC"}

    return ds
