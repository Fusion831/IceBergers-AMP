"""Risk Engine Interface definition."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Tuple
import numpy as np
from domain.coordinates import BoundingBox, GridSpec, GeoPoint
from domain.risk import RiskField, RiskWeightsConfig, RiskFactorAttribution
from domain.vessel import VesselProfile


class RiskEngineInterface(ABC):
    """Abstract interface for environmental risk calculation and factor attribution."""

    @abstractmethod
    def compute_risk_field(
        self,
        valid_time: datetime,
        lead_time_days: int,
        vessel: VesselProfile,
        weights: Optional[RiskWeightsConfig] = None,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
    ) -> Tuple[RiskField, np.ndarray, np.ndarray]:
        """
        Computes the composite 2D risk field R(x, y, t) and hard constraint impassable mask.
        Returns:
            RiskField metadata, composite_risk (2D array), impassable_mask (2D boolean array)
        """
        pass

    @abstractmethod
    def evaluate_point_risk(
        self,
        point: GeoPoint,
        timestamp: datetime,
        vessel: VesselProfile,
        weights: Optional[RiskWeightsConfig] = None,
    ) -> RiskFactorAttribution:
        """
        Evaluates local environmental hazard breakdown and dominant risk factor at a specific point.
        """
        pass
