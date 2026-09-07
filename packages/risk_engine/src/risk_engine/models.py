"""
Canonical Data Models and Schemas for the AMIP Risk Engine.
Provides strongly-typed RiskProfile, RouteRiskProfile, RiskContext, and inspection interfaces.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, model_validator
from risk_engine.warnings import RiskWarning, RiskWarningCode


class RiskComponentScores(BaseModel):
    """Normalized individual risk components bounded to [0.0, 1.0]."""
    geographic_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    bathymetric_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    sea_ice_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    iceberg_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    wave_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    wind_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    current_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    data_quality_risk: float = Field(default=0.0, ge=0.0, le=1.0)


class DataQualityConfidence(BaseModel):
    """Data quality assessment and confidence score."""
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence_class: str = Field(default="HIGH", description="HIGH, MEDIUM, LOW, UNKNOWN")
    missing_variables: List[str] = Field(default_factory=list)
    quality_status: str = Field(default="OBSERVED")
    is_mock_sic: bool = False
    is_extended_projection: bool = False


class RiskContext(BaseModel):
    """
    Evaluation context encapsulating environmental state, vessel, transit, and policy.
    Heading and performance are optional (populated for transitions and routes).
    """
    environment: Any
    vessel: Optional[Any] = None
    vessel_performance: Optional[Any] = None
    policy: Optional[Any] = None
    timestamp: Optional[datetime] = None
    heading: Optional[float] = None
    cell_id: Optional[str] = None


class RiskProfile(BaseModel):
    """
    Canonical environmental risk evaluation for a discrete H3 cell or edge transition.
    Consumed by Router, Frontend Inspector, and Route Aggregator.
    """
    cell_id: str = Field(..., description="Canonical H3 spatial index")
    timestamp: datetime = Field(..., description="Valid timestamp of evaluation")

    # Hard Constraints vs Soft Risk
    hard_blocked: bool = Field(default=False, description="True if cell or transition is impassable")
    block_reason: Optional[str] = Field(default=None, description="Detailed explanation of blocking condition")
    blocking_rule: Optional[str] = Field(default=None, description="Policy rule identifier enforcing the block")

    # Composite & Confidence
    composite_risk: float = Field(default=0.0, ge=0.0, le=1.0, description="Weighted composite risk [0.0, 1.0]")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Overall confidence [0.0, 1.0]")
    confidence_class: str = Field(default="HIGH", description="HIGH, MEDIUM, LOW, UNKNOWN")

    # Decomposed Component Scores [0.0, 1.0]
    geographic_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    bathymetric_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    sea_ice_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    iceberg_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    wave_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    wind_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    current_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    data_quality_risk: float = Field(default=0.0, ge=0.0, le=1.0)

    # Physical Forcings Preserved (Never hidden behind scalars)
    SIC: Optional[float] = Field(default=None, description="Sea ice concentration fraction [0.0, 1.0]")
    SIC_uncertainty: Optional[float] = Field(default=None, description="Sea ice uncertainty fraction [0.0, 1.0]")
    iceberg_hazard: float = Field(default=0.0, ge=0.0, le=1.0, description="Iceberg ensemble occupancy hazard proxy")
    distinct_iceberg_count: int = Field(default=0, ge=0)
    contributing_iceberg_ids: List[str] = Field(default_factory=list)

    wave_height: Optional[float] = Field(default=None, description="Significant wave height Hs in meters")
    wave_period: Optional[float] = Field(default=None, description="Wave peak period Tp in seconds")
    wind_speed: Optional[float] = Field(default=None, description="Wind speed in m/s")
    current_speed: Optional[float] = Field(default=None, description="Current speed in m/s")
    current_direction: Optional[float] = Field(default=None, description="Current direction in degrees")
    current_assistance: Optional[float] = Field(default=None, description="Current assistance (+) or penalty (-) in knots if heading known")
    bathymetry_depth: Optional[float] = Field(default=None, description="Water depth positive in meters")
    clearance_m: Optional[float] = Field(default=None, description="Under-keel clearance in meters (depth - draft)")

    geographic_status: str = Field(default="OPEN_OCEAN")
    ocean_fraction: float = Field(default=1.0, ge=0.0, le=1.0)
    land_fraction: float = Field(default=0.0, ge=0.0, le=1.0)
    ice_shelf_fraction: float = Field(default=0.0, ge=0.0, le=1.0)

    # Machine-readable Warnings
    warnings: List[RiskWarning] = Field(default_factory=list)
    warning_codes: List[str] = Field(default_factory=list)

    # Provenance & Audit
    provenance: Dict[str, Any] = Field(default_factory=dict)
    policy_name: str = "AMIP_POC_BASELINE"
    policy_version: str = "1.0.0"
    model_version: str = "AMIP-RiskEngine-2026.1"

    @model_validator(mode="after")
    def sync_warning_codes(self) -> "RiskProfile":
        if self.warnings and not self.warning_codes:
            self.warning_codes = [w.code.value for w in self.warnings]
        return self

    def to_inspector_dict(self) -> Dict[str, Any]:
        """
        Formats risk breakdown for the Frontend Cell Inspector.
        Allows users to click any H3 cell and inspect complete risk decomposition.
        """
        return {
            "cell_id": self.cell_id,
            "timestamp": self.timestamp.isoformat() if hasattr(self.timestamp, "isoformat") else str(self.timestamp),
            "feasibility": {
                "hard_blocked": self.hard_blocked,
                "block_reason": self.block_reason,
                "blocking_rule": self.blocking_rule,
            },
            "composite": {
                "overall_risk": round(self.composite_risk, 4),
                "confidence_score": round(self.confidence_score, 4),
                "confidence_class": self.confidence_class,
            },
            "component_risks": {
                "geographic": round(self.geographic_risk, 4),
                "bathymetric": round(self.bathymetric_risk, 4),
                "sea_ice": round(self.sea_ice_risk, 4),
                "iceberg": round(self.iceberg_risk, 4),
                "wave": round(self.wave_risk, 4),
                "wind": round(self.wind_risk, 4),
                "current": round(self.current_risk, 4),
                "data_quality": round(self.data_quality_risk, 4),
            },
            "physical_forcings": {
                "sea_ice_concentration_fraction": self.SIC,
                "sea_ice_percentage": round(self.SIC * 100.0, 1) if self.SIC is not None else None,
                "sea_ice_uncertainty_fraction": self.SIC_uncertainty,
                "iceberg_hazard_proxy": round(self.iceberg_hazard, 4),
                "distinct_iceberg_count": self.distinct_iceberg_count,
                "contributing_iceberg_ids": self.contributing_iceberg_ids,
                "significant_wave_height_m": self.wave_height,
                "wave_peak_period_s": self.wave_period,
                "wind_speed_ms": self.wind_speed,
                "ocean_current_speed_ms": self.current_speed,
                "ocean_current_direction_deg": self.current_direction,
                "current_assistance_knots": self.current_assistance,
                "water_depth_m": self.bathymetry_depth,
                "under_keel_clearance_m": self.clearance_m,
                "geographic_status": self.geographic_status,
                "ocean_fraction": self.ocean_fraction,
                "land_fraction": self.land_fraction,
                "ice_shelf_fraction": self.ice_shelf_fraction,
            },
            "warnings": [
                {
                    "code": w.code.value if hasattr(w.code, "value") else str(w.code),
                    "message": w.message,
                    "severity": w.severity,
                }
                for w in self.warnings
            ],
            "warning_codes": self.warning_codes,
            "policy": {
                "policy_name": self.policy_name,
                "policy_version": self.policy_version,
                "model_version": self.model_version,
            },
            "provenance": self.provenance,
        }

    def to_h3_layer_dict(self) -> Dict[str, Any]:
        """Provides raw numeric values for H3 deck.gl / Mapbox layer styling."""
        return {
            "cell_id": self.cell_id,
            "composite_risk": self.composite_risk,
            "confidence_score": self.confidence_score,
            "geographic_risk": self.geographic_risk,
            "bathymetric_risk": self.bathymetric_risk,
            "sea_ice_risk": self.sea_ice_risk,
            "iceberg_risk": self.iceberg_risk,
            "wave_risk": self.wave_risk,
            "wind_risk": self.wind_risk,
            "current_risk": self.current_risk,
            "hard_blocked": self.hard_blocked,
        }


class RouteRiskProfile(BaseModel):
    """
    Cumulative and tail exposure risk profile for an entire evaluated route trajectory.
    Accounts for time spent in each state (dt-weighted integrals) and tail risk (P90, P95, P99).
    """
    total_duration_hours: float = Field(..., ge=0.0)
    segment_count: int = Field(..., ge=0)
    hard_block_count: int = Field(default=0, ge=0)

    # Risk Metrics
    mean_risk: float = Field(..., ge=0.0, le=1.0)
    max_risk: float = Field(..., ge=0.0, le=1.0)
    risk_integral: float = Field(..., ge=0.0, description="Time-weighted risk integral: sum(risk_i * dt_i) in risk*hours")
    time_weighted_mean_risk: float = Field(..., ge=0.0, le=1.0)

    # Tail Risk Exposure (Non-probabilistic descriptive statistics)
    p90_risk: float = Field(..., ge=0.0, le=1.0)
    p95_risk: float = Field(..., ge=0.0, le=1.0)
    p99_risk: float = Field(..., ge=0.0, le=1.0)

    high_risk_exposure_hours: float = Field(default=0.0, ge=0.0, description="Hours in states with composite_risk > 0.6")
    critical_exposure_hours: float = Field(default=0.0, ge=0.0, description="Hours in states with composite_risk > 0.8")

    # Time-Weighted Component Exposure (Integral R_comp * dt in comp*hours)
    sea_ice_exposure: float = Field(default=0.0, ge=0.0)
    iceberg_exposure: float = Field(default=0.0, ge=0.0)
    wave_exposure: float = Field(default=0.0, ge=0.0)
    wind_exposure: float = Field(default=0.0, ge=0.0)
    current_exposure: float = Field(default=0.0, ge=0.0)
    bathymetric_exposure: float = Field(default=0.0, ge=0.0)

    # Iceberg Specific Route Exposure
    total_iceberg_hazard_exposure: float = Field(default=0.0, ge=0.0, description="Integral of raw hazard * dt")
    max_iceberg_hazard: float = Field(default=0.0, ge=0.0, le=1.0)
    time_above_hazard_threshold_hours: float = Field(default=0.0, ge=0.0)
    distinct_icebergs_encountered: List[str] = Field(default_factory=list)
    distinct_iceberg_count: int = Field(default=0, ge=0)

    # Confidence Metrics
    mean_confidence: float = Field(..., ge=0.0, le=1.0)
    minimum_confidence: float = Field(..., ge=0.0, le=1.0)
    low_confidence_exposure_hours: float = Field(default=0.0, ge=0.0, description="Hours with confidence < 0.5")

    # Warnings Summary
    total_warnings_count: int = Field(default=0, ge=0)
    warning_code_summary: Dict[str, int] = Field(default_factory=dict)

    # Policy Context
    policy_name: str = "AMIP_POC_BASELINE"
    policy_version: str = "1.0.0"
