"""Mission analysis, station accessibility windows, and decision support outputs."""

from datetime import datetime, timezone
from typing import List, Optional, Any
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator
from domain.coordinates import GeoPoint
from domain.route import RouteAlternative, RouteComparison


class StationAccessibilityPoint(BaseModel):
    """Daily or horizon-based accessibility status for an Antarctic research station."""
    date: Optional[datetime] = None
    valid_time: Optional[datetime] = None
    horizon_days: int = 0
    accessibility_score: float = Field(default=0.8, ge=0.0, le=1.0)
    is_accessible: bool = True
    approach_ice_concentration: Optional[float] = None
    expected_sic: Optional[float] = None
    approach_mean_risk: Optional[float] = None
    fast_ice_status: str = Field(default="BREAKING_UP", json_schema_extra={"example": "BREAKING_UP"})
    ice_barrier_thickness_nm: Optional[float] = 0.0
    recommended_entry_speed_knots: Optional[float] = 10.0

    @model_validator(mode="after")
    def sync_point(self) -> "StationAccessibilityPoint":
        if self.date is not None and self.valid_time is None:
            self.valid_time = self.date
        elif self.valid_time is not None and self.date is None:
            self.date = self.valid_time
        elif self.date is None and self.valid_time is None:
            self.date = datetime.now(timezone.utc)
            self.valid_time = self.date

        if self.expected_sic is not None and self.approach_ice_concentration is None:
            self.approach_ice_concentration = self.expected_sic
        elif self.approach_ice_concentration is not None and self.expected_sic is None:
            self.expected_sic = self.approach_ice_concentration
        elif self.expected_sic is None:
            self.expected_sic = 0.2
            self.approach_ice_concentration = 0.2

        if self.approach_mean_risk is None:
            self.approach_mean_risk = round(1.0 - self.accessibility_score, 3)

        return self


class StationAccessibilityWindow(BaseModel):
    """Seasonal accessibility window evaluation for a specific station (Bharati / Maitri)."""
    station_code: Optional[str] = None
    station_name: str
    location: Optional[GeoPoint] = None
    reference_time: Optional[datetime] = None
    season_start: Optional[datetime] = None
    season_end: Optional[datetime] = None
    optimal_window_start: Optional[datetime] = None
    optimal_window_end: Optional[datetime] = None
    optimal_arrival_window: Optional[str] = None
    days_accessible_count: int = 30
    accessibility_series: Optional[List[StationAccessibilityPoint]] = None
    accessibility_points: Optional[List[StationAccessibilityPoint]] = None

    @model_validator(mode="after")
    def sync_series(self) -> "StationAccessibilityWindow":
        if self.accessibility_series is not None and self.accessibility_points is None:
            self.accessibility_points = self.accessibility_series
        elif self.accessibility_points is not None and self.accessibility_series is None:
            self.accessibility_series = self.accessibility_points

        if not self.station_code:
            self.station_code = self.station_name.upper()[:8]

        if not self.season_start:
            self.season_start = self.reference_time or datetime.now(timezone.utc)
        return self


class MissionAnalysisResult(BaseModel):
    """Consolidated mission decision support report."""
    mission_id: str
    analysis_id: str = Field(default_factory=lambda: f"ans-{uuid4().hex[:8]}")
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_feasible: bool = True
    overall_accessibility_score: float = 0.8
    station_windows: Optional[List[StationAccessibilityWindow]] = None
    station_accessibility: Optional[List[StationAccessibilityWindow]] = None
    routes: Optional[List[RouteAlternative]] = None
    route_comparison: Optional[RouteComparison] = None
    operational_recommendations: List[str] = Field(default_factory=list)
    executive_recommendation: Optional[str] = None
    provenance_run_id: Optional[str] = None

    @model_validator(mode="after")
    def sync_analysis(self) -> "MissionAnalysisResult":
        if self.station_windows is not None and self.station_accessibility is None:
            self.station_accessibility = self.station_windows
        elif self.station_accessibility is not None and self.station_windows is None:
            self.station_windows = self.station_accessibility

        if not self.executive_recommendation and self.operational_recommendations:
            self.executive_recommendation = self.operational_recommendations[0]
        return self
