"""
Runner script for end-to-end Antarctic Iceberg Trajectory Pipeline.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, "c:/Users/daksh/Projects/SIH2026")

from data_ingestion.iceberg.pipeline import IcebergTrajectoryPipeline

def main():
    print("=== Launching Iceberg Trajectory Pipeline for All 73 Icebergs ===")
    pipeline = IcebergTrajectoryPipeline()
    manifest = pipeline.run_pipeline(
        mode="auto",
        max_byu_files=40,          # 40 historical icebergs from BYU (42,431 records) + 33 USNIC = 73 icebergs
        target_icebergs_count=73,  # Run all 73 distinct icebergs
    )
    print("\n=== Pipeline Execution Finished ===")
    print("Manifest:")
    import json
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
