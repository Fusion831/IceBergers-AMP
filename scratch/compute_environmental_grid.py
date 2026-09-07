"""
Driver script to compute and save unified dynamic environmental state (currents, waves, wind, SIC, bathymetry, hazard)
for canonical H3 cells.
"""

import sys
import json
sys.path.insert(0, ".")

from data_ingestion.h3.environmental_grid_builder import H3EnvironmentalGridBuilder

def main():
    print("=== Computing Unified Environmental State Across H3 Cells ===")
    builder = H3EnvironmentalGridBuilder()
    df_env, meta = builder.build_environmental_grid()
    print("\nComputation Metadata:")
    print(json.dumps(meta, indent=2))
    print(f"\nSuccessfully generated {len(df_env)} environment cell states!")
    print("\nSample records:")
    print(df_env[["cell_id", "current_speed_ms", "wind_speed_ms", "wave_height_m", "bathymetry_depth_m", "iceberg_hazard", "is_navigable"]].head(5).to_string())

if __name__ == "__main__":
    main()
