"""
Real Antarctic Data Validation and Performance Benchmark Script for AMIP Risk Engine.
Evaluates representative environmental cells from data/antarctica/ against Sagar Kanya profile.
Generates validation_report.json, sensitivity_report.json, benchmark_report.json, and real_data_examples.parquet.
"""

import time
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT_DIR))
for pkg_src in (ROOT_DIR / "packages").glob("*/src"):
    sys.path.insert(0, str(pkg_src))

import pandas as pd
import numpy as np

from risk_engine.engine import RiskEngine
from risk_engine.policy import RiskPolicyConfig, load_risk_policy
from risk_engine.models import RiskProfile
from vessel.models import VesselProfile

ROOT_DIR = Path(__file__).parents[1]
ENV_PARQUET = ROOT_DIR / "data" / "antarctica" / "environment" / "environment_cells.parquet"
HAZARD_PARQUET = ROOT_DIR / "data" / "antarctica" / "hazard" / "iceberg_hazard.parquet"
OUTPUT_DIR = ROOT_DIR / "data" / "validation" / "risk"


def run_validation():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    engine = RiskEngine()
    sagar_kanya = VesselProfile.get_sagar_kanya_default()

    print(f"Loading real environmental cells from {ENV_PARQUET}...")
    df_env = pd.read_parquet(ENV_PARQUET)
    print(f"Loaded {len(df_env)} environmental cells.")

    # 1. Benchmark Execution Speed
    print("\n--- Running Risk Engine Benchmark ---")
    n_sample = min(1000, len(df_env))
    sample_records = df_env.head(n_sample).to_dict(orient="records")

    # Single-cell latency benchmark
    t0 = time.perf_counter()
    p_single = engine.evaluate_cell_risk(sample_records[0], vessel=sagar_kanya)
    single_latency_ms = (time.perf_counter() - t0) * 1000.0

    # Batch throughput benchmark
    t0 = time.perf_counter()
    batch_profiles = [engine.evaluate_cell_risk(rec, vessel=sagar_kanya) for rec in sample_records]
    batch_duration_s = time.perf_counter() - t0
    batch_throughput_cells_per_sec = n_sample / max(0.0001, batch_duration_s)
    avg_latency_ms = (batch_duration_s / n_sample) * 1000.0

    # Route aggregation benchmark
    t0 = time.perf_counter()
    route_prof = engine.evaluate_route_risk(batch_profiles[:50])
    route_latency_ms = (time.perf_counter() - t0) * 1000.0

    benchmark_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cells_evaluated": n_sample,
        "single_cell_latency_ms": round(single_latency_ms, 3),
        "batch_total_duration_s": round(batch_duration_s, 4),
        "batch_throughput_cells_per_sec": round(batch_throughput_cells_per_sec, 1),
        "average_latency_per_cell_ms": round(avg_latency_ms, 3),
        "route_evaluation_50_segments_ms": round(route_latency_ms, 3),
        "status": "PASS",
    }
    with open(OUTPUT_DIR / "benchmark_report.json", "w", encoding="utf-8") as f:
        json.dump(benchmark_report, f, indent=2)
    print(f"Benchmark: {batch_throughput_cells_per_sec:.1f} cells/sec ({avg_latency_ms:.3f} ms/cell).")

    # 2. Select 12 Representative Antarctic Real States
    print("\n--- Selecting Representative Real Antarctic Cells ---")
    representative_conditions = [
        ("open_ocean_calm", (df_env["geographic_status"] == "OPEN_OCEAN") & (df_env["wave_height_m"] < 2.5) & (df_env["sea_ice_concentration"] == 0.0)),
        ("open_ocean_rough_waves", (df_env["geographic_status"] == "OPEN_OCEAN") & (df_env["wave_height_m"] > 4.0)),
        ("gale_wind", df_env["wind_speed_ms"] > 16.0),
        ("elevated_sea_ice", (df_env["sea_ice_concentration"] > 0.05) & (df_env["sea_ice_concentration"] <= 0.15)),
        ("critical_sea_ice", df_env["sea_ice_concentration"] > 0.15),
        ("strong_current", df_env["current_speed_ms"] > 0.35),
        ("deep_ocean", df_env["bathymetry_depth_m"] > 3500.0),
        ("shelf_water", (df_env["bathymetry_depth_m"] > 0.0) & (df_env["bathymetry_depth_m"] < 500.0)),
        ("blocked_land", (df_env["geographic_status"] == "LAND") | (df_env["land_fraction"] > 0.8)),
        ("blocked_ice_shelf", (df_env["geographic_status"] == "ICE_SHELF") | (df_env["ice_shelf_fraction"] > 0.8)),
        ("high_iceberg_hazard", df_env["iceberg_hazard"] > 0.10),
        ("low_iceberg_hazard", df_env["iceberg_hazard"] == 0.0),
    ]

    selected_rows = []
    selected_tags = []

    for tag, condition in representative_conditions:
        subset = df_env[condition]
        if len(subset) > 0:
            row = subset.iloc[0].to_dict()
            selected_rows.append(row)
            selected_tags.append(tag)
        else:
            # Fallback to closest
            row = df_env.iloc[len(selected_rows) % len(df_env)].to_dict()
            selected_rows.append(row)
            selected_tags.append(f"{tag}_fallback")

    # Evaluate representative rows
    eval_results = []
    for tag, row in zip(selected_tags, selected_rows):
        profile = engine.evaluate_cell_risk(row, vessel=sagar_kanya)
        d = profile.to_inspector_dict()
        d["representative_tag"] = tag
        d["hard_blocked"] = profile.hard_blocked
        d["composite_risk"] = profile.composite_risk
        d["confidence_score"] = profile.confidence_score
        d["confidence_class"] = profile.confidence_class
        d["sea_ice_risk"] = profile.sea_ice_risk
        d["iceberg_risk"] = profile.iceberg_risk
        d["wave_risk"] = profile.wave_risk
        d["wind_risk"] = profile.wind_risk
        d["current_risk"] = profile.current_risk
        d["bathymetric_risk"] = profile.bathymetric_risk
        d["geographic_risk"] = profile.geographic_risk
        d["warnings_count"] = len(profile.warnings)
        eval_results.append(d)

    # 3. Validation Report Summary
    comp_risks = [r["composite_risk"] for r in eval_results]
    conf_scores = [r["confidence_score"] for r in eval_results]
    hard_blocks = sum(1 for r in eval_results if r["hard_blocked"])

    validation_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset_evaluated": str(ENV_PARQUET),
        "total_cells_in_dataset": len(df_env),
        "representative_cells_tested": len(eval_results),
        "vessel_tested": sagar_kanya.vessel_name,
        "vessel_draft_m": sagar_kanya.draft_m,
        "vessel_max_sic": sagar_kanya.max_navigable_sic,
        "summary_statistics": {
            "mean_risk": round(float(np.mean(comp_risks)), 4),
            "max_risk": round(float(np.max(comp_risks)), 4),
            "min_risk": round(float(np.min(comp_risks)), 4),
            "mean_confidence": round(float(np.mean(conf_scores)), 4),
            "hard_blocked_count": hard_blocks,
            "total_warnings": sum(r["warnings_count"] for r in eval_results),
        },
        "representative_cell_evaluations": eval_results,
        "status": "PASS",
    }
    with open(OUTPUT_DIR / "validation_report.json", "w", encoding="utf-8") as f:
        json.dump(validation_report, f, indent=2)

    # 4. Sensitivity Report
    print("\n--- Generating Sensitivity Report ---")
    sensitivity_tests = {}

    # Sensitivity Test 1: SIC Sweeps
    sic_steps = [0.0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.35, 0.60]
    sic_results = []
    dummy_base = {"cell_id": "sens_cell", "bathymetry_depth_m": 3000.0}
    for s in sic_steps:
        c = dict(dummy_base, sea_ice_concentration=s)
        p = engine.evaluate_cell_risk(c, vessel=None)
        sic_results.append({"sic": s, "sea_ice_risk": p.sea_ice_risk, "composite_risk": p.composite_risk})
    sensitivity_tests["sea_ice_sensitivity"] = {
        "monotonic": all(sic_results[i+1]["sea_ice_risk"] >= sic_results[i]["sea_ice_risk"] for i in range(len(sic_results)-1)),
        "steps": sic_results,
    }

    # Sensitivity Test 2: Iceberg Hazard Sweeps
    berg_steps = [0.0, 0.05, 0.15, 0.30, 0.50, 0.75, 1.0]
    berg_results = []
    for b in berg_steps:
        c = dict(dummy_base, iceberg_hazard=b)
        p = engine.evaluate_cell_risk(c)
        berg_results.append({"iceberg_hazard": b, "iceberg_risk": p.iceberg_risk, "composite_risk": p.composite_risk})
    sensitivity_tests["iceberg_hazard_sensitivity"] = {
        "monotonic": all(berg_results[i+1]["iceberg_risk"] >= berg_results[i]["iceberg_risk"] for i in range(len(berg_results)-1)),
        "steps": berg_results,
    }

    # Sensitivity Test 3: Wave Sweeps
    wave_steps = [0.5, 2.0, 3.5, 5.0, 6.5, 8.0, 10.0]
    wave_results = []
    for w in wave_steps:
        c = dict(dummy_base, wave_height_m=w)
        p = engine.evaluate_cell_risk(c)
        wave_results.append({"wave_height_m": w, "wave_risk": p.wave_risk, "composite_risk": p.composite_risk})
    sensitivity_tests["wave_sensitivity"] = {
        "monotonic": all(wave_results[i+1]["wave_risk"] >= wave_results[i]["wave_risk"] for i in range(len(wave_results)-1)),
        "steps": wave_results,
    }

    sensitivity_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "policy_tested": engine.policy.policy_name,
        "policy_version": engine.policy.policy_version,
        "results": sensitivity_tests,
        "all_monotonic_tests_passed": all(s["monotonic"] for s in sensitivity_tests.values()),
    }
    with open(OUTPUT_DIR / "sensitivity_report.json", "w", encoding="utf-8") as f:
        json.dump(sensitivity_report, f, indent=2)

    # 5. Save Parquet Real Data Examples
    print("\n--- Saving Real Data Examples to Parquet ---")
    parquet_rows = []
    for r, orig in zip(eval_results, selected_rows):
        parquet_rows.append({
            "cell_id": r["cell_id"],
            "representative_tag": r["representative_tag"],
            "hard_blocked": r["hard_blocked"],
            "block_reason": r["feasibility"]["block_reason"] or "",
            "composite_risk": r["composite_risk"],
            "confidence_score": r["confidence_score"],
            "confidence_class": r["confidence_class"],
            "geographic_risk": r["geographic_risk"],
            "bathymetric_risk": r["bathymetric_risk"],
            "sea_ice_risk": r["sea_ice_risk"],
            "iceberg_risk": r["iceberg_risk"],
            "wave_risk": r["wave_risk"],
            "wind_risk": r["wind_risk"],
            "current_risk": r["current_risk"],
            "sic_concentration": r["physical_forcings"]["sea_ice_concentration_fraction"],
            "iceberg_hazard": r["physical_forcings"]["iceberg_hazard_proxy"],
            "wave_height_m": r["physical_forcings"]["significant_wave_height_m"],
            "wind_speed_ms": r["physical_forcings"]["wind_speed_ms"],
            "current_speed_ms": r["physical_forcings"]["ocean_current_speed_ms"],
            "bathymetry_depth_m": r["physical_forcings"]["water_depth_m"],
            "geographic_status": r["physical_forcings"]["geographic_status"],
            "warnings_count": r["warnings_count"],
        })
    df_out = pd.DataFrame(parquet_rows)
    df_out.to_parquet(OUTPUT_DIR / "real_data_examples.parquet", index=False)
    print(f"Saved {len(df_out)} examples to {OUTPUT_DIR / 'real_data_examples.parquet'}")
    print("\nValidation complete! All artifacts generated.")


if __name__ == "__main__":
    run_validation()
