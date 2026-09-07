"""
Unit and scenario validation tests for ControlledSyntheticSICProvider.
Verifies spatial and temporal determinism, 4 scenarios, physical boundaries, and H3 resolution.
"""

from datetime import datetime, timezone, timedelta
import pytest
from data_access.sea_ice_provider import ControlledSyntheticSICProvider, get_sea_ice_provider


def test_synthetic_sic_provider_scenarios():
    provider = ControlledSyntheticSICProvider("open_ocean")
    assert provider.is_mock is True
    assert "synthetic" in provider.source_name.lower()

    # Scenario A: Open ocean - minimal SIC everywhere
    t0 = datetime(2020, 1, 1, tzinfo=timezone.utc)
    res_ct = provider.get_sea_ice_at("", t0, lat=-33.92, lon=18.42)
    assert res_ct["sea_ice_concentration"] == 0.0
    res_bh = provider.get_sea_ice_at("", t0, lat=-69.40, lon=76.19)
    assert res_bh["sea_ice_concentration"] <= 0.05

    # Scenario B: Moderate (Realistic Summer Expedition Profile)
    provider.set_scenario("moderate")
    # Roaring 40s open ocean
    res_45 = provider.get_sea_ice_at("", t0, lat=-45.0, lon=30.0)
    assert res_45["sea_ice_concentration"] == 0.0
    # Bharati Prydz Bay corridor (should be navigable < 15%)
    res_bh_mod = provider.get_sea_ice_at("", t0, lat=-69.40, lon=76.19)
    assert 0.02 <= res_bh_mod["sea_ice_concentration"] <= 0.12
    # Maitri India Bay corridor (should be navigable < 15%)
    res_mt_mod = provider.get_sea_ice_at("", t0, lat=-69.95, lon=11.73)
    assert 0.05 <= res_mt_mod["sea_ice_concentration"] <= 0.14
    # Weddell interior pack (should be heavy > 30%)
    res_weddell = provider.get_sea_ice_at("", t0, lat=-68.0, lon=0.0)
    assert res_weddell["sea_ice_concentration"] >= 0.30

    # Scenario C: Heavy Ice
    provider.set_scenario("heavy")
    res_heavy = provider.get_sea_ice_at("", t0, lat=-69.40, lon=76.19)
    assert res_heavy["sea_ice_concentration"] > res_bh_mod["sea_ice_concentration"]

    # Scenario D: Severe Ice
    provider.set_scenario("severe")
    res_severe = provider.get_sea_ice_at("", t0, lat=-69.40, lon=76.19)
    assert res_severe["sea_ice_concentration"] >= 0.40


def test_synthetic_sic_temporal_variation():
    provider = ControlledSyntheticSICProvider("moderate")
    t0 = datetime(2020, 1, 1, tzinfo=timezone.utc)
    t7 = t0 + timedelta(days=7)
    t14 = t0 + timedelta(days=14)

    res_t0 = provider.get_sea_ice_at("", t0, lat=-69.40, lon=76.19)
    res_t7 = provider.get_sea_ice_at("", t7, lat=-69.40, lon=76.19)
    res_t14 = provider.get_sea_ice_at("", t14, lat=-69.40, lon=76.19)

    # Time variation must be deterministic and non-constant
    assert res_t0["sea_ice_concentration"] != res_t7["sea_ice_concentration"]
    assert res_t7["sea_ice_concentration"] != res_t14["sea_ice_concentration"]


def test_synthetic_sic_h3_resolution():
    provider = ControlledSyntheticSICProvider("moderate")
    t0 = datetime(2020, 1, 1, tzinfo=timezone.utc)
    # Cape Town cell
    ct_cell = "85ad3617fffffff"
    res = provider.get_sea_ice_at(ct_cell, t0)
    assert res["sea_ice_concentration"] == 0.0

    # Quantile bounds consistency
    assert res["sic_q05"] <= res["sea_ice_concentration"] <= res["sic_q95"]


def test_get_sea_ice_provider_factory():
    p_syn = get_sea_ice_provider("synthetic", scenario="moderate")
    assert p_syn.is_mock is True
    p_syn.set_scenario("open_ocean")
    assert p_syn.current_scenario in ("open_ocean", "historical_trend_low_ice")
