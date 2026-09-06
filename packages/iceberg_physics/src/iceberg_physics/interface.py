from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Tuple
import numpy as np
from domain.coordinates import BoundingBox, GridSpec
from domain.iceberg import (
    IcebergObservation,
    IcebergTrajectoryEnsemble,
    IcebergHazardField,
)


class IcebergDriftEngineInterface(ABC):
    """Abstract interface for Lagrangian iceberg trajectory drift engines."""

    @abstractmethod
    def simulate(
        self,
        observations: List[IcebergObservation],
        simulation_start: datetime,
        horizon_days: int,
        ensemble_size: int = 50,
    ) -> List[IcebergTrajectoryEnsemble]:
        """
        Simulates future trajectory paths forward in time.
        Returns ensemble realizations, mean tracks, and 50%/90% probability corridor polygons.
        """
        pass


class IcebergHazardGeneratorInterface(ABC):
    """Abstract interface for converting trajectory ensembles into 2D spatial hazard fields."""

    @abstractmethod
    def generate_hazard_field(
        self,
        ensembles: List[IcebergTrajectoryEnsemble],
        valid_time: datetime,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
    ) -> Tuple[IcebergHazardField, np.ndarray]:
        """
        Converts trajectory positions at valid_time into a 2D spatial collision probability field H(x, y, t).
        """
        pass
