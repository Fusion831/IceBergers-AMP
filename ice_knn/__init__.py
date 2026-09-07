"""
AMIP Ice-kNN-South Package
Provides loading, serving, and H3 mapping for the trained Antarctic sea-ice concentration model.
"""

from ice_knn.model import IceKNNSouthModel, load_ice_knn_model
from ice_knn.inference import IceKNNInferenceService

__all__ = [
    "IceKNNSouthModel",
    "load_ice_knn_model",
    "IceKNNInferenceService",
]
