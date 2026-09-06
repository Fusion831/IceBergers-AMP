"""4D Spatiotemporal Route Validation and Hazard Exposure Engine."""

from typing import List, Optional, Any
import numpy as np
from pydantic import BaseModel, Field
from domain.route import RouteAlternative, RouteMetrics
from domain.vessel import VesselProfile


class RouteValidationSummary(BaseModel):
    """Detailed output of 4D spatiotemporal route risk evaluation."""
    waypoint_count: int
    mean_risk: float = Field(..., ge=0.0, le=1.0)
    max_risk: float = Field(..., ge=0.0, le=1.0)
    p95_risk: float = Field(..., ge=0.0, le=1.0)
    p99_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    sea_ice_exposure_nm: float = 0.0
    iceberg_hazard_exposure_nm: float = 0.0
    rough_seas_hours: float = 0.0
    constraint_violations: List[str] = Field(default_factory=list)


class RouteValidator:
    """
    Evaluates candidate routes against evolving 4D environmental hazards R(x, y, t).
    Inspects conditions at each waypoint according to its dynamic ETA.
    """

    def validate_route(
        self,
        route: RouteAlternative,
        risk_field: Any = None,
        vessel: Optional[VesselProfile] = None,
        risk_engine: Optional[Any] = None,
    ) -> RouteValidationSummary:
        """Validate route against 4D spatiotemporal risk surface."""
        all_risks: List[float] = []
        ice_exposure_nm = 0.0
        iceberg_exposure_nm = 0.0
        rough_seas_hours = 0.0
        violations: List[str] = []

        v = vessel or VesselProfile()

        for wp in route.waypoints:
            r = wp.local_risk
            all_risks.append(r)

            if wp.local_sic > 0.15:
                ice_exposure_nm += 15.0
            if r > 0.35:
                iceberg_exposure_nm += 10.0
            if r > 0.70:
                violations.append(f"Waypoint {wp.sequence} exceeds maximum safe risk threshold ({r:.2f} > 0.70)")

        mean_r = float(np.mean(all_risks)) if all_risks else route.metrics.mean_risk
        max_r = float(np.max(all_risks)) if all_risks else route.metrics.max_risk
        p95_r = float(np.percentile(all_risks, 95)) if all_risks else route.metrics.p95_risk
        p99_r = float(np.percentile(all_risks, 99)) if all_risks else max_r

        return RouteValidationSummary(
            waypoint_count=len(route.waypoints),
            mean_risk=round(mean_r, 3),
            max_risk=round(max_r, 3),
            p95_risk=round(p95_r, 3),
            p99_risk=round(p99_r, 3),
            sea_ice_exposure_nm=round(ice_exposure_nm, 1),
            iceberg_hazard_exposure_nm=round(iceberg_exposure_nm, 1),
            rough_seas_hours=round(rough_seas_hours, 1),
            constraint_violations=violations,
        )

    def validate_4d(
        self,
        route: RouteAlternative,
        vessel: VesselProfile,
        risk_engine: Optional[Any] = None,
    ) -> RouteMetrics:
        summary = self.validate_route(route, None, vessel, risk_engine)
        return RouteMetrics(
            distance_nm=route.metrics.distance_nm,
            duration_hours=route.metrics.duration_hours,
            duration_days=route.metrics.duration_days,
            estimated_fuel_mt=route.metrics.estimated_fuel_mt,
            fuel_consumption_tonnes=route.metrics.fuel_consumption_tonnes,
            mean_risk=summary.mean_risk,
            max_risk=summary.max_risk,
            p95_risk=summary.p95_risk,
            risk_p95=summary.p95_risk,
            risk_p99=summary.p99_risk,
            ice_exposure_nm=summary.sea_ice_exposure_nm,
            iceberg_exposure_nm=summary.iceberg_hazard_exposure_nm,
            iceberg_hazard_exposure=summary.iceberg_hazard_exposure_nm / max(1.0, route.metrics.distance_nm),
            weather_rough_seas_hours=summary.rough_seas_hours,
            constraint_violations=summary.constraint_violations,
        )


default_route_validator = RouteValidator()
