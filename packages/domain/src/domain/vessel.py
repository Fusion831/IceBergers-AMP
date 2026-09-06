"""Vessel Profile domain schema and default naval architecture parameters."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator
from domain.enums import IceClass


class FuelConsumptionParams(BaseModel):
    """Specific fuel oil consumption coefficients."""
    base_burn_rate_mt_per_day: float = Field(default=16.5, gt=0.0)
    auxiliary_burn_rate_mt_per_day: float = Field(default=2.5, ge=0.0)
    ice_resistance_power_factor: float = Field(default=1.8, ge=1.0)
    wave_resistance_factor: float = Field(default=1.2, ge=1.0)


class VesselProfile(BaseModel):
    """
    Naval architecture specifications for polar research vessels.
    Defaults to NCPOR's documented reference vessel ORV Sagar Kanya.
    All operational values are configurable and marked as provisional until verified.
    """
    vessel_id: str = Field(default="vessel-orv-sagar-kanya", description="Unique vessel profile ID")
    name: str = Field(default="ORV Sagar Kanya", description="Vessel name")
    length_m: float = Field(default=100.34, gt=0.0, description="Length overall in meters")
    length_meters: Optional[float] = None
    beam_m: float = Field(default=16.39, gt=0.0, description="Beam breadth in meters")
    beam_meters: Optional[float] = None
    draft_m: float = Field(default=5.60, gt=0.0, description="Maximum operating draft in meters")
    draft_meters: Optional[float] = None
    displacement_mt: float = Field(default=4180.0, gt=0.0, description="Displacement in metric tons")
    displacement_tonnes: Optional[float] = None
    ice_class: IceClass = Field(default=IceClass.ICE_CLASS_1B)
    cruising_speed_knots: float = Field(default=10.0, ge=4.0, le=18.0)
    service_speed_knots: Optional[float] = None
    max_speed_knots: float = Field(default=14.0, ge=6.0, le=24.0)
    endurance_days: int = Field(default=45, ge=5, le=120)
    max_navigable_sic: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Maximum permissible sea-ice concentration for safe transit",
    )
    under_keel_margin_m: float = Field(
        default=3.0,
        ge=0.5,
        description="Safety clearance required between keel and sea floor",
    )
    ice_clearance_depth_margin_m: Optional[float] = None
    fuel_params: FuelConsumptionParams = Field(default_factory=FuelConsumptionParams)
    is_verified_operational: bool = Field(
        default=False,
        description="False flags that specifications are provisional research estimates",
    )
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_vessel_fields(self) -> "VesselProfile":
        if self.draft_meters is not None:
            self.draft_m = self.draft_meters
        else:
            self.draft_meters = self.draft_m

        if self.length_meters is not None:
            self.length_m = self.length_meters
        else:
            self.length_meters = self.length_m

        if self.beam_meters is not None:
            self.beam_m = self.beam_meters
        else:
            self.beam_meters = self.beam_m

        if self.displacement_tonnes is not None:
            self.displacement_mt = self.displacement_tonnes
        else:
            self.displacement_tonnes = self.displacement_mt

        if self.service_speed_knots is not None:
            self.cruising_speed_knots = self.service_speed_knots
        else:
            self.service_speed_knots = self.cruising_speed_knots

        if self.ice_clearance_depth_margin_m is not None:
            self.under_keel_margin_m = self.ice_clearance_depth_margin_m
        else:
            self.ice_clearance_depth_margin_m = self.under_keel_margin_m
        return self

    @property
    def safe_clearance_depth_m(self) -> float:
        return self.draft_m + self.under_keel_margin_m

    @classmethod
    def get_sagar_kanya_default(cls) -> "VesselProfile":
        """Returns the standard documented reference vessel for NCPOR missions."""
        return cls()
