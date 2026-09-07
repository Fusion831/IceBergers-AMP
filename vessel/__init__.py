"""
AMIP Vessel Configuration and Performance Subsystem.
Implements naval architectural profiles, parameter provenance, and H3-coupled hydrodynamic/meteorological/cryospheric performance evaluation.
"""

from vessel.provenance import ParameterClassification, ParameterProvenance
from vessel.models import (
    VesselProfile,
    VesselGeometry,
    VesselTonnage,
    VesselPropulsion,
    VesselSpeedSpec,
    VesselFuelSpec,
    VesselIceCapability,
    EnvironmentalOperationalLimits,
    GeographicConstraints,
)
from vessel.config import (
    load_vessel_profile,
    get_sagar_kanya_profile,
    list_available_vessels,
    get_vessel_config_dir,
)
from vessel.fuel import FuelConsumptionModel, FuelRateResult
from vessel.constraints import VesselConstraintChecker, ConstraintResult
from vessel.evaluator import (
    VesselPerformanceEvaluator,
    EdgeEvaluation,
    evaluate_transition,
    evaluate_route_transitions,
    METERS_PER_NAUTICAL_MILE,
    MS_PER_KNOT,
)
from vessel.route_metrics import RoutePerformanceSummary, aggregate_route_metrics
from vessel.routing_adapter import VesselRoutingCostAdapter
from vessel.inspector import format_transition_inspector
from vessel.mission_nodes import (
    MaritimeAccessNode,
    CAPE_TOWN,
    BHARATI_MARITIME_ACCESS,
    MAITRI_MARITIME_ACCESS,
    MAITRI_INLAND_STATION,
    get_canonical_mission_transect,
    explain_maitri_node_selection,
)

__all__ = [
    "ParameterClassification",
    "ParameterProvenance",
    "VesselProfile",
    "VesselGeometry",
    "VesselTonnage",
    "VesselPropulsion",
    "VesselSpeedSpec",
    "VesselFuelSpec",
    "VesselIceCapability",
    "EnvironmentalOperationalLimits",
    "GeographicConstraints",
    "load_vessel_profile",
    "get_sagar_kanya_profile",
    "list_available_vessels",
    "get_vessel_config_dir",
    "FuelConsumptionModel",
    "FuelRateResult",
    "VesselConstraintChecker",
    "ConstraintResult",
    "VesselPerformanceEvaluator",
    "EdgeEvaluation",
    "evaluate_transition",
    "evaluate_route_transitions",
    "METERS_PER_NAUTICAL_MILE",
    "MS_PER_KNOT",
    "RoutePerformanceSummary",
    "aggregate_route_metrics",
    "VesselRoutingCostAdapter",
    "format_transition_inspector",
    "MaritimeAccessNode",
    "CAPE_TOWN",
    "BHARATI_MARITIME_ACCESS",
    "MAITRI_MARITIME_ACCESS",
    "MAITRI_INLAND_STATION",
    "get_canonical_mission_transect",
    "explain_maitri_node_selection",
]

