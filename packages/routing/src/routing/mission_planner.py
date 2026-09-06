"""
Mission Planner for Multi-Target Antarctic Expeditions.
Handles multi-stop sequencing across ports, research stations, science sites,
and selected grid cells (e.g. S17, S42) with avoidance zones and dwell times.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4

from domain.coordinates import GeoPoint
from domain.vessel import VesselProfile
from domain.enums import RouteObjective, MissionTargetType
from domain.mission import MissionTarget, AvoidanceZone
from domain.route import RouteAlternative, RouteWaypoint, RouteMetrics
from routing.amip_custom_router import AMIPCustomRouter


class MissionPlanner:
    """
    Orchestrates multi-stop Antarctic mission routes.
    Computes sequenced legs connecting ports, science survey polygons, and selected grid cells.
    """

    def __init__(self, router: Optional[AMIPCustomRouter] = None):
        self.router = router or AMIPCustomRouter()

    def plan_multi_target_mission(
        self,
        origin: GeoPoint,
        targets: List[MissionTarget],
        departure_time: datetime,
        vessel: VesselProfile,
        objective: RouteObjective = RouteObjective.BALANCED,
        avoidance_zones: Optional[List[AvoidanceZone]] = None,
    ) -> RouteAlternative:
        """
        Sequence multi-stop targets into a continuous 4D mission route.
        """
        if not targets:
            raise ValueError("Mission must contain at least one destination target.")

        # Sort targets by explicit sequence_order if provided, otherwise preserve list order
        sorted_targets = sorted(targets, key=lambda t: t.sequence_order if t.sequence_order is not None else 999)

        all_waypoints: List[RouteWaypoint] = []
        current_dep_point = origin
        current_dep_time = departure_time
        total_distance = 0.0
        total_fuel = 0.0
        all_risks: List[float] = []
        waypoint_seq = 0

        for target_idx, target in enumerate(sorted_targets):
            # Optimize leg between current position and target
            leg_route = self.router.optimize_leg(
                origin=current_dep_point,
                destination=target.location,
                departure_time=current_dep_time,
                vessel=vessel,
                objective=objective,
                avoidance_zones=avoidance_zones,
            )

            # Append leg waypoints with updated cumulative sequence and distance
            for wp_idx, wp in enumerate(leg_route.waypoints):
                # Skip first waypoint of subsequent legs to prevent duplicate points at intermediate stops
                if target_idx > 0 and wp_idx == 0:
                    continue

                all_waypoints.append(
                    RouteWaypoint(
                        sequence=waypoint_seq,
                        point=wp.point,
                        eta=wp.eta,
                        speed_knots=wp.speed_knots,
                        leg_distance_nm=wp.leg_distance_nm,
                        cumulative_distance_nm=round(total_distance + wp.cumulative_distance_nm, 1),
                        leg_fuel_tonnes=wp.leg_fuel_tonnes,
                        cumulative_fuel_tonnes=round(total_fuel + wp.cumulative_fuel_tonnes, 2),
                        local_risk=wp.local_risk,
                        ice_concentration=wp.ice_concentration,
                        bathymetry_depth_m=wp.bathymetry_depth_m,
                    )
                )
                all_risks.append(wp.local_risk)
                waypoint_seq += 1

            # Update cumulative metrics
            total_distance += leg_route.metrics.distance_nm
            total_fuel += leg_route.metrics.estimated_fuel_tonnes

            # Arrival time at target
            arrival_time = leg_route.waypoints[-1].eta

            # Add target dwell / survey time (e.g. 24 hours CTD sampling at grid cell S17)
            dwell_hours = target.dwell_hours or 0.0
            next_departure = arrival_time + timedelta(hours=dwell_hours)

            # Advance current state for next leg
            current_dep_point = target.location
            current_dep_time = next_departure

        total_duration_hours = (current_dep_time - departure_time).total_seconds() / 3600.0
        mean_risk = sum(all_risks) / len(all_risks) if all_risks else 0.1
        max_risk = max(all_risks) if all_risks else 0.1

        metrics = RouteMetrics(
            distance_nm=round(total_distance, 1),
            duration_hours=round(total_duration_hours, 1),
            duration_days=round(total_duration_hours / 24.0, 2),
            estimated_fuel_tonnes=round(total_fuel, 1),
            mean_risk_score=round(mean_risk, 3),
            max_risk_score=round(max_risk, 3),
            sea_ice_exposure_percent=12.5,
            iceberg_hazard_exposure=0.10,
            constraint_violations=[],
            is_feasible=True,
        )

        return RouteAlternative(
            route_id=f"mission-route-{uuid4().hex[:8]}",
            objective=objective,
            departure_time=departure_time,
            metrics=metrics,
            waypoints=all_waypoints,
            explanation=f"Multi-target mission itinerary visiting {len(sorted_targets)} targets ({[t.name for t in sorted_targets]}).",
            is_mock=True,
        )
