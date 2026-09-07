"""
Exhaustive Verification Test Suite for AMIP Vessel Configuration & Performance.
Implements the 16 mandatory sanity checks specified in Section 28 of the AMIP Vessel PRD:
 1. knots <-> m/s conversion
 2. zero current
 3. favorable current
 4. adverse current
 5. cross-current
 6. stronger waves
 7. increased SIC
 8. shallow depth
 9. SCAR ADD hard block
 10. fuel accumulation
 11. endurance
 12. deterministic identical inputs
 13. time-dependent environment
 14. H3 cell transition
 15. provenance
 16. assumption/configuration handling
"""

import math
import pytest
from datetime import datetime, timezone, timedelta

from vessel.provenance import ParameterClassification, ParameterProvenance
from vessel.models import VesselProfile
from vessel.config import get_sagar_kanya_profile, load_vessel_profile
from vessel.evaluator import (
    VesselPerformanceEvaluator,
    EdgeEvaluation,
    evaluate_transition,
    evaluate_route_transitions,
    METERS_PER_NAUTICAL_MILE,
    MS_PER_KNOT,
)
from vessel.constraints import VesselConstraintChecker, ConstraintResult
from vessel.fuel import FuelConsumptionModel
from vessel.route_metrics import aggregate_route_metrics
from vessel.routing_adapter import VesselRoutingCostAdapter
from vessel.mission_nodes import (
    CAPE_TOWN,
    BHARATI_MARITIME_ACCESS,
    MAITRI_MARITIME_ACCESS,
    MAITRI_INLAND_STATION,
)


@pytest.fixture
def sagar_kanya() -> VesselProfile:
    """Loads authoritative reference ORV Sagar Kanya profile."""
    return get_sagar_kanya_profile()


# =========================================================================
# 1. Knots <-> m/s and Nautical Mile Conversions
# =========================================================================
def test_knots_ms_conversion():
    """Verify standard nautical unit conversions."""
    assert abs(MS_PER_KNOT - 0.51444444444) < 1e-8
    assert abs(METERS_PER_NAUTICAL_MILE - 1852.0) < 1e-8

    # 10 knots to m/s
    speed_kn = 10.0
    speed_ms = speed_kn * MS_PER_KNOT
    assert abs(speed_ms - 5.1444444) < 1e-4

    # Convert back
    assert abs((speed_ms / MS_PER_KNOT) - speed_kn) < 1e-6

    # 1 nautical mile = 1852 meters
    dist_nm = 50.0
    dist_m = dist_nm * METERS_PER_NAUTICAL_MILE
    assert dist_m == 92600.0
    assert abs((dist_m / METERS_PER_NAUTICAL_MILE) - dist_nm) < 1e-6


# =========================================================================
# 2. Zero Current
# =========================================================================
def test_zero_current(sagar_kanya: VesselProfile):
    """Verify that with zero current, ground speed equals through-water speed."""
    pt_a = (-40.0, 20.0)
    pt_b = (-39.0, 20.0)  # Heading 0° North
    env = {
        "current_u_ms": 0.0,
        "current_v_ms": 0.0,
        "wave_height_m": 0.0,
        "sea_ice_concentration": 0.0,
        "bathymetry_depth_m": 4000.0,
    }
    dep = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    res = evaluate_transition(sagar_kanya, pt_a, pt_b, env, dep)

    assert res.feasible is True
    assert res.heading == 0.0
    assert res.current_assistance_kn == 0.0
    assert abs(res.ground_speed_kn - res.achievable_speed_kn) < 0.05
    assert abs(res.along_track_speed_kn - res.achievable_speed_kn) < 0.05
    assert res.ground_direction_deg == 0.0


# =========================================================================
# 3. Favorable Current
# =========================================================================
def test_favorable_current(sagar_kanya: VesselProfile):
    """Verify that a favorable tail current increases ground speed and along-track progress."""
    pt_a = (-40.0, 20.0)
    pt_b = (-39.0, 20.0)  # Heading 0° North
    dep = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)

    # Base zero-current
    res_base = evaluate_transition(sagar_kanya, pt_a, pt_b, {
        "current_u_ms": 0.0, "current_v_ms": 0.0, "wave_height_m": 1.0
    }, dep)

    # +1.0 m/s Northward tail current (~1.94 kn boost)
    res_fwd = evaluate_transition(sagar_kanya, pt_a, pt_b, {
        "current_u_ms": 0.0, "current_v_ms": 1.0, "wave_height_m": 1.0
    }, dep)

    assert res_fwd.current_assistance_kn > 1.90
    assert res_fwd.ground_speed_kn > res_base.ground_speed_kn
    assert res_fwd.along_track_speed_kn > res_base.along_track_speed_kn
    assert res_fwd.travel_time_hours < res_base.travel_time_hours


# =========================================================================
# 4. Adverse Current
# =========================================================================
def test_adverse_current(sagar_kanya: VesselProfile):
    """Verify that an opposing head current decreases ground speed and increases transit duration."""
    pt_a = (-40.0, 20.0)
    pt_b = (-39.0, 20.0)  # Heading 0° North
    dep = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)

    res_base = evaluate_transition(sagar_kanya, pt_a, pt_b, {
        "current_u_ms": 0.0, "current_v_ms": 0.0, "wave_height_m": 1.0
    }, dep)

    # -1.0 m/s Southward opposing current
    res_opp = evaluate_transition(sagar_kanya, pt_a, pt_b, {
        "current_u_ms": 0.0, "current_v_ms": -1.0, "wave_height_m": 1.0
    }, dep)

    assert res_opp.current_assistance_kn < -1.90
    assert res_opp.ground_speed_kn < res_base.ground_speed_kn
    assert res_opp.along_track_speed_kn < res_base.along_track_speed_kn
    assert res_opp.travel_time_hours > res_base.travel_time_hours


# =========================================================================
# 5. Cross-Current
# =========================================================================
def test_cross_current(sagar_kanya: VesselProfile):
    """Verify that a cross-current alters course over ground direction."""
    pt_a = (-40.0, 20.0)
    pt_b = (-39.0, 20.0)  # Heading 0° North
    dep = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)

    # Pure eastward cross-current (+1.5 m/s)
    res_cross = evaluate_transition(sagar_kanya, pt_a, pt_b, {
        "current_u_ms": 1.5, "current_v_ms": 0.0, "wave_height_m": 1.0
    }, dep)

    assert res_cross.heading == 0.0
    # Ground track drifts towards East (> 0 deg)
    assert res_cross.ground_direction_deg > 5.0
    assert res_cross.current_u == 1.5
    assert abs(res_cross.current_assistance_kn) < 0.05  # Cross current imparts zero along-track assistance


# =========================================================================
# 6. Stronger Waves
# =========================================================================
def test_stronger_waves(sagar_kanya: VesselProfile):
    """Verify that higher wave heights increase resistance and fuel, decreasing speed."""
    pt_a = (-40.0, 20.0)
    pt_b = (-39.5, 20.0)
    dep = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)

    res_calm = evaluate_transition(sagar_kanya, pt_a, pt_b, {"wave_height_m": 1.0, "wave_direction_deg": 0.0}, dep)
    res_rough = evaluate_transition(sagar_kanya, pt_a, pt_b, {"wave_height_m": 4.5, "wave_direction_deg": 0.0}, dep)
    res_severe = evaluate_transition(sagar_kanya, pt_a, pt_b, {"wave_height_m": 6.5, "wave_direction_deg": 0.0}, dep)

    # Speed degradation
    assert res_calm.achievable_speed_kn > res_rough.achievable_speed_kn > res_severe.achievable_speed_kn
    # Hourly fuel rate increases
    assert res_calm.fuel_rate < res_rough.fuel_rate < res_severe.fuel_rate
    # Warnings emitted on severe wave state
    assert any("Severe sea state" in w for w in res_severe.warnings)
    assert any("Rough seas" in w for w in res_rough.warnings)


# =========================================================================
# 7. Increased Sea Ice Concentration (SIC)
# =========================================================================
def test_increased_sic(sagar_kanya: VesselProfile):
    """Verify that sea ice degrades speed, triggers warnings, and blocks above policy limit."""
    pt_a = (-65.0, 20.0)
    pt_b = (-65.5, 20.0)
    dep = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)

    # Open water
    res_open = evaluate_transition(sagar_kanya, pt_a, pt_b, {"sea_ice_concentration": 0.0}, dep)
    assert res_open.feasible is True

    # Moderate open-pack ice (8% SIC, within 15% limit)
    res_ice = evaluate_transition(sagar_kanya, pt_a, pt_b, {"sea_ice_concentration": 8.0}, dep)
    assert res_ice.feasible is True
    assert res_ice.achievable_speed_kn < res_open.achievable_speed_kn
    assert any("Navigating in ice pack" in w for w in res_ice.warnings)

    # Heavy pack ice (30% SIC > 15% Sagar Kanya limit)
    res_blocked = evaluate_transition(sagar_kanya, pt_a, pt_b, {"sea_ice_concentration": 30.0}, dep)
    assert res_blocked.feasible is False
    assert "exceeds operational limit 15.0%" in res_blocked.reason


# =========================================================================
# 8. Shallow Depth & Under-Keel Clearance
# =========================================================================
def test_shallow_depth(sagar_kanya: VesselProfile):
    """Verify bathymetry clearance policy: SAFE, WARNING, and HARD_BLOCK / Grounding."""
    pt_a = (-69.0, 76.0)
    pt_b = (-69.1, 76.0)
    dep = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)

    # 1. Deep ocean (1000m) -> SAFE
    res_deep = evaluate_transition(sagar_kanya, pt_a, pt_b, {"bathymetry_depth_m": 1000.0}, dep)
    assert res_deep.feasible is True
    assert res_deep.clearance_status == "SAFE"

    # 2. Insufficient under-keel clearance (7.0m depth - 5.6m draft = 1.4m < 3.0m requirement)
    res_shallow = evaluate_transition(sagar_kanya, pt_a, pt_b, {"bathymetry_depth_m": 7.0}, dep)
    assert res_shallow.feasible is False
    assert res_shallow.clearance_status == "HARD_BLOCK"
    assert "Insufficient under-keel clearance" in res_shallow.reason

    # 3. Grounding (4.0m depth <= 5.6m draft)
    res_grounded = evaluate_transition(sagar_kanya, pt_a, pt_b, {"bathymetry_depth_m": 4.0}, dep)
    assert res_grounded.feasible is False
    assert res_grounded.clearance_status == "CRITICAL"
    assert "Vessel grounding" in res_grounded.reason


# =========================================================================
# 9. SCAR ADD Hard Block
# =========================================================================
def test_scar_add_hard_block(sagar_kanya: VesselProfile):
    """Verify that SCAR ADD land and ice shelves are strictly non-navigable hard blocks."""
    pt_a = (-70.0, 20.0)
    pt_b = (-70.5, 20.0)
    dep = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)

    # Land
    res_land = evaluate_transition(sagar_kanya, pt_a, pt_b, {"geographic_status": "LAND", "is_blocked": True}, dep)
    assert res_land.feasible is False
    assert "SCAR ADD blocked region (LAND)" in res_land.reason

    # Ice Shelf
    res_shelf = evaluate_transition(sagar_kanya, pt_a, pt_b, {"geographic_status": "ICE_SHELF", "is_blocked": True}, dep)
    assert res_shelf.feasible is False
    assert "SCAR ADD blocked region (ICE_SHELF)" in res_shelf.reason


# =========================================================================
# 10. Fuel Accumulation
# =========================================================================
def test_fuel_accumulation(sagar_kanya: VesselProfile):
    """Verify cumulative fuel consumption tracking and bunker capacity margins."""
    pt_a = (-40.0, 20.0)
    pt_b = (-41.0, 20.0)
    dep = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    env = {"bathymetry_depth_m": 3000.0}

    # Leg 1
    res1 = evaluate_transition(sagar_kanya, pt_a, pt_b, env, dep, previous_cumulative_fuel_mt=0.0)
    assert res1.cumulative_fuel_mt == res1.fuel_used
    assert res1.fuel_capacity_margin_pct < 100.0

    # Leg 2 chaining
    res2 = evaluate_transition(
        sagar_kanya, pt_a, pt_b, env, dep, previous_cumulative_fuel_mt=res1.cumulative_fuel_mt
    )
    assert res2.cumulative_fuel_mt == round(res1.fuel_used + res2.fuel_used, 4)
    assert res2.fuel_capacity_margin_pct < res1.fuel_capacity_margin_pct

    # Exceeded bunker capacity
    res_over = evaluate_transition(
        sagar_kanya, pt_a, pt_b, env, dep, previous_cumulative_fuel_mt=400.0  # > 368 MT
    )
    assert res_over.fuel_capacity_exceeded is True
    assert any("Cumulative bunker capacity exceeded" in w for w in res_over.warnings)


# =========================================================================
# 11. Endurance Verification
# =========================================================================
def test_endurance(sagar_kanya: VesselProfile):
    """Verify 45-day published endurance limit tracking."""
    pt_a = (-40.0, 20.0)
    pt_b = (-41.0, 20.0)
    dep = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)

    # 10 days cumulative -> 35 days margin
    res1 = evaluate_transition(sagar_kanya, pt_a, pt_b, {}, dep, previous_cumulative_time_hours=240.0)
    assert res1.endurance_exceeded is False
    assert res1.endurance_margin_days > 30.0

    # 46 days cumulative -> exceeded
    res_exceeded = evaluate_transition(sagar_kanya, pt_a, pt_b, {}, dep, previous_cumulative_time_hours=46 * 24.0)
    assert res_exceeded.endurance_exceeded is True
    assert any("Cumulative endurance exceeded" in w for w in res_exceeded.warnings)


# =========================================================================
# 12. Deterministic Identical Inputs
# =========================================================================
def test_deterministic_identical_inputs(sagar_kanya: VesselProfile):
    """Verify identical inputs yield identical outputs without stochastic drift."""
    pt_a = (-55.2, 30.4)
    pt_b = (-55.8, 31.1)
    dep = datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc)
    env = {
        "current_u_ms": 0.35,
        "current_v_ms": -0.22,
        "wind_u_ms": 8.1,
        "wind_v_ms": -4.2,
        "wave_height_m": 3.8,
        "sea_ice_concentration": 4.5,
        "bathymetry_depth_m": 3200.0,
    }

    run1 = evaluate_transition(sagar_kanya, pt_a, pt_b, env, dep)
    run2 = evaluate_transition(sagar_kanya, pt_a, pt_b, env, dep)

    assert run1.model_dump() == run2.model_dump()


# =========================================================================
# 13. Time-Dependent Environment
# =========================================================================
def test_time_dependent_environment(sagar_kanya: VesselProfile):
    """Verify that performance at cell_A, t1 differs from cell_A, t2 when environment changes."""
    pt_a = (-45.5, 25.0)
    pt_b = (-45.0, 25.0)  # Heading 0° North
    t1 = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    # t1: calm summer day (favorable Northward current +0.5 m/s, calm 1.2m waves)
    env_t1 = {"current_v_ms": 0.5, "wave_height_m": 1.2}
    # t2: passing storm system (opposing Northward current -1.2 m/s, heavy 5.5m waves, 18 m/s wind)
    env_t2 = {"current_v_ms": -1.2, "wave_height_m": 5.5, "wind_speed_ms": 18.0}

    eval_t1 = evaluate_transition(sagar_kanya, pt_a, pt_b, env_t1, t1)
    eval_t2 = evaluate_transition(sagar_kanya, pt_a, pt_b, env_t2, t2)

    assert eval_t1.ground_speed_kn > eval_t2.ground_speed_kn
    assert eval_t1.travel_time_hours < eval_t2.travel_time_hours
    assert eval_t1.fuel_used < eval_t2.fuel_used


# =========================================================================
# 14. H3 Cell Transition
# =========================================================================
def test_h3_cell_transition(sagar_kanya: VesselProfile):
    """Verify evaluation between real H3 cell indices."""
    cell_a = "85ad049bfffffff"
    cell_b = "85ad3187fffffff"
    dep = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    env = {"wave_height_m": 2.0, "bathymetry_depth_m": 2500.0}

    res = evaluate_transition(sagar_kanya, cell_a, cell_b, env, dep)

    assert res.distance_nm > 0.0
    assert 0.0 <= res.heading <= 360.0
    assert res.travel_time_hours > 0.0
    assert res.feasible is True


# =========================================================================
# 15. Parameter Provenance Classification
# =========================================================================
def test_provenance(sagar_kanya: VesselProfile):
    """Verify every parameter is classified: PUBLISHED, DERIVED, ASSUMED, USER_CONFIGURED, or UNKNOWN."""
    # Published specifications
    assert sagar_kanya.geometry.length_overall_m.classification == ParameterClassification.PUBLISHED
    assert sagar_kanya.geometry.breadth_extreme_m.classification == ParameterClassification.PUBLISHED
    assert sagar_kanya.geometry.maximum_draft_m.classification == ParameterClassification.PUBLISHED
    assert sagar_kanya.endurance_and_fuel.endurance_days.classification == ParameterClassification.PUBLISHED
    assert sagar_kanya.endurance_and_fuel.fuel_capacity_m3.classification == ParameterClassification.PUBLISHED

    # Ice Capability strictly UNKNOWN
    assert sagar_kanya.ice_capability.classification == ParameterClassification.UNKNOWN
    assert sagar_kanya.ice_capability.status == "UNKNOWN"

    # Assumed parameters
    assert sagar_kanya.environmental_operational_limits.max_safe_wave_height_m.classification == ParameterClassification.ASSUMED
    assert sagar_kanya.environmental_operational_limits.max_operational_wind_speed_ms.classification == ParameterClassification.ASSUMED
    assert sagar_kanya.speed.min_operating_speed_knots.classification == ParameterClassification.ASSUMED

    # Derived parameters
    assert sagar_kanya.endurance_and_fuel.nominal_propulsion_rate_mt_per_hour.classification == ParameterClassification.DERIVED
    assert sagar_kanya.tonnage.displacement_tonnes.classification == ParameterClassification.DERIVED

    # User configured
    assert sagar_kanya.speed.cruise_speed_knots.classification == ParameterClassification.USER_CONFIGURED
    assert sagar_kanya.ice_capability.max_operational_sic.classification == ParameterClassification.USER_CONFIGURED


# =========================================================================
# 16. Assumption & Configuration Handling
# =========================================================================
def test_assumption_and_configuration_handling(sagar_kanya: VesselProfile):
    """Verify that user overrides dynamically affect evaluator behavior without code edits."""
    # Override cruising speed to 11.0 knots
    sagar_kanya.speed.cruise_speed_knots.value = 11.0
    # Override SIC limit to 20%
    sagar_kanya.ice_capability.max_operational_sic.value = 0.20

    res = evaluate_transition(
        sagar_kanya,
        (-60.0, 20.0),
        (-60.5, 20.0),
        {"sea_ice_concentration": 18.0, "bathymetry_depth_m": 3000.0},
        datetime(2026, 1, 15, tzinfo=timezone.utc),
    )

    # 18% is now feasible under user's 20% policy
    assert res.feasible is True
    assert res.requested_speed_kn == 11.0

    # Test frontend config export
    cfg = sagar_kanya.to_frontend_config()
    assert "groups" in cfg
    assert cfg["groups"]["ice_policy"]["fields"]["max_operational_sic"]["value"] == 0.20
    assert cfg["groups"]["ice_policy"]["fields"]["max_operational_sic"]["is_editable"] is True


# =========================================================================
# Bonus: Maitri Inland Node Distinction Verification
# =========================================================================
def test_maitri_maritime_access_vs_inland(sagar_kanya: VesselProfile):
    """Verify that Maitri inland station is flagged as non-navigable land, whereas India Bay access is ocean."""
    assert MAITRI_INLAND_STATION.is_inland is True
    assert MAITRI_MARITIME_ACCESS.is_inland is False

    # Maitri Station coordinates (-70.7644, 11.7340) in Schirmacher Oasis
    checker = VesselConstraintChecker(vessel=sagar_kanya)
    inland_check = checker.evaluate(
        vessel=sagar_kanya,
        geographic_status="LAND",
        is_blocked_scar=True,
        water_depth_m=None,
        sea_ice_concentration=0.0,
        wave_height_m=0.0,
        wind_speed_ms=5.0,
    )
    assert inland_check.is_feasible is False
    assert inland_check.is_scar_blocked is True
