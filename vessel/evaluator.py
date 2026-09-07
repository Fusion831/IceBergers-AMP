"""
Vessel Performance Evaluator for AMIP.
Evaluates the physical transit of a vessel between spatial states against normalized H3 x Time environment.
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from pydantic import BaseModel, Field

from vessel.models import VesselProfile
from vessel.fuel import FuelConsumptionModel
from vessel.constraints import VesselConstraintChecker, ConstraintResult

# Unit Conversion Constants
METERS_PER_NAUTICAL_MILE = 1852.0
MS_PER_KNOT = 0.51444444444


class EdgeEvaluation(BaseModel):
    """
    Detailed, transparent diagnostic evaluation of a vessel transition between two cells.
    Consumed by Router, Risk Engine, and Frontend Performance Inspector.
    """
    # Feasibility & Diagnostics
    feasible: bool = Field(..., description="True if transition satisfies all hard physical and regulatory constraints")
    reason: Optional[str] = Field(default=None, description="Primary failure explanation if infeasible")
    warnings: List[str] = Field(default_factory=list, description="Operational soft constraint warnings")

    # Geometry & Kinematics
    heading: float = Field(..., description="Forward azimuth from state A to state B in degrees [0, 360)")
    distance_m: float = Field(..., description="Geodesic distance between cell centroids in meters")
    distance_nm: float = Field(..., description="Distance in international nautical miles")

    # Speeds (Distinguishing Requested, Achievable, and Ground)
    requested_speed_kn: float = Field(..., description="Target service cruising speed requested by operator")
    achievable_speed_kn: float = Field(..., description="Effective through-water speed after wave/wind/ice resistance")
    ground_speed_kn: float = Field(..., description="Speed over ground after 2D vector current addition")
    ground_direction_deg: float = Field(..., description="Course over ground azimuth in degrees [0, 360)")
    along_track_speed_kn: float = Field(..., description="Ground velocity component projected along planned track")

    # Environmental Forcings at Transition
    current_u: Optional[float] = Field(default=None, description="Eastward ocean current (m/s)")
    current_v: Optional[float] = Field(default=None, description="Northward ocean current (m/s)")
    current_speed_kn: Optional[float] = Field(default=None, description="Current magnitude in knots")
    current_assistance_kn: float = Field(default=0.0, description="Along-track current component (+ fwd, - opposing)")

    wind_u: Optional[float] = Field(default=None, description="Eastward 10m wind (m/s)")
    wind_v: Optional[float] = Field(default=None, description="Northward 10m wind (m/s)")
    wind_speed_ms: Optional[float] = Field(default=None, description="Wind magnitude in m/s")
    relative_wind_speed_ms: Optional[float] = Field(default=None, description="Relative apparent wind speed")
    relative_wind_direction_deg: Optional[float] = Field(default=None, description="Relative apparent wind angle to heading")

    wave_height: Optional[float] = Field(default=None, description="Significant wave height Hs in meters")
    wave_direction: Optional[float] = Field(default=None, description="Wave mean direction in degrees")
    wave_period: Optional[float] = Field(default=None, description="Wave peak period Tp in seconds")
    wave_encounter_deg: Optional[float] = Field(default=None, description="Relative wave encounter angle")

    # Cryosphere & Bathymetry
    sic: Optional[float] = Field(default=None, description="Sea ice concentration fraction [0.0, 1.0]")
    sic_uncertainty: Optional[float] = Field(default=None, description="Sea ice concentration uncertainty fraction [0.0, 1.0]")
    bathymetry_depth: Optional[float] = Field(default=None, description="Water depth positive in meters")
    draft: float = Field(..., description="Vessel operating draft in meters")
    clearance: Optional[float] = Field(default=None, description="Under-keel clearance (depth - draft)")
    clearance_status: Optional[str] = Field(default="SAFE", description="UKC status: SAFE, WARNING, CRITICAL, HARD_BLOCK")

    # Time & Fuel Consumption
    travel_time_hours: float = Field(..., description="Segment transit time in hours")
    departure_time: str = Field(..., description="Departure timestamp (ISO 8601 UTC)")
    arrival_time: str = Field(..., description="Estimated arrival timestamp at destination (ISO 8601 UTC)")

    fuel_rate: float = Field(..., description="Fuel consumption rate in metric tonnes / hour")
    fuel_used: float = Field(..., description="Total fuel used for transition in metric tonnes")
    fuel_used_m3: float = Field(..., description="Total fuel used in cubic meters")

    # Cumulative Tracking across Route Legs
    cumulative_fuel_mt: Optional[float] = Field(default=None, description="Cumulative fuel consumed up to this transition (MT)")
    fuel_capacity_margin_pct: Optional[float] = Field(default=None, description="Remaining bunker margin percentage")
    fuel_capacity_exceeded: Optional[bool] = Field(default=None)
    cumulative_time_hours: Optional[float] = Field(default=None, description="Cumulative transit time in hours")
    endurance_margin_days: Optional[float] = Field(default=None, description="Remaining endurance days")
    endurance_exceeded: Optional[bool] = Field(default=None)

    # Context & Versioning
    constraint_state: Dict[str, Any] = Field(default_factory=dict)
    model_version: str = "AMIP-VesselPerf-2026.1 (ORV Sagar Kanya POC Model)"

    @property
    def SIC(self) -> Optional[float]:
        """Upper-case alias for sea ice concentration."""
        return self.sic

    @property
    def SIC_uncertainty(self) -> Optional[float]:
        """Upper-case alias for sea ice uncertainty."""
        return self.sic_uncertainty

    def to_inspector_dict(self, cell_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Formats performance metrics for the Frontend Performance Inspector.
        Enables users to select an H3 cell / route transition and understand
        the physical forces and operational constraints governing performance.
        """
        return {
            "cell_id": cell_id or self.constraint_state.get("cell_id"),
            "departure_time": self.departure_time,
            "arrival_time": self.arrival_time,
            "heading_deg": self.heading,
            "distance_nm": self.distance_nm,
            "speeds": {
                "requested_kn": self.requested_speed_kn,
                "achievable_through_water_kn": self.achievable_speed_kn,
                "ground_speed_kn": self.ground_speed_kn,
                "along_track_kn": self.along_track_speed_kn,
                "ground_direction_deg": self.ground_direction_deg,
            },
            "environment": {
                "current": {
                    "u_ms": self.current_u,
                    "v_ms": self.current_v,
                    "speed_kn": self.current_speed_kn,
                    "assistance_kn": self.current_assistance_kn,
                },
                "wind": {
                    "u_ms": self.wind_u,
                    "v_ms": self.wind_v,
                    "speed_ms": self.wind_speed_ms,
                    "relative_speed_ms": self.relative_wind_speed_ms,
                    "relative_angle_deg": self.relative_wind_direction_deg,
                },
                "waves": {
                    "height_m": self.wave_height,
                    "direction_deg": self.wave_direction,
                    "period_s": self.wave_period,
                    "encounter_deg": self.wave_encounter_deg,
                },
                "cryosphere": {
                    "sea_ice_concentration_fraction": self.sic,
                    "sea_ice_percentage": round(self.sic * 100.0, 1) if self.sic is not None else None,
                    "sea_ice_uncertainty_fraction": self.sic_uncertainty,
                },
                "bathymetry": {
                    "depth_m": self.bathymetry_depth,
                    "draft_m": self.draft,
                    "clearance_m": self.clearance,
                    "status": self.clearance_status,
                },
            },
            "fuel_and_endurance": {
                "fuel_rate_mt_h": self.fuel_rate,
                "fuel_used_mt": self.fuel_used,
                "fuel_used_m3": self.fuel_used_m3,
                "cumulative_fuel_mt": self.cumulative_fuel_mt,
                "bunker_margin_pct": self.fuel_capacity_margin_pct,
                "bunker_exceeded": self.fuel_capacity_exceeded,
                "travel_time_hours": self.travel_time_hours,
                "cumulative_time_hours": self.cumulative_time_hours,
                "endurance_margin_days": self.endurance_margin_days,
                "endurance_exceeded": self.endurance_exceeded,
            },
            "feasibility": {
                "is_feasible": self.feasible,
                "reason": self.reason,
                "warnings": self.warnings,
            },
            "model_version": self.model_version,
        }


def _extract_lat_lon(state: Any) -> Tuple[float, float]:
    """Extracts (latitude, longitude) from coordinates, GeoPoint, cell, dict, or H3 index."""
    if isinstance(state, (tuple, list)) and len(state) >= 2:
        return float(state[0]), float(state[1])
    if isinstance(state, str):
        # Could be an H3 cell index string (e.g. '85ad049bfffffff')
        try:
            from data_ingestion.h3.geometry import H3GeometryEngine
            engine = H3GeometryEngine()
            return engine.cell_to_latlng(state)
        except Exception:
            try:
                import h3
                return h3.cell_to_latlng(state)
            except Exception as e:
                raise ValueError(f"Cannot resolve H3 index string '{state}' to coordinates: {e}")
    if isinstance(state, dict):
        lat = state.get("centroid_lat", state.get("latitude", state.get("lat")))
        lon = state.get("centroid_lon", state.get("longitude", state.get("lon")))
        if lat is not None and lon is not None:
            return float(lat), float(lon)
    lat = getattr(state, "centroid_lat", getattr(state, "latitude", None))
    lon = getattr(state, "centroid_lon", getattr(state, "longitude", None))
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    raise ValueError(f"Cannot extract latitude/longitude from state: {state}")


class VesselPerformanceEvaluator:
    """
    Evaluator computing hydrodynamic, meteorological, and cryospheric vessel performance.
    """

    def __init__(self, vessel: Optional[VesselProfile] = None):
        self.vessel = vessel
        self.fuel_model = FuelConsumptionModel(vessel=vessel)
        self.constraint_checker = VesselConstraintChecker(vessel=vessel)

    @staticmethod
    def calculate_great_circle(
        lat1: float, lon1: float, lat2: float, lon2: float
    ) -> Tuple[float, float]:
        """
        Computes great-circle distance (meters) and initial forward bearing (degrees).
        """
        r_earth = 6371000.0  # Mean spherical Earth radius in meters

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        # Haversine distance
        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
        distance_m = r_earth * c

        # Forward azimuth / heading angle
        y = math.sin(delta_lambda) * math.cos(phi2)
        x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
        bearing_rad = math.atan2(y, x)
        bearing_deg = (math.degrees(bearing_rad) + 360.0) % 360.0

        return distance_m, bearing_deg

    def evaluate_transition(
        self,
        vessel: VesselProfile,
        state_a: Any,
        state_b: Any,
        environment: Any,
        departure_time: datetime,
        requested_speed_knots: Optional[float] = None,
        previous_cumulative_fuel_mt: float = 0.0,
        previous_cumulative_time_hours: float = 0.0,
    ) -> EdgeEvaluation:
        """
        Evaluates a candidate transition from state_a to state_b against the environmental state.
        Accepts cells as objects (StaticH3Cell, UnifiedEnvironmentCell, EnvironmentCell, or dict).
        """
        v = vessel or self.vessel
        if v is None:
            raise ValueError("VesselProfile required for transition evaluation.")

        # 1. Extract Coordinates
        lat_a, lon_a = _extract_lat_lon(state_a)
        lat_b, lon_b = _extract_lat_lon(state_b)

        dist_m, heading_deg = self.calculate_great_circle(lat_a, lon_a, lat_b, lon_b)
        dist_nm = dist_m / METERS_PER_NAUTICAL_MILE

        # Heading unit vector [East, North]
        hdg_rad = math.radians(heading_deg)
        u_hdg = math.sin(hdg_rad)
        v_hdg = math.cos(hdg_rad)

        # 2. Extract Environmental Parameters
        # Cleans out float NaNs so missing variables fallback to None
        def _get(field_name: str, alt_names: List[str] = [], default=None):
            def _clean(val):
                if val is None:
                    return None
                if isinstance(val, float) and math.isnan(val):
                    return None
                return val

            val = _clean(getattr(environment, field_name, None))
            if val is not None:
                return val
            if isinstance(environment, dict):
                val = _clean(environment.get(field_name))
                if val is not None:
                    return val
            for alt in alt_names:
                val = _clean(getattr(environment, alt, None))
                if val is not None:
                    return val
                if isinstance(environment, dict):
                    val = _clean(environment.get(alt))
                    if val is not None:
                        return val
            return default

        curr_u = _get("current_u_ms", ["current_u"])
        curr_v = _get("current_v_ms", ["current_v"])
        wind_u = _get("wind_u_ms", ["wind_u"])
        wind_v = _get("wind_v_ms", ["wind_v"])
        wind_spd = _get("wind_speed_ms", ["wind_speed"])
        if wind_spd is None and wind_u is not None and wind_v is not None:
            wind_spd = math.hypot(wind_u, wind_v)

        wave_h = _get("wave_height_m", ["wave_height", "VHM0"])
        wave_dir = _get("wave_direction_deg", ["wave_direction", "VMDR"])
        wave_tp = _get("wave_period_s", ["wave_period", "VTPK"])

        raw_sic = _get("sea_ice_concentration", ["sic", "SIC"])
        sic_fraction: Optional[float] = None
        if raw_sic is not None:
            sic_fraction = raw_sic / 100.0 if raw_sic > 1.0 else raw_sic

        raw_sic_unc = _get("sea_ice_uncertainty", ["sic_uncertainty", "SIC_uncertainty"])
        sic_unc_fraction: Optional[float] = None
        if raw_sic_unc is not None:
            sic_unc_fraction = raw_sic_unc / 100.0 if raw_sic_unc > 1.0 else raw_sic_unc

        water_depth = _get("bathymetry_depth_m", ["bathymetry_depth", "bathymetry_mean_m", "depth"])
        geo_status = str(_get("geographic_status", ["status"], default="OPEN_OCEAN"))
        is_land_flag = bool(_get("is_land", default=False))
        is_shelf_flag = bool(_get("is_ice_shelf", default=False))
        scar_blocked = bool(_get("is_blocked", ["is_scar_blocked"], default=False)) or is_land_flag or is_shelf_flag

        if is_land_flag and geo_status == "OPEN_OCEAN":
            geo_status = "LAND"
        elif is_shelf_flag and geo_status == "OPEN_OCEAN":
            geo_status = "ICE_SHELF"

        iceberg_hz = float(_get("iceberg_hazard", ["hazard"], default=0.0))

        # 3. Determine Speeds: Requested -> Achievable -> Ground
        req_spd = requested_speed_knots or v.cruising_speed_knots
        nom_spd = min(v.max_speed_knots, max(v.min_speed_knots, req_spd))

        # --- A. Wave Resistance & Penalty ---
        wave_enc_deg: Optional[float] = None
        f_wave = 1.0
        wave_res_factor = 0.0
        if wave_h is not None and wave_h > 0.5:
            # Encounter angle: difference between heading and wave direction
            if wave_dir is not None:
                wave_enc_deg = abs(heading_deg - wave_dir) % 360.0
                if wave_enc_deg > 180.0:
                    wave_enc_deg = 360.0 - wave_enc_deg
                # Head seas enc ~ 0 deg -> C_enc = 1.0; Following seas ~ 180 -> 0.0
                c_enc = 0.5 * (1.0 + math.cos(math.radians(wave_enc_deg)))
            else:
                c_enc = 0.5
                wave_enc_deg = 90.0

            h_ratio = wave_h / 2.5
            wave_loss = 0.08 * (h_ratio ** 2) * (0.4 + 0.6 * c_enc)
            f_wave = max(0.35, 1.0 - wave_loss)
            wave_res_factor = 0.12 * (h_ratio ** 2) * (0.4 + 0.6 * c_enc)

        # --- B. Wind Aerodynamic Resistance ---
        f_wind = 1.0
        wind_res_factor = 0.0
        rel_wind_spd: Optional[float] = None
        rel_wind_deg: Optional[float] = None

        nom_spd_ms = nom_spd * MS_PER_KNOT
        v_vessel_w = [nom_spd_ms * u_hdg, nom_spd_ms * v_hdg]

        if wind_u is not None and wind_v is not None:
            # Apparent relative wind vector: V_rel_air = V_wind - V_vessel
            u_rel = wind_u - v_vessel_w[0]
            v_rel = wind_v - v_vessel_w[1]
            rel_wind_spd = round(math.hypot(u_rel, v_rel), 2)
            rel_wind_dir = (math.degrees(math.atan2(u_rel, v_rel)) + 360.0) % 360.0
            rel_wind_deg = round(abs(heading_deg - rel_wind_dir) % 360.0, 1)

            # Headwind component (opposing heading)
            w_head = -(u_rel * u_hdg + v_rel * v_hdg)
            if w_head > 0.0:
                head_ratio = w_head / 10.0
                wind_loss = 0.03 * (head_ratio ** 1.5)
                f_wind = max(0.70, 1.0 - wind_loss)
                wind_res_factor = 0.05 * (head_ratio ** 1.5)

        # --- C. Sea Ice Resistance ---
        f_ice = 1.0
        ice_res_factor = 0.0
        if sic_fraction is not None and sic_fraction > 0.0:
            max_sic = v.max_navigable_sic
            if sic_fraction <= max_sic:
                sic_ratio = sic_fraction / max(0.01, max_sic)
                f_ice = max(0.20, 1.0 - 0.65 * (sic_ratio ** 2))
                ice_res_factor = 0.80 * (sic_ratio ** 2)
            else:
                f_ice = 0.05  # Severe degradation if exceeding limit
                ice_res_factor = 2.0

        # Achievable through-water speed
        achievable_spd_kn = nom_spd * f_wave * f_wind * f_ice
        achievable_spd_kn = max(1.5, achievable_spd_kn)  # Steerage minimum

        # --- D. 2D Vector Ocean Current Addition ---
        achievable_ms = achievable_spd_kn * MS_PER_KNOT
        v_vessel_e = achievable_ms * u_hdg
        v_vessel_n = achievable_ms * v_hdg

        c_u = curr_u if curr_u is not None else 0.0
        c_v = curr_v if curr_v is not None else 0.0

        # Ground velocity vector: V_ground = V_vessel + V_current
        v_ground_e = v_vessel_e + c_u
        v_ground_n = v_vessel_n + c_v

        ground_spd_ms = math.hypot(v_ground_e, v_ground_n)
        ground_spd_kn = ground_spd_ms / MS_PER_KNOT
        ground_dir_deg = (math.degrees(math.atan2(v_ground_e, v_ground_n)) + 360.0) % 360.0

        # Along-track speed (projection on heading)
        along_track_ms = v_ground_e * u_hdg + v_ground_n * v_hdg
        along_track_kn = along_track_ms / MS_PER_KNOT
        current_assist_kn = (c_u * u_hdg + c_v * v_hdg) / MS_PER_KNOT

        current_spd_kn = (math.hypot(c_u, c_v) / MS_PER_KNOT) if (curr_u is not None and curr_v is not None) else None

        # 4. Travel Time Calculation
        # Along-track speed governs forward progression across the segment
        effective_progression_ms = max(0.1, along_track_ms)
        travel_time_h = dist_m / (effective_progression_ms * 3600.0)

        # 5. Fuel Consumption
        fuel_res = self.fuel_model.evaluate_transit_fuel(
            achievable_speed_knots=achievable_spd_kn,
            transit_duration_hours=travel_time_h,
            vessel=v,
            wave_resistance_factor=wave_res_factor,
            wind_resistance_factor=wind_res_factor,
            ice_resistance_factor=ice_res_factor,
            requested_speed_knots=req_spd,
        )

        # 6. Constraint Evaluation
        c_res: ConstraintResult = self.constraint_checker.evaluate(
            vessel=v,
            geographic_status=geo_status,
            is_blocked_scar=scar_blocked,
            water_depth_m=water_depth,
            sea_ice_concentration=raw_sic,
            wave_height_m=wave_h,
            wind_speed_ms=wind_spd,
            iceberg_hazard=iceberg_hz,
            ground_speed_knots=along_track_kn,
        )

        # 7. Time and Cumulative Fuel / Endurance Propagation
        dep_dt = departure_time if departure_time.tzinfo else departure_time.replace(tzinfo=timezone.utc)
        arr_dt = dep_dt + timedelta(hours=travel_time_h)

        cum_fuel = round(previous_cumulative_fuel_mt + fuel_res["fuel_used_mt"], 4)
        cum_fuel_m3 = round(cum_fuel / 0.850, 4)
        max_bunker_m3 = v.fuel_capacity_m3
        fuel_margin_pct = max(0.0, ((max_bunker_m3 - cum_fuel_m3) / max_bunker_m3) * 100.0)
        fuel_exceeded = cum_fuel_m3 > max_bunker_m3

        cum_time_h = round(previous_cumulative_time_hours + travel_time_h, 3)
        cum_time_days = cum_time_h / 24.0
        endurance_d = v.endurance_days
        endurance_margin_d = round(endurance_d - cum_time_days, 2)
        endurance_exceeded = cum_time_days > endurance_d

        warnings = list(c_res.soft_warnings)
        if fuel_exceeded:
            warnings.append(f"Cumulative bunker capacity exceeded: {cum_fuel_m3:.1f} m3 > {max_bunker_m3:.1f} m3")
        if endurance_exceeded:
            warnings.append(f"Cumulative endurance exceeded: {cum_time_days:.1f} days > {endurance_d} days")

        primary_reason = c_res.hard_violations[0] if c_res.hard_violations else None

        # Record cell ID context if present in environment or state_b
        cell_id_ctx = getattr(state_b, "cell_id", None) or _get("cell_id")
        constraint_dict = c_res.model_dump()
        if cell_id_ctx:
            constraint_dict["cell_id"] = str(cell_id_ctx)

        return EdgeEvaluation(
            feasible=c_res.is_feasible,
            reason=primary_reason,
            warnings=warnings,
            heading=round(heading_deg, 2),
            distance_m=round(dist_m, 1),
            distance_nm=round(dist_nm, 2),
            requested_speed_kn=round(req_spd, 2),
            achievable_speed_kn=round(achievable_spd_kn, 2),
            ground_speed_kn=round(ground_spd_kn, 2),
            ground_direction_deg=round(ground_dir_deg, 2),
            along_track_speed_kn=round(along_track_kn, 2),
            current_u=curr_u,
            current_v=curr_v,
            current_speed_kn=round(current_spd_kn, 2) if current_spd_kn is not None else None,
            current_assistance_kn=round(current_assist_kn, 2),
            wind_u=wind_u,
            wind_v=wind_v,
            wind_speed_ms=round(wind_spd, 2) if wind_spd is not None else None,
            relative_wind_speed_ms=rel_wind_spd,
            relative_wind_direction_deg=rel_wind_deg,
            wave_height=round(wave_h, 2) if wave_h is not None else None,
            wave_direction=round(wave_dir, 1) if wave_dir is not None else None,
            wave_period=round(wave_tp, 1) if wave_tp is not None else None,
            wave_encounter_deg=round(wave_enc_deg, 1) if wave_enc_deg is not None else None,
            sic=round(sic_fraction, 3) if sic_fraction is not None else None,
            sic_uncertainty=round(sic_unc_fraction, 3) if sic_unc_fraction is not None else None,
            bathymetry_depth=round(water_depth, 1) if water_depth is not None else None,
            draft=v.draft_m,
            clearance=c_res.under_keel_clearance_m,
            clearance_status=c_res.clearance_status,
            travel_time_hours=round(travel_time_h, 3),
            departure_time=dep_dt.isoformat(),
            arrival_time=arr_dt.isoformat(),
            fuel_rate=fuel_res["fuel_rate_mt_per_hour"],
            fuel_used=fuel_res["fuel_used_mt"],
            fuel_used_m3=fuel_res["fuel_used_m3"],
            cumulative_fuel_mt=cum_fuel,
            fuel_capacity_margin_pct=round(fuel_margin_pct, 1),
            fuel_capacity_exceeded=fuel_exceeded,
            cumulative_time_hours=cum_time_h,
            endurance_margin_days=endurance_margin_d,
            endurance_exceeded=endurance_exceeded,
            constraint_state=constraint_dict,
        )


def evaluate_transition(
    vessel: VesselProfile,
    state_a: Any,
    state_b: Any,
    environment: Any,
    departure_time: datetime,
    requested_speed_knots: Optional[float] = None,
    previous_cumulative_fuel_mt: float = 0.0,
    previous_cumulative_time_hours: float = 0.0,
) -> EdgeEvaluation:
    """
    Standard procedural interface for transition evaluation.
    """
    evaluator = VesselPerformanceEvaluator(vessel=vessel)
    return evaluator.evaluate_transition(
        vessel=vessel,
        state_a=state_a,
        state_b=state_b,
        environment=environment,
        departure_time=departure_time,
        requested_speed_knots=requested_speed_knots,
        previous_cumulative_fuel_mt=previous_cumulative_fuel_mt,
        previous_cumulative_time_hours=previous_cumulative_time_hours,
    )


def evaluate_route_transitions(
    vessel: VesselProfile,
    waypoints_or_cells: List[Any],
    environment_provider: Any,
    departure_time: datetime,
    requested_speed_knots: Optional[float] = None,
) -> List[EdgeEvaluation]:
    """
    Sequentially evaluates a route trajectory with time evolution:
    t_arrival = t_departure + travel_time.
    The next cell transition queries the environment at the arrival timestamp.
    """
    if len(waypoints_or_cells) < 2:
        raise ValueError("At least two waypoints/cells are required to evaluate route transitions.")

    evaluator = VesselPerformanceEvaluator(vessel=vessel)
    evaluations: List[EdgeEvaluation] = []
    current_time = departure_time
    cum_fuel = 0.0
    cum_time = 0.0

    for i in range(len(waypoints_or_cells) - 1):
        st_a = waypoints_or_cells[i]
        st_b = waypoints_or_cells[i + 1]

        # Determine target cell index or coordinate to query environment
        if hasattr(environment_provider, "get_environment"):
            cell_id_b = getattr(st_b, "cell_id", str(st_b) if isinstance(st_b, str) else None)
            if cell_id_b:
                env_state = environment_provider.get_environment(cell_id_b, current_time)
            else:
                lat_b, lon_b = _extract_lat_lon(st_b)
                from domain.coordinates import GeoPoint
                env_state = environment_provider.get_point_environment(GeoPoint(latitude=lat_b, longitude=lon_b), current_time)
        elif callable(environment_provider):
            env_state = environment_provider(st_b, current_time)
        elif isinstance(environment_provider, list) and i < len(environment_provider):
            env_state = environment_provider[i]
        else:
            env_state = environment_provider

        edge_eval = evaluator.evaluate_transition(
            vessel=vessel,
            state_a=st_a,
            state_b=st_b,
            environment=env_state,
            departure_time=current_time,
            requested_speed_knots=requested_speed_knots,
            previous_cumulative_fuel_mt=cum_fuel,
            previous_cumulative_time_hours=cum_time,
        )

        evaluations.append(edge_eval)

        # Evolve time for the subsequent transition
        current_time = datetime.fromisoformat(edge_eval.arrival_time)
        cum_fuel = edge_eval.cumulative_fuel_mt or (cum_fuel + edge_eval.fuel_used)
        cum_time = edge_eval.cumulative_time_hours or (cum_time + edge_eval.travel_time_hours)

    return evaluations

