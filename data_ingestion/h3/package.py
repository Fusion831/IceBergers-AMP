"""
Precomputed Frontend and Application Package Builder.
Coordinates static/dynamic partitioning and exports consolidated datasets under data/antarctica/.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
from core.logging import get_logger
from data_ingestion.h3.config import H3Config, default_h3_config
from data_ingestion.h3.grid import AntarcticH3GridGenerator
from data_ingestion.h3.static_layers import H3StaticLayerMapper
from data_ingestion.h3.iceberg import H3IcebergIndexer
from data_ingestion.h3.hazard import H3HazardMapper
from data_ingestion.h3.temporal import H3TemporalAligner
from data_ingestion.h3.provenance import CANONICAL_DATASET_PROVENANCE

logger = get_logger("data_ingestion.h3.package")


class H3PackageBuilder:
    """Orchestrates end-to-end building of the canonical H3 application package."""

    def __init__(self, config: Optional[H3Config] = None):
        self.config = config or default_h3_config
        self.grid_gen = AntarcticH3GridGenerator(config=self.config)
        self.static_mapper = H3StaticLayerMapper(config=self.config)
        self.iceberg_indexer = H3IcebergIndexer(config=self.config)
        self.hazard_mapper = H3HazardMapper(config=self.config)
        self.temporal_aligner = H3TemporalAligner(step_hours=self.config.temporal_step_hours)

    def build_full_package(self, sample_limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Builds and saves the complete canonical H3 package:
        1. Generates Antarctic domain cells
        2. Maps SCAR ADD & GEBCO static attributes
        3. Indexes all 73 iceberg observations and trajectories
        4. Indexes iceberg hazard field
        5. Generates canonical 6-hour time index
        6. Saves all manifests and lookup indices
        """
        logger.info("=== Starting AMIP Canonical H3 Package Build ===", resolution=self.config.resolution)
        self.config.ensure_directories()

        # 1. Generate domain cells
        all_cells = self.grid_gen.generate_domain_cells()
        if sample_limit is not None and sample_limit < len(all_cells):
            logger.info(f"Sampling {sample_limit} cells across domain latitudes for evaluation")
            stride = max(1, len(all_cells) // sample_limit)
            cells_to_process = all_cells[::stride][:sample_limit]
        else:
            cells_to_process = all_cells

        # 2. Static Layer Mapping
        cells_df, static_meta = self.static_mapper.generate_static_grid_table(cells_to_process)
        cells_pq, geojson_path, meta_path = self.static_mapper.save_static_grid(cells_df, static_meta)

        # 3. Iceberg Observations & Trajectories
        obs_df, obs_meta = self.iceberg_indexer.index_observations()
        traj_df, traj_meta = self.iceberg_indexer.index_trajectories()

        # 4. Iceberg Hazard
        hazard_df, hazard_meta = self.hazard_mapper.process_hazard_field()

        # 5. Canonical Time Index (e.g. 7-day forecast cycle)
        start_t = datetime(2026, 9, 4, 0, 0, tzinfo=timezone.utc)
        end_t = start_t + timedelta(days=7)
        canonical_times = self.temporal_aligner.generate_canonical_time_index(start_t, end_t)
        time_index_manifest = self.temporal_aligner.build_time_index_manifest(canonical_times, base_time=start_t)

        time_index_path = self.config.env_dir / "time_index.json"
        with open(time_index_path, "w", encoding="utf-8") as f:
            json.dump(time_index_manifest, f, indent=2)

        # 6. Lookup cell metadata summary
        lookup_dir = self.config.antarctica_root / "lookup"
        lookup_dir.mkdir(parents=True, exist_ok=True)
        lookup_path = lookup_dir / "cell_metadata.json"

        lookup_summary = {
            "h3_resolution": self.config.resolution,
            "total_canonical_cells": len(cells_df),
            "blocked_cells": int(cells_df["is_blocked"].sum()),
            "ocean_cells": int((cells_df["geographic_status"] == "OPEN_OCEAN").sum()),
            "all_73_icebergs_present": obs_meta["all_73_icebergs_present"],
            "distinct_iceberg_ids_count": obs_meta["distinct_iceberg_ids_count"],
            "hazard_distinct_cells": hazard_meta["distinct_cells_affected"],
            "dataset_provenance": CANONICAL_DATASET_PROVENANCE,
            "paths": {
                "cells_parquet": str(cells_pq.resolve()),
                "geometry_geojson": str(geojson_path.resolve()),
                "time_index": str(time_index_path.resolve()),
                "observations_parquet": str((self.config.iceberg_dir / "observations.parquet").resolve()),
                "trajectories_parquet": str((self.config.iceberg_dir / "trajectories.parquet").resolve()),
                "hazard_parquet": str((self.config.hazard_dir / "iceberg_hazard.parquet").resolve()),
            }
        }
        with open(lookup_path, "w", encoding="utf-8") as f:
            json.dump(lookup_summary, f, indent=2)

        logger.info("=== AMIP Canonical H3 Package Build Complete ===")
        return lookup_summary
