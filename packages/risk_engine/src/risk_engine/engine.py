"""
Main Deterministic Environmental Risk Engine for AMIP.
Fuses normalized H3 x Time state, 73-iceberg hazard, vessel performance,
and SCAR ADD / GEBCO constraints into explainable RiskProfile and RouteRiskProfile.
"""

import math
from datetime import datetime, timezone
from typing import Optional, Tuple, Any, List, Dict, Union
from pathlib import Path

import numpy as np

from domain.coordinates import BoundingBox, GridSpec, GeoPoint
from domain.risk import RiskField, RiskWeightsConfig, RiskFactorAttribution
from domain.vessel import VesselProfile
from risk_engine.policy import RiskPolicyConfig, load_risk_policy
from risk_engine.models import RiskProfile, RouteRiskProfile, RiskContext, RiskComponentScores, DataQualityConfidence
from risk_engine.warnings import RiskWarning, RiskWarningCode
from risk_engine.components import (
    evaluate_geographic_risk,
    evaluate_bathymetric_risk,
    evaluate_sea_ice_risk,
    evaluate_iceberg_risk,
    evaluate_wave_risk,
    evaluate_wind_risk,
    evaluate_current_risk,
    evaluate_data_quality,
)
from risk_engine.route import aggregate_route_risk
from risk_engine.constraints import evaluate_hard_constraints
from risk_engine.soft_costs import compute_soft_risk_factors, combine_risk_field


class RiskEngine:
    """
    AMIP Environmental Risk Engine.
    Evaluates cell-level, transition-level, and route-level environmental risk
    with strict separation of hard constraints, soft costs, and epistemic confidence.
    """

    def __init__(self, policy: Optional[Union[RiskPolicyConfig, str, Path, Dict[str, Any]]] = None) -> None:
        if policy is None:
            self.policy = load_risk_policy()
        elif isinstance(policy, RiskPolicyConfig):
            self.policy = policy
        elif isinstance(policy, (str, Path)):
            self.policy = load_risk_policy(policy)
        elif isinstance(policy, dict):
            self.policy = RiskPolicyConfig.model_validate(policy)
        else:
            raise TypeError(f"Invalid policy specification: {type(policy)}")

    # =========================================================================
    # CANONICAL H3 ENVIRONMENTAL RISK EVALUATION
    # =========================================================================

    def evaluate_cell_risk(
        self,
        cell: Any,
        vessel: Optional[Any] = None,
        policy: Optional[Union[RiskPolicyConfig, Dict[str, Any]]] = None,
        timestamp: Optional[datetime] = None,
        heading_deg: Optional[float] = None,
    ) -> RiskProfile:
        """
        Evaluates the comprehensive environmental risk profile for a single H3 cell state.
        Accepts UnifiedEnvironmentCell, EnvironmentCell, StaticH3Cell, dict, or generic object.
        """
        active_policy = self.policy
        if policy is not None:
            if isinstance(policy, RiskPolicyConfig):
                active_policy = policy
            elif isinstance(policy, dict):
                active_policy = RiskPolicyConfig.model_validate(policy)

        # 1. Extract Cell Identifier & Timestamp
        cell_id = getattr(cell, "cell_id", None) or (cell.get("cell_id") if isinstance(cell, dict) else "unknown_cell")

        valid_dt = timestamp or getattr(cell, "valid_time", None) or getattr(cell, "timestamp", None)
        if valid_dt is None and isinstance(cell, dict):
            valid_dt = cell.get("valid_time") or cell.get("timestamp")
        if valid_dt is None:
            valid_dt = datetime.now(timezone.utc)
        elif isinstance(valid_dt, str):
            try:
                valid_dt = datetime.fromisoformat(valid_dt)
            except Exception:
                valid_dt = datetime.now(timezone.utc)

        # Helper to extract and sanitize values
        def _get_val(primary_key: str, alt_keys: List[str] = [], default=None):
            def _clean(v):
                if v is None:
                    return None
                if isinstance(v, float) and math.isnan(v):
                    return None
                return v

            v = _clean(getattr(cell, primary_key, None))
            if v is not None:
                return v
            if isinstance(cell, dict):
                v = _clean(cell.get(primary_key))
                if v is not None:
                    return v
            for alt in alt_keys:
                v = _clean(getattr(cell, alt, None))
                if v is not None:
                    return v
                if isinstance(cell, dict):
                    v = _clean(cell.get(alt))
                    if v is not None:
                        return v
            return default

        # 2. Extract Physical Variables
        geo_status = str(_get_val("geographic_status", ["status"], default="OPEN_OCEAN"))
        ocean_frac = float(_get_val("ocean_fraction", default=1.0))
        land_frac = float(_get_val("land_fraction", default=0.0))
        shelf_frac = float(_get_val("ice_shelf_fraction", default=0.0))
        tongue_frac = float(_get_val("ice_tongue_fraction", default=0.0))
        rumple_frac = float(_get_val("rumple_fraction", default=0.0))
        is_blocked_flag = bool(_get_val("is_blocked", ["is_scar_blocked"], default=False))

        depth_m = _get_val("bathymetry_depth_m", ["bathymetry_depth", "bathymetry_mean_m", "depth"])
        sic_raw = _get_val("sea_ice_concentration", ["sic", "SIC"])
        sic_unc_raw = _get_val("sea_ice_uncertainty", ["sic_uncertainty", "SIC_uncertainty"])
        iceberg_hz = float(_get_val("iceberg_hazard", ["hazard", "hazard_score"], default=0.0))
        distinct_berg_count = int(_get_val("distinct_iceberg_count", ["supporting_iceberg_count"], default=0))
        berg_ids = _get_val("contributing_iceberg_ids", ["active_icebergs"], default=[])
        if isinstance(berg_ids, np.ndarray):
            berg_ids = berg_ids.tolist()
        elif not isinstance(berg_ids, list):
            berg_ids = [str(berg_ids)] if berg_ids else []

        wave_h = _get_val("wave_height_m", ["wave_height", "significant_wave_height_m", "VHM0"])
        wave_dir = _get_val("wave_direction_deg", ["wave_direction", "VMDR"])
        wave_tp = _get_val("wave_period_s", ["wave_period", "wave_peak_period_s", "VTPK"])

        wind_u = _get_val("wind_u_ms", ["wind_u"])
        wind_v = _get_val("wind_v_ms", ["wind_v"])
        wind_spd = _get_val("wind_speed_ms", ["wind_speed", "wind_speed_knots"])
        if wind_spd is not None and getattr(cell, "wind_speed_knots", None) is not None and wind_u is None:
            # Check if provided in knots
            if "knots" in str(getattr(cell, "wind_speed_knots", "")):
                wind_spd = wind_spd * 0.514444

        curr_u = _get_val("current_u_ms", ["current_u"])
        curr_v = _get_val("current_v_ms", ["current_v"])
        curr_spd = _get_val("current_speed_ms", ["current_speed"])
        curr_dir = _get_val("current_direction_deg", ["current_direction"])

        quality_status = str(_get_val("quality_status", default="OBSERVED"))
        prov_dict = _get_val("provenance", default={})
        if not isinstance(prov_dict, dict):
            prov_dict = {"raw_provenance": str(prov_dict)}
        sic_source = prov_dict.get("sic_source", "OBSERVED" if "MOCK" not in str(prov_dict).upper() else "MOCK")

        # Track missing variables
        missing_vars: List[str] = []
        if depth_m is None:
            missing_vars.append("bathymetry_depth_m")
        if sic_raw is None:
            missing_vars.append("sea_ice_concentration")
        if wave_h is None:
            missing_vars.append("wave_height_m")
        if wind_spd is None and (wind_u is None or wind_v is None):
            missing_vars.append("wind_speed_ms")
        if curr_spd is None and (curr_u is None or curr_v is None):
            missing_vars.append("current_speed_ms")

        # 3. Evaluate Individual Components
        # Geographic
        r_geo, block_geo, reason_geo, rule_geo, warn_geo = evaluate_geographic_risk(
            geographic_status=geo_status,
            ocean_fraction=ocean_frac,
            land_fraction=land_frac,
            ice_shelf_fraction=shelf_frac,
            ice_tongue_fraction=tongue_frac,
            rumple_fraction=rumple_frac,
            is_blocked=is_blocked_flag,
            policy=active_policy,
        )

        # Bathymetric
        draft = 5.6
        if vessel:
            draft = getattr(vessel, "draft_m", getattr(vessel, "draft_meters", 5.6))
        r_bathy, block_bathy, reason_bathy, rule_bathy, status_bathy, clearance_m, warn_bathy = evaluate_bathymetric_risk(
            depth_m=depth_m,
            draft_m=draft,
            policy=active_policy,
            vessel=vessel,
        )

        # Sea-Ice
        r_ice, block_ice, reason_ice, rule_ice, status_ice, conf_ice, warn_ice = evaluate_sea_ice_risk(
            sic=sic_raw,
            sic_uncertainty=sic_unc_raw,
            sic_source=sic_source,
            policy=active_policy,
            vessel=vessel,
        )

        # Iceberg Hazard
        r_berg, status_berg, warn_berg, distinct_count, active_berg_ids = evaluate_iceberg_risk(
            iceberg_hazard=iceberg_hz,
            distinct_iceberg_count=distinct_berg_count,
            contributing_iceberg_ids=berg_ids,
            policy=active_policy,
        )

        # Waves
        r_wave, status_wave, warn_wave = evaluate_wave_risk(
            wave_height_m=wave_h,
            wave_direction_deg=wave_dir,
            wave_period_s=wave_tp,
            heading_deg=heading_deg,
            policy=active_policy,
            vessel=vessel,
        )

        # Wind
        r_wind, spd_wind, dir_wind, status_wind, warn_wind = evaluate_wind_risk(
            wind_u_ms=wind_u,
            wind_v_ms=wind_v,
            wind_speed_ms=wind_spd,
            heading_deg=heading_deg,
            policy=active_policy,
            vessel=vessel,
        )

        # Current
        r_curr, spd_curr, dir_curr, assist_curr, status_curr, warn_curr = evaluate_current_risk(
            current_u_ms=curr_u,
            current_v_ms=curr_v,
            current_speed_ms=curr_spd,
            current_direction_deg=curr_dir,
            heading_deg=heading_deg,
            policy=active_policy,
        )

        # Confidence & Data Quality
        conf_score, conf_class, r_data_qual, warn_conf = evaluate_data_quality(
            missing_variables=missing_vars,
            quality_status=quality_status,
            sic_uncertainty=sic_unc_raw,
            sic_source=sic_source,
            lead_time_days=0,
            policy=active_policy,
        )

        # 4. Composite Risk Calculation
        w_ice = active_policy.get_weight("sea_ice")
        w_berg = active_policy.get_weight("iceberg")
        w_wave = active_policy.get_weight("waves")
        w_wind = active_policy.get_weight("wind")
        w_bathy = active_policy.get_weight("bathymetry")
        w_curr = active_policy.get_weight("current")
        w_conf = active_policy.get_weight("confidence")

        composite = (
            w_ice * r_ice
            + w_berg * r_berg
            + w_wave * r_wave
            + w_wind * r_wind
            + w_bathy * r_bathy
            + w_curr * r_curr
            + w_conf * r_data_qual
        )

        # 5. Hard Block Synthesis
        hard_blocked = block_geo or block_bathy or block_ice
        primary_reason = reason_geo or reason_bathy or reason_ice
        primary_rule = rule_geo or rule_bathy or rule_ice

        all_warnings: List[RiskWarning] = (
            warn_geo + warn_bathy + warn_ice + warn_berg + warn_wave + warn_wind + warn_curr + warn_conf
        )

        # Clean normalized SIC and uncertainty
        clean_sic = (sic_raw / 100.0 if sic_raw > 1.0 else sic_raw) if sic_raw is not None else None
        clean_unc = (sic_unc_raw / 100.0 if sic_unc_raw > 1.0 else sic_unc_raw) if sic_unc_raw is not None else None

        return RiskProfile(
            cell_id=str(cell_id),
            timestamp=valid_dt,
            hard_blocked=hard_blocked,
            block_reason=primary_reason,
            blocking_rule=primary_rule,
            composite_risk=round(min(1.0, max(0.0, composite)), 4),
            confidence_score=conf_score,
            confidence_class=conf_class,
            geographic_risk=round(r_geo, 4),
            bathymetric_risk=round(r_bathy, 4),
            sea_ice_risk=round(r_ice, 4),
            iceberg_risk=round(r_berg, 4),
            wave_risk=round(r_wave, 4),
            wind_risk=round(r_wind, 4),
            current_risk=round(r_curr, 4),
            data_quality_risk=round(r_data_qual, 4),
            SIC=clean_sic,
            SIC_uncertainty=clean_unc,
            iceberg_hazard=round(iceberg_hz, 4),
            distinct_iceberg_count=distinct_count,
            contributing_iceberg_ids=active_berg_ids,
            wave_height=round(wave_h, 2) if wave_h is not None else None,
            wave_period=round(wave_tp, 1) if wave_tp is not None else None,
            wind_speed=spd_wind,
            current_speed=spd_curr,
            current_direction=dir_curr,
            current_assistance=assist_curr,
            bathymetry_depth=round(depth_m, 1) if depth_m is not None else None,
            clearance_m=round(clearance_m, 2) if clearance_m is not None else None,
            geographic_status=geo_status,
            ocean_fraction=round(ocean_frac, 3),
            land_fraction=round(land_frac, 3),
            ice_shelf_fraction=round(shelf_frac, 3),
            warnings=all_warnings,
            provenance=prov_dict,
            policy_name=active_policy.policy_name,
            policy_version=active_policy.policy_version,
            model_version="AMIP-RiskEngine-2026.1",
        )

    def evaluate_transition_risk(
        self,
        cell_a: Any,
        cell_b: Any,
        vessel: Optional[Any] = None,
        performance: Optional[Any] = None,
        policy: Optional[Union[RiskPolicyConfig, Dict[str, Any]]] = None,
        departure_time: Optional[datetime] = None,
        heading_deg: Optional[float] = None,
    ) -> RiskProfile:
        """
        Evaluates risk along a transition between cell_a and cell_b.
        Incorporate heading to evaluate apparent current assistance/penalty and wave encounter.
        """
        hdg = heading_deg
        if hdg is None and performance is not None and hasattr(performance, "heading"):
            hdg = float(performance.heading)

        # Evaluate target cell B with transit heading context
        profile_b = self.evaluate_cell_risk(
            cell=cell_b,
            vessel=vessel,
            policy=policy,
            timestamp=departure_time,
            heading_deg=hdg,
        )

        return profile_b

    def evaluate_route_risk(
        self,
        evaluations: List[Union[RiskProfile, Dict[str, Any]]],
        segment_durations_hours: Optional[List[float]] = None,
        policy: Optional[Union[RiskPolicyConfig, Dict[str, Any]]] = None,
    ) -> RouteRiskProfile:
        """
        Aggregates a sequence of cell/transition evaluations into a RouteRiskProfile.
        """
        active_policy = self.policy
        if policy is not None:
            if isinstance(policy, RiskPolicyConfig):
                active_policy = policy
            elif isinstance(policy, dict):
                active_policy = RiskPolicyConfig.model_validate(policy)

        return aggregate_route_risk(
            evaluations=evaluations,
            segment_durations_hours=segment_durations_hours,
            policy_name=active_policy.policy_name,
            policy_version=active_policy.policy_version,
        )

    # =========================================================================
    # LEGACY / BACKWARD COMPATIBILITY INTERFACES
    # =========================================================================

    def compute_risk_field(
        self,
        valid_time: datetime,
        lead_time_days: int,
        vessel: VesselProfile,
        weights: Optional[RiskWeightsConfig] = None,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
    ) -> Tuple[RiskField, np.ndarray, np.ndarray]:
        """Legacy 2D grid risk computation using Zarr reader for backward compatibility."""
        from data_access.zarr_reader import default_zarr_reader

        weights = weights or RiskWeightsConfig()

        if bbox is None:
            bbox = BoundingBox(
                min_latitude=-80.0,
                min_longitude=-20.0,
                max_latitude=-30.0,
                max_longitude=100.0,
            )

        # 1. Fetch physical layers from Zarr reader
        _, _, sic_grid = default_zarr_reader.get_grid_slice("sea_ice_concentration", valid_time, bbox, grid_spec)
        _, _, unc_grid = default_zarr_reader.get_grid_slice("sic_uncertainty", valid_time, bbox, grid_spec)
        _, _, depth_grid = default_zarr_reader.get_grid_slice("bathymetry", valid_time, bbox, grid_spec)
        _, _, wind_u = default_zarr_reader.get_grid_slice("wind_u", valid_time, bbox, grid_spec)
        _, _, wind_v = default_zarr_reader.get_grid_slice("wind_v", valid_time, bbox, grid_spec)
        _, _, current_u = default_zarr_reader.get_grid_slice("ocean_u", valid_time, bbox, grid_spec)
        _, _, current_v = default_zarr_reader.get_grid_slice("ocean_v", valid_time, bbox, grid_spec)
        _, _, wave_hs = default_zarr_reader.get_grid_slice("significant_wave_height", valid_time, bbox, grid_spec)

        # 2. Iceberg hazard surface
        lat_grid, lon_grid = np.meshgrid(
            np.linspace(bbox.min_latitude, bbox.max_latitude, sic_grid.shape[0]),
            np.linspace(bbox.min_longitude, bbox.max_longitude, sic_grid.shape[1]),
            indexing="ij",
        )
        berg_center_lat = -63.5 + (0.02 * lead_time_days)
        berg_center_lon = 45.0 + (0.25 * lead_time_days)
        d_berg = ((lat_grid - berg_center_lat) ** 2) + (((lon_grid - berg_center_lon) * 0.5) ** 2)
        iceberg_hazard_grid = np.clip(0.85 * np.exp(-d_berg / 8.0), 0.0, 1.0)

        # 3. Evaluate Hard Constraints
        impassable_mask = evaluate_hard_constraints(
            depth_grid=depth_grid,
            sic_grid=sic_grid,
            iceberg_hazard_grid=iceberg_hazard_grid,
            vessel=vessel,
            min_depth_margin_m=vessel.under_keel_margin_m,
            max_navigable_sic=vessel.max_navigable_sic,
        )

        # 4. Evaluate Soft Costs
        r_ice, r_berg, r_wind, r_wave, c_current = compute_soft_risk_factors(
            sic_grid=sic_grid,
            sic_unc_grid=unc_grid,
            iceberg_hazard_grid=iceberg_hazard_grid,
            wind_u=wind_u,
            wind_v=wind_v,
            current_u=current_u,
            current_v=current_v,
            wave_hs=wave_hs,
            max_navigable_sic=vessel.max_navigable_sic,
        )

        composite_risk = combine_risk_field(
            r_ice=r_ice,
            r_berg=r_berg,
            r_wind=r_wind,
            r_wave=r_wave,
            c_current=c_current,
            r_unc=unc_grid,
            weights=weights,
        )

        composite_risk[impassable_mask] = 1.0

        mean_r = float(np.mean(composite_risk))
        max_r = float(np.max(composite_risk))
        p90_r = float(np.percentile(composite_risk, 90))
        p95_r = float(np.percentile(composite_risk, 95))
        impassable_count = int(np.sum(impassable_mask))
        impassable_area = float(impassable_count * 100.0)

        risk_field = RiskField(
            valid_time=valid_time,
            lead_time_days=lead_time_days,
            bounds=bbox,
            bbox=bbox,
            grid_shape=list(composite_risk.shape),
            mean_risk=round(mean_r, 4),
            max_risk=round(max_r, 4),
            p90_risk=round(p90_r, 4),
            p95_risk=round(p95_r, 4),
            impassable_cells_count=impassable_count,
            impassable_area_sqkm=round(impassable_area, 1),
            data_ref=f"data/processed/risk/{valid_time.strftime('%Y%m%d')}",
            values=composite_risk.tolist(),
            hard_constraint_mask=impassable_mask.tolist(),
        )

        return risk_field, composite_risk, impassable_mask

    def evaluate_grid(
        self,
        valid_time: datetime,
        env_slice: Any = None,
        sea_ice_forecast: Any = None,
        iceberg_hazard: Any = None,
        vessel: Optional[VesselProfile] = None,
        weights: Optional[RiskWeightsConfig] = None,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
        horizon_days: int = 14,
    ) -> RiskField:
        """Legacy grid evaluator."""
        v = vessel or VesselProfile()
        target_bbox = bbox or (getattr(env_slice, "bounds", None) if env_slice else None)
        target_grid = grid_spec
        if target_grid is None and env_slice and hasattr(env_slice, "grid_shape") and env_slice.grid_shape:
            target_grid = GridSpec(
                bounds=target_bbox,
                n_lat=env_slice.grid_shape[0],
                n_lon=env_slice.grid_shape[1],
            )
        field, _, _ = self.compute_risk_field(
            valid_time=valid_time,
            lead_time_days=horizon_days,
            vessel=v,
            weights=weights,
            bbox=target_bbox,
            grid_spec=target_grid,
        )
        return field

    def evaluate_point(
        self,
        point: GeoPoint,
        valid_time: datetime,
        point_env: Any = None,
        sea_ice_forecast: Any = None,
        iceberg_hazard: Any = None,
        vessel: Optional[VesselProfile] = None,
        weights: Optional[RiskWeightsConfig] = None,
    ) -> RiskFactorAttribution:
        """Legacy point evaluator."""
        v = vessel or VesselProfile()
        attrib = self.evaluate_point_risk(point=point, timestamp=valid_time, vessel=v, weights=weights)
        if point_env:
            attrib.sea_ice_concentration = getattr(point_env, "sea_ice_concentration", attrib.sea_ice_risk)
        attrib.composite_risk = max(attrib.sea_ice_risk, attrib.iceberg_risk, attrib.wave_risk)
        return attrib

    def evaluate_point_risk(
        self,
        point: GeoPoint,
        timestamp: datetime,
        vessel: VesselProfile,
        weights: Optional[RiskWeightsConfig] = None,
    ) -> RiskFactorAttribution:
        """Legacy point risk evaluator."""
        weights = weights or RiskWeightsConfig()

        lat = point.latitude
        lon = point.longitude

        is_hard = False
        dominant = "FAVORABLE_OPEN_WATER"

        if lat < -71.0:
            is_hard = True
            dominant = "GROUNDED_ICE_SHELF"
            explanation = "Point intersects grounded Antarctic ice shelf."
            return RiskFactorAttribution(
                sea_ice_risk=1.0,
                iceberg_risk=0.1,
                weather_risk=0.2,
                wave_risk=0.0,
                current_penalty=0.0,
                is_hard_constrained=True,
                dominant_hazard=dominant,
                explanation=explanation,
            )

        ice_risk = max(0.0, min(1.0, (-62.0 - lat) / 8.0))
        if ice_risk > vessel.max_navigable_sic:
            is_hard = True
            dominant = "MAXIMUM_SEA_ICE_EXCEEDED"

        d_berg = ((lat + 63.5) ** 2) + (((lon - 45.0) * 0.5) ** 2)
        berg_risk = float(np.clip(0.85 * np.exp(-d_berg / 8.0), 0.0, 1.0))

        storm_risk = 0.45 if -55.0 <= lat <= -45.0 else 0.15
        wave_risk = 0.40 if -55.0 <= lat <= -48.0 else 0.10

        if is_hard:
            explanation = f"Hard constraint violation: {dominant}."
        elif ice_risk > 0.40:
            dominant = "SEA_ICE_CONCENTRATION"
            explanation = f"Elevated hazard from {round(ice_risk * 100)}% sea-ice concentration near approach."
        elif berg_risk > 0.30:
            dominant = "ICEBERG_COLLISION_HAZARD"
            explanation = "Elevated risk due to proximity to active iceberg drift corridor."
        elif storm_risk > 0.35:
            dominant = "ROUGH_SEAS_AND_WIND"
            explanation = "Significant wave height and gale-force westerly winds in the Southern Ocean belt."
        else:
            explanation = "Conditions within normal operating envelope."

        return RiskFactorAttribution(
            sea_ice_risk=round(ice_risk, 3),
            iceberg_risk=round(berg_risk, 3),
            weather_risk=round(storm_risk, 3),
            wave_risk=round(wave_risk, 3),
            current_penalty=0.05,
            is_hard_constrained=is_hard,
            dominant_hazard=dominant,
            explanation=explanation,
        )


default_risk_engine = RiskEngine()
