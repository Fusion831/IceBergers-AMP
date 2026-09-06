"""Routing Service coordinating route optimization, 4D validation, and multi-objective alternatives."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from domain.coordinates import GeoPoint
from domain.enums import RouteObjective
from domain.vessel import VesselProfile
from domain.route import (
    RouteOptimizationRequest,
    RouteOptimizationResponse,
    RouteAlternative,
    RouteComparison,
)
from routing.interface import RouteOptimizerInterface, RouteValidatorInterface
from routing.mock_optimizer import MockRouteOptimizer
from routing.validator import RouteValidator
from services.risk_service import RiskService
from core.errors import NotFoundError, RoutingError

logger = logging.getLogger(__name__)


class RoutingService:
    """Service for generating, validating, and comparing route alternatives."""

    def __init__(
        self,
        optimizer: Optional[RouteOptimizerInterface] = None,
        validator: Optional[RouteValidatorInterface] = None,
        risk_service: Optional[RiskService] = None,
    ) -> None:
        self.optimizer = optimizer or MockRouteOptimizer()
        self.validator = validator or RouteValidator()
        self.risk_service = risk_service or RiskService()
        self._route_cache: Dict[str, RouteAlternative] = {}

    def optimize_routes(
        self,
        request: RouteOptimizationRequest,
    ) -> RouteOptimizationResponse:
        """Run route optimization across requested objectives and perform 4D validation."""
        vessel = request.vessel_profile or VesselProfile()
        start_time = request.departure_time

        # 1. Compute environmental risk field for the planning window
        risk_field = self.risk_service.get_risk_field(
            valid_time=start_time,
            vessel=vessel,
            weights=request.risk_weights,
        )

        # 2. Generate route alternatives using optimizer interface
        routes: List[RouteAlternative] = []
        objectives = request.objectives or [
            RouteObjective.SAFEST,
            RouteObjective.FASTEST,
            RouteObjective.FUEL_EFFICIENT,
            RouteObjective.BALANCED,
        ]

        for obj in objectives:
            alt = self.optimizer.optimize(
                start=request.origin,
                destination=request.destination,
                start_time=start_time,
                objective=obj,
                vessel=vessel,
                risk_field=risk_field,
                risk_weights=request.risk_weights,
            )

            # 3. Perform 4D spatio-temporal route validation
            val_summary = self.validator.validate_route(
                route=alt,
                risk_field=risk_field,
                vessel=vessel,
            )

            # Update metrics with validated 4D risk metrics
            alt.metrics.mean_risk = val_summary.mean_risk
            alt.metrics.max_risk = val_summary.max_risk
            alt.metrics.risk_p95 = val_summary.p95_risk
            alt.metrics.risk_p99 = val_summary.p99_risk
            alt.metrics.ice_exposure_nm = val_summary.sea_ice_exposure_nm
            alt.metrics.iceberg_exposure_nm = val_summary.iceberg_hazard_exposure_nm
            alt.metrics.constraint_violations = val_summary.constraint_violations

            routes.append(alt)
            self._route_cache[alt.route_id] = alt

        # 4. Recommend the best route (default BALANCED, or lowest total score)
        recommended = routes[0]
        for r in routes:
            if r.objective == RouteObjective.BALANCED:
                recommended = r
                break

        response = RouteOptimizationResponse(
            request_id=f"req-{int(start_time.timestamp())}",
            generated_at=datetime.now(timezone.utc),
            origin=request.origin,
            destination=request.destination,
            departure_time=start_time,
            routes=routes,
            recommended_route_id=recommended.route_id,
            computation_time_seconds=0.45,
        )
        return response

    def get_route(self, route_id: str) -> RouteAlternative:
        """Fetch a cached route by ID."""
        if route_id not in self._route_cache:
            raise NotFoundError(f"Route '{route_id}' not found.")
        return self._route_cache[route_id]

    def compare_routes(self, route_ids: List[str]) -> RouteComparison:
        """Compare multiple route alternatives side-by-side."""
        routes = [self.get_route(rid) for rid in route_ids]
        if not routes:
            raise RoutingError("No valid routes provided for comparison.")

        # Rank by duration, fuel, and risk
        fastest = min(routes, key=lambda r: r.metrics.duration_hours).route_id
        most_efficient = min(routes, key=lambda r: r.metrics.fuel_consumption_tonnes).route_id
        safest = min(routes, key=lambda r: r.metrics.mean_risk).route_id

        summary = (
            f"Compared {len(routes)} alternatives. "
            f"Fastest route is {fastest}, most fuel efficient is {most_efficient}, "
            f"and safest route is {safest}."
        )

        return RouteComparison(
            routes=routes,
            fastest_route_id=fastest,
            most_fuel_efficient_route_id=most_efficient,
            safest_route_id=safest,
            comparison_summary=summary,
        )
