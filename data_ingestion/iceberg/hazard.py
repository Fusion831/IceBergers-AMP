"""
Time-dependent H3 spatial occupancy hazard generator for Antarctic icebergs.
Converts trajectory ensembles into dynamic spatial hazard proxies H(cell, t)
to feed into AMIP's unified environmental grid and risk engine.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from core.logging import get_logger
from data_ingestion.iceberg.metadata import (
    TrajectoryPoint,
    H3HazardCell,
    ForcingMode,
)

logger = get_logger("data_ingestion.iceberg.hazard")


class IcebergHazardFieldGenerator:
    """Generates time-dependent H3 spatial hazard fields from trajectory ensembles."""

    def __init__(self, model_version: str = "1.0.0"):
        self.model_version = model_version

    def generate_hazard_field(
        self,
        trajectory_points: List[TrajectoryPoint],
        total_ensemble_size: Optional[int] = None,
    ) -> List[H3HazardCell]:
        """
        Calculates cell occupancy fraction per simulation timestamp across all icebergs.
        """
        if not trajectory_points:
            return []

        # Group by (time, h3_cell)
        cell_time_groups: Dict[Any, List[TrajectoryPoint]] = {}
        distinct_ensembles_by_time: Dict[datetime, set] = {}

        for pt in trajectory_points:
            if not pt.h3_cell:
                continue
            key = (pt.time, pt.h3_cell)
            cell_time_groups.setdefault(key, []).append(pt)
            distinct_ensembles_by_time.setdefault(pt.time, set()).add((pt.iceberg_id, pt.ensemble_id))

        hazard_cells: List[H3HazardCell] = []

        for (sim_time, cell_id), points in cell_time_groups.items():
            # Get total active ensemble realizations at this timestamp
            total_realizations = total_ensemble_size or len(distinct_ensembles_by_time.get(sim_time, {1}))
            total_realizations = max(1, total_realizations)

            # Count unique ensemble realizations occupying this cell at sim_time
            occupying_realizations = len({(p.iceberg_id, p.ensemble_id) for p in points})
            occupancy_fraction = min(1.0, occupying_realizations / total_realizations)

            active_icebergs = sorted(list({p.iceberg_id for p in points}))
            forcing_mode = points[0].forcing_mode

            hazard_cells.append(
                H3HazardCell(
                    h3_cell=cell_id,
                    valid_time=sim_time,
                    hazard=round(occupancy_fraction, 4),
                    supporting_iceberg_count=len(active_icebergs),
                    ensemble_count=total_realizations,
                    active_icebergs=active_icebergs,
                    model_version=self.model_version,
                    forcing_mode=forcing_mode,
                    geographic_mask_mode="REAL",
                )
            )

        logger.info(
            "Generated H3 hazard field",
            total_hazard_records=len(hazard_cells),
            distinct_cells=len({c.h3_cell for c in hazard_cells}),
        )
        return hazard_cells

    def to_dataframe(self, hazard_cells: List[H3HazardCell]) -> pd.DataFrame:
        """Converts hazard cells to a pandas DataFrame."""
        rows = [
            {
                "h3_cell": c.h3_cell,
                "valid_time": c.valid_time,
                "hazard": c.hazard,
                "supporting_iceberg_count": c.supporting_iceberg_count,
                "ensemble_count": c.ensemble_count,
                "active_icebergs": ",".join(c.active_icebergs),
                "model_version": c.model_version,
                "forcing_mode": c.forcing_mode.value,
                "geographic_mask_mode": c.geographic_mask_mode,
            }
            for c in hazard_cells
        ]
        return pd.DataFrame(rows)
