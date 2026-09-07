"""
Ice-kNN-South Service CLI & Serving Utilities.
Provides command-line inspection and forecast serving endpoints.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from ice_knn.inference import IceKNNInferenceService
from ice_knn.model import load_ice_knn_model


def serve_summary_cli(output_json: Optional[str] = None):
    svc = IceKNNInferenceService()
    summary = svc.get_forecast_summary()
    print("=== Ice-kNN-South Forecast Service Summary ===")
    print(json.dumps(summary, indent=2))
    if output_json:
        Path(output_json).parent.mkdir(parents=True, exist_ok=True)
        with open(output_json, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"Summary written to {output_json}")


def main():
    parser = argparse.ArgumentParser(description="AMIP Ice-kNN-South Service Runner")
    subparsers = parser.add_subparsers(dest="command")

    summary_parser = subparsers.add_parser("summary", help="Print forecast summary")
    summary_parser.add_argument("--out", type=str, default=None, help="Optional output JSON path")

    query_parser = subparsers.add_parser("query", help="Query SIC at lat/lon/time")
    query_parser.add_argument("--lat", type=float, required=True, help="Latitude (-90 to -45)")
    query_parser.add_argument("--lon", type=float, required=True, help="Longitude (0 to 360)")
    query_parser.add_argument("--lead-day", type=int, default=0, help="Lead day (0 to 89)")

    args = parser.parse_args()

    if args.command == "summary":
        serve_summary_cli(args.out)
    elif args.command == "query":
        svc = IceKNNInferenceService()
        res = svc.query_sic(args.lat, args.lon, time_target=args.lead_day)
        print(json.dumps(res, indent=2))
    else:
        # Default: print summary
        serve_summary_cli()


if __name__ == "__main__":
    main()
