"""
Routing Engine Adapter for Vessel Performance Evaluation.
Integrates VesselPerformanceEvaluator with candidate H3 graph transitions
without altering internal search algorithms (A*, Dijkstra, etc.).
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Callable, Tuple
from vessel.models import VesselProfile
from vessel.evaluator import VesselPerformanceEvaluator, EdgeEvaluation
from vessel.config import get_sagar_kanya_profile


class VesselRoutingCostAdapter:
    """
    Supplies edge cost and feasibility callbacks to existing routers.
    Evaluates candidate H3 transitions against the dynamic environmental state at transition time.
    """

    def __init__(
        self,
        vessel: Optional[VesselProfile] = None,
        objective: str = "BALANCED",  # FASTEST, SAFEST, FUEL_EFFICIENT, SHORTEST, BALANCED
        evaluator: Optional[VesselPerformanceEvaluator] = None,
    ):
        self.vessel = vessel or get_sagar_kanya_profile()
        self.objective = objective.upper()
        self.evaluator = evaluator or VesselPerformanceEvaluator(vessel=self.vessel)

    def evaluate_edge(
        self,
        state_a: Any,
        state_b: Any,
        environment_at_time: Any,
        current_time: datetime,
        requested_speed_knots: Optional[float] = None,
    ) -> EdgeEvaluation:
        """
        Evaluates a candidate graph edge transition.
        """
        return self.evaluator.evaluate_transition(
            vessel=self.vessel,
            state_a=state_a,
            state_b=state_b,
            environment=environment_at_time,
            departure_time=current_time,
            requested_speed_knots=requested_speed_knots,
        )

    def calculate_edge_cost(
        self,
        edge_eval: EdgeEvaluation,
        objective: Optional[str] = None,
    ) -> float:
        """
        Computes a scalar objective cost for graph edge traversal based on physical diagnostics.
        If infeasible, returns float('inf').
        """
        if not edge_eval.feasible:
            return float("inf")

        obj = (objective or self.objective).upper()

        time_weight = 1.0
        fuel_weight = 0.0
        safety_penalty = 0.0

        # Incorporate soft warnings into safety cost
        if edge_eval.warnings:
            safety_penalty += len(edge_eval.warnings) * 1.5

        if edge_eval.sic is not None and edge_eval.sic > 0.0:
            safety_penalty += edge_eval.sic * 10.0

        if edge_eval.wave_height is not None and edge_eval.wave_height > 4.0:
            safety_penalty += (edge_eval.wave_height - 4.0) * 2.0

        if obj == "FASTEST":
            return edge_eval.travel_time_hours + (safety_penalty * 0.1)

        elif obj == "FUEL_EFFICIENT":
            # 1 MT of fuel ~ normalized cost equivalent to hours
            return (edge_eval.fuel_used * 10.0) + (edge_eval.travel_time_hours * 0.2) + (safety_penalty * 0.1)

        elif obj == "SAFEST":
            return (edge_eval.travel_time_hours * 0.5) + (safety_penalty * 5.0)

        elif obj == "SHORTEST":
            return edge_eval.distance_nm

        else:  # BALANCED
            return (
                (edge_eval.travel_time_hours * 1.0)
                + (edge_eval.fuel_used * 5.0)
                + (safety_penalty * 2.0)
            )
