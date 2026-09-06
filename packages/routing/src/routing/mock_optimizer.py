"""Deterministic Mock Route Optimizer producing genuinely differentiated routes."""

import time
from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Optional, Any, Union
from uuid import uuid4
import numpy as np
from domain.coordinates import GeoPoint
from domain.enums import RouteObjective
from domain.route import (
    RouteOptimizationRequest,
    RouteOptimizationResponse,
    RouteAlternative,
    RouteWaypoint,
    RouteMetrics,
)
from domain.vessel import VesselProfile
from routing.interface import RouteOptimizerInterface
from routing.fuel_model import default_fuel_model
from data_access.spatial import interpolate_great_circle_path, haversine_distance_nm


class MockRouteOptimizer(RouteOptimizerInterface):
    """
    Deterministic mock router.
    Generates four geometrically distinct, internally consistent route alternatives.
    """

    def optimize(
        self,
        *args,
        **kwargs,
    ) -> Union[RouteOptimizationResponse, RouteAlternative]:
        # Handle call with single RouteOptimizationRequest
        if args and isinstance(args[0], RouteOptimizationRequest):
            return self._optimize_request(args[0])
        elif "request" in kwargs and isinstance(kwargs["request"], RouteOptimizationRequest):
            return self._optimize_request(kwargs["request"])
        else:
            # Handle multi-argument call: (start, destination, start_time, objective, vessel, risk_field, risk_weights)
            start = kwargs.get("start", args[0] if len(args) > 0 else None)
            destination = kwargs.get("destination", args[1] if len(args) > 1 else None)
            start_time = kwargs.get("start_time", args[2] if len(args) > 2 else datetime.now(timezone.utc))
            objective = kwargs.get("objective", args[3] if len(args) > 3 else RouteObjective.BALANCED)
            vessel = kwargs.get("vessel", args[4] if len(args) > 4 else None) or VesselProfile()

            req = RouteOptimizationRequest(
                origin=start,
                destination=destination,
                departure_time=start_time,
                vessel_profile=vessel,
                objectives=[objective],
            )
            return self._generate_objective_route(
                request=req,
                objective=objective,
                vessel=vessel,
            )

    def _optimize_request(self, request: RouteOptimizationRequest) -> RouteOptimizationResponse:
        start_time = time.time()
        vessel = request.vessel_profile or request.vessel or VesselProfile()

        routes: List[RouteAlternative] = []
        objectives = request.objectives or [
            RouteObjective.SAFEST,
            RouteObjective.FASTEST,
            RouteObjective.FUEL_EFFICIENT,
            RouteObjective.BALANCED,
        ]

        for obj in objectives:
            route = self._generate_objective_route(
                request=request,
                objective=obj,
                vessel=vessel,
            )
            routes.append(route)

        exec_time = round(time.time() - start_time, 3)

        return RouteOptimizationResponse(
            request_id=f"req-{uuid4().hex[:8]}",
            mission_id=request.mission_id,
            departure_time=request.departure_time,
            origin=request.origin,
            destination=request.destination,
            routes=routes,
            recommended_objective=RouteObjective.BALANCED,
            recommended_route_id=routes[0].route_id,
            computation_time_seconds=exec_time,
            execution_time_seconds=exec_time,
        )

    def _generate_objective_route(
        self,
        request: RouteOptimizationRequest,
        objective: RouteObjective,
        vessel: VesselProfile,
    ) -> RouteAlternative:
        base_points = interpolate_great_circle_path(request.origin, request.destination, n_points=45)

        # Apply geometrically distinct offsets according to the objective
        offset_coords: List[Tuple[float, float]] = []

        for lat, lon in base_points:
            # Only apply detour offsets in the Southern Ocean hazard belt (-45S to -66S)
            if -66.0 <= lat <= -45.0:
                bell = np.exp(-0.5 * ((lat + 55.0) / 5.0) ** 2)
                if objective == RouteObjective.SAFEST:
                    # Steer eastward away from iceberg cluster and western pack ice
                    detour_lon = lon + (6.5 * bell)
                    offset_coords.append((lat, detour_lon))
                elif objective == RouteObjective.FASTEST:
                    # Direct near-great-circle path (minimal deviation)
                    detour_lon = lon + (0.5 * bell)
                    offset_coords.append((lat, detour_lon))
                elif objective == RouteObjective.FUEL_EFFICIENT:
                    # Exploit eastward flowing ACC jet near -52S
                    detour_lon = lon + (3.8 * bell)
                    offset_coords.append((lat, detour_lon))
                else:  # BALANCED
                    detour_lon = lon + (2.5 * bell)
                    offset_coords.append((lat, detour_lon))
            elif lat < -66.0:
                coastal_bell = np.sin((lat + 66.0) * np.pi / 3.0)
                if objective == RouteObjective.SAFEST:
                    detour_lon = lon + (1.2 * coastal_bell)
                    offset_coords.append((lat, detour_lon))
                elif objective == RouteObjective.FASTEST:
                    detour_lon = lon
                    offset_coords.append((lat, detour_lon))
                elif objective == RouteObjective.FUEL_EFFICIENT:
                    detour_lon = lon + (0.6 * coastal_bell)
                    offset_coords.append((lat, detour_lon))
                else:  # BALANCED
                    detour_lon = lon + (0.4 * coastal_bell)
                    offset_coords.append((lat, detour_lon))
            else:
                offset_coords.append((lat, lon))

        # Speed policy per objective
        if objective == RouteObjective.FASTEST:
            base_speed = vessel.max_speed_knots * 0.95  # ~13.3 knots
            explanation = (
                "Fastest route minimizes voyage duration by adhering closely to the great-circle transect. "
                "Maintains near-maximum cruising speed, accepting moderate storm exposure in the roaring forties."
            )
        elif objective == RouteObjective.SAFEST:
            base_speed = vessel.cruising_speed_knots * 0.85  # ~8.5 knots
            explanation = (
                "Safest route executes a wide 160 NM eastward detour between 50°S and 63°S, completely bypassing "
                "a dense iceberg drift cluster and heavy pack ice tongue, reducing mean navigational risk."
            )
        elif objective == RouteObjective.FUEL_EFFICIENT:
            base_speed = vessel.cruising_speed_knots * 0.78  # ~7.8 knots (economical hull speed)
            explanation = (
                "Fuel-efficient route routes through the core of the Antarctic Circumpolar Current to exploit tail currents, "
                "reducing total fuel burn at an acceptable travel time trade-off."
            )
        else:  # BALANCED
            base_speed = vessel.cruising_speed_knots * 0.90  # ~9.0 knots
            explanation = (
                "Balanced route represents the optimal Pareto compromise, balancing transit time with "
                "fuel burn and maintaining adequate safe clearance from high-risk iceberg corridors."
            )

        # Build waypoints with cumulative distance and arrival timestamps
        waypoints: List[RouteWaypoint] = []
        curr_time = request.departure_time
        total_distance_nm = 0.0
        ice_exposure_nm = 0.0
        rough_seas_hours = 0.0
        all_risks = []

        for seq, (p_lat, p_lon) in enumerate(offset_coords):
            if seq > 0:
                prev_lat, prev_lon = offset_coords[seq - 1]
                leg_dist = haversine_distance_nm(prev_lat, prev_lon, p_lat, p_lon)
                total_distance_nm += leg_dist
                leg_hours = leg_dist / base_speed
                curr_time += timedelta(hours=leg_hours)

                if -55.0 <= p_lat <= -48.0:
                    rough_seas_hours += leg_hours

            # Local conditions
            if p_lat < -63.0:
                local_sic = min(0.55, max(0.0, (-63.0 - p_lat) / 10.0))
                ice_exposure_nm += 15.0
            else:
                local_sic = 0.0

            # Objective-modulated local risk
            if objective == RouteObjective.SAFEST:
                local_risk = 0.06 + (0.15 * local_sic)
            elif objective == RouteObjective.FASTEST:
                local_risk = 0.20 + (0.35 * local_sic)
            elif objective == RouteObjective.FUEL_EFFICIENT:
                local_risk = 0.14 + (0.24 * local_sic)
            else:
                local_risk = 0.11 + (0.22 * local_sic)

            all_risks.append(local_risk)

            waypoints.append(
                RouteWaypoint(
                    sequence=seq,
                    position=GeoPoint(latitude=round(p_lat, 5), longitude=round(p_lon, 5)),
                    point=GeoPoint(latitude=round(p_lat, 5), longitude=round(p_lon, 5)),
                    estimated_arrival=curr_time,
                    eta=curr_time,
                    speed_knots=round(base_speed, 1),
                    local_risk=round(local_risk, 3),
                    local_sic=round(local_sic, 3),
                )
            )

        duration_hours = (curr_time - request.departure_time).total_seconds() / 3600.0
        duration_days = duration_hours / 24.0

        # Estimate fuel burn
        fuel_mt, _ = default_fuel_model.estimate_fuel_burn(
            vessel=vessel,
            speed_knots=base_speed,
            duration_hours=duration_hours,
            mean_sic=0.15 if objective == RouteObjective.FASTEST else 0.06,
            wave_height_m=3.8 if objective == RouteObjective.FASTEST else 3.0,
        )

        mean_r = float(np.mean(all_risks))
        max_r = float(np.max(all_risks))
        p95_r = float(np.percentile(all_risks, 95))

        metrics = RouteMetrics(
            distance_nm=round(total_distance_nm, 1),
            duration_hours=round(duration_hours, 1),
            duration_days=round(duration_days, 2),
            estimated_fuel_mt=round(fuel_mt, 1),
            fuel_consumption_tonnes=round(fuel_mt, 1),
            mean_risk=round(mean_r, 3),
            max_risk=round(max_r, 3),
            p95_risk=round(p95_r, 3),
            risk_p95=round(p95_r, 3),
            ice_exposure_nm=round(ice_exposure_nm, 1),
            iceberg_hazard_exposure=0.02 if objective == RouteObjective.SAFEST else 0.08,
            weather_rough_seas_hours=round(rough_seas_hours, 1),
            waypoint_risks=[wp.local_risk for wp in waypoints],
        )

        linestring_geojson = {
            "type": "LineString",
            "coordinates": [[round(lon, 5), round(lat, 5)] for lat, lon in offset_coords],
        }

        return RouteAlternative(
            route_id=f"route-{uuid4().hex[:8]}",
            mission_id=str(request.mission_id) if request.mission_id else None,
            objective=objective,
            departure_time=request.departure_time,
            metrics=metrics,
            waypoints=waypoints,
            geojson_linestring=linestring_geojson,
            geojson=linestring_geojson,
            explanation=explanation,
            is_mock=True,
        )


default_route_optimizer = MockRouteOptimizer()
