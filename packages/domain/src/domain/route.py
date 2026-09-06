"""Route optimization, waypoint profiles, metrics, and comparisons."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator
from domain.coordinates import GeoPoint
from domain.enums import RouteObjective
from domain.risk import RiskFactorAttribution, RiskWeightsConfig
from domain.vessel import VesselProfile


class RouteWaypoint(BaseModel):
    """Discrete waypoint along a generated voyage path with local environmental attribution."""
    sequence: int = 0
    position: Optional[GeoPoint] = None
    point: Optional[GeoPoint] = None
    estimated_arrival: Optional[datetime] = None
    eta: Optional[datetime] = None
    speed_knots: float = Field(default=11.0, ge=0.0, le=25.0)
    local_risk: float = Field(default=0.2, ge=0.0, le=1.0)
    local_sic: float = Field(default=0.0, ge=0.0, le=1.0)
    local_depth_m: Optional[float] = None
    risk_attribution: Optional[RiskFactorAttribution] = None
    leg_distance_nm: Optional[float] = 0.0
    cumulative_distance_nm: Optional[float] = 0.0
    leg_fuel_tonnes: Optional[float] = 0.0
    cumulative_fuel_tonnes: Optional[float] = 0.0
    ice_concentration: Optional[float] = 0.0
    bathymetry_depth_m: Optional[float] = None

    @model_validator(mode="after")
    def sync_waypoint(self) -> "RouteWaypoint":
        if self.position is not None and self.point is None:
            self.point = self.position
        elif self.point is not None and self.position is None:
            self.position = self.point

        if self.estimated_arrival is not None and self.eta is None:
            self.eta = self.estimated_arrival
        elif self.eta is not None and self.estimated_arrival is None:
            self.estimated_arrival = self.eta

        if self.eta is None:
            self.eta = datetime.now(timezone.utc)
            self.estimated_arrival = self.eta

        if self.ice_concentration and not self.local_sic:
            self.local_sic = self.ice_concentration
        elif self.local_sic and not self.ice_concentration:
            self.ice_concentration = self.local_sic

        if self.bathymetry_depth_m and not self.local_depth_m:
            self.local_depth_m = self.bathymetry_depth_m
        elif self.local_depth_m and not self.bathymetry_depth_m:
            self.bathymetry_depth_m = self.local_depth_m
        return self


class RouteMetrics(BaseModel):
    """Aggregated navigation, fuel, and safety exposure metrics for a route."""
    distance_nm: float = Field(default=0.0, ge=0.0)
    duration_hours: float = Field(default=0.0, ge=0.0)
    duration_days: float = Field(default=0.0, ge=0.0)
    estimated_fuel_mt: float = Field(default=0.0, ge=0.0)
    fuel_consumption_tonnes: Optional[float] = None
    mean_risk: float = Field(default=0.2, ge=0.0, le=1.0)
    max_risk: float = Field(default=0.5, ge=0.0, le=1.0)
    p95_risk: float = Field(default=0.4, ge=0.0, le=1.0)
    risk_p95: Optional[float] = None
    risk_p99: Optional[float] = None
    ice_exposure_nm: float = Field(default=0.0, ge=0.0)
    iceberg_exposure_nm: Optional[float] = None
    iceberg_hazard_exposure: float = Field(default=0.0, ge=0.0, le=1.0)
    weather_rough_seas_hours: float = Field(default=0.0, ge=0.0)
    constraint_violations: List[str] = Field(default_factory=list)
    waypoint_risks: Optional[List[float]] = None
    estimated_fuel_tonnes: Optional[float] = None
    mean_risk_score: Optional[float] = None
    max_risk_score: Optional[float] = None
    sea_ice_exposure_percent: Optional[float] = None
    is_feasible: Optional[bool] = True

    @model_validator(mode="after")
    def sync_metrics(self) -> "RouteMetrics":
        if self.estimated_fuel_tonnes is not None and self.estimated_fuel_mt == 0.0:
            self.estimated_fuel_mt = self.estimated_fuel_tonnes
        elif self.estimated_fuel_mt > 0.0 and self.estimated_fuel_tonnes is None:
            self.estimated_fuel_tonnes = self.estimated_fuel_mt

        if self.fuel_consumption_tonnes is not None and self.estimated_fuel_mt == 0.0:
            self.estimated_fuel_mt = self.fuel_consumption_tonnes
            self.estimated_fuel_tonnes = self.fuel_consumption_tonnes
        elif self.estimated_fuel_mt > 0.0 and self.fuel_consumption_tonnes is None:
            self.fuel_consumption_tonnes = self.estimated_fuel_mt
        elif self.fuel_consumption_tonnes is None:
            self.fuel_consumption_tonnes = self.estimated_fuel_mt

        if self.mean_risk_score is not None and self.mean_risk == 0.2:
            self.mean_risk = self.mean_risk_score
        elif self.mean_risk != 0.2 and self.mean_risk_score is None:
            self.mean_risk_score = self.mean_risk

        if self.max_risk_score is not None and self.max_risk == 0.5:
            self.max_risk = self.max_risk_score
        elif self.max_risk != 0.5 and self.max_risk_score is None:
            self.max_risk_score = self.max_risk

        if self.risk_p95 is not None:
            self.p95_risk = self.risk_p95
        else:
            self.risk_p95 = self.p95_risk

        if self.iceberg_exposure_nm is not None:
            self.iceberg_hazard_exposure = min(1.0, self.iceberg_exposure_nm / max(1.0, self.distance_nm))
        else:
            self.iceberg_exposure_nm = self.iceberg_hazard_exposure * self.distance_nm

        if self.duration_days == 0.0 and self.duration_hours > 0.0:
            self.duration_days = round(self.duration_hours / 24.0, 2)
        elif self.duration_hours == 0.0 and self.duration_days > 0.0:
            self.duration_hours = round(self.duration_days * 24.0, 2)
        return self


class RouteAlternative(BaseModel):
    """A generated route option for a specific navigation objective."""
    route_id: str = Field(default_factory=lambda: f"route-{uuid4().hex[:8]}")
    mission_id: Optional[str] = None
    objective: RouteObjective
    departure_time: datetime
    metrics: RouteMetrics
    waypoints: List[RouteWaypoint]
    geojson_linestring: Optional[Dict[str, Any]] = None
    geojson: Optional[Dict[str, Any]] = None
    explanation: str = "Route generated under multi-hazard risk optimization."
    is_mock: bool = Field(default=True)

    @model_validator(mode="after")
    def sync_linestring(self) -> "RouteAlternative":
        if self.geojson_linestring is not None and self.geojson is None:
            self.geojson = self.geojson_linestring
        elif self.geojson is not None and self.geojson_linestring is None:
            self.geojson_linestring = self.geojson
        elif self.geojson is None and self.geojson_linestring is None:
            coords = [
                [wp.point.longitude, wp.point.latitude]
                for wp in self.waypoints if wp.point
            ]
            feature = {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {"objective": self.objective.value},
            }
            self.geojson = feature
            self.geojson_linestring = feature
        return self


from domain.mission import MissionTarget, AvoidanceZone
from domain.enums import RouterEngineType


class RouteOptimizationRequest(BaseModel):
    """Request payload to calculate optimized routes."""
    mission_id: Optional[str] = None
    origin: GeoPoint
    destination: GeoPoint
    departure_time: datetime
    vessel: Optional[VesselProfile] = None
    vessel_profile: Optional[VesselProfile] = None
    risk_weights: Optional[RiskWeightsConfig] = None
    targets: Optional[List[MissionTarget]] = None
    avoidance_zones: Optional[List[AvoidanceZone]] = None
    engine: Optional[RouterEngineType] = Field(default=RouterEngineType.AMIP_CUSTOM)
    objectives: Optional[List[RouteObjective]] = Field(
        default_factory=lambda: [
            RouteObjective.SHORTEST,
            RouteObjective.FASTEST,
            RouteObjective.SAFEST,
            RouteObjective.FUEL_EFFICIENT,
            RouteObjective.BALANCED,
        ]
    )

    @model_validator(mode="after")
    def sync_vessel(self) -> "RouteOptimizationRequest":
        if self.vessel_profile is not None and self.vessel is None:
            self.vessel = self.vessel_profile
        elif self.vessel is not None and self.vessel_profile is None:
            self.vessel_profile = self.vessel
        elif self.vessel is None and self.vessel_profile is None:
            self.vessel = VesselProfile()
            self.vessel_profile = self.vessel
        return self


class RouteOptimizationResponse(BaseModel):
    """Optimization response carrying all calculated alternative routes."""
    request_id: Optional[str] = None
    mission_id: Optional[str] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    origin: Optional[GeoPoint] = None
    destination: Optional[GeoPoint] = None
    departure_time: Optional[datetime] = None
    routes: List[RouteAlternative]
    recommended_objective: Optional[RouteObjective] = RouteObjective.BALANCED
    recommended_route_id: Optional[str] = None
    execution_time_seconds: Optional[float] = None
    computation_time_seconds: Optional[float] = 0.45

    @model_validator(mode="after")
    def sync_response(self) -> "RouteOptimizationResponse":
        if self.execution_time_seconds is not None and self.computation_time_seconds is None:
            self.computation_time_seconds = self.execution_time_seconds
        elif self.computation_time_seconds is not None and self.execution_time_seconds is None:
            self.execution_time_seconds = self.computation_time_seconds

        if not self.recommended_route_id and self.routes:
            for r in self.routes:
                if r.objective == RouteObjective.BALANCED:
                    self.recommended_route_id = r.route_id
                    break
            if not self.recommended_route_id:
                self.recommended_route_id = self.routes[0].route_id
        return self


class RouteComparison(BaseModel):
    """Side-by-side evaluation comparison of generated route alternatives."""
    routes: List[RouteAlternative]
    shortest_route_id: Optional[str] = None
    fastest_route_id: str
    most_fuel_efficient_route_id: str
    safest_route_id: str
    comparison_summary: str
