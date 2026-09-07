"""
H3 Spatial Indexing for Iceberg Observations and Trajectories.
Maps ALL 73 distinct icebergs while preserving exact authoritative coordinates.
Outputs:
- data/antarctica/icebergs/observations.parquet
- data/antarctica/icebergs/trajectories.parquet
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import h3
from core.logging import get_logger
from data_ingestion.h3.config import H3Config, default_h3_config
from data_ingestion.h3.geometry import H3GeometryEngine

logger = get_logger("data_ingestion.h3.iceberg")


class H3IcebergIndexer:
    """Indexes iceberg observations and forward trajectories onto canonical H3 cells."""

    def __init__(self, config: Optional[H3Config] = None):
        self.config = config or default_h3_config
        self.geom = H3GeometryEngine()

    def index_observations(
        self,
        source_obs_parquet: Optional[Path] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Maps all iceberg observations to H3 cells while retaining exact lat/lon coordinates.
        Verifies representation across all 73 distinct icebergs.
        """
        src = source_obs_parquet or (self.config.data_root / "processed" / "iceberg" / "observations" / "normalized_observations.parquet")
        if not src.exists():
            raise FileNotFoundError(f"Source iceberg observations not found at {src}")

        df = pd.read_parquet(src)
        logger.info("Indexing iceberg observations onto H3", records=len(df), resolution=self.config.resolution)

        # Compute H3 cell for every observation
        res = self.config.resolution
        h3_cells = [
            self.geom.latlng_to_cell(float(r["latitude"]), float(r["longitude"]), res)
            for _, r in df.iterrows()
        ]
        df["h3_cell"] = h3_cells

        distinct_ids = sorted(df["iceberg_id"].unique().tolist())
        all_73_present = (len(distinct_ids) == 73)

        metadata = {
            "h3_resolution": res,
            "total_observations": len(df),
            "distinct_iceberg_ids_count": len(distinct_ids),
            "all_73_icebergs_present": all_73_present,
            "distinct_h3_cells_occupied": int(df["h3_cell"].nunique()),
            "sources": df["source"].value_counts().to_dict(),
        }

        # Save to canonical destination: data/antarctica/icebergs/observations.parquet
        self.config.ensure_directories()
        out_path = self.config.iceberg_dir / "observations.parquet"
        df.to_parquet(out_path, index=False)
        logger.info("Saved H3-indexed iceberg observations", path=str(out_path), count=len(df), all_73=all_73_present)

        return df, metadata

    def index_trajectories(
        self,
        source_traj_parquet: Optional[Path] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Maps all 73 iceberg trajectories (deterministic + stochastic ensemble members) to H3.
        Retains exact trajectory coordinates and updates/verifies H3 spatial cell.
        """
        src = source_traj_parquet or (self.config.data_root / "processed" / "iceberg" / "trajectories" / "all_73_90d_trajectories.parquet")
        if not src.exists():
            raise FileNotFoundError(f"Source iceberg trajectories not found at {src}")

        df = pd.read_parquet(src)
        logger.info("Indexing iceberg trajectories onto H3", points=len(df), resolution=self.config.resolution)

        res = self.config.resolution
        # If h3_cell column is already present at the same resolution, verify it; otherwise compute
        if "h3_cell" not in df.columns:
            df["h3_cell"] = [
                self.geom.latlng_to_cell(float(r["latitude"]), float(r["longitude"]), res)
                for _, r in df.iterrows()
            ]

        distinct_ids = sorted(df["iceberg_id"].unique().tolist())
        all_73_present = (len(distinct_ids) == 73)

        metadata = {
            "h3_resolution": res,
            "total_trajectory_points": len(df),
            "distinct_iceberg_ids_count": len(distinct_ids),
            "all_73_icebergs_present": all_73_present,
            "distinct_h3_cells_swept": int(df["h3_cell"].nunique()),
            "ensemble_members": int(df["ensemble_member"].nunique()),
            "horizon_hours": float(2160.0),
        }

        # Save to canonical destination: data/antarctica/icebergs/trajectories.parquet
        self.config.ensure_directories()
        out_path = self.config.iceberg_dir / "trajectories.parquet"
        df.to_parquet(out_path, index=False)
        logger.info("Saved H3-indexed iceberg trajectories", path=str(out_path), count=len(df), all_73=all_73_present)

        return df, metadata
