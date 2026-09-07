"""
Standardized H3 Interface for Sea-Ice Machine Learning Subsystems.
Provides seamless pluggability for future ML models (Ice-kNN-South, ANTSIC-UNet)
without requiring architectural changes to the downstream grid, risk, or routing layers.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from data_ingestion.h3.schema import TemporalQualityStatus


class SeaIceForecastCell(BaseModel):
    """
    Normalized data contract for Sea-Ice Machine Learning model forecasts on H3 cells.
    Allows interchangeable consumption of Ice-kNN-South, ANTSIC-UNet, or physical persistence.
    """
    cell_id: str = Field(..., description="Canonical H3 cell index")
    valid_time: datetime = Field(..., description="Target forecast timestamp (UTC)")
    
    # Predicted Sea Ice Concentration
    sic: float = Field(..., ge=0.0, le=100.0, description="Predicted sea ice concentration % [0, 100]")
    sic_uncertainty: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="1-sigma uncertainty %")
    
    # Model Metadata
    model: str = Field(..., description="Model identifier, e.g. Ice-kNN-South, ANTSIC-UNet, or PersistenceBaseline")
    model_version: str = Field(default="1.0.0", description="Model training version or checkpoint tag")
    forecast_horizon_hours: float = Field(..., ge=0.0, description="Lead time in hours from forecast initialization")
    
    # Quality and provenance
    quality_status: TemporalQualityStatus = Field(default=TemporalQualityStatus.MODEL_PREDICTED)
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Input dataset attribution and run metadata")


class MockSeaIceMLProvider:
    """
    Mock ML forecast provider implementing the SeaIceForecastCell contract.
    Used for architectural validation while upstream models are being trained.
    """

    def __init__(self, model_name: str = "Ice-kNN-South-Mock", version: str = "0.1.0"):
        self.model_name = model_name
        self.version = version

    def predict_cell(
        self,
        cell_id: str,
        valid_time: datetime,
        base_sic: Optional[float] = None,
        lead_hours: float = 24.0,
    ) -> SeaIceForecastCell:
        """Generates a contract-compliant sea ice forecast for an H3 cell."""
        predicted_sic = base_sic if base_sic is not None else 15.0
        uncertainty = round(3.5 + 0.05 * lead_hours, 2)

        return SeaIceForecastCell(
            cell_id=cell_id,
            valid_time=valid_time,
            sic=round(predicted_sic, 2),
            sic_uncertainty=uncertainty,
            model=self.model_name,
            model_version=self.version,
            forecast_horizon_hours=lead_hours,
            quality_status=TemporalQualityStatus.MODEL_PREDICTED,
            provenance={
                "base_source": "NSIDC_G02202_v6",
                "inference_engine": "mock_pipeline",
            },
        )
