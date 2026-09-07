"""
Frontend Performance Inspector Contract and Formatter.
Prepares human-readable, interactive inspection payloads for route segments and H3 cells.
Explains the hydrodynamic, meteorological, cryospheric, and bathymetric forces
affecting vessel behavior in specific locations.
"""

from typing import Dict, Any, Optional
from vessel.models import VesselProfile
from vessel.evaluator import EdgeEvaluation


def format_transition_inspector(
    evaluation: EdgeEvaluation,
    vessel: VesselProfile,
    cell_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates an exhaustive, transparent performance diagnostic card
    for consumption by the frontend Route Segment / H3 Cell Inspector.
    """
    cid = cell_id or evaluation.constraint_state.get("cell_id") or "H3-TRANSITION"

    # Generate human-readable narrative explaining performance differences
    narratives = []

    # 1. Currents narrative
    assist = evaluation.current_assistance_kn
    if assist > 0.3:
        narratives.append(f"Favorable ocean current increases ground progression by +{assist:.1f} kn.")
    elif assist < -0.3:
        narratives.append(f"Adverse head current reduces ground progression by {abs(assist):.1f} kn.")

    # 2. Waves narrative
    if evaluation.wave_height and evaluation.wave_height > 2.5:
        wave_loss_pct = round((1.0 - (evaluation.achievable_speed_kn / max(0.1, evaluation.requested_speed_kn))) * 100.0, 1)
        narratives.append(f"Wave height Hs={evaluation.wave_height:.1f}m imparts added hull resistance (loss ~{wave_loss_pct}%).")

    # 3. Ice narrative
    if evaluation.sic and evaluation.sic > 0.0:
        narratives.append(f"Sea ice concentration of {evaluation.sic*100.0:.1f}% degrades through-water speed and elevates propulsion power.")

    # 4. Bathymetry narrative
    if evaluation.bathymetry_depth is not None:
        if evaluation.clearance_status == "CRITICAL":
            narratives.append(f"CRITICAL GROUNDING RISK: Water depth {evaluation.bathymetry_depth:.1f}m provides insufficient clearance below {evaluation.draft:.1f}m keel.")
        elif evaluation.clearance_status == "WARNING":
            narratives.append(f"Caution: Under-keel clearance ({evaluation.clearance:.1f}m) approaches the safety threshold.")

    if not narratives:
        narratives.append("Near-baseline open ocean conditions with calm sea state.")

    return {
        "inspector_schema_version": "AMIP-VesselInspector-2026.1",
        "vessel": {
            "vessel_id": vessel.vessel_id,
            "vessel_name": vessel.vessel_name,
            "callsign": vessel.callsign,
            "vessel_type": vessel.vessel_type,
            "draft_m": vessel.draft_m,
            "cruising_speed_knots": vessel.cruising_speed_knots,
        },
        "cell": {
            "cell_id": cid,
            "departure_time": evaluation.departure_time,
            "arrival_time": evaluation.arrival_time,
            "transit_duration_hours": evaluation.travel_time_hours,
            "distance_nm": evaluation.distance_nm,
            "distance_m": evaluation.distance_m,
            "heading_deg": evaluation.heading,
        },
        "kinematics": {
            "requested_speed_kn": evaluation.requested_speed_kn,
            "achievable_through_water_speed_kn": evaluation.achievable_speed_kn,
            "ground_speed_kn": evaluation.ground_speed_kn,
            "along_track_speed_kn": evaluation.along_track_speed_kn,
            "ground_direction_deg": evaluation.ground_direction_deg,
        },
        "environmental_forcings": {
            "current": {
                "u_ms": evaluation.current_u,
                "v_ms": evaluation.current_v,
                "speed_kn": evaluation.current_speed_kn,
                "along_track_assistance_kn": evaluation.current_assistance_kn,
            },
            "wind": {
                "u_ms": evaluation.wind_u,
                "v_ms": evaluation.wind_v,
                "speed_ms": evaluation.wind_speed_ms,
                "relative_speed_ms": evaluation.relative_wind_speed_ms,
                "relative_direction_deg": evaluation.relative_wind_direction_deg,
            },
            "waves": {
                "significant_height_m": evaluation.wave_height,
                "direction_deg": evaluation.wave_direction,
                "peak_period_s": evaluation.wave_period,
                "encounter_angle_deg": evaluation.wave_encounter_deg,
            },
            "cryosphere": {
                "sea_ice_concentration_fraction": evaluation.sic,
                "sea_ice_percent": round(evaluation.sic * 100.0, 1) if evaluation.sic is not None else None,
                "sea_ice_uncertainty_fraction": evaluation.sic_uncertainty,
            },
            "bathymetry": {
                "depth_m": evaluation.bathymetry_depth,
                "draft_m": evaluation.draft,
                "under_keel_clearance_m": evaluation.clearance,
                "clearance_status": evaluation.clearance_status,
            },
        },
        "fuel_and_endurance": {
            "hourly_rate_mt_per_hour": evaluation.fuel_rate,
            "leg_fuel_used_mt": evaluation.fuel_used,
            "leg_fuel_used_m3": evaluation.fuel_used_m3,
            "cumulative_fuel_mt": evaluation.cumulative_fuel_mt,
            "remaining_bunker_margin_pct": evaluation.fuel_capacity_margin_pct,
            "bunker_capacity_exceeded": evaluation.fuel_capacity_exceeded,
            "cumulative_voyage_hours": evaluation.cumulative_time_hours,
            "remaining_endurance_days": evaluation.endurance_margin_days,
            "endurance_exceeded": evaluation.endurance_exceeded,
        },
        "feasibility": {
            "is_feasible": evaluation.feasible,
            "primary_blocking_reason": evaluation.reason,
            "operational_warnings": evaluation.warnings,
        },
        "performance_narrative": " ".join(narratives),
    }
