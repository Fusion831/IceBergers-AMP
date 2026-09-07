"""
CLI Inspection Utility for NOAA@NSIDC G02202 Sea-Ice Concentration NetCDF files.
Usage:
    python -m data_ingestion.nsidc.inspect <path_to_netcdf_file>
"""

import sys
from pathlib import Path

# Ensure repository root and package paths are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
for pkg in (REPO_ROOT / "packages").glob("*/src"):
    sys.path.insert(0, str(pkg))

from data_ingestion.nsidc.reader import NSIDCReader


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m data_ingestion.nsidc.inspect <path_to_netcdf_file>")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: File '{filepath}' does not exist.")
        sys.exit(1)

    print("=" * 70)
    print(f"NSIDC NetCDF Inspection: {filepath.name}")
    print("=" * 70)

    try:
        report = NSIDCReader.inspect_metadata(filepath)
    except Exception as e:
        print(f"Failed to inspect {filepath}: {e}")
        sys.exit(1)

    print(f"\n[File Size]: {report['file_size_bytes'] / (1024*1024):.3f} MB ({report['file_size_bytes']} bytes)")
    print(f"[Dimensions]: {report['dimensions']}")

    print("\n--- Data Variables ---")
    for name, info in report["data_variables"].items():
        print(f"  * {name}:")
        print(f"      shape: {info['shape']}, dtype: {info['dtype']}")
        attrs = info.get("attributes", {})
        if "long_name" in attrs:
            print(f"      long_name: {attrs['long_name']}")
        if "units" in attrs:
            print(f"      units: {attrs['units']}")
        if "valid_range" in attrs:
            print(f"      valid_range: {attrs['valid_range']}")

    print("\n--- Coordinate Variables ---")
    for name, info in report["coordinate_variables"].items():
        print(f"  * {name}:")
        print(f"      shape: {info['shape']}, dtype: {info['dtype']}")
        attrs = info.get("attributes", {})
        if "units" in attrs:
            print(f"      units: {attrs['units']}")

    print("\n--- Coordinate Reference System (CRS) ---")
    crs_info = report.get("crs_info", {})
    if crs_info:
        for k, v in crs_info.items():
            print(f"  {k}: {v}")
    else:
        print("  No 'crs' variable found.")

    print("\n--- Key Global Attributes ---")
    attrs = report.get("global_attributes", {})
    for key in [
        "title",
        "institution",
        "product_version",
        "spatial_resolution",
        "geospatial_bounds_crs",
        "source",
        "Conventions",
    ]:
        if key in attrs:
            print(f"  {key}: {attrs[key]}")

    print("=" * 70)


if __name__ == "__main__":
    main()
