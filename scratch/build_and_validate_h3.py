"""
Driver script to build and validate the Canonical H3 Spatial Integration Package for AMIP.
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, ".")

from data_ingestion.h3.package import H3PackageBuilder
from data_ingestion.h3.validator import H3Validator
from data_ingestion.h3.config import default_h3_config

def main():
    print("=== Launching Canonical H3 Package Build ===")
    builder = H3PackageBuilder(config=default_h3_config)
    # Generate canonical package covering domain
    summary = builder.build_full_package(sample_limit=2000)
    print("\nPackage Build Summary:")
    print(json.dumps(summary, indent=2))

    print("\n=== Running H3 Validation Suite ===")
    validator = H3Validator(config=default_h3_config)
    val_rep = validator.run_all_validations()
    print(f"Validation Result: {val_rep['passed_checks']}/{val_rep['total_checks']} checks passed. (All passed: {val_rep['all_passed']})")

    print("\n=== Running Source Consistency Checks ===")
    sc_rep = validator.run_source_consistency_checks()
    print(f"Consistency Checks: {len(sc_rep['comparisons'])} source comparisons recorded.")

    print("\n=== Running Performance Benchmarks ===")
    bench_rep = validator.run_benchmarks()
    print(f"Latency: {bench_rep['point_to_cell_latency_us']} us/point -> Throughput: {bench_rep['point_to_cell_throughput_queries_per_sec']} queries/sec.")

if __name__ == "__main__":
    main()
