"""
Integration tests for Ice-kNN-South SIC forecast serving.
Tests that: (1) model .pkl loads, (2) .nc predictions are valid,
(3) H3 mapping is correct, (4) provider serves real SIC by lat/lon,
(5) API endpoints return proper values.
"""
import sys
from pathlib import Path

# Ensure all packages are resolvable
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.extend([
    str(REPO_ROOT / "apps/backend/src"),
    str(REPO_ROOT / "packages/core/src"),
    str(REPO_ROOT / "packages/domain/src"),
    str(REPO_ROOT / "packages/data_access/src"),
    str(REPO_ROOT / "packages/models/src"),
    str(REPO_ROOT / "packages/iceberg_physics/src"),
    str(REPO_ROOT / "packages/risk_engine/src"),
    str(REPO_ROOT / "packages/routing/src"),
    str(REPO_ROOT / "packages/services/src"),
    str(REPO_ROOT),
])

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone


# ============================================================
# 1. Model loading (serves the .pkl, no retraining)
# ============================================================
class TestModelLoading:
    def test_model_loads_from_pkl(self):
        from ice_knn.model import load_ice_knn_model
        model = load_ice_knn_model()
        assert model is not None
        assert model.is_fitted is True
        assert model.k_neighbors == 5
        assert model.n_components == 10
        assert model.lat is not None
        assert model.lon is not None

    def test_model_lat_lon_shape(self):
        from ice_knn.model import load_ice_knn_model
        model = load_ice_knn_model()
        assert model.lat.shape == (45,)
        assert model.lon.shape == (120,)
        assert float(model.lat.min()) == pytest.approx(-90.0, abs=0.1)
        assert float(model.lat.max()) == pytest.approx(-45.0, abs=0.1)
        assert float(model.lon.min()) == pytest.approx(0.0, abs=0.1)

    def test_model_has_climatology(self):
        from ice_knn.model import load_ice_knn_model
        model = load_ice_knn_model()
        assert "sic" in model.climatology
        for v in ["sic", "u10", "v10", "t2m", "sst", "mld"]:
            assert v in model.climatology, f"Missing climatology variable: {v}"


# ============================================================
# 2. NetCDF forecast (.nc) validation
# ============================================================
class TestNetCDFForecast:
    def _get_ds(self):
        from ice_knn.inference import IceKNNInferenceService
        return IceKNNInferenceService().forecast_dataset

    def test_nc_dimensions(self):
        ds = self._get_ds()
        assert len(ds["time"]) == 90
        assert len(ds["lat"]) == 45
        assert len(ds["lon"]) == 120

    def test_nc_sic_bounds(self):
        ds = self._get_ds()
        sic = ds["sic"].values
        assert float(np.nanmin(sic)) >= 0.0
        assert float(np.nanmax(sic)) <= 100.0
        assert int(np.isnan(sic).sum()) == 0

    def test_nc_quantile_ordering(self):
        ds = self._get_ds()
        q05 = ds["sic_q05"].values
        q95 = ds["sic_q95"].values
        inversions = np.sum(q05 > q95 + 1e-5)
        assert inversions == 0, f"{inversions} quantile inversions detected"

    def test_nc_variables_present(self):
        ds = self._get_ds()
        for var in ["sic", "sica", "sic_uncertainty", "sic_q05", "sic_q95", "sic_clim"]:
            assert var in ds, f"Missing variable: {var}"

    def test_nc_coordinates_with_latlon(self):
        ds = self._get_ds()
        lats = ds["lat"].values
        lons = ds["lon"].values
        assert lats.min() <= -80.0, "Should cover deep Antarctic"
        assert lats.max() >= -46.0, "Should reach southern open ocean"
        assert lons.min() >= 0.0
        assert lons.max() <= 360.0


# ============================================================
# 3. H3 parquet mapping
# ============================================================
class TestH3Mapping:
    PARQUET = REPO_ROOT / "data/processed/ice_knn/h3_sic_forecast_90d.parquet"

    def test_parquet_exists(self):
        assert self.PARQUET.is_file(), f"H3 parquet not found at {self.PARQUET}"

    def test_parquet_schema(self):
        df = pd.read_parquet(self.PARQUET)
        expected_cols = ["cell_id", "lead_day", "valid_time", "centroid_lat", "centroid_lon",
                         "sea_ice_concentration", "sea_ice_percent",
                         "sea_ice_uncertainty", "uncertainty_percent",
                         "sic_q05", "sic_q95", "sic_clim"]
        for col in expected_cols:
            assert col in df.columns, f"Missing column: {col}"

    def test_parquet_row_count(self):
        df = pd.read_parquet(self.PARQUET)
        # 2000 cells × 90 lead days = 180,000
        assert len(df) == 180_000, f"Expected 180,000 rows, got {len(df)}"

    def test_parquet_sic_fraction_bounds(self):
        df = pd.read_parquet(self.PARQUET)
        assert df["sea_ice_concentration"].min() >= 0.0
        assert df["sea_ice_concentration"].max() <= 1.0

    def test_parquet_southern_cells_have_nonzero_sic(self):
        df = pd.read_parquet(self.PARQUET)
        southern = df[(df["centroid_lat"] < -65) & (df["lead_day"] == 0)]
        assert len(southern) > 0, "No southern cells found"
        mean_sic = southern["sea_ice_concentration"].mean()
        assert mean_sic > 0.05, f"Southern cells should have significant SIC, got {mean_sic:.3f}"


# ============================================================
# 4. Sea-ice provider: lat/lon propagation
# ============================================================
class TestSeaIceProvider:
    def _provider(self):
        from data_access.sea_ice_provider import IceKNNSeaIceProvider
        return IceKNNSeaIceProvider()

    def test_cell_id_lookup_returns_real_sic(self):
        p = self._provider()
        dt = datetime(2020, 1, 15, tzinfo=timezone.utc)
        result = p.get_sea_ice_at("85dd2087fffffff", dt)
        assert result["is_mock"] is False
        assert result["source"] == "Ice-kNN-South"
        assert 0.0 <= result["sea_ice_concentration"] <= 1.0

    def test_latlon_fallback_returns_real_nc_sic(self):
        p = self._provider()
        dt = datetime(2020, 1, 15, tzinfo=timezone.utc)
        result = p.get_sea_ice_at("", dt, lat=-69.4, lon=76.2)
        assert result["is_mock"] is False
        assert result["source"] == "Ice-kNN-South"
        assert 0.0 <= result["sea_ice_concentration"] <= 1.0
        assert result["sic_q05"] <= result["sic_q95"], "q05 should be <= q95"

    def test_lead_day_computation(self):
        p = self._provider()
        assert p._compute_lead_day(datetime(2020, 1, 1, tzinfo=timezone.utc)) == 0
        assert p._compute_lead_day(datetime(2020, 1, 15, tzinfo=timezone.utc)) == 14
        assert p._compute_lead_day(datetime(2020, 3, 30, tzinfo=timezone.utc)) == 89
        # Clamp at 89
        assert p._compute_lead_day(datetime(2025, 1, 1, tzinfo=timezone.utc)) == 89

    def test_uncertainty_propagates(self):
        p = self._provider()
        dt = datetime(2020, 1, 1, tzinfo=timezone.utc)
        result = p.get_sea_ice_at("85dd2087fffffff", dt)
        assert "sea_ice_uncertainty" in result
        assert result["sea_ice_uncertainty"] >= 0.0


# ============================================================
# 5. API endpoint correctness
# ============================================================
class TestSeaIceAPI:
    @pytest.mark.asyncio
    async def test_forecast_summary(self):
        from api.routers.sea_ice import get_forecast_summary
        s = await get_forecast_summary()
        assert s["lead_days"] == 90
        assert s["model_name"] == "Ice-kNN-South"
        assert s["sic_stats"]["min"] >= 0.0
        assert s["sic_stats"]["max"] <= 100.0

    @pytest.mark.asyncio
    async def test_point_query_with_lat_lon(self):
        from api.routers.sea_ice import get_sic_at_point
        # Bharati approach
        result = await get_sic_at_point(lat=-69.4, lon=76.2, lead_day=0)
        assert result["lat"] == pytest.approx(-69.4, abs=0.01)
        assert result["lon"] == pytest.approx(76.2, abs=0.01)
        assert 0.0 <= result["sic_percent"] <= 100.0
        assert 0.0 <= result["sic_fraction"] <= 1.0

    @pytest.mark.asyncio
    async def test_grid_returns_lat_lon_per_cell(self):
        from api.routers.sea_ice import get_sic_grid
        g = await get_sic_grid(lead_day=0, min_lat=-75.0, max_lat=-65.0, min_lon=60.0, max_lon=100.0)
        assert g["cell_count"] > 0
        feature = g["features"][0]
        assert "lat" in feature
        assert "lon" in feature
        assert "sic_fraction" in feature
        assert "sic_percent" in feature
        assert "uncertainty_fraction" in feature
        assert "q05" in feature
        assert "q95" in feature
        assert -90.0 <= feature["lat"] <= 0.0, "Latitude should be in Southern hemisphere"

    @pytest.mark.asyncio
    async def test_forecast_dates_coverage(self):
        from api.routers.sea_ice import get_forecast_dates
        d = await get_forecast_dates()
        assert len(d["dates"]) == 90
        assert len(d["lead_days"]) == 90
        assert d["lead_days"][0] == 0
        assert d["lead_days"][-1] == 89
