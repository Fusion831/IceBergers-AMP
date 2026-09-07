"""
H3 Spatial-Temporal Iceberg Hazard Mapping.
Quantifies ensemble trajectory occupancy across discrete H3 cells over time.
Outputs:
- data/antarctica/hazard/iceberg_hazard.parquet
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
from core.logging import get_logger
from data_ingestion.h3.config import H3Config, default_h3_config

logger = get_logger("data_ingestion.h3.hazard")


class H3HazardMapper:
    """
    Manages canonical H3 spatial hazard fields.
    Computes ensemble occupancy proxy across discrete cells and timestamps.
    """

    def __init__(self, config: Optional[H3Config] = None):
        self.config = config or default_h3_config

    def process_hazard_field(
        self,
        source_hazard_parquet: Optional[Path] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Loads and verifies canonical iceberg hazard dataset, ensuring cell_id normalization.
        """
        src = source_hazard_parquet or (self.config.data_root / "processed" / "iceberg" / "hazard" / "h3_iceberg_hazard.parquet")
        if not src.exists():
            raise FileNotFoundError(f"Source iceberg hazard dataset not found at {src}")

        df = pd.read_parquet(src)
        logger.info("Processing H3 iceberg hazard field", records=len(df))

        # Ensure canonical column names: cell_id and hazard_score
        if "h3_cell" in df.columns and "cell_id" not in df.columns:
            df["cell_id"] = df["h3_cell"]

        if "hazard" in df.columns and "hazard_score" not in df.columns:
            df["hazard_score"] = df["hazard"]

        # Ensure contributing_iceberg_ids is list or string
        if "active_icebergs" in df.columns and "contributing_iceberg_ids" not in df.columns:
            df["contributing_iceberg_ids"] = df["active_icebergs"]
        elif "contributing_icebergs" in df.columns and "contributing_iceberg_ids" not in df.columns:
            df["contributing_iceberg_ids"] = df["contributing_icebergs"]

        distinct_cells = int(df["cell_id"].nunique())
        max_hazard = float(df["hazard_score"].max()) if "hazard_score" in df.columns else 0.0

        metadata = {
            "h3_resolution": self.config.resolution,
            "total_hazard_records": len(df),
            "distinct_cells_affected": distinct_cells,
            "max_hazard_score": round(max_hazard, 4),
            "hazard_definition": "Ensemble trajectory spatial occupancy proxy [0.0, 1.0]",
            "collision_probability_distinction": "Iceberg hazard is an occupancy proxy, NOT a validated vessel collision probability.",
            "provenance": "AMIP Iceberg Trajectory Ensemble (73 icebergs, 90-day horizon)",
        }

        # Save to canonical destination: data/antarctica/hazard/iceberg_hazard.parquet
        self.config.ensure_directories()
        out_path = self.config.hazard_dir / "iceberg_hazard.parquet"
        df.to_parquet(out_path, index=False)
        logger.info("Saved canonical H3 iceberg hazard field", path=str(out_path), records=len(df), cells=distinct_cells)

        return df, metadata
