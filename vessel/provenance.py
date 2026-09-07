"""
Parameter provenance and classification definitions for AMIP vessel specifications.
"""

from enum import Enum
from typing import Any, Optional, Dict
from pydantic import BaseModel, Field


class ParameterClassification(str, Enum):
    """
    Authoritative classification for vessel parameters.
    Ensures speculative assumptions are never disguised as official specifications.
    """
    PUBLISHED = "PUBLISHED"            # Directly documented in authoritative NCPOR publications/tenders
    DERIVED = "DERIVED"                # Mathematically calculated from published parameters
    ASSUMED = "ASSUMED"                # Engineering estimate where authoritative data is not released
    USER_CONFIGURED = "USER_CONFIGURED"# Operational threshold adjustable by the mission planner
    UNKNOWN = "UNKNOWN"                # Explicitly uncertified or undocumented by the authority


class ParameterProvenance(BaseModel):
    """Container for a single vessel parameter with its classification and citation."""
    value: Any
    classification: ParameterClassification
    source: Optional[str] = None
    notes: Optional[str] = None
    confidence: Optional[str] = "HIGH"
    discrepancy_note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "classification": self.classification.value,
            "source": self.source,
            "notes": self.notes,
            "confidence": self.confidence,
            "discrepancy_note": self.discrepancy_note,
        }
