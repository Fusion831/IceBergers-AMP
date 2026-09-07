"""
Evaluate Sagar Kanya performance against 12 representative real H3 environmental states.
Reads actual Unified H3 x Time environment cells from data/antarctica/environment/environment_cells.parquet.
Produces a structured diagnostic table and saves it to docs/real_h3_evaluations_table.md.
"""

import math
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root and all package source directories to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
for p in [
    BASE_DIR,
    BASE_DIR / "packages" / "core" / "src",
    BASE_DIR / "packages" / "domain" / "src",
    BASE_DIR / "packages" / "data_access" / "src",
    BASE_DIR / "packages" / "models" / "src",
    BASE_DIR / "packages" / "iceberg_physics" / "src",
    BASE_DIR / "packages" / "risk_engine" / "src",
    BASE_DIR / "packages" / "routing" / "src",
    BASE_DIR / "packages" / "services" / "src",
    BASE_DIR / "apps" / "backend" / "src",
]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import pandas as pd


from vessel.config import get_sagar_kanya_profile
from vessel.evaluator import VesselPerformanceEvaluator, EdgeEvaluation
from vessel.inspector import format_transition_inspector


DATA_PARQUET = Path("data/antarctica/environment/environment_cells.parquet")
OUTPUT_MD = Path("docs/real_h3_evaluations_table.md")


def run_representative_evaluation():
    print(f"Loading real unified H3 environment cells from {DATA_PARQUET}...")
    df = pd.read_parquet(DATA_PARQUET)
    vessel = get_sagar_kanya_profile()
    evaluator = VesselPerformanceEvaluator(vessel=vessel)

    # Filter representative cells for the 12 conditions
    categories = {}

    # 1. Open Ocean (calm, deep, unblocked)
    open_sub = df[(df["geographic_status"] == "OPEN_OCEAN") & (df["wave_height_m"] < 3.0) & (df["bathymetry_depth_m"] > 3000) & (df["sea_ice_concentration"].isna() | (df["sea_ice_concentration"] == 0))]
    categories["Open Ocean (Baseline)"] = open_sub.iloc[0]

    # 2. Coastal / Mixed
    mixed_sub = df[df["geographic_status"] == "MIXED"]
    categories["Coastal / Mixed"] = mixed_sub.iloc[0] if len(mixed_sub) > 0 else df[df["ocean_fraction"] < 0.9].iloc[0]

    # 3. High SIC (Heavy pack ice > 50%)
    high_sic_sub = df[df["sea_ice_concentration"] > 50.0]
    categories["High SIC (Pack Ice)"] = high_sic_sub.iloc[0]

    # 4. Low SIC (Marginal open pack ice - lowest non-zero observed in dataset)
    low_sic_sub = df[df["sea_ice_concentration"] > 0.0].sort_values("sea_ice_concentration")
    categories["Low SIC (Marginal Pack)"] = low_sic_sub.iloc[0]


    # 5. High Wave (Hs > 5.0m)
    high_wave_sub = df[df["wave_height_m"] >= 5.0]
    categories["High Wave State (Rough)"] = high_wave_sub.iloc[0]

    # 6. Low Wave (Hs < 1.0m)
    low_wave_sub = df[df["wave_height_m"] < 1.0]
    categories["Low Wave State (Calm)"] = low_wave_sub.iloc[0]

    # 7. Strong Ocean Current (|V| > 0.5 m/s)
    strong_curr_sub = df[df["current_speed_ms"] > 0.5]
    categories["Strong Current"] = strong_curr_sub.iloc[0]

    # 8. Weak Ocean Current (|V| < 0.05 m/s)
    weak_curr_sub = df[df["current_speed_ms"] < 0.05]
    categories["Weak Current"] = weak_curr_sub.iloc[0]

    # 9. Deep Bathymetry (Depth > 4000m)
    deep_sub = df[df["bathymetry_depth_m"] > 4000.0]
    categories["Deep Bathymetry"] = deep_sub.iloc[0]

    # 10. Shallow Bathymetry (Depth < 50m / near grounding)
    shallow_sub = df[df["bathymetry_depth_m"] < 50.0]
    categories["Shallow Bathymetry"] = shallow_sub.iloc[0]

    # 11. Iceberg Hazard (hazard > 0.005)
    hz_sub = df[df["iceberg_hazard"] > 0.005]
    categories["Iceberg Hazard Exposure"] = hz_sub.iloc[0]

    # 12. Blocked SCAR ADD (Land or Ice Shelf)
    blocked_sub = df[df["is_blocked"] == True]
    categories["Blocked SCAR ADD Mask"] = blocked_sub.iloc[0]

    results = []
    dep_time = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)

    for cat_name, row in categories.items():
        cell_id = row["cell_id"]
        lat = float(row["centroid_lat"])
        lon = float(row["centroid_lon"])

        # Create adjacent target step (0.1 deg North)
        target_lat = lat + 0.1
        target_lon = lon

        env_dict = row.to_dict()
        edge_eval = evaluator.evaluate_transition(
            vessel=vessel,
            state_a={"centroid_lat": lat, "centroid_lon": lon},
            state_b={"centroid_lat": target_lat, "centroid_lon": target_lon, "cell_id": cell_id},
            environment=env_dict,
            departure_time=dep_time,
            requested_speed_knots=9.0,
        )

        inspector_data = format_transition_inspector(edge_eval, vessel, cell_id=cell_id)

        results.append({
            "category": cat_name,
            "cell_id": cell_id,
            "lat": lat,
            "lon": lon,
            "geo_status": row.get("geographic_status", "OPEN_OCEAN"),
            "depth_m": round(float(row["bathymetry_depth_m"]), 1) if pd.notnull(row.get("bathymetry_depth_m")) else None,
            "sic_pct": round(float(row["sea_ice_concentration"]), 1) if pd.notnull(row.get("sea_ice_concentration")) else 0.0,
            "hs_m": round(float(row["wave_height_m"]), 2) if pd.notnull(row.get("wave_height_m")) else None,
            "curr_spd_kn": round(float(row["current_speed_ms"]) * 1.94384, 2) if pd.notnull(row.get("current_speed_ms")) else None,
            "achievable_kn": edge_eval.achievable_speed_kn,
            "ground_kn": edge_eval.ground_speed_kn,
            "current_assist_kn": edge_eval.current_assistance_kn,
            "fuel_rate_mt_h": edge_eval.fuel_rate,
            "feasible": edge_eval.feasible,
            "blocking_reason": edge_eval.reason or "None",
            "warnings_count": len(edge_eval.warnings),
            "narrative": inspector_data["performance_narrative"],
        })

    # Build Markdown table
    lines = [
        "# Real H3 Environmental Conditions — ORV Sagar Kanya Performance Diagnostic Table",
        "",
        "Evaluated using the canonical **Unified H3 × Time Environment** (`data/antarctica/environment/environment_cells.parquet`).",
        "Reference vessel: **ORV Sagar Kanya** (LOA: 100.34m, Draft: 5.6m, Service Speed: 9.0 kn, Bunker: 433 m³ / 368 MT, Endurance: 45 days).",
        "",
        "| Category | H3 Cell ID | Coordinates (Lat, Lon) | Geo Status | Depth (m) | SIC (%) | Hs (m) | Current (kn) | Ground Spd (kn) | Fuel Rate (MT/h) | Feasible | Blocking Reason |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for r in results:
        depth_str = f"{r['depth_m']}m" if r['depth_m'] is not None else "N/A"
        hs_str = f"{r['hs_m']}m" if r['hs_m'] is not None else "N/A"
        curr_str = f"{r['curr_spd_kn']} kn" if r['curr_spd_kn'] is not None else "N/A"
        coord_str = f"{r['lat']:.2f}°, {r['lon']:.2f}°"
        feas_str = "**YES**" if r['feasible'] else "<span style='color:red'>**NO**</span>"
        reason_str = r['blocking_reason'] if r['blocking_reason'] != "None" else "—"

        lines.append(
            f"| **{r['category']}** | `{r['cell_id']}` | {coord_str} | {r['geo_status']} | {depth_str} | {r['sic_pct']}% | {hs_str} | {curr_str} | {r['ground_kn']} kn | {r['fuel_rate_mt_h']} | {feas_str} | {reason_str} |"
        )

    lines.extend([
        "",
        "## Performance Insights & Diagnostics",
        "",
    ])

    for r in results:
        lines.append(f"### {r['category']} (`{r['cell_id']}`)")
        lines.append(f"- **Environmental Context**: Depth: {r['depth_m']}m, SIC: {r['sic_pct']}%, Hs: {r['hs_m']}m, Current Assistance: {r['current_assist_kn']} kn.")
        lines.append(f"- **Vessel Response**: Achievable: {r['achievable_kn']} kn, Ground Speed: {r['ground_kn']} kn, Fuel Burn: {r['fuel_rate_mt_h']} MT/h.")
        lines.append(f"- **Feasibility**: {'Feasible' if r['feasible'] else 'Infeasible'} (Reason: {r['blocking_reason']}).")
        lines.append(f"- **Inspector Narrative**: {r['narrative']}")
        lines.append("")

    content = "\n".join(lines)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Successfully generated diagnostic table at {OUTPUT_MD}")
    return results


if __name__ == "__main__":
    run_representative_evaluation()
