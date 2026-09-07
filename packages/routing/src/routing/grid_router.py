"""
AMIP Discrete 4D Grid Router.
A* pathfinding over discrete environmental grid cells.
State: (cell_id, time_bucket). Parent pointers for O(states) memory vs old O(paths×length).
"""

from __future__ import annotations

import heapq
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from domain.coordinates import GeoPoint, BoundingBox
from domain.vessel import VesselProfile
from domain.enums import RouteObjective
from domain.mission import AvoidanceZone
from domain.route import RouteAlternative, RouteWaypoint, RouteMetrics
from data_access.spatial import haversine_distance_nm
from data_access.environment_provider import default_environment_provider, EnvironmentalDataProviderInterface
from routing.speed_model import VesselSpeedModel
from routing.fuel_model import NavalArchitectureFuelModel
from routing.grid_graph import EnvironmentalGridGraph, H3EnvironmentalGridGraph
from risk_engine.engine import RiskEngine
from risk_engine.models import RiskProfile, RouteRiskProfile
from risk_engine.route import aggregate_route_risk
from vessel.evaluator import VesselPerformanceEvaluator

# Type alias for a 4D state
State = Tuple[str, int]  # (cell_id, time_bucket)


class AMIPGridRouter:
    """
    Discrete 4D environmental grid router over canonical H3 cells and environmental grids.
    Uses A* with (cell_id, time_bucket) states and parent-pointer path reconstruction.
    Each routing objective has genuinely different edge costs rooted in physical trade-offs.
    """

    def __init__(
        self,
        env_provider: Optional[EnvironmentalDataProviderInterface] = None,
        speed_model: Optional[VesselSpeedModel] = None,
        fuel_model: Optional[NavalArchitectureFuelModel] = None,
        risk_engine: Optional[RiskEngine] = None,
        vessel_evaluator: Optional[VesselPerformanceEvaluator] = None,
        resolution_deg: Optional[float] = None,
        graph_type: Optional[str] = None,
        h3_resolution: int = 5,
        time_bucket_hours: float = 12.0,
        max_expansions: int = 6000,
    ):
        self.env = env_provider or default_environment_provider
        self.speed_model = speed_model or VesselSpeedModel()
        self.fuel_model = fuel_model or NavalArchitectureFuelModel()
        self.risk_engine = risk_engine or RiskEngine()
        self.vessel_evaluator = vessel_evaluator or VesselPerformanceEvaluator()

        # Backward compatibility: if resolution_deg explicitly provided without graph_type, default to "deg"
        if graph_type is not None:
            self.graph_type = graph_type
        elif resolution_deg is not None:
            self.graph_type = "deg"
        else:
            self.graph_type = "h3"

        self.resolution_deg = resolution_deg or 1.0
        self.h3_resolution = h3_resolution
        self.time_bucket_hours = time_bucket_hours
        self.max_expansions = max_expansions

    def _time_bucket(self, t: datetime, t0: datetime) -> int:
        """Discretize elapsed time into a bucket index."""
        diff = (t - t0).total_seconds() / 3600.0
        return max(0, int(diff // self.time_bucket_hours))

    def _edge_cost(
        self,
        objective: RouteObjective,
        dist_nm: float,
        dt_hours: float,
        leg_fuel: float,
        sic: float,
        wave_h: float,
        risk_profile: Optional[RiskProfile] = None,
        iceberg_hazard: float = 0.0,
    ) -> float:
        """
        Objective-specific edge cost rooted in physical trade-offs.

        SHORTEST  → pure nautical miles; cuts directly.
        FASTEST   → pure travel time; avoids ice because ice reduces vessel speed.
        SAFEST    → distance heavily penalised by composite risk, sea ice, wave exposure,
                    and iceberg occupancy hazard.
        FUEL      → actual fuel tonnes from naval architecture model.
        BALANCED  → normalised multi-criteria compromise of time, fuel, risk, and distance.
        """
        if objective == RouteObjective.SHORTEST:
            return dist_nm

        elif objective == RouteObjective.FASTEST:
            return dt_hours

        elif objective == RouteObjective.SAFEST:
            comp_risk = (
                risk_profile.composite_risk
                if risk_profile
                else min(0.95, 0.55 * sic + 0.25 * max(0.0, (wave_h - 2.0) / 6.0) + 0.05)
            )
            ice_penalty = 15.0 * (sic ** 1.5)
            wave_penalty = 3.0 * max(0.0, (wave_h - 3.0) / 4.0)
            iceberg_penalty = 10.0 * (iceberg_hazard ** 1.5)
            comp_penalty = 20.0 * (comp_risk ** 1.5)
            return dist_nm * (1.0 + ice_penalty + wave_penalty + iceberg_penalty + comp_penalty)

        elif objective == RouteObjective.FUEL_EFFICIENT:
            return leg_fuel

        else:  # BALANCED
            t_norm = dt_hours / 24.0
            f_norm = leg_fuel / 20.0
            comp_risk = risk_profile.composite_risk if risk_profile else sic
            risk_nm = comp_risk * dist_nm / 30.0
            dist_term = dist_nm / 100.0
            return 0.35 * t_norm + 0.35 * f_norm + 0.20 * risk_nm + 0.10 * dist_term

    def _heuristic(
        self,
        curr_pt: GeoPoint,
        dest_pt: GeoPoint,
        objective: RouteObjective,
        v_max: float,
        min_fuel_per_nm: float,
    ) -> float:
        """
        Admissible A* lower-bound heuristic in the same units as edge cost.
        """
        dist = haversine_distance_nm(
            curr_pt.latitude, curr_pt.longitude,
            dest_pt.latitude, dest_pt.longitude,
        )
        if objective == RouteObjective.SHORTEST:
            return dist
        elif objective == RouteObjective.FASTEST:
            return dist / max(1.0, v_max)
        elif objective == RouteObjective.SAFEST:
            return dist
        elif objective == RouteObjective.FUEL_EFFICIENT:
            return dist * min_fuel_per_nm
        else:  # BALANCED
            return dist * 0.01

    def _target_speed(self, objective: RouteObjective, vessel: VesselProfile, v_max: float) -> float:
        if objective == RouteObjective.FASTEST:
            return v_max
        elif objective == RouteObjective.SAFEST:
            return vessel.service_speed_knots * 0.85
        elif objective == RouteObjective.FUEL_EFFICIENT:
            return vessel.service_speed_knots * 0.75
        return vessel.service_speed_knots

    def optimize_leg(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        departure_time: datetime,
        vessel: VesselProfile,
        objective: RouteObjective = RouteObjective.BALANCED,
        avoidance_zones: Optional[List[AvoidanceZone]] = None,
        grid_resolution_deg: Optional[float] = None,
        h3_resolution: Optional[int] = None,
        graph_type: Optional[str] = None,
    ) -> Optional[RouteAlternative]:
        """
        Run 4D A* over the discrete environmental grid / H3 grid.
        Returns None when search exceeds max_expansions or is blocked.
        """
        # Determine graph type and resolution
        active_graph_type = graph_type or self.graph_type
        if grid_resolution_deg is not None and graph_type is None:
            active_graph_type = "deg"

        res_deg = grid_resolution_deg or self.resolution_deg
        h3_res = h3_resolution or self.h3_resolution

        v_max = getattr(vessel, "max_speed_knots", vessel.service_speed_knots * 1.15)
        tgt_speed = self._target_speed(objective, vessel, v_max)

        # Pre-compute open-water minimum fuel per nm for heuristic
        min_fuel_per_nm = self.fuel_model.estimate_leg_fuel(
            vessel=vessel, distance_nm=1.0, speed_knots=v_max, sic=0.0, wave_height_m=1.0
        )

        # Build search domain bounding box
        margin = max(3.0, res_deg * 4.0 if active_graph_type == "deg" else (8 - h3_res) * 2.0)
        max_lat = min(-20.0, max(origin.latitude, destination.latitude) + margin)
        min_lat = max(-80.0, min(origin.latitude, destination.latitude) - margin)
        min_lon = min(origin.longitude, destination.longitude) - margin
        max_lon = max(origin.longitude, destination.longitude) + margin

        bounds = BoundingBox(
            min_latitude=round(min_lat, 2),
            max_latitude=round(max_lat, 2),
            min_longitude=round(min_lon, 2),
            max_longitude=round(max_lon, 2),
        )

        # Instantiate graph
        if active_graph_type == "h3":
            graph = H3EnvironmentalGridGraph(
                bounds=bounds,
                h3_resolution=h3_res,
                env_provider=self.env,
            )
        else:
            graph = EnvironmentalGridGraph(
                bounds=bounds,
                resolution_deg=res_deg,
                env_provider=self.env,
            )

        graph.apply_hard_constraints(vessel=vessel, avoidance_zones=avoidance_zones)

        start_id = graph.find_closest_node_id(origin, navigable_only=True)
        dest_id = graph.find_closest_node_id(destination, navigable_only=True)
        if not start_id or not dest_id:
            return None

        # A* with parent-pointer reconstruction
        h0 = self._heuristic(graph.nodes[start_id].point, graph.nodes[dest_id].point, objective, v_max, min_fuel_per_nm)
        queue: List[Tuple[float, float, str, datetime, int]] = [(h0, 0.0, start_id, departure_time, 0)]

        best_g: Dict[State, float] = {(start_id, 0): 0.0}
        came_from: Dict[State, Optional[State]] = {(start_id, 0): None}
        step_data: Dict[State, Dict[str, Any]] = {}

        expansions = 0
        dest_state: Optional[State] = None

        while queue and expansions < self.max_expansions:
            expansions += 1
            f, g, curr_id, curr_time, curr_bucket = heapq.heappop(queue)

            if curr_id == dest_id:
                dest_state = (curr_id, curr_bucket)
                break

            curr_state = (curr_id, curr_bucket)
            if g > best_g.get(curr_state, float("inf")):
                continue  # stale entry

            for nbr_id, dist_nm, heading_deg in graph.get_neighbors(curr_id):
                nbr_node = graph.nodes[nbr_id]
                env = self.env.get_point_environment(nbr_node.point, curr_time)

                sic = float(env.get("sea_ice_concentration", 0.0))
                wave_h = float(env.get("wave_height_m", 1.0))
                wind_spd = float(env.get("wind_speed_ms", 5.0))
                curr_u = float(env.get("current_u_ms", 0.0))
                curr_v = float(env.get("current_v_ms", 0.0))
                depth_m = float(env.get("bathymetry_depth_m", getattr(nbr_node, "depth_m", 3000.0)))
                iceberg_hz = float(env.get("iceberg_hazard", 0.0))
                distinct_icebergs = int(env.get("distinct_iceberg_count", 0))

                # Dynamic RiskEngine evaluation: hard constraint pruning (strictly enforced on H3)
                cell_risk: Optional[RiskProfile] = None
                if self.risk_engine is not None:
                    risk_input = {
                        "cell_id": nbr_id,
                        "valid_time": curr_time,
                        "geographic_status": "LAND" if getattr(nbr_node, "land_mask", False) else "OPEN_OCEAN",
                        "is_land": getattr(nbr_node, "land_mask", False),
                        "is_ice_shelf": False,
                        "bathymetry_depth_m": depth_m,
                        "sea_ice_concentration": sic,
                        "wave_height_m": wave_h,
                        "wind_speed_ms": wind_spd,
                        "current_u_ms": curr_u,
                        "current_v_ms": curr_v,
                        "iceberg_hazard": iceberg_hz,
                        "distinct_iceberg_count": distinct_icebergs,
                    }
                    cell_risk = self.risk_engine.evaluate_cell_risk(
                        cell=risk_input,
                        vessel=vessel,
                        timestamp=curr_time,
                        heading_deg=heading_deg,
                    )
                    if active_graph_type == "h3" and cell_risk.hard_blocked:
                        continue

                # Speed evaluation incorporating 2D currents & wave/ice degradation
                speed_res = self.speed_model.calculate_segment_speed(
                    vessel=vessel,
                    distance_nm=dist_nm,
                    heading_deg=heading_deg,
                    sic=sic,
                    wave_height_m=wave_h,
                    wind_speed_ms=wind_spd,
                    current_u_ms=curr_u,
                    current_v_ms=curr_v,
                    desired_speed_knots=tgt_speed,
                )

                if active_graph_type == "h3" and not speed_res.is_passable:
                    continue

                v_eff = speed_res.effective_speed_knots if speed_res.is_passable else 1.5
                dt_h = dist_nm / max(0.5, v_eff)
                next_time = curr_time + timedelta(hours=dt_h)
                next_bucket = self._time_bucket(next_time, departure_time)

                # Fuel evaluation
                leg_fuel = self.fuel_model.estimate_leg_fuel(
                    vessel=vessel,
                    distance_nm=dist_nm,
                    speed_knots=v_eff,
                    sic=sic,
                    wave_height_m=wave_h,
                )

                local_risk = (
                    cell_risk.composite_risk
                    if cell_risk
                    else min(0.95, 0.55 * sic + 0.25 * max(0.0, (wave_h - 2.0) / 6.0) + 0.05)
                )

                edge = self._edge_cost(
                    objective=objective,
                    dist_nm=dist_nm,
                    dt_hours=dt_h,
                    leg_fuel=leg_fuel,
                    sic=sic,
                    wave_h=wave_h,
                    risk_profile=cell_risk,
                    iceberg_hazard=iceberg_hz,
                )
                new_g = g + edge
                nbr_state: State = (nbr_id, next_bucket)

                if new_g < best_g.get(nbr_state, float("inf")):
                    best_g[nbr_state] = new_g
                    came_from[nbr_state] = curr_state
                    step_data[nbr_state] = {
                        "cell_id": nbr_id,
                        "point": nbr_node.point,
                        "eta": next_time,
                        "leg_dist_nm": dist_nm,
                        "speed_knots": v_eff,
                        "base_speed_knots": speed_res.base_speed_knots,
                        "current_boost_knots": speed_res.current_boost_knots,
                        "dt_hours": dt_h,
                        "leg_fuel_tonnes": leg_fuel,
                        "local_risk": local_risk,
                        "risk_profile": cell_risk,
                        "sic": sic,
                        "bathymetry_depth_m": depth_m,
                        "current_u_ms": curr_u,
                        "current_v_ms": curr_v,
                        "wind_speed_ms": wind_spd,
                        "wave_height_m": wave_h,
                        "iceberg_hazard": iceberg_hz,
                        "heading_deg": heading_deg,
                        "limiting_factor": speed_res.limiting_factor,
                    }
                    h = self._heuristic(nbr_node.point, graph.nodes[dest_id].point, objective, v_max, min_fuel_per_nm)
                    heapq.heappush(queue, (new_g + h, new_g, nbr_id, next_time, next_bucket))

        if dest_state is None:
            return None

        # Reconstruct path via parent pointers
        states: List[State] = []
        cur = dest_state
        while cur is not None:
            states.append(cur)
            cur = came_from.get(cur)
        states.reverse()

        # Build waypoints, ordered H3 cells, and segment-level diagnostics
        waypoints: List[RouteWaypoint] = []
        segments: List[Dict[str, Any]] = []
        ordered_cells: List[str] = [s[0] for s in states]
        risk_profiles: List[RiskProfile] = []
        segment_durations: List[float] = []

        cum_dist = 0.0
        cum_fuel = 0.0
        risk_vals: List[float] = []
        ice_nms: List[float] = []
        iceberg_hazards: List[float] = []

        for seq, state in enumerate(states):
            if seq == 0:
                sn = graph.nodes[start_id]
                e0 = self.env.get_point_environment(sn.point, departure_time)
                sic_0 = float(e0.get("sea_ice_concentration", 0.0))
                depth_0 = float(e0.get("bathymetry_depth_m", getattr(sn, "depth_m", 3000.0)))
                hz_0 = float(e0.get("iceberg_hazard", 0.0))

                start_risk = None
                if self.risk_engine:
                    start_risk = self.risk_engine.evaluate_cell_risk(
                        cell={
                            "cell_id": start_id,
                            "valid_time": departure_time,
                            "bathymetry_depth_m": depth_0,
                            "sea_ice_concentration": sic_0,
                            "wave_height_m": float(e0.get("wave_height_m", 1.0)),
                            "wind_speed_ms": float(e0.get("wind_speed_ms", 5.0)),
                            "current_u_ms": float(e0.get("current_u_ms", 0.0)),
                            "current_v_ms": float(e0.get("current_v_ms", 0.0)),
                            "iceberg_hazard": hz_0,
                        },
                        vessel=vessel,
                        timestamp=departure_time,
                    )
                    risk_profiles.append(start_risk)

                start_risk_val = start_risk.composite_risk if start_risk else 0.05

                waypoints.append(RouteWaypoint(
                    sequence=0,
                    point=sn.point,
                    grid_cell_id=start_id,
                    eta=departure_time,
                    speed_knots=round(tgt_speed, 1),
                    leg_distance_nm=0.0,
                    cumulative_distance_nm=0.0,
                    leg_fuel_tonnes=0.0,
                    cumulative_fuel_tonnes=0.0,
                    local_risk=round(start_risk_val, 3),
                    ice_concentration=round(sic_0, 3),
                    bathymetry_depth_m=round(depth_0, 1),
                    current_u_ms=round(float(e0.get("current_u_ms", 0.0)), 3),
                    current_v_ms=round(float(e0.get("current_v_ms", 0.0)), 3),
                    wind_speed_ms=round(float(e0.get("wind_speed_ms", 5.0)), 2),
                    wave_height_m=round(float(e0.get("wave_height_m", 1.0)), 2),
                    fuel_rate_tonnes_per_day=0.0,
                ))
                risk_vals.append(start_risk_val)
                iceberg_hazards.append(hz_0)
                continue

            sd = step_data.get(state)
            if sd is None:
                continue

            leg_dist = sd["leg_dist_nm"]
            f_t = sd["leg_fuel_tonnes"]
            spd = sd["speed_knots"]
            risk = sd["local_risk"]
            sic_v = sd["sic"]
            dt_h = sd["dt_hours"]
            hz = sd["iceberg_hazard"]

            cum_dist += leg_dist
            cum_fuel += f_t
            risk_vals.append(risk)
            iceberg_hazards.append(hz)
            segment_durations.append(dt_h)
            if sic_v > 0.15:
                ice_nms.append(leg_dist)

            if sd.get("risk_profile"):
                risk_profiles.append(sd["risk_profile"])

            fuel_rate = (f_t / max(0.001, dt_h)) * 24.0

            waypoints.append(RouteWaypoint(
                sequence=seq,
                point=sd["point"],
                grid_cell_id=sd["cell_id"],
                eta=sd["eta"],
                speed_knots=round(spd, 1),
                leg_distance_nm=round(leg_dist, 1),
                cumulative_distance_nm=round(cum_dist, 1),
                leg_fuel_tonnes=round(f_t, 2),
                cumulative_fuel_tonnes=round(cum_fuel, 2),
                local_risk=round(risk, 3),
                ice_concentration=round(sic_v, 3),
                bathymetry_depth_m=round(sd["bathymetry_depth_m"], 1),
                current_u_ms=round(sd["current_u_ms"], 3),
                current_v_ms=round(sd["current_v_ms"], 3),
                wind_speed_ms=round(sd["wind_speed_ms"], 2),
                wave_height_m=round(sd["wave_height_m"], 2),
                fuel_rate_tonnes_per_day=round(fuel_rate, 2),
            ))

            # Segment diagnostics
            segments.append({
                "sequence": seq,
                "from_cell": states[seq - 1][0],
                "to_cell": sd["cell_id"],
                "distance_nm": round(leg_dist, 2),
                "heading_deg": round(sd["heading_deg"], 1),
                "speed_over_ground_knots": round(spd, 2),
                "base_speed_knots": round(sd["base_speed_knots"], 2),
                "current_boost_knots": round(sd["current_boost_knots"], 2),
                "transit_duration_hours": round(dt_h, 2),
                "fuel_tonnes": round(f_t, 3),
                "fuel_rate_tonnes_per_day": round(fuel_rate, 2),
                "composite_risk": round(risk, 3),
                "sea_ice_concentration": round(sic_v, 3),
                "iceberg_hazard": round(hz, 3),
                "wave_height_m": round(sd["wave_height_m"], 2),
                "wind_speed_ms": round(sd["wind_speed_ms"], 2),
                "bathymetry_depth_m": round(sd["bathymetry_depth_m"], 1),
                "limiting_factor": sd["limiting_factor"],
            })

        if not waypoints:
            return None

        total_h = (waypoints[-1].eta - departure_time).total_seconds() / 3600.0
        mean_risk = sum(risk_vals) / len(risk_vals) if risk_vals else 0.1
        max_risk = max(risk_vals) if risk_vals else 0.1
        ice_pct = (sum(ice_nms) / cum_dist * 100.0) if cum_dist > 0 else 0.0
        mean_iceberg_hz = sum(iceberg_hazards) / len(iceberg_hazards) if iceberg_hazards else 0.05

        # Compute RouteRiskProfile if risk profiles were collected
        route_risk_profile: Optional[RouteRiskProfile] = None
        if risk_profiles:
            try:
                route_risk_profile = aggregate_route_risk(
                    risk_profiles,
                    segment_durations_hours=[1.0] + segment_durations if len(risk_profiles) == len(segment_durations) + 1 else None,
                )
            except Exception:
                route_risk_profile = None

        metrics = RouteMetrics(
            distance_nm=round(cum_dist, 1),
            duration_hours=round(total_h, 1),
            duration_days=round(total_h / 24.0, 2),
            estimated_fuel_tonnes=round(cum_fuel, 1),
            mean_risk_score=round(route_risk_profile.mean_risk if route_risk_profile else mean_risk, 3),
            max_risk_score=round(route_risk_profile.max_risk if route_risk_profile else max_risk, 3),
            waypoint_risks=risk_vals,
            sea_ice_exposure_percent=round(ice_pct, 1),
            iceberg_hazard_exposure=round(mean_iceberg_hz, 3),
            constraint_violations=[],
            is_feasible=True,
        )

        labels = {
            RouteObjective.SHORTEST: "Shortest geographic path; direct geodesic trajectory.",
            RouteObjective.FASTEST: "Minimum transit time; minimizes slowing caused by sea ice and adverse currents.",
            RouteObjective.SAFEST: "Maximum safety margin; heavily penalises ice concentration, wave exposure, and iceberg hazards.",
            RouteObjective.FUEL_EFFICIENT: "Minimum fuel burn; leverages current vectors and economical transit RPM.",
            RouteObjective.BALANCED: "Multi-criteria compromise balancing travel time, fuel burn, and navigational safety.",
        }

        diagnostics = {
            "graph_type": active_graph_type,
            "h3_resolution": h3_res if active_graph_type == "h3" else None,
            "total_cells": len(ordered_cells),
            "total_expansions": expansions,
            "total_duration_hours": round(total_h, 2),
            "total_distance_nm": round(cum_dist, 2),
            "total_fuel_tonnes": round(cum_fuel, 2),
            "route_risk_profile": route_risk_profile.model_dump() if route_risk_profile else None,
            "mean_composite_risk": round(route_risk_profile.mean_risk, 3) if route_risk_profile else round(mean_risk, 3),
            "p95_composite_risk": round(route_risk_profile.p95_risk, 3) if route_risk_profile else round(max_risk, 3),
            "max_composite_risk": round(route_risk_profile.max_risk, 3) if route_risk_profile else round(max_risk, 3),
        }

        return RouteAlternative(
            route_id=f"route-{uuid4().hex[:8]}",
            objective=objective,
            departure_time=departure_time,
            metrics=metrics,
            waypoints=waypoints,
            cells=ordered_cells,
            segments=segments,
            diagnostics=diagnostics,
            explanation=labels.get(objective, "AMIP discrete grid optimised Antarctic route."),
            is_mock=False if active_graph_type == "h3" else True,
        )
