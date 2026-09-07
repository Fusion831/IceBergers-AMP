"""
Canonical Vessel Profile and Configuration Models for AMIP.
Provides generic, typed vessel representations supporting multi-vessel routing.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, model_validator
from vessel.provenance import ParameterClassification, ParameterProvenance


class VesselGeometry(BaseModel):
    """Hull dimensions and draft with parameter-level provenance."""
    length_overall_m: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=100.34, classification=ParameterClassification.PUBLISHED, source="NCPOR_PAGE"
        )
    )
    length_bp_m: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=89.0, classification=ParameterClassification.PUBLISHED, source="NCPOR_TENDER_2026"
        )
    )
    breadth_extreme_m: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=16.39, classification=ParameterClassification.PUBLISHED, source="NCPOR_PAGE"
        )
    )
    breadth_moulded_m: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=16.3, classification=ParameterClassification.PUBLISHED, source="NCPOR_TENDER_2026"
        )
    )
    maximum_draft_m: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=5.6, classification=ParameterClassification.PUBLISHED, source="NCPOR_PAGE & NCPOR_TENDER_2026"
        )
    )


class VesselTonnage(BaseModel):
    """Gross tonnage, deadweight, and displacement."""
    gross_tonnage: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=4888,
            classification=ParameterClassification.PUBLISHED,
            source="NCPOR_TENDER_2026",
            discrepancy_note="4888 GT (2026 tender) vs 4209 GRT (website)",
        )
    )
    deadweight_tonnes: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=796.0, classification=ParameterClassification.PUBLISHED, source="NCPOR_TENDER_2026"
        )
    )
    displacement_tonnes: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=4180.0, classification=ParameterClassification.DERIVED, source="Cb ~ 0.51 block coefficient estimate"
        )
    )


class VesselPropulsion(BaseModel):
    """Engine plant output and drive configuration."""
    engine_type: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value="Diesel-Electric Propulsion", classification=ParameterClassification.PUBLISHED, source="NCPOR_PAGE"
        )
    )
    engine_output_kw: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=2460.0, classification=ParameterClassification.PUBLISHED, source="NCPOR_TENDER_2026"
        )
    )


class VesselSpeedSpec(BaseModel):
    """Operational speed window."""
    cruise_speed_knots: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=9.0,
            classification=ParameterClassification.USER_CONFIGURED,
            source="Nominal operating point from 8-10 kn NCPOR range",
        )
    )
    min_operating_speed_knots: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=4.0, classification=ParameterClassification.ASSUMED, source="Steerageway engineering minimum"
        )
    )
    max_operating_speed_knots: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=12.0, classification=ParameterClassification.ASSUMED, source="Calm water sprint limit"
        )
    )


class VesselFuelSpec(BaseModel):
    """Bunker capacities, endurance, and reduced-order fuel model."""
    endurance_days: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=45, classification=ParameterClassification.PUBLISHED, source="NCPOR_PAGE & NCPOR_TENDER_2026"
        )
    )
    fuel_capacity_m3: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=433.0, classification=ParameterClassification.PUBLISHED, source="NCPOR_TENDER_2026"
        )
    )
    fuel_capacity_metric_tonnes: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=368.05, classification=ParameterClassification.DERIVED, source="Density 0.85 t/m3 MGO"
        )
    )
    model_type: str = "reduced_order_cubic_propulsion"
    model_status: str = "POC estimate (reduced-order cubic propulsion model + auxiliary hotel load)"
    nominal_propulsion_rate_mt_per_hour: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=0.28, classification=ParameterClassification.DERIVED, notes="~6.72 MT/day at nominal 9.0 kn"
        )
    )
    hotel_auxiliary_rate_mt_per_hour: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=0.06, classification=ParameterClassification.DERIVED, notes="~1.44 MT/day hotel/scientific load"
        )
    )


class VesselIceCapability(BaseModel):
    """
    Antarctic sea-ice capability specification.
    CRITICAL: Sagar Kanya has NO certified Polar Class; status is strictly UNKNOWN.
    """
    status: str = Field(default="UNKNOWN", description="Polar / Ice class status")
    classification: ParameterClassification = Field(default=ParameterClassification.UNKNOWN)
    source: str = Field(
        default="NCPOR official records contain no certified Polar Class (PC) or Finnish-Swedish Ice Class rating"
    )
    confidence: str = Field(default="HIGH_CONFIDENCE_OF_ABSENCE")
    notes: str = Field(
        default="Vessel is not an icebreaker. Operating in open pack (<15%) requires severe caution and user limits."
    )
    max_operational_sic: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=0.15,
            classification=ParameterClassification.USER_CONFIGURED,
            notes="Conservative 15% SIC open-pack limit",
        )
    )
    preferred_max_sic: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=0.05,
            classification=ParameterClassification.USER_CONFIGURED,
            notes="Preferred 5% open-water margin",
        )
    )


class EnvironmentalOperationalLimits(BaseModel):
    """Met-ocean thresholds and safety clearance."""
    max_safe_wave_height_m: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=6.0, classification=ParameterClassification.ASSUMED, notes="Hs threshold for mandatory course alteration"
        )
    )
    preferred_max_wave_height_m: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=4.0, classification=ParameterClassification.USER_CONFIGURED, notes="Standard operational sea state"
        )
    )
    max_operational_wind_speed_ms: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=20.0, classification=ParameterClassification.ASSUMED, notes="~39 knots Gale Force 8 limit"
        )
    )
    safety_under_keel_clearance_m: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value=3.0, classification=ParameterClassification.USER_CONFIGURED, notes="Safety clearance below draft"
        )
    )
    under_keel_rule: ParameterProvenance = Field(
        default_factory=lambda: ParameterProvenance(
            value="HARD_BLOCK",
            classification=ParameterClassification.USER_CONFIGURED,
            notes="Action on depth - draft < safety clearance",
        )
    )


class GeographicConstraints(BaseModel):
    """Hard geographic boundaries derived from authoritative SCAR ADD."""
    respect_scar_add_mask: bool = True
    blocked_statuses: List[str] = Field(default_factory=lambda: ["LAND", "ICE_SHELF", "ICE_TONGUE"])
    classification: ParameterClassification = ParameterClassification.PUBLISHED
    source: str = "SCAR Antarctic Digital Database v7.12"
    rule_type: str = "HARD_BLOCK"


class VesselProfile(BaseModel):
    """
    Generic, typed Vessel Profile abstraction for AMIP.
    Supports multi-vessel configurations loaded from data/config/vessels/<vessel_id>.json.
    """
    vessel_id: str = Field(default="orv_sagar_kanya", description="Unique vessel profile identifier")
    vessel_name: str = Field(default="ORV Sagar Kanya", description="Human-readable vessel name")
    callsign: str = Field(default="ATSK", description="Maritime callsign")
    vessel_type: str = Field(default="Oceanographic Research Vessel", description="Vessel classification")
    flag: str = Field(default="India")
    owner: str = Field(default="Ministry of Earth Sciences (MoES) / NCPOR")
    operator: str = Field(default="Shipping Corporation of India (SCI)")
    year_built: int = Field(default=1983)
    builder: str = Field(default="Schlichting Werft, Travemünde, Germany")

    geometry: VesselGeometry = Field(default_factory=VesselGeometry)
    tonnage: VesselTonnage = Field(default_factory=VesselTonnage)
    propulsion: VesselPropulsion = Field(default_factory=VesselPropulsion)
    speed: VesselSpeedSpec = Field(default_factory=VesselSpeedSpec)
    endurance_and_fuel: VesselFuelSpec = Field(default_factory=VesselFuelSpec)
    ice_capability: VesselIceCapability = Field(default_factory=VesselIceCapability)
    environmental_operational_limits: EnvironmentalOperationalLimits = Field(
        default_factory=EnvironmentalOperationalLimits
    )
    geographic_constraints: GeographicConstraints = Field(default_factory=GeographicConstraints)
    discrepancies: List[Dict[str, Any]] = Field(default_factory=list)

    # Convenience Properties for Fast Evaluator Access
    @property
    def length_m(self) -> float:
        return float(self.geometry.length_overall_m.value)

    @property
    def length_bp_m(self) -> float:
        return float(self.geometry.length_bp_m.value)

    @property
    def beam_m(self) -> float:
        return float(self.geometry.breadth_extreme_m.value)

    @property
    def draft_m(self) -> float:
        return float(self.geometry.maximum_draft_m.value)

    @property
    def gross_tonnage(self) -> float:
        return float(self.tonnage.gross_tonnage.value)

    @property
    def deadweight_t(self) -> float:
        return float(self.tonnage.deadweight_tonnes.value)

    @property
    def displacement_mt(self) -> float:
        return float(self.tonnage.displacement_tonnes.value)

    @property
    def displacement_tonnes(self) -> float:
        return float(self.tonnage.displacement_tonnes.value)

    @property
    def engine_power_kw(self) -> float:
        return float(self.propulsion.engine_output_kw.value)

    @property
    def cruising_speed_knots(self) -> float:
        return float(self.speed.cruise_speed_knots.value)

    @property
    def service_speed_knots(self) -> float:
        return self.cruising_speed_knots

    @property
    def min_speed_knots(self) -> float:
        return float(self.speed.min_operating_speed_knots.value)

    @property
    def max_speed_knots(self) -> float:
        return float(self.speed.max_operating_speed_knots.value)

    @property
    def endurance_days(self) -> int:
        return int(self.endurance_and_fuel.endurance_days.value)

    @property
    def fuel_capacity_m3(self) -> float:
        return float(self.endurance_and_fuel.fuel_capacity_m3.value)

    @property
    def fuel_capacity_mt(self) -> float:
        return float(self.endurance_and_fuel.fuel_capacity_metric_tonnes.value)

    @property
    def max_navigable_sic(self) -> float:
        return float(self.ice_capability.max_operational_sic.value)

    @property
    def under_keel_margin_m(self) -> float:
        return float(self.environmental_operational_limits.safety_under_keel_clearance_m.value)

    @property
    def safe_clearance_depth_m(self) -> float:
        return self.draft_m + self.under_keel_margin_m

    @property
    def max_wave_height_m(self) -> float:
        return float(self.environmental_operational_limits.max_safe_wave_height_m.value)

    @property
    def max_wind_speed_ms(self) -> float:
        return float(self.environmental_operational_limits.max_operational_wind_speed_ms.value)

    @property
    def loa_m(self) -> float:
        return self.length_m

    @property
    def cruise_speed_kn(self) -> float:
        return self.cruising_speed_knots

    @property
    def min_operating_speed_kn(self) -> float:
        return self.min_speed_knots

    @property
    def max_operating_speed_kn(self) -> float:
        return self.max_speed_knots

    @property
    def environmental_limits(self) -> EnvironmentalOperationalLimits:
        return self.environmental_operational_limits

    @property
    def fuel_model(self) -> VesselFuelSpec:
        return self.endurance_and_fuel

    @property
    def assumptions(self) -> List[Dict[str, Any]]:
        """Collects all vessel parameters marked as ASSUMED."""
        assumed_list = []
        # Check all models for ParameterClassification.ASSUMED
        submodels = [
            ("geometry", self.geometry),
            ("tonnage", self.tonnage),
            ("propulsion", self.propulsion),
            ("speed", self.speed),
            ("endurance_and_fuel", self.endurance_and_fuel),
            ("ice_capability", self.ice_capability),
            ("environmental_operational_limits", self.environmental_operational_limits),
        ]
        for group_name, sub in submodels:
            for field_name, val in sub:
                if isinstance(val, ParameterProvenance) and val.classification == ParameterClassification.ASSUMED:
                    assumed_list.append({
                        "group": group_name,
                        "parameter": field_name,
                        "value": val.value,
                        "source": val.source,
                        "notes": val.notes,
                    })
        return assumed_list

    @property
    def provenance_summary(self) -> Dict[str, Dict[str, str]]:
        """Maps each parameter to its classification and source."""
        summary = {}
        submodels = [
            ("geometry", self.geometry),
            ("tonnage", self.tonnage),
            ("propulsion", self.propulsion),
            ("speed", self.speed),
            ("endurance_and_fuel", self.endurance_and_fuel),
            ("ice_capability", self.ice_capability),
            ("environmental_operational_limits", self.environmental_operational_limits),
        ]
        for group_name, sub in submodels:
            summary[group_name] = {}
            for field_name, val in sub:
                if isinstance(val, ParameterProvenance):
                    summary[group_name][field_name] = {
                        "value": val.value,
                        "classification": val.classification.value,
                        "source": val.source or "",
                        "notes": val.notes or "",
                    }
        return summary

    def to_frontend_config(self) -> Dict[str, Any]:
        """
        Formats vessel parameters for the UI configuration panel.
        Explicitly distinguishes PUBLISHED, DERIVED, ASSUMED, USER_CONFIGURED, and UNKNOWN.
        Highlights which parameters are editable operational assumptions.
        """
        def _format_item(prov: ParameterProvenance, unit: str = "", editable: bool = False):
            return {
                "value": prov.value,
                "unit": unit,
                "classification": prov.classification.value,
                "is_editable": editable,
                "source": prov.source,
                "notes": prov.notes,
                "discrepancy_note": prov.discrepancy_note,
            }

        return {
            "vessel_id": self.vessel_id,
            "vessel_name": self.vessel_name,
            "vessel_type": self.vessel_type,
            "callsign": self.callsign,
            "owner": self.owner,
            "operator": self.operator,
            "groups": {
                "geometry": {
                    "label": "Hull Dimensions",
                    "fields": {
                        "length_overall_m": _format_item(self.geometry.length_overall_m, "m", False),
                        "length_bp_m": _format_item(self.geometry.length_bp_m, "m", False),
                        "breadth_extreme_m": _format_item(self.geometry.breadth_extreme_m, "m", False),
                        "breadth_moulded_m": _format_item(self.geometry.breadth_moulded_m, "m", False),
                        "maximum_draft_m": _format_item(self.geometry.maximum_draft_m, "m", False),
                    },
                },
                "tonnage_and_power": {
                    "label": "Tonnage & Propulsion Power",
                    "fields": {
                        "gross_tonnage": _format_item(self.tonnage.gross_tonnage, "GT", False),
                        "deadweight_tonnes": _format_item(self.tonnage.deadweight_tonnes, "MT", False),
                        "displacement_tonnes": _format_item(self.tonnage.displacement_tonnes, "MT", False),
                        "engine_type": _format_item(self.propulsion.engine_type, "", False),
                        "engine_output_kw": _format_item(self.propulsion.engine_output_kw, "kW", False),
                    },
                },
                "speed_preferences": {
                    "label": "Speed Profile & Preferences",
                    "fields": {
                        "cruise_speed_knots": _format_item(self.speed.cruise_speed_knots, "kn", True),
                        "min_operating_speed_knots": _format_item(self.speed.min_operating_speed_knots, "kn", True),
                        "max_operating_speed_knots": _format_item(self.speed.max_operating_speed_knots, "kn", True),
                    },
                },
                "endurance_and_fuel": {
                    "label": "Endurance & Fuel Capacity",
                    "fields": {
                        "endurance_days": _format_item(self.endurance_and_fuel.endurance_days, "days", False),
                        "fuel_capacity_m3": _format_item(self.endurance_and_fuel.fuel_capacity_m3, "m3", False),
                        "fuel_capacity_metric_tonnes": _format_item(self.endurance_and_fuel.fuel_capacity_metric_tonnes, "MT", False),
                        "nominal_propulsion_rate_mt_per_hour": _format_item(self.endurance_and_fuel.nominal_propulsion_rate_mt_per_hour, "MT/h", False),
                        "hotel_auxiliary_rate_mt_per_hour": _format_item(self.endurance_and_fuel.hotel_auxiliary_rate_mt_per_hour, "MT/h", False),
                    },
                },
                "ice_policy": {
                    "label": "Sea Ice Policy & Capability",
                    "fields": {
                        "ice_class_status": {
                            "value": self.ice_capability.status,
                            "classification": self.ice_capability.classification.value,
                            "source": self.ice_capability.source,
                            "notes": self.ice_capability.notes,
                            "is_editable": False,
                        },
                        "max_operational_sic": _format_item(self.ice_capability.max_operational_sic, "fraction", True),
                        "preferred_max_sic": _format_item(self.ice_capability.preferred_max_sic, "fraction", True),
                    },
                },
                "environmental_limits": {
                    "label": "Operational Metocean Limits",
                    "fields": {
                        "max_safe_wave_height_m": _format_item(self.environmental_operational_limits.max_safe_wave_height_m, "m", True),
                        "preferred_max_wave_height_m": _format_item(self.environmental_operational_limits.preferred_max_wave_height_m, "m", True),
                        "max_operational_wind_speed_ms": _format_item(self.environmental_operational_limits.max_operational_wind_speed_ms, "m/s", True),
                        "safety_under_keel_clearance_m": _format_item(self.environmental_operational_limits.safety_under_keel_clearance_m, "m", True),
                        "under_keel_rule": _format_item(self.environmental_operational_limits.under_keel_rule, "", True),
                    },
                },
            },
            "discrepancies": self.discrepancies,
        }

    @classmethod
    def get_sagar_kanya_default(cls) -> "VesselProfile":
        """Returns the standard documented reference vessel for NCPOR missions."""
        from vessel.config import get_sagar_kanya_profile
        return get_sagar_kanya_profile()

    def to_dict(self) -> Dict[str, Any]:
        """Serializes complete profile including all parameter provenance."""
        return self.model_dump()

