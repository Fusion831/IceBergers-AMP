"""Mission configuration and lifecycle schemas."""

from datetime import datetime, timezone
from typing import List, Optional, Union
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator
from domain.coordinates import GeoPoint
from domain.enums import MissionStatus, MissionSeason
from domain.vessel import VesselProfile


class MissionPriorities(BaseModel):
    """User objective priorities for route and decision ranking."""
    safety: float = Field(default=0.5, ge=0.0, le=1.0)
    fuel: float = Field(default=0.3, ge=0.0, le=1.0)
    time: float = Field(default=0.2, ge=0.0, le=1.0)
    science: float = Field(default=0.1, ge=0.0, le=1.0)


class PlanningWindow(BaseModel):
    """Voyage planning time window."""
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    earliest_departure: Optional[datetime] = None
    latest_departure: Optional[datetime] = None
    latest_return: Optional[datetime] = None

    @model_validator(mode="after")
    def populate_window_aliases(self) -> "PlanningWindow":
        if self.start is None:
            self.start = self.earliest_departure or datetime.now(timezone.utc)
        if self.earliest_departure is None:
            self.earliest_departure = self.start
        if self.end is None:
            self.end = self.latest_return or (self.start + timedelta(days=60))
        if self.latest_return is None:
            self.latest_return = self.end
        if self.latest_departure is None:
            self.latest_departure = self.earliest_departure
        return self


from datetime import timedelta


class MissionDestination(BaseModel):
    """Destination station with coordinate and arrival preference."""
    station_name: str
    location: GeoPoint
    entry_corridor: Optional[GeoPoint] = None
    min_stay_days: int = Field(default=7, ge=1)
    preferred_arrival: Optional[datetime] = None

    @model_validator(mode="after")
    def populate_corridor(self) -> "MissionDestination":
        if self.entry_corridor is None:
            self.entry_corridor = GeoPoint(
                latitude=self.location.latitude + 2.0,
                longitude=self.location.longitude,
                name=f"{self.station_name} Entry Corridor",
            )
        return self


class MissionCreate(BaseModel):
    """Payload to configure a new Antarctic expedition planning scenario."""
    name: str = Field(..., min_length=3, max_length=255)
    expedition_code: Optional[str] = Field(default="ISEA-45")
    season: Optional[MissionSeason] = Field(default=MissionSeason.SUMMER_2026)
    description: Optional[str] = Field(default=None)
    origin: Optional[GeoPoint] = Field(
        default_factory=lambda: GeoPoint(latitude=-33.9249, longitude=18.4241, name="Cape Town")
    )
    destinations: List[MissionDestination] = Field(
        default_factory=lambda: [
            MissionDestination(
                station_name="Bharati",
                location=GeoPoint(latitude=-69.4072, longitude=76.1911, name="Bharati Station", station_code="BHARATI"),
            ),
            MissionDestination(
                station_name="Maitri",
                location=GeoPoint(latitude=-70.7670, longitude=11.7330, name="Maitri Station", station_code="MAITRI"),
            ),
        ]
    )
    planning_window: PlanningWindow
    vessel_id: Optional[str] = Field(default="vessel-orv-sagar-kanya")
    vessel_profile: Optional[VesselProfile] = Field(default_factory=VesselProfile)
    priorities: MissionPriorities = Field(default_factory=MissionPriorities)


class Mission(BaseModel):
    """Full mission domain entity."""
    id: str = Field(default_factory=lambda: f"msn-{uuid4().hex[:8]}")
    mission_id: Optional[str] = None
    name: str
    expedition_code: Optional[str] = "ISEA-45"
    season: Optional[MissionSeason] = MissionSeason.SUMMER_2026
    description: Optional[str] = None
    origin: Optional[GeoPoint] = Field(
        default_factory=lambda: GeoPoint(latitude=-33.9249, longitude=18.4241, name="Cape Town")
    )
    destinations: List[MissionDestination]
    planning_window: PlanningWindow
    vessel_id: Optional[str] = "vessel-orv-sagar-kanya"
    vessel_profile: Optional[VesselProfile] = Field(default_factory=VesselProfile)
    priorities: MissionPriorities = Field(default_factory=MissionPriorities)
    status: MissionStatus = Field(default=MissionStatus.DRAFT)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def sync_ids(self) -> "Mission":
        if not self.mission_id:
            self.mission_id = self.id
        return self
