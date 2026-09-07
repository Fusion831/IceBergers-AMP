"""
Comprehensive verification and regression suite for the AMIP Risk Profile & Risk Engine.
Validates hard constraints, monotonicity, weight sensitivity, determinism, missing data,
route aggregation, iceberg hazard interpretation, and vessel context.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path

from risk_engine.engine import RiskEngine
from risk_engine.models import RiskProfile, RouteRiskProfile
from risk_engine.policy import RiskPolicyConfig, load_risk_policy
from risk_engine.warnings import RiskWarningCode
from vessel.models import VesselProfile


@pytest.fixture
def risk_engine():
    return RiskEngine()


@pytest.fixture
def sagar_kanya():
    return VesselProfile.get_sagar_kanya_default()


# =============================================================================
# 1. HARD CONSTRAINTS VS SOFT RISK
# =============================================================================

def test_hard_constraints_vs_soft_risk(risk_engine, sagar_kanya):
    # SCAR ADD Land Block
    land_cell = {
        "cell_id": "85ad049bfffffff",
        "geographic_status": "LAND",
        "ocean_fraction": 0.0,
        "land_fraction": 1.0,
        "bathymetry_depth_m": 0.0,
    }
    p_land = risk_engine.evaluate_cell_risk(land_cell, vessel=sagar_kanya)
    assert p_land.hard_blocked is True
    assert p_land.blocking_rule == "SCAR_ADD_GEOGRAPHIC_MASK"
    assert "LAND" in (p_land.block_reason or "")
    assert RiskWarningCode.GEOGRAPHIC_BLOCK.value in p_land.warning_codes

    # SCAR ADD Ice Shelf Block
    shelf_cell = {
        "cell_id": "85ad049bfffffff",
        "geographic_status": "ICE_SHELF",
        "ocean_fraction": 0.0,
        "ice_shelf_fraction": 1.0,
    }
    p_shelf = risk_engine.evaluate_cell_risk(shelf_cell, vessel=sagar_kanya)
    assert p_shelf.hard_blocked is True
    assert p_shelf.blocking_rule == "SCAR_ADD_GEOGRAPHIC_MASK"

    # Bathymetric Grounding (depth 4.0m <= draft 5.6m)
    ground_cell = {
        "cell_id": "85ad049bfffffff",
        "geographic_status": "OPEN_OCEAN",
        "bathymetry_depth_m": 4.0,
    }
    p_ground = risk_engine.evaluate_cell_risk(ground_cell, vessel=sagar_kanya)
    assert p_ground.hard_blocked is True
    assert p_ground.blocking_rule == "BATHYMETRIC_GROUNDING"
    assert p_ground.clearance_m < 0.0
    assert RiskWarningCode.BATHYMETRIC_GROUNDING.value in p_ground.warning_codes

    # Sea-ice exceeding Sagar Kanya limit (15% limit; tested with 25% SIC)
    heavy_ice_cell = {
        "cell_id": "85ad049bfffffff",
        "geographic_status": "OPEN_OCEAN",
        "bathymetry_depth_m": 3000.0,
        "sea_ice_concentration": 0.25,
    }
    p_ice = risk_engine.evaluate_cell_risk(heavy_ice_cell, vessel=sagar_kanya)
    assert p_ice.hard_blocked is True
    assert p_ice.blocking_rule == "VESSEL_SEA_ICE_CAPABILITY_EXCEEDED"

    # High iceberg hazard is a SOFT risk, NOT a hard block
    iceberg_cell = {
        "cell_id": "85ad049bfffffff",
        "geographic_status": "OPEN_OCEAN",
        "bathymetry_depth_m": 3000.0,
        "sea_ice_concentration": 0.02,
        "iceberg_hazard": 0.85,
    }
    p_berg = risk_engine.evaluate_cell_risk(iceberg_cell, vessel=sagar_kanya)
    assert p_berg.hard_blocked is False
    assert p_berg.iceberg_risk > 0.80
    assert RiskWarningCode.CRITICAL_ICEBERG_HAZARD.value in p_berg.warning_codes

    # High wave height is a SOFT risk by default
    wave_cell = {
        "cell_id": "85ad049bfffffff",
        "geographic_status": "OPEN_OCEAN",
        "bathymetry_depth_m": 3000.0,
        "sea_ice_concentration": 0.0,
        "wave_height_m": 7.0,
    }
    p_wave = risk_engine.evaluate_cell_risk(wave_cell, vessel=sagar_kanya)
    assert p_wave.hard_blocked is False
    assert p_wave.wave_risk > 0.65
    assert RiskWarningCode.CRITICAL_WAVE.value in p_wave.warning_codes


# =============================================================================
# 2. MONOTONIC SENSITIVITY TESTS
# =============================================================================

def test_monotonic_sea_ice_sensitivity(risk_engine):
    sic_values = [0.0, 0.03, 0.08, 0.12, 0.20, 0.50, 0.90]
    risks = []
    for sic in sic_values:
        cell = {
            "cell_id": "cell_test",
            "bathymetry_depth_m": 2000.0,
            "sea_ice_concentration": sic,
        }
        # Evaluate without vessel limit hard-blocking so we can check soft curve monotonicity
        p = risk_engine.evaluate_cell_risk(cell, vessel=None)
        risks.append(p.sea_ice_risk)

    for i in range(len(risks) - 1):
        assert risks[i + 1] >= risks[i], f"SIC risk not monotonic: {risks[i]} > {risks[i+1]}"


def test_monotonic_iceberg_hazard_sensitivity(risk_engine):
    hazards = [0.0, 0.02, 0.08, 0.15, 0.35, 0.65, 0.95]
    risks = []
    for h in hazards:
        cell = {
            "cell_id": "cell_test",
            "bathymetry_depth_m": 2000.0,
            "iceberg_hazard": h,
        }
        p = risk_engine.evaluate_cell_risk(cell)
        risks.append(p.iceberg_risk)

    for i in range(len(risks) - 1):
        assert risks[i + 1] >= risks[i], f"Iceberg risk not monotonic: {risks[i]} > {risks[i+1]}"


def test_monotonic_wave_sensitivity(risk_engine):
    wave_heights = [0.5, 1.5, 2.5, 3.8, 5.2, 7.0, 9.5]
    risks = []
    for wh in wave_heights:
        cell = {
            "cell_id": "cell_test",
            "bathymetry_depth_m": 2000.0,
            "wave_height_m": wh,
        }
        p = risk_engine.evaluate_cell_risk(cell)
        risks.append(p.wave_risk)

    for i in range(len(risks) - 1):
        assert risks[i + 1] >= risks[i], f"Wave risk not monotonic: {risks[i]} > {risks[i+1]}"


def test_monotonic_wind_sensitivity(risk_engine):
    wind_speeds = [2.0, 8.0, 12.0, 18.0, 24.0, 32.0]
    risks = []
    for ws in wind_speeds:
        cell = {
            "cell_id": "cell_test",
            "bathymetry_depth_m": 2000.0,
            "wind_speed_ms": ws,
        }
        p = risk_engine.evaluate_cell_risk(cell)
        risks.append(p.wind_risk)

    for i in range(len(risks) - 1):
        assert risks[i + 1] >= risks[i], f"Wind risk not monotonic: {risks[i]} > {risks[i+1]}"


def test_monotonic_bathymetric_depth_sensitivity(risk_engine):
    # As depth gets shallower, risk must not decrease
    depths = [3000.0, 500.0, 50.0, 18.0, 12.0, 8.0]
    risks = []
    for d in depths:
        cell = {
            "cell_id": "cell_test",
            "bathymetry_depth_m": d,
        }
        p = risk_engine.evaluate_cell_risk(cell)
        risks.append(p.bathymetric_risk)

    for i in range(len(risks) - 1):
        assert risks[i + 1] >= risks[i], f"Bathymetric risk not monotonic: {risks[i]} > {risks[i+1]}"


def test_data_completeness_confidence_sensitivity(risk_engine):
    # Complete data
    c_full = {
        "cell_id": "cell_test",
        "bathymetry_depth_m": 2000.0,
        "sea_ice_concentration": 0.05,
        "wave_height_m": 2.5,
        "wind_speed_ms": 10.0,
        "current_speed_ms": 0.4,
    }
    p_full = risk_engine.evaluate_cell_risk(c_full)

    # Missing wave
    c_no_wave = dict(c_full)
    c_no_wave.pop("wave_height_m")
    p_no_wave = risk_engine.evaluate_cell_risk(c_no_wave)

    # Missing wave and wind and current
    c_sparse = dict(c_no_wave)
    c_sparse.pop("wind_speed_ms")
    c_sparse.pop("current_speed_ms")
    p_sparse = risk_engine.evaluate_cell_risk(c_sparse)

    assert p_full.confidence_score >= p_no_wave.confidence_score
    assert p_no_wave.confidence_score >= p_sparse.confidence_score
    assert len(p_sparse.warnings) > 0


# =============================================================================
# 3. WEIGHT SENSITIVITY
# =============================================================================

def test_weight_sensitivity(risk_engine):
    cell = {
        "cell_id": "cell_test",
        "bathymetry_depth_m": 2000.0,
        "sea_ice_concentration": 0.12,  # high ice
        "wave_height_m": 1.0,           # low wave
        "wind_speed_ms": 5.0,
        "current_speed_ms": 0.2,
    }

    # Policy 1: Sea-ice heavy
    policy_ice = RiskPolicyConfig.model_validate(risk_engine.policy.model_dump())
    policy_ice.component_weights["sea_ice"].weight = 0.70
    policy_ice.component_weights["waves"].weight = 0.05
    policy_ice.component_weights["iceberg"].weight = 0.05
    policy_ice.component_weights["wind"].weight = 0.05
    policy_ice.component_weights["bathymetry"].weight = 0.05
    policy_ice.component_weights["current"].weight = 0.05
    policy_ice.component_weights["confidence"].weight = 0.05

    # Policy 2: Wave heavy
    policy_wave = RiskPolicyConfig.model_validate(risk_engine.policy.model_dump())
    policy_wave.component_weights["sea_ice"].weight = 0.05
    policy_wave.component_weights["waves"].weight = 0.70
    policy_wave.component_weights["iceberg"].weight = 0.05
    policy_wave.component_weights["wind"].weight = 0.05
    policy_wave.component_weights["bathymetry"].weight = 0.05
    policy_wave.component_weights["current"].weight = 0.05
    policy_wave.component_weights["confidence"].weight = 0.05

    p1 = risk_engine.evaluate_cell_risk(cell, policy=policy_ice)
    p2 = risk_engine.evaluate_cell_risk(cell, policy=policy_wave)

    # Component risks should be identical
    assert p1.sea_ice_risk == p2.sea_ice_risk
    assert p1.wave_risk == p2.wave_risk
    # Composite risk should be significantly higher under ice-heavy policy
    assert p1.composite_risk > p2.composite_risk


# =============================================================================
# 4. DETERMINISM
# =============================================================================

def test_determinism(risk_engine, sagar_kanya):
    cell = {
        "cell_id": "85ad049bfffffff",
        "valid_time": "2026-01-15T12:00:00Z",
        "bathymetry_depth_m": 2500.0,
        "sea_ice_concentration": 0.08,
        "sea_ice_uncertainty": 0.03,
        "wave_height_m": 3.2,
        "wind_speed_ms": 12.5,
        "current_speed_ms": 0.45,
        "iceberg_hazard": 0.22,
        "contributing_iceberg_ids": ["B15A", "A68A"],
    }
    p1 = risk_engine.evaluate_cell_risk(cell, vessel=sagar_kanya)
    p2 = risk_engine.evaluate_cell_risk(cell, vessel=sagar_kanya)

    assert p1.composite_risk == p2.composite_risk
    assert p1.confidence_score == p2.confidence_score
    assert p1.sea_ice_risk == p2.sea_ice_risk
    assert p1.iceberg_risk == p2.iceberg_risk
    assert p1.wave_risk == p2.wave_risk
    assert p1.warning_codes == p2.warning_codes


# =============================================================================
# 5. MOCK SIC PROVENANCE
# =============================================================================

def test_mock_sic_provenance(risk_engine):
    cell_mock = {
        "cell_id": "cell_mock",
        "bathymetry_depth_m": 2000.0,
        "sea_ice_concentration": 0.05,
        "provenance": {"sic_source": "MOCK"},
    }
    p_mock = risk_engine.evaluate_cell_risk(cell_mock)
    assert RiskWarningCode.MOCK_SIC.value in p_mock.warning_codes
    assert p_mock.confidence_score < 0.85  # penalized for mock source


# =============================================================================
# 6. ROUTE RISK INTEGRATION & TAIL METRICS
# =============================================================================

def test_route_risk_time_weighting_and_tail(risk_engine):
    # Segment 1: Low risk, 10 hours
    c1 = {
        "cell_id": "cell_1",
        "bathymetry_depth_m": 3000.0,
        "sea_ice_concentration": 0.0,
        "wave_height_m": 1.5,
    }
    p1 = risk_engine.evaluate_cell_risk(c1)

    # Segment 2: Extreme risk, 1 hour
    c2 = {
        "cell_id": "cell_2",
        "bathymetry_depth_m": 3000.0,
        "sea_ice_concentration": 0.14,
        "wave_height_m": 6.5,
        "iceberg_hazard": 0.70,
        "contributing_iceberg_ids": ["A23A"],
    }
    p2 = risk_engine.evaluate_cell_risk(c2)

    durations = [10.0, 1.0]
    route_profile = risk_engine.evaluate_route_risk([p1, p2], segment_durations_hours=durations)

    assert route_profile.total_duration_hours == 11.0
    assert route_profile.segment_count == 2
    # Mean risk (unweighted average) is (p1 + p2)/2
    unweighted_mean = (p1.composite_risk + p2.composite_risk) / 2.0
    # Time weighted mean should be much closer to p1 because of 10h duration vs 1h
    assert route_profile.time_weighted_mean_risk < unweighted_mean
    assert route_profile.max_risk == p2.composite_risk
    assert route_profile.p95_risk >= route_profile.time_weighted_mean_risk
    assert route_profile.distinct_iceberg_count == 1
    assert "A23A" in route_profile.distinct_icebergs_encountered


# =============================================================================
# 7. POLICY VALIDATION
# =============================================================================

def test_invalid_policy_fails_loudly():
    policy_dict = {
        "policy_name": "INVALID_POLICY",
        "component_weights": {
            "sea_ice": {"weight": 0.80},
            "waves": {"weight": 0.50},  # Sum = 1.30 > 1.0
        },
    }
    with pytest.raises(ValueError, match="component weights must sum to 1.0"):
        RiskPolicyConfig.model_validate(policy_dict)

    # Non-monotonic thresholds
    bad_thresh_dict = {
        "policy_name": "BAD_THRESH",
        "component_weights": {
            "sea_ice": {"weight": 1.0},
        },
        "thresholds": {
            "sea_ice": {
                "safe_fraction": {"value": 0.20},
                "elevated_fraction": {"value": 0.10},  # Error: elevated < safe
            }
        }
    }
    with pytest.raises(ValueError, match="Sea-ice thresholds not monotonic"):
        RiskPolicyConfig.model_validate(bad_thresh_dict)


# =============================================================================
# 8. FRONTEND INSPECTOR AND LAYER CONTRACTS
# =============================================================================

def test_frontend_inspector_and_layer_contracts(risk_engine):
    cell = {
        "cell_id": "85ad049bfffffff",
        "valid_time": "2026-01-15T12:00:00Z",
        "bathymetry_depth_m": 2500.0,
        "sea_ice_concentration": 0.08,
        "wave_height_m": 3.2,
        "wind_speed_ms": 12.5,
        "current_speed_ms": 0.45,
        "iceberg_hazard": 0.22,
    }
    p = risk_engine.evaluate_cell_risk(cell)

    insp = p.to_inspector_dict()
    assert insp["cell_id"] == "85ad049bfffffff"
    assert "feasibility" in insp
    assert "composite" in insp
    assert "component_risks" in insp
    assert "physical_forcings" in insp
    assert "warnings" in insp
    assert "policy" in insp
    assert insp["component_risks"]["sea_ice"] == round(p.sea_ice_risk, 4)

    h3_layer = p.to_h3_layer_dict()
    assert h3_layer["cell_id"] == "85ad049bfffffff"
    assert "composite_risk" in h3_layer
    assert "sea_ice_risk" in h3_layer
    assert "iceberg_risk" in h3_layer
    assert "hard_blocked" in h3_layer
