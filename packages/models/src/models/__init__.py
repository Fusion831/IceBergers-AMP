"""AMIP Models Package."""
from models.base import SeaIceModelInterface
from models.registry import ModelRegistry, model_registry
from models.sea_ice.mock_model import MockSeaIceModel
from models.sea_ice.baselines import (
    PersistenceBaseline,
    ClimatologyBaseline,
    compute_baseline_comparison,
)

__all__ = [
    "SeaIceModelInterface",
    "ModelRegistry",
    "model_registry",
    "MockSeaIceModel",
    "PersistenceBaseline",
    "ClimatologyBaseline",
    "compute_baseline_comparison",
]
