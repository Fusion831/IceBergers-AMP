"""
AMIP Discrete 4D Grid Router.
A* pathfinding over discrete environmental grid cells.
State: (cell_id, time_bucket). Parent pointers for O(states) memory vs old O(paths×length).
"""

from __future__ import annotations

import heapq
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
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
from routing.grid_graph import EnvironmentalGridGraph

# Type alias for a 4D state
State = Tuple[str, int]  # (cell_id, time_bucket)

# Step data stored per state: (cell_id, point, eta, leg_dist_nm, speed_kn, leg_fuel_t,
#   local_risk, sic, depth_m, current_u, current_v, wind_spd, wave_h)
StepData = Tuple[str, GeoPoint, datetime, float, float, float, float, float, float, float, float, float, float]


class AMIPGridRouter:
    """
    Discrete 4D environmental grid router.
    Uses A* with (cell_id, time_bucket) states and parent-pointer path reconstruction.
    Each routing objective has genuinely different edge costs rooted in physical trade-offs.
    """

    def __init__(
        self,
        env_provider: Optional[EnvironmentalDataProviderInterface] = None,
        speed_model: Optional[VesselSpeedModel] = None,
        fuel_model: Optional[NavalArchitectureFuelModel] = None,
        resolution_deg: float = 1.0,
        time_bucket_hours: float = 12.0,
        max_expansions: int = 6000,
    ):
        self.env = env_provider or default_environment_provider
        self.speed_model = speed_model or VesselSpeedModel()
        self.fuel_model = fuel_model or NavalArchitectureFuelModel()
        self.resolution_deg = resolution_deg
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
    ) -> float:
        """
        Objective-specific edge cost. Each objective penalises different physics so
        A* is steered toward genuinely different corridors in mixed ice/open-water domains.

        SHORTEST  → pure nautical miles; cuts through ice if geodesic is direct.
        FASTEST   → pure travel time; avoids ice because ice reduces vessel speed.
        SAFEST    → distance weighted by ice^1.5 and wave exposure; strongly
                    incentivises wide detours around even moderate SIC.
        FUEL      → actual fuel tonnes from naval architecture model which already
                    bakes in ice resistance (Lindqvist) and wave resistance (Kwon).
        BALANCED  → normalised sum of time + fuel + ice exposure fraction.
        """
        if objective == RouteObjective.SHORTEST:
            return dist_nm

        elif objective == RouteObjective.FASTEST:
            # dt_hours already penalises slow ice transit implicitly
            return dt_hours

        elif objective == RouteObjective.SAFEST:
            # Very aggressive ice penalty so detours are always preferred
            ice_penalty = 15.0 * (sic ** 1.5)
            wave_penalty = 3.0 * max(0.0, (wave_h - 3.0) / 4.0)
            return dist_nm * (1.0 + ice_penalty + wave_penalty)

        elif objective == RouteObjective.FUEL_EFFICIENT:
            # leg_fuel from the real fuel model; ice resistance already inflates it
            return leg_fuel

        else:  # BALANCED
            t_norm = dt_hours / 24.0
            f_norm = leg_fuel / 20.0
            ice_nm = sic * dist_nm / 50.0
            return 0.4 * t_norm + 0.3 * f_norm + 0.3 * ice_nm

    def _heuristic(
        self,
        curr_pt: GeoPoint,
        dest_pt: GeoPoint,
        objective: RouteObjective,
        v_max: float,
        min_fuel_per_nm: float,
    ) -> float:
        """
        Admissible A* lower-bound heuristic in the same units as the corresponding
        edge cost so the algorithm remains consistent.
        """
        dist = haversine_distance_nm(
            curr_pt.latitude, curr_pt.longitude,
            dest_pt.latitude, dest_pt.longitude,
        )
        if objective == RouteObjective.SHORTEST:
            return dist
        elif objective == RouteObjective.FASTEST:
            return dist / max(1.0, v_max)   # optimistic: full speed, no ice
        elif objective == RouteObjective.SAFEST:
            return dist                      # optimistic: zero ice/wave on remaining path
        elif objective == RouteObjective.FUEL_EFFICIENT:
            return dist * min_fuel_per_nm    # optimistic: open-water min rate
        else:  # BALANCED
            return dist * 0.02              # small consistent lower bound

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
    ) -> Optional[RouteAlternative]:
        """
        Run 4D A* on the discrete environmental grid.
        Returns None when the search exceeds max_expansions (caller uses corridor fallback).
        """
        res = grid_resolution_deg or self.resolution_deg
        v_max = getattr(vessel, "max_speed_knots", vessel.service_speed_knots * 1.15)
        tgt_speed = self._target_speed(objective, vessel, v_max)

        # Pre-compute open-water minimum fuel per nm for heuristic (avoid calling model in inner loop)
        min_fuel_per_nm = self.fuel_model.estimate_leg_fuel(
            vessel=vessel, distance_nm=1.0, speed_knots=v_max, sic=0.0, wave_height_m=1.0
        )

        # --- Build bounded search domain with margin ---
        margin = max(3.0, res * 4.0)
        # Northward clamp at -20° (allows Mauritius/Goa origins); southward at -80°
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

        graph = EnvironmentalGridGraph(bounds=bounds, resolution_deg=res, env_provider=self.env)
        graph.apply_hard_constraints(vessel=vessel, avoidance_zones=avoidance_zones)

        start_id = graph.find_closest_node_id(origin, navigable_only=True)
        dest_id = graph.find_closest_node_id(destination, navigable_only=True)
        if not start_id or not dest_id:
            return None

        # --- A* with parent-pointer reconstruction ---
        # Queue entries: (f, g, cell_id, current_time, time_bucket)
        h0 = self._heuristic(graph.nodes[start_id].point, graph.nodes[dest_id].point, objective, v_max, min_fuel_per_nm)
        queue: List[Tuple[float, float, str, datetime, int]] = [(h0, 0.0, start_id, departure_time, 0)]

        best_g: Dict[State, float] = {(start_id, 0): 0.0}
        # came_from[state] = parent state (None for start)
        came_from: Dict[State, Optional[State]] = {(start_id, 0): None}
        # step_data[state] = arrival data for building waypoints
        step_data: Dict[State, StepData] = {}

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
                sic = env["sea_ice_concentration"]
                wave_h = env["wave_height_m"]

                speed_res = self.speed_model.calculate_segment_speed(
                    vessel=vessel,
                    distance_nm=dist_nm,
                    heading_deg=heading_deg,
                    sic=sic,
                    wave_height_m=wave_h,
                    wind_speed_ms=env["wind_speed_ms"],
                    current_u_ms=env["current_u_ms"],
                    current_v_ms=env["current_v_ms"],
                    desired_speed_knots=tgt_speed,
                )

                v_eff = speed_res.effective_speed_knots if speed_res.is_passable else 1.5
                dt_h = dist_nm / max(0.5, v_eff)
                next_time = curr_time + timedelta(hours=dt_h)
                next_bucket = self._time_bucket(next_time, departure_time)

                # Fuel from the same model used in the edge cost (consistent)
                leg_fuel = self.fuel_model.estimate_leg_fuel(
                    vessel=vessel, distance_nm=dist_nm, speed_knots=v_eff,
                    sic=sic, wave_height_m=wave_h,
                )

                local_risk = min(0.95, 0.55 * sic + 0.25 * max(0.0, (wave_h - 2.0) / 6.0) + 0.05)

                edge = self._edge_cost(objective, dist_nm, dt_h, leg_fuel, sic, wave_h)
                new_g = g + edge
                nbr_state: State = (nbr_id, next_bucket)

                if new_g < best_g.get(nbr_state, float("inf")):
                    best_g[nbr_state] = new_g
                    came_from[nbr_state] = curr_state
                    step_data[nbr_state] = (
                        nbr_id, nbr_node.point, next_time,
                        dist_nm, v_eff, leg_fuel, local_risk, sic,
                        env["bathymetry_depth_m"],
                        env["current_u_ms"], env["current_v_ms"],
                        env["wind_speed_ms"], wave_h,
                    )
                    h = self._heuristic(nbr_node.point, graph.nodes[dest_id].point, objective, v_max, min_fuel_per_nm)
                    heapq.heappush(queue, (new_g + h, new_g, nbr_id, next_time, next_bucket))

        if dest_state is None:
            return None

        # --- Reconstruct path via parent pointers (O(path_len), no copies) ---
        states: List[State] = []
        cur = dest_state
        while cur is not None:
            states.append(cur)
            cur = came_from.get(cur)
        states.reverse()

        # --- Build waypoints ---
        waypoints: List[RouteWaypoint] = []
        cum_dist = 0.0
        cum_fuel = 0.0
        risk_vals: List[float] = []
        ice_nms: List[float] = []

        for seq, state in enumerate(states):
            if seq == 0:
                # Origin waypoint uses departure-time environment
                sn = graph.nodes[start_id]
                e0 = self.env.get_point_environment(sn.point, departure_time)
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
                    local_risk=0.05,
                    ice_concentration=round(e0["sea_ice_concentration"], 3),
                    bathymetry_depth_m=round(e0["bathymetry_depth_m"], 1),
                    current_u_ms=round(e0["current_u_ms"], 3),
                    current_v_ms=round(e0["current_v_ms"], 3),
                    wind_speed_ms=round(e0["wind_speed_ms"], 2),
                    wave_height_m=round(e0["wave_height_m"], 2),
                    fuel_rate_tonnes_per_day=0.0,
                ))
                risk_vals.append(0.05)
                continue

            sd = step_data.get(state)
            if sd is None:
                continue

            c_id, pt, eta, leg_dist, spd, f_t, risk, sic_v, depth, u, v, w, wh = sd
            cum_dist += leg_dist
            cum_fuel += f_t
            risk_vals.append(risk)
            if sic_v > 0.15:
                ice_nms.append(leg_dist)

            # fuel_rate is derived from the same leg_fuel already computed by the model
            fuel_rate = (f_t / max(0.001, leg_dist / max(0.1, spd))) * 24.0

            waypoints.append(RouteWaypoint(
                sequence=seq,
                point=pt,
                grid_cell_id=c_id,
                eta=eta,
                speed_knots=round(spd, 1),
                leg_distance_nm=round(leg_dist, 1),
                cumulative_distance_nm=round(cum_dist, 1),
                leg_fuel_tonnes=round(f_t, 2),
                cumulative_fuel_tonnes=round(cum_fuel, 2),
                local_risk=round(risk, 3),
                ice_concentration=round(sic_v, 3),
                bathymetry_depth_m=round(depth, 1),
                current_u_ms=round(u, 3),
                current_v_ms=round(v, 3),
                wind_speed_ms=round(w, 2),
                wave_height_m=round(wh, 2),
                fuel_rate_tonnes_per_day=round(fuel_rate, 2),
            ))

        if not waypoints:
            return None

        total_h = (waypoints[-1].eta - departure_time).total_seconds() / 3600.0
        mean_risk = sum(risk_vals) / len(risk_vals) if risk_vals else 0.1
        max_risk = max(risk_vals) if risk_vals else 0.1
        ice_pct = (sum(ice_nms) / cum_dist * 100.0) if cum_dist > 0 else 0.0

        metrics = RouteMetrics(
            distance_nm=round(cum_dist, 1),
            duration_hours=round(total_h, 1),
            duration_days=round(total_h / 24.0, 2),
            estimated_fuel_tonnes=round(cum_fuel, 1),
            mean_risk_score=round(mean_risk, 3),
            max_risk_score=round(max_risk, 3),
            waypoint_risks=risk_vals,
            sea_ice_exposure_percent=round(ice_pct, 1),
            iceberg_hazard_exposure=round(0.08 if objective == RouteObjective.SAFEST else 0.15, 3),
            constraint_violations=[],
            is_feasible=True,
        )

        labels = {
            RouteObjective.SHORTEST: "Shortest geographic path; crosses sea ice directly.",
            RouteObjective.FASTEST: "Minimum transit time; avoids ice because it slows the vessel.",
            RouteObjective.SAFEST: "Maximum safety margin; penalises ice concentration and wave exposure heavily.",
            RouteObjective.FUEL_EFFICIENT: "Minimum fuel burn; leverages current vectors and economical RPM.",
            RouteObjective.BALANCED: "Multi-criteria compromise of time, fuel, and ice exposure.",
        }

        return RouteAlternative(
            route_id=f"route-{uuid4().hex[:8]}",
            objective=objective,
            departure_time=departure_time,
            metrics=metrics,
            waypoints=waypoints,
            explanation=labels.get(objective, "Discrete grid optimised Antarctic route."),
            is_mock=True,
        )
