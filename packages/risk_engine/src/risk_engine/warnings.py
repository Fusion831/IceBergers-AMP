"""Structured, machine-readable warning definitions for the AMIP Risk Engine."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RiskWarningCode(str, Enum):
    """Machine-readable risk and constraint warning identifiers."""
    GEOGRAPHIC_BLOCK = "GEOGRAPHIC_BLOCK"
    SHALLOW_WATER = "SHALLOW_WATER"
    BATHYMETRIC_GROUNDING = "BATHYMETRIC_GROUNDING"
    HIGH_SEA_ICE = "HIGH_SEA_ICE"
    CRITICAL_SEA_ICE = "CRITICAL_SEA_ICE"
    HIGH_ICEBERG_HAZARD = "HIGH_ICEBERG_HAZARD"
    CRITICAL_ICEBERG_HAZARD = "CRITICAL_ICEBERG_HAZARD"
    HIGH_WAVE = "HIGH_WAVE"
    CRITICAL_WAVE = "CRITICAL_WAVE"
    HIGH_WIND = "HIGH_WIND"
    CRITICAL_WIND = "CRITICAL_WIND"
    ADVERSE_CURRENT = "ADVERSE_CURRENT"
    LOW_DATA_CONFIDENCE = "LOW_DATA_CONFIDENCE"
    HIGH_SIC_UNCERTAINTY = "HIGH_SIC_UNCERTAINTY"
    EXTENDED_PROJECTION = "EXTENDED_PROJECTION"
    MOCK_SIC = "MOCK_SIC"
    MISSING_VARIABLES = "MISSING_VARIABLES"
    UNKNOWN_VESSEL_LIMIT = "UNKNOWN_VESSEL_LIMIT"


class RiskWarning(BaseModel):
    """Machine-readable warning instance with severity and details."""
    code: RiskWarningCode
    message: str
    severity: str = Field(default="WARNING", description="WARNING, CRITICAL, or INFO")
    variable: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None

    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message}"
