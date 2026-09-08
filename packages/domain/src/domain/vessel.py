"""
Vessel Profile domain schema and authoritative naval architecture parameters.
Includes official NCPOR ORV Sagar Kanya specifications, provenance classifications,
and explicit configuration fields for AMIP routing.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, model_validator
from domain.enums import IceClass


class FuelConsumptionParams(BaseModel):
    """Specific fuel oil consumption coefficients."""
    base_burn_rate_mt_per_day: float = Field(default=6.72, gt=0.0, description="Calibrated propulsion burn at nominal cruise (DERIVED)")
    auxiliary_burn_rate_mt_per_day: float = Field(default=1.44, ge=0.0, description="Hotel and science lab electrical generator burn (DERIVED)")
    ice_resistance_power_factor: float = Field(default=2.5, ge=1.0, description="Quadratic ice resistance scaling")
    wave_resistance_factor: float = Field(default=1.2, ge=1.0, description="Wave resistance slowdown factor")
    sfoc_main_engine_g_kwh: float = Field(default=185.0, description="Specific fuel oil consumption in g/kWh")
    hotel_load_kw: float = Field(default=300.0, description="Continuous auxiliary hotel load in kW")


class VesselProfile(BaseModel):
    """
    Naval architecture specifications for polar research vessels.
    Authoritative reference: NCPOR / MoES documented vessel ORV Sagar Kanya.
    Distinguishes PUBLISHED specifications, DERIVED values, and USER_CONFIGURED thresholds.
    """
    vessel_id: str = Field(default="orv_sagar_kanya", description="Unique vessel profile ID")
    name: str = Field(default="ORV Sagar Kanya", description="Official vessel name (PUBLISHED)")
    length_m: float = Field(default=100.34, gt=0.0, description="Length overall (LOA) in meters (PUBLISHED)")
    length_meters: Optional[float] = None
    beam_m: float = Field(default=16.39, gt=0.0, description="Beam breadth extreme in meters (PUBLISHED)")
    beam_meters: Optional[float] = None
    draft_m: float = Field(default=5.60, gt=0.0, description="Maximum operating draft in meters (PUBLISHED)")
    draft_meters: Optional[float] = None
    displacement_mt: float = Field(default=4180.0, gt=0.0, description="Displacement in metric tonnes (DERIVED)")
    displacement_tonnes: Optional[float] = None
    ice_class: IceClass = Field(default=IceClass.ICE_CLASS_1B, description="Ice class rating (PROVISIONAL/UNKNOWN)")

    # Speed specifications
    cruising_speed_range_knots: List[float] = Field(
        default_factory=lambda: [8.0, 10.0],
        description="Official published cruising speed range 8-10 kt (PUBLISHED)",
    )
    cruising_speed_knots: float = Field(default=9.0, ge=4.0, le=18.0, description="Nominal cruise speed reference point (USER_CONFIGURED)")
    service_speed_knots: Optional[float] = None
    max_speed_knots: float = Field(default=12.0, ge=6.0, le=24.0, description="Sprint/maximum speed (ASSUMED)")
    configured_balanced_target_speed_kt: float = Field(
        default=7.5,
        description="Configured operating target speed for balanced routing (USER_CONFIGURED / MODELLED)",
    )

    # Endurance and fuel
    endurance_days: int = Field(default=45, ge=5, le=120, description="Published continuous voyage endurance in days (PUBLISHED)")
    endurance_days_published: int = Field(default=45, description="Official published endurance limit (PUBLISHED)")
    fuel_capacity_m3: float = Field(default=433.0, description="Total usable Marine Gas Oil bunker capacity in m³ (PUBLISHED)")
    fuel_density_assumption: float = Field(
        default=0.85,
        description="MGO fuel density assumption at 15°C in t/m³ for mass calculation (DERIVED)",
    )
    fuel_capacity_metric_tonnes_derived: float = Field(
        default=368.05,
        description="Derived mass equivalent capacity: 433.0 m³ * 0.85 t/m³ = 368.05 MT (DERIVED)",
    )

    # Operational environmental limits
    configured_operational_sic_limit: float = Field(
        default=0.15,
        description="Configured operational sea-ice concentration limit (15%) for open water transit (USER_CONFIGURED)",
    )
    max_navigable_sic: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Maximum permissible sea-ice concentration for safe transit (USER_CONFIGURED)",
    )
    under_keel_margin_m: float = Field(
        default=3.0,
        ge=0.5,
        description="Safety clearance required between keel and sea floor (USER_CONFIGURED)",
    )
    ice_clearance_depth_margin_m: Optional[float] = None

    fuel_params: FuelConsumptionParams = Field(default_factory=FuelConsumptionParams)
    is_verified_operational: bool = Field(
        default=True,
        description="Specifications audited against NCPOR 2026 Fleet tender documentation",
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

        if self.max_navigable_sic is not None:
            self.configured_operational_sic_limit = self.max_navigable_sic
        return self

    @property
    def safe_clearance_depth_m(self) -> float:
        return self.draft_m + self.under_keel_margin_m

    @classmethod
    def get_sagar_kanya_default(cls) -> "VesselProfile":
        """Returns the authoritative ORV Sagar Kanya profile."""
        return cls()
