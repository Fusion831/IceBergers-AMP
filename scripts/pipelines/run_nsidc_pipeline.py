"""
Full End-to-End Run: Download sample NSIDC data, process, validate, and plot.
"""

from datetime import date
from pathlib import Path
import sys

# Ensure repository root and package paths are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
for pkg in (REPO_ROOT / "packages").glob("*/src"):
    sys.path.insert(0, str(pkg))

from data_ingestion.nsidc.downloader import NSIDCDownloader
from data_ingestion.nsidc.processor import NSIDCProcessor
from data_ingestion.nsidc.validator import NSIDCValidator
from data_ingestion.nsidc.interface import NSIDCSeaIceInterface

def main():
    print("=" * 70)
    print("STEP 1: Downloading Official Ancillary Reference Grid File")
    print("=" * 70)
    downloader = NSIDCDownloader(raw_data_dir="data/raw/nsidc/g02202")
    anc_path = downloader.download_ancillary()
    print(f"Ancillary file downloaded: {anc_path} (size: {anc_path.stat().st_size} bytes)")

    print("\n" + "=" * 70)
    print("STEP 2: Downloading Sample Daily Files (2024-01-01 to 2024-01-03)")
    print("=" * 70)
    daily_files = downloader.download_date_range(date(2024, 1, 1), date(2024, 1, 3))
    for f in daily_files:
        print(f"  Downloaded: {f.name} (size: {f.stat().st_size} bytes)")

    print("\n" + "=" * 70)
    print("STEP 3: Processing Raw Files to Georeferenced NetCDF")
    print("=" * 70)
    processor = NSIDCProcessor(
        processed_data_dir="data/processed/nsidc/g02202",
        ancillary_file_path=anc_path,
    )

    processed_files = []
    for raw_f in daily_files:
        proc_f = processor.process_file(raw_f)
        processed_files.append(proc_f)
        print(f"  Processed: {proc_f.name} -> {proc_f}")

    print("\n" + "=" * 70)
    print("STEP 4: Validating Processed Datasets")
    print("=" * 70)
    for proc_f in processed_files:
        report = NSIDCValidator.validate_dataset(proc_f)
        print(f"  Validation for {proc_f.name}: PASSED (bounds: {report['details']['spatial_bounds']})")

    print("\n" + "=" * 70)
    print("STEP 5: Generating Visual Validation Map")
    print("=" * 70)
    plot_path = Path("data/validation/nsidc/antarctica_sic_validation.png")
    saved_plot = NSIDCValidator.generate_validation_plot(processed_files[0], plot_path)
    print(f"  Saved Antarctic SIC Map: {saved_plot} (size: {saved_plot.stat().st_size} bytes)")

    print("\n" + "=" * 70)
    print("STEP 6: Testing Application-Level Query Interface")
    print("=" * 70)
    interface = NSIDCSeaIceInterface(processed_data_dir="data/processed/nsidc/g02202")

    test_points = [
        ("Open Southern Ocean", -55.0, 20.0),
        ("Pack Ice near Bharati", -69.4, 76.2),
        ("Heavy Pack in Weddell Sea", -73.0, -40.0),
        ("Continental Interior (Land)", -85.0, 0.0),
    ]

    query_date = date(2024, 1, 1)
    for name, lat, lon in test_points:
        sic = interface.get_sic(lat, lon, query_date)
        status = f"{sic:.1f}%" if sic is not None else "LAND / COAST (None)"
        print(f"  {name} ({lat}°N, {lon}°E): SIC = {status}")

    interface.close()
    print("\n" + "=" * 70)
    print("COMPLETE WORKFLOW FINISHED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
