"""AMIP Canonical Domain Models and Schemas."""
from domain.constants import (
    CRS_WGS84,
    CRS_ANTARCTIC_POLAR_STEREOGRAPHIC,
    CAPE_TOWN_COORDS,
    BHARATI_STATION_COORDS,
    MAITRI_STATION_COORDS,
    ANTARCTIC_OPERATIONAL_BBOX,
)
from domain.enums import (
    RouteObjective,
    IceClass,
    HorizonTier,
    MissionStatus,
    JobStatus,
    MissionSeason,
    HorizonDay,
)
from domain.coordinates import GeoPoint, BoundingBox, GridSpec
from domain.vessel import VesselProfile, FuelConsumptionParams
from domain.mission import (
    Mission,
    MissionCreate,
    MissionPriorities,
    PlanningWindow,
    MissionDestination,
)
from domain.environment import (
    LayerMetadata,
    GridSlice,
    PointEnvironment,
    EnvironmentalState,
)
from domain.sea_ice import (
    SeaIceForecast,
    SeaIceUncertainty,
    SeaIcePredictionResult,
    SeaIceSkillMetrics,
    BaselineComparison,
)
from domain.iceberg import (
    IcebergObservation,
    IcebergSizeClass,
    IcebergTrajectoryStep,
    IcebergTrajectoryEnsemble,
    IcebergHazardField,
)
from domain.risk import (
    RiskWeightsConfig,
    RiskFactorAttribution,
    RiskField,
    PointRiskQuery,
)
from domain.route import (
    RouteWaypoint,
    RouteMetrics,
    RouteAlternative,
    RouteOptimizationRequest,
    RouteOptimizationResponse,
    RouteComparison,
)
from domain.analysis import (
    StationAccessibilityPoint,
    StationAccessibilityWindow,
    MissionAnalysisResult,
)
from domain.provenance import (
    ModelRunRecord,
    DatasetProvenance,
    JobProgress,
)

__all__ = [
    "CRS_WGS84",
    "CRS_ANTARCTIC_POLAR_STEREOGRAPHIC",
    "CAPE_TOWN_COORDS",
    "BHARATI_STATION_COORDS",
    "MAITRI_STATION_COORDS",
    "ANTARCTIC_OPERATIONAL_BBOX",
    "RouteObjective",
    "IceClass",
    "HorizonTier",
    "MissionStatus",
    "JobStatus",
    "GeoPoint",
    "BoundingBox",
    "GridSpec",
    "VesselProfile",
    "FuelConsumptionParams",
    "Mission",
    "MissionCreate",
    "MissionPriorities",
    "PlanningWindow",
    "LayerMetadata",
    "GridSlice",
    "PointEnvironment",
    "EnvironmentalState",
    "SeaIceForecast",
    "SeaIceUncertainty",
    "SeaIcePredictionResult",
    "SeaIceSkillMetrics",
    "BaselineComparison",
    "IcebergObservation",
    "IcebergTrajectoryStep",
    "IcebergTrajectoryEnsemble",
    "IcebergHazardField",
    "RiskWeightsConfig",
    "RiskFactorAttribution",
    "RiskField",
    "PointRiskQuery",
    "RouteWaypoint",
    "RouteMetrics",
    "RouteAlternative",
    "RouteOptimizationRequest",
    "RouteOptimizationResponse",
    "RouteComparison",
    "StationAccessibilityPoint",
    "StationAccessibilityWindow",
    "MissionAnalysisResult",
    "ModelRunRecord",
    "DatasetProvenance",
    "JobProgress",
]
