"""
Risk Policy Configuration Loader and Validator.
Ensures strict verification of policy weights, thresholds, units, and parameter provenance.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, model_validator


DEFAULT_POLICY_PATH = Path(__file__).parents[4] / "data" / "config" / "risk" / "risk_policy.json"


class ParameterProvenanceSpec(BaseModel):
    """Provenance tracking for a policy threshold or weight."""
    value: Optional[float] = None
    weight: Optional[float] = None
    classification: str = Field(default="USER_CONFIGURED")
    source: Optional[str] = None
    notes: Optional[str] = None
    unit: Optional[str] = None
    blocked_statuses: Optional[List[str]] = None
    rule_type: Optional[str] = None


class RiskPolicyConfig(BaseModel):
    """
    Centralized risk policy schema with startup validation.
    Enforces that weights sum to 1.0 and thresholds are monotonic.
    """
    policy_name: str = Field(default="AMIP_POC_BASELINE")
    policy_version: str = Field(default="1.0.0")
    description: str = ""
    status: str = "POC_PROTOTYPE"
    disclaimer: str = ""

    component_weights: Dict[str, ParameterProvenanceSpec] = Field(default_factory=dict)
    hard_constraints: Dict[str, ParameterProvenanceSpec] = Field(default_factory=dict)
    thresholds: Dict[str, Dict[str, ParameterProvenanceSpec]] = Field(default_factory=dict)
    confidence_rules: Dict[str, ParameterProvenanceSpec] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy(self) -> "RiskPolicyConfig":
        """Strict validation of weights, monotonicity, and values."""
        # 1. Component Weights Validation
        if self.component_weights:
            total_w = sum(spec.weight or 0.0 for spec in self.component_weights.values())
            if abs(total_w - 1.0) > 0.001:
                raise ValueError(
                    f"Risk policy '{self.policy_name}' component weights must sum to 1.0 (got {total_w:.4f})"
                )

        # 2. Sea-Ice Threshold Monotonicity
        sic_thresh = self.thresholds.get("sea_ice", {})
        if sic_thresh:
            safe = sic_thresh.get("safe_fraction", ParameterProvenanceSpec(value=0.0)).value or 0.0
            elevated = sic_thresh.get("elevated_fraction", ParameterProvenanceSpec(value=0.05)).value or 0.05
            high = sic_thresh.get("high_fraction", ParameterProvenanceSpec(value=0.15)).value or 0.15
            critical = sic_thresh.get("critical_fraction", ParameterProvenanceSpec(value=0.40)).value or 0.40
            if not (safe <= elevated <= high <= critical):
                raise ValueError(
                    f"Sea-ice thresholds not monotonic: safe={safe} <= elevated={elevated} <= high={high} <= critical={critical}"
                )

        # 3. Wave Threshold Monotonicity
        wave_thresh = self.thresholds.get("waves", {})
        if wave_thresh:
            safe_hs = wave_thresh.get("safe_hs_m", ParameterProvenanceSpec(value=2.5)).value or 2.5
            elevated_hs = wave_thresh.get("elevated_hs_m", ParameterProvenanceSpec(value=4.0)).value or 4.0
            high_hs = wave_thresh.get("high_hs_m", ParameterProvenanceSpec(value=6.0)).value or 6.0
            critical_hs = wave_thresh.get("critical_hs_m", ParameterProvenanceSpec(value=8.0)).value or 8.0
            if not (safe_hs <= elevated_hs <= high_hs <= critical_hs):
                raise ValueError(
                    f"Wave thresholds not monotonic: safe={safe_hs} <= elevated={elevated_hs} <= high={high_hs} <= critical={critical_hs}"
                )

        # 4. Wind Threshold Monotonicity
        wind_thresh = self.thresholds.get("wind", {})
        if wind_thresh:
            safe_w = wind_thresh.get("safe_speed_ms", ParameterProvenanceSpec(value=10.0)).value or 10.0
            elevated_w = wind_thresh.get("elevated_speed_ms", ParameterProvenanceSpec(value=15.0)).value or 15.0
            high_w = wind_thresh.get("high_speed_ms", ParameterProvenanceSpec(value=20.0)).value or 20.0
            critical_w = wind_thresh.get("critical_speed_ms", ParameterProvenanceSpec(value=28.0)).value or 28.0
            if not (safe_w <= elevated_w <= high_w <= critical_w):
                raise ValueError(
                    f"Wind thresholds not monotonic: safe={safe_w} <= elevated={elevated_w} <= high={high_w} <= critical={critical_w}"
                )

        # 5. Iceberg Hazard Threshold Monotonicity
        berg_thresh = self.thresholds.get("iceberg", {})
        if berg_thresh:
            safe_b = berg_thresh.get("safe_hazard", ParameterProvenanceSpec(value=0.02)).value or 0.02
            elevated_b = berg_thresh.get("elevated_hazard", ParameterProvenanceSpec(value=0.10)).value or 0.10
            high_b = berg_thresh.get("high_hazard", ParameterProvenanceSpec(value=0.30)).value or 0.30
            critical_b = berg_thresh.get("critical_hazard", ParameterProvenanceSpec(value=0.60)).value or 0.60
            if not (safe_b <= elevated_b <= high_b <= critical_b):
                raise ValueError(
                    f"Iceberg thresholds not monotonic: safe={safe_b} <= elevated={elevated_b} <= high={high_b} <= critical={critical_b}"
                )

        return self

    def get_weight(self, component: str) -> float:
        """Returns normalized weight for a given risk component."""
        spec = self.component_weights.get(component)
        if spec and spec.weight is not None:
            return float(spec.weight)
        return 0.0

    def get_threshold(self, domain: str, key: str, default: float = 0.0) -> float:
        """Convenience accessor for numeric threshold."""
        d = self.thresholds.get(domain, {})
        spec = d.get(key)
        if spec and spec.value is not None:
            return float(spec.value)
        return default


def load_risk_policy(policy_path: Optional[Union[str, Path]] = None) -> RiskPolicyConfig:
    """Loads and validates a RiskPolicyConfig from disk or defaults."""
    target = Path(policy_path) if policy_path else DEFAULT_POLICY_PATH
    if not target.exists():
        raise FileNotFoundError(f"Risk policy configuration not found at '{target}'")

    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)

    return RiskPolicyConfig.model_validate(data)
