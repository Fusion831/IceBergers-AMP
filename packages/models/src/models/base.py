"""Abstract Model Interfaces for AMIP ML Model Serving."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
import numpy as np
from domain.coordinates import BoundingBox, GridSpec
from domain.sea_ice import SeaIcePredictionResult


class SeaIceModelInterface(ABC):
    """Abstract interface for all sea-ice forecasting models (Mock, Baselines, and future U-Net)."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the model (e.g. 'AMIP-UNet-v1', 'MockSeaIceModel')."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Version tag of the model."""
        pass

    @property
    @abstractmethod
    def is_mock(self) -> bool:
        """Whether this implementation is a mock or a real trained model."""
        pass

    @abstractmethod
    def predict(
        self,
        initialization_time: datetime,
        horizon_days: int,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
    ) -> SeaIcePredictionResult:
        """
        Generates a 2D gridded sea-ice concentration prediction and uncertainty bounds.
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Returns model metadata, input variables, training date, and checksums."""
        pass
