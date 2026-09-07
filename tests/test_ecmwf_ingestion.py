import os
import pytest
from data_ingestion.ecmwf import open_ecmwf_wind_dataset, ECMWFWindProvider, WindState


@pytest.fixture
def grib_path():
    path = "data/raw/ecmwf/wind/ecmwf_wind_surface_0_48h.grib2"
    if not os.path.exists(path):
        pytest.skip(f"Test GRIB2 file not found: {path}")
    return path


def test_open_ecmwf_wind_dataset(grib_path):
    ds = open_ecmwf_wind_dataset(grib_path)
    assert "u10" in ds.data_vars
    assert "v10" in ds.data_vars
    assert "t2m" in ds.data_vars
    assert "wind_speed" in ds.data_vars
    assert "wind_direction" in ds.data_vars
    assert "t2m_c" in ds.data_vars
    assert "icing_risk" in ds.data_vars

    # Check non-negative wind speed
    assert (ds["wind_speed"].values >= 0.0).all()
    # Check direction in [0, 360)
    assert (ds["wind_direction"].values >= 0.0).all()
    assert (ds["wind_direction"].values <= 360.0).all()


def test_ecmwf_wind_provider(grib_path):
    provider = ECMWFWindProvider(grib_path)

    # Query Indian Antarctic stations: Maitri (-70.77 S, 11.73 E) and Bharati (-69.41 S, 76.19 E)
    state_maitri = provider.get_wind(latitude=-70.77, longitude=11.73, step_index=0)
    assert isinstance(state_maitri, WindState)
    assert state_maitri.wind_speed >= 0.0
    assert 0.0 <= state_maitri.wind_direction <= 360.0
    assert state_maitri.t2m_c is not None
    assert isinstance(state_maitri.icing_risk, bool)

    state_bharati = provider.get_wind(latitude=-69.41, longitude=76.19, step_index=0)
    assert isinstance(state_bharati, WindState)
    assert state_bharati.wind_speed >= 0.0
    assert state_bharati.t2m_c is not None
