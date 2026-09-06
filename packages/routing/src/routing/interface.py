"""Abstract Interfaces for Route Optimization and 4D Route Validation."""
from abc import ABC, abstractmethod
from typing import List, Tuple
from domain.route import (
    RouteOptimizationRequest,
    RouteOptimizationResponse,
    RouteAlternative,
    RouteMetrics,
)
from domain.vessel import VesselProfile
from risk_engine.interface import RiskEngineInterface


class RouteOptimizerInterface(ABC):
    """
    Abstract interface for route optimization engines.
    Isolates routing algorithms (MockRouteOptimizer now; PolarRoute later) from MissionService.
    """

    @abstractmethod
    def optimize(self, request: RouteOptimizationRequest) -> RouteOptimizationResponse:
        """
        Calculates optimized route alternatives for the requested objectives.
        """
        pass


class RouteValidatorInterface(ABC):
    """
    Abstract interface for evaluating candidate routes against evolving 4D environmental risk R(x,y,t).
    """

    @abstractmethod
    def validate_4d(
        self,
        route: RouteAlternative,
        vessel: VesselProfile,
        risk_engine: RiskEngineInterface,
    ) -> RouteMetrics:
        """
        Evaluates a route trajectory against the time-varying risk field at each waypoint's ETA.
        """
        pass
