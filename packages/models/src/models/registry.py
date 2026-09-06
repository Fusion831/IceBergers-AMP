"""Model Registry and Artifact Loader."""
from pathlib import Path
from typing import Dict, Optional, Any
from core.config import settings
from core.logging import get_logger
from core.errors import ModelNotFoundError
from models.base import SeaIceModelInterface

logger = get_logger("models.registry")


class ModelRegistry:
    """Central registry and lazy-loader for ML models and baselines."""

    def __init__(self, models_dir: Optional[str] = None):
        self.models_dir = Path(models_dir or settings.MODELS_DIR)
        self._loaded_models: Dict[str, SeaIceModelInterface] = {}

    def register_model(self, model_id: str, model_instance: SeaIceModelInterface) -> None:
        """Explicitly registers a model instance in memory."""
        self._loaded_models[model_id] = model_instance
        logger.info(
            "Registered model in registry",
            model_id=model_id,
            name=model_instance.model_name,
            version=model_instance.version,
            is_mock=model_instance.is_mock,
        )

    def get_model(self, model_id: str = "default") -> SeaIceModelInterface:
        return self.get_sea_ice_model(model_id)

    def get_sea_ice_model(self, model_id: str = "default") -> SeaIceModelInterface:
        """
        Retrieves the requested sea-ice forecasting model.
        Falls back to MockSeaIceModel if in MOCK_MODE or if artifacts are not found.
        """
        if model_id in self._loaded_models:
            return self._loaded_models[model_id]

        # In Mock Mode, provide mock implementation
        if settings.MOCK_MODE or model_id in ("default", "mock", "AMIP-Mock-v1"):
            from models.sea_ice.mock_model import MockSeaIceModel
            mock_model = MockSeaIceModel()
            self._loaded_models[model_id] = mock_model
            return mock_model

        # Look for real artifact directory
        artifact_path = self.models_dir / "sea_ice" / model_id
        if not artifact_path.exists():
            logger.warning(
                "Model artifact path not found; falling back to MockSeaIceModel",
                path=str(artifact_path)
            )
            from models.sea_ice.mock_model import MockSeaIceModel
            mock_model = MockSeaIceModel()
            self._loaded_models[model_id] = mock_model
            return mock_model

        raise ModelNotFoundError(model_name="sea_ice", version=model_id)


model_registry = ModelRegistry()
