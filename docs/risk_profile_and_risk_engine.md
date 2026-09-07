# AMIP Risk Profile & Risk Engine Subsystem

## 1. Purpose & Core Mission

The AMIP Environmental Risk Engine transforms multi-modal Antarctic environmental data—normalized H3 × Time spatial grids, real 73-iceberg ensemble occupancy hazards, vessel configuration/performance capabilities, and authoritative geographic/bathymetric boundaries—into a transparent, explainable, and vessel-aware risk profile.

Rather than collapsing environmental conditions into an opaque scalar "risk score", the Risk Engine answers:
1. **At Cell Level**: *"Given this H3 cell, at this timestamp, under this environmental state, and optionally for this vessel, how risky is this state and why?"*
2. **At Transition Level**: *"Given a transit from cell A to cell B with heading and vessel performance, what are the directional risks, current assistance/penalties, and feasibility constraints?"*
3. **At Route Level**: *"How much cumulative and tail exposure does this route have to each risk factor across time?"*

```
Normalized H3 × Time State (EnvironmentCell / UnifiedEnvironmentCell)
   + 73-Iceberg Hazard Field (Ensemble Occupancy Density)
   + Vessel Profile & Performance (VesselProfile / EdgeEvaluation)
   + Authoritative Constraints (SCAR ADD v7.12 / GEBCO 2026)
                        │
                        ▼
            ┌──────────────────────┐
            │      RiskEngine      │
            │ (AMIP_POC_BASELINE)  │
            └──────────┬───────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
   RiskProfile               RouteRiskProfile
 (Cell / Transition)         (Trajectory Exposure)
  - hard_blocked              - time-weighted integral
  - component scores [0, 1]   - tail risk (P90, P95, P99)
  - confidence score          - component exposures
  - machine warnings          - distinct iceberg counts
  - raw physical forcings     - hard block count
```

---

## 2. Critical Conceptual Distinctions & Caveats

To ensure scientific integrity, the AMIP Risk Engine maintains strict conceptual boundaries:

| Concept | Distinction | Explicit Boundary |
|---|---|---|
| **Hazard vs. Risk** | Hazard is the presence of an environmental threat (e.g. iceberg occupancy, wave height); Risk is the evaluated operational vulnerability of a vessel in that hazard. | Iceberg hazard is derived from ensemble occupancy density; it is **NOT** a certified collision probability. |
| **Observation vs. Forecast vs. Projection** | Differentiates measured satellite observations (NSIDC, CMEMS), near-term atmospheric forecasts (ECMWF), and multi-month kinematic projections. | A 90-day iceberg ensemble projection is an exploratory uncertainty envelope, not a deterministic weather forecast. |
| **Performance vs. Risk** | Vessel performance calculates achievable speed, fuel burn rate, and engine loading; Risk calculates environmental safety and operational feasibility. | Speed reduction and fuel increases inform risk, but do not substitute for environmental risk components. |
| **Hard Constraints vs. Soft Risk** | Hard constraints represent physical/regulatory impossibility (`hard_blocked = True`); soft costs represent navigable but undesirable states. | A hard block is **never** encoded merely as `risk = 1.0` or a high routing cost; it sets explicit boolean blocks with rules and reasons. |
| **POC Risk Index vs. Certified Safety** | Risk profiles provide relative decision-support indices in [0.0, 1.0]. | The baseline policy is a prototype decision-support tool, **NOT** certified maritime navigation guidance or official NCPOR operational doctrine. |

---

## 3. Architecture & Input Contracts

The Risk Engine consumes **normalized state** and is completely decoupled from raw file formats (NetCDF, GRIB2, GeoPackage, Shapefiles).

### 3.1 Supported Input Types
- `data_ingestion.h3.schema.UnifiedEnvironmentCell` (Canonical H3 dynamic state)
- `domain.environment.EnvironmentCell` (Point/grid environmental cell)
- `data_ingestion.h3.schema.StaticH3Cell` (Static geography and bathymetry)
- `vessel.models.VesselProfile` (Typed vessel parameters with parameter-level provenance)
- `vessel.evaluator.EdgeEvaluation` (Transition kinematics and hydrodynamics)
- Python `dict` conforming to normalized attribute keys.

### 3.2 Evaluation Context (`RiskContext`)
```python
class RiskContext(BaseModel):
    environment: Any
    vessel: Optional[VesselProfile] = None
    vessel_performance: Optional[EdgeEvaluation] = None
    policy: Optional[RiskPolicyConfig] = None
    timestamp: Optional[datetime] = None
    heading: Optional[float] = None
```
- When `heading` is absent (cell-level inspection), the engine evaluates **ambient environmental severity** without fabricating directional assumptions.
- When `heading` is provided (transition/route evaluation), relative current assistance/penalty and wave encounter angles are evaluated.

---

## 4. Decomposed Risk Components

Every evaluation independently calculates seven physical risk components and one epistemic confidence component, normalized to `[0.0, 1.0]`:

### 4.1 Geographic Risk (`evaluate_geographic_risk`)
- **Authoritative Source**: SCAR Antarctic Digital Database (ADD) v7.12.
- **Statuses**: `OPEN_OCEAN`, `MIXED`, `LAND`, `ICE_SHELF`, `ICE_TONGUE`, `RUMPLE`, `UNKNOWN`.
- **Hard Constraints**: Any cell intersecting `LAND`, `ICE_SHELF`, `ICE_TONGUE`, or `RUMPLE` sets:
  - `hard_blocked = True`
  - `blocking_rule = "SCAR_ADD_GEOGRAPHIC_MASK"`
  - `geographic_risk = 1.0`
- **Mixed / Coastal Cells**: Preserves exact fractions (`land_fraction`, `ice_shelf_fraction`, `ocean_fraction`). Continuous soft risk: $R_{\text{geo}} = \min(0.95, 1.0 - \text{ocean\_fraction})$.

### 4.2 Bathymetric Risk (`evaluate_bathymetric_risk`)
- **Authoritative Source**: GEBCO 2026 sub-ice water depth ($D_{\text{bathy}} > 0$).
- **Vessel Ingestion**: Operating draft $T$ (default 5.6 m for Sagar Kanya).
- **Under-Keel Clearance (UKC)**: $\text{UKC} = D_{\text{bathy}} - T$.
- **Grounding Rule**: If $\text{UKC} \le 0.0$ m:
  - `hard_blocked = True`
  - `blocking_rule = "BATHYMETRIC_GROUNDING"`
  - Status: `HARD_BLOCK`
- **UKC Safety Margin**: Configured critical margin (e.g. 3.0 m) and warning margin (e.g. 10.0 m):
  - $\text{UKC} < 3.0$ m: Hard blocked under Sagar Kanya policy; status `CRITICAL`.
  - $3.0 \le \text{UKC} < 10.0$ m: Soft shallow-water approach warning; status `WARNING`.
  - $\text{UKC} \ge 10.0$ m: Safe deep water; $R_{\text{bathy}} = 0.0$; status `SAFE`.

### 4.3 Sea-Ice Risk (`evaluate_sea_ice_risk`)
- **Input**: Sea Ice Concentration ($\text{SIC} \in [0.0, 1.0]$), $\text{SIC}_{\text{uncertainty}}$.
- **Vessel Operating Limit**: Sagar Kanya conservative 15% open-pack operational limit.
- **Hard Constraints**: If $\text{SIC} > \text{SIC}_{\text{vessel\_limit}}$ and `enforce_vessel_sic_limit == True`:
  - `hard_blocked = True`
  - `blocking_rule = "VESSEL_SEA_ICE_CAPABILITY_EXCEEDED"`
- **Monotonic Severity Curve**:
  - $\text{SIC} \le 0.0$: $R_{\text{ice}} = 0.0$ (`SAFE`)
  - $0.0 < \text{SIC} \le 0.05$: $R_{\text{ice}} \in [0.0, 0.15]$ (`LOW`)
  - $0.05 < \text{SIC} \le 0.15$: $R_{\text{ice}} \in [0.15, 0.50]$ (`ELEVATED`)
  - $0.15 < \text{SIC} \le 0.40$: $R_{\text{ice}} \in [0.50, 0.85]$ (`HIGH`)
  - $\text{SIC} > 0.40$: $R_{\text{ice}} \in [0.85, 1.00]$ (`CRITICAL`)
- **Uncertainty Modulation**: A cell with high $\text{SIC}_{\text{uncertainty}}$ scales the risk margin and emits a `HIGH_SIC_UNCERTAINTY` warning.
- **Provenance Tracking**: If $\text{SIC}$ is generated by mock providers, the output explicitly tags `sic_source = "MOCK"` and emits `MOCK_SIC`.

### 4.4 Iceberg Hazard Risk (`evaluate_iceberg_risk`)
- **Input**: Real H3 hazard field derived from the 73-iceberg dataset across 42,464 historical and operational observations and 25-member ensemble drift trajectories.
- **Interpretation**: Raw hazard represents **ensemble spatial occupancy density**, not independent icebergs. 25 ensemble members of a single iceberg represent trajectory dispersion, NOT 25 separate icebergs.
- **Distinct Bergs**: Preserves `distinct_iceberg_count` and `contributing_iceberg_ids`. Multi-iceberg proximity adds an operational vigilance margin.
- **Thresholds**: Safe ($\le 0.02$), Elevated ($0.10$), High ($0.30$), Critical ($0.60$).
- **Soft Nature**: Iceberg hazard is treated as a severe soft navigation cost, allowing the router to alter course dynamically rather than severing network connectivity.

### 4.5 Wave Risk (`evaluate_wave_risk`)
- **Input**: Significant wave height $H_s$, peak wave period $T_p$, wave direction $\theta_{\text{wave}}$, and vessel heading $\theta_{\text{vessel}}$.
- **Baseline Severity**: Monotonic mapping based on Southern Ocean operational thresholds:
  - $H_s \le 2.5$ m: $R_{\text{wave}} \le 0.10$ (`SAFE`)
  - $2.5 < H_s \le 4.0$ m: $R_{\text{wave}} \in [0.10, 0.35]$ (`LOW`)
  - $4.0 < H_s \le 6.0$ m: $R_{\text{wave}} \in [0.35, 0.70]$ (`ELEVATED`)
  - $6.0 < H_s \le 8.0$ m: $R_{\text{wave}} \in [0.70, 0.90]$ (`HIGH`)
  - $H_s > 8.0$ m: $R_{\text{wave}} > 0.90$ (`CRITICAL`)
- **Encounter Angle Modulation**: When heading is provided, relative encounter angle $\Delta\theta = |\theta_{\text{vessel}} - \theta_{\text{wave}}|$ applies a multiplier:
  - Head seas ($\Delta\theta < 45^\circ$): $+15\%$ penalty
  - Beam seas ($70^\circ \le \Delta\theta \le 110^\circ$): $+10\%$ rolling penalty
  - Following seas ($\Delta\theta > 135^\circ$): $-10\%$ reduction

### 4.6 Wind Risk (`evaluate_wind_risk`)
- **Input**: $10\text{m}$ vector components $u_{\text{wind}}, v_{\text{wind}}$ or speed $V_{\text{wind}}$.
- **Cell-Level**: Maps scalar speed monotonically using Beaufort/operational thresholds: Fresh Breeze ($\le 10$ m/s), Near Gale ($15$ m/s), Gale Force 8 ($20$ m/s), Storm Force 10 ($28$ m/s).
- **Transition-Level**: Computes relative apparent wind vector against vessel motion and applies headwind resistance factors.

### 4.7 Current Risk (`evaluate_current_risk`)
- **Fundamental Principle**: Ocean currents are **not intrinsically dangerous**. Their impact is relative to vessel trajectory:
  - **Along-Track Component**: $V_{\text{along}} = u_{\text{curr}}\sin\theta_{\text{vessel}} + v_{\text{curr}}\cos\theta_{\text{vessel}}$.
  - **Favorable ($V_{\text{along}} > 0.2$ kn)**: Current pushes vessel forward $\to R_{\text{curr}} = 0.0$, reports positive `current_assistance`.
  - **Neutral ($-0.3 \le V_{\text{along}} \le 0.2$ kn)**: Negligible effect $\to R_{\text{curr}} = 0.05$.
  - **Adverse ($V_{\text{along}} < -0.3$ kn)**: Opposing current slows ground progression $\to$ proportional soft penalty $R_{\text{curr}} \in [0.10, 1.0]$.
- **Cell-Level (Unknown Heading)**: Reports ambient environmental current speed without inventing directional penalties.

### 4.8 Data Quality & Confidence (`evaluate_data_quality`)
- **Epistemic Model**: Confidence is evaluated independently of risk severity.
- **Inputs**: Missing physical variables, temporal quality status (`OBSERVED`, `FORECAST`, `PERSISTED`, `MOCK`), SIC uncertainty, lead time.
- **Rules**:
  - Missing variable penalty: $-0.15$ per missing primary field.
  - Mock data penalty: $-0.25$ if SIC is synthetic.
  - Extended projection penalty: $-0.20$ if lead time $> 14$ days.
  - Clamped to $[0.05, 1.0]$.
- **Classes**: `HIGH` ($\ge 0.80$), `MEDIUM` ($\ge 0.50$), `LOW` ($\ge 0.20$), `UNKNOWN` ($< 0.20$).

---

## 5. Risk Policy (`AMIP_POC_BASELINE`)

Configuration resides in [`data/config/risk/risk_policy.json`](file:///c:/Users/daksh/Projects/SIH2026/data/config/risk/risk_policy.json).

### Component Weights
$$\sum_{i=1}^7 w_i = 1.0$$
- Sea Ice ($w_{\text{ice}}$): **0.35**
- Iceberg Hazard ($w_{\text{berg}}$): **0.25**
- Waves ($w_{\text{wave}}$): **0.15**
- Wind ($w_{\text{wind}}$): **0.10**
- Bathymetry ($w_{\text{bathy}}$): **0.05**
- Current ($w_{\text{curr}}$): **0.05**
- Confidence ($w_{\text{conf}}$): **0.05**

### Startup Validation
The policy validator strictly checks:
- Weights sum to $1.0 \pm 0.001$.
- Threshold monotonicity ($\text{safe} \le \text{elevated} \le \text{high} \le \text{critical}$).
- Presence of units, parameter classifications (`PUBLISHED`, `DERIVED`, `ASSUMED`, `USER_CONFIGURED`), and version tags.
- Fails loudly with `ValueError` on startup if invalid.

---

## 6. Route Risk Aggregation (`RouteRiskProfile`)

The router and analytics layer aggregate risk across a sequence of transitions $[(c_1, t_1), \dots, (c_n, t_n)]$ with durations $\Delta t_i$:

1. **Total Duration**: $T = \sum_{i=1}^n \Delta t_i$.
2. **Time-Weighted Risk Integral**:
   $$\text{RiskIntegral} = \int_0^T R(t) dt = \sum_{i=1}^n R_i \cdot \Delta t_i \quad [\text{risk} \cdot \text{hours}]$$
3. **Time-Weighted Mean Risk**:
   $$\bar{R}_{\text{weighted}} = \frac{\text{RiskIntegral}}{T}$$
4. **Tail Risk Percentiles**: $P_{90}, P_{95}, P_{99}$ computed across segment evaluations (preserving extreme exposures rather than hiding them under a simple mean).
5. **High/Critical Exposure**: Cumulative hours spent in states with $R > 0.60$ and $R > 0.80$.
6. **Component Exposures**: Dedicated integrals for sea-ice, iceberg, wave, wind, current, and bathymetry exposure.
7. **Iceberg Metrics**: Total integrated hazard exposure, peak hazard encountered, time above threshold ($>0.10$), and deduplicated list of all distinct contributing icebergs.

---

## 7. Frontend Integration Contract

### 7.1 Cell Inspector (`profile.to_inspector_dict()`)
Allows operators to click any H3 cell and inspect complete diagnostics:
```json
{
  "cell_id": "85ad049bfffffff",
  "timestamp": "2026-01-15T12:00:00Z",
  "feasibility": {
    "hard_blocked": false,
    "block_reason": null,
    "blocking_rule": null
  },
  "composite": {
    "overall_risk": 0.1845,
    "confidence_score": 0.8500,
    "confidence_class": "HIGH"
  },
  "component_risks": {
    "geographic": 0.0,
    "bathymetric": 0.0,
    "sea_ice": 0.1550,
    "iceberg": 0.2200,
    "wave": 0.3500,
    "wind": 0.1800,
    "current": 0.0500,
    "data_quality": 0.1500
  },
  "physical_forcings": {
    "sea_ice_concentration_fraction": 0.08,
    "significant_wave_height_m": 3.2,
    "iceberg_hazard_proxy": 0.22,
    "distinct_iceberg_count": 2,
    "contributing_iceberg_ids": ["B15A", "A68A"]
  },
  "warnings": [ ... ],
  "policy": { "policy_name": "AMIP_POC_BASELINE", "policy_version": "1.0.0" }
}
```

### 7.2 H3 Map Layer Format (`profile.to_h3_layer_dict()`)
Provides raw numeric keys for deck.gl H3HexagonLayer:
```json
{
  "cell_id": "85ad049bfffffff",
  "composite_risk": 0.1845,
  "confidence_score": 0.85,
  "sea_ice_risk": 0.155,
  "iceberg_risk": 0.22,
  "wave_risk": 0.35,
  "wind_risk": 0.18,
  "hard_blocked": false
}
```

---

## 8. Real Antarctic Verification & Benchmarks

Validated against 2,000 real environmental H3 cells in `data/antarctica/environment/environment_cells.parquet`:
- **Single-Cell Latency**: `0.143 ms`
- **Batch Throughput**: `30,196 cells/second` (`0.033 ms/cell`)
- **Route Trajectory Evaluation (50 segments)**: `0.45 ms`
- **Sensitivity Sweeps**: 100% monotonic response verified across SIC, iceberg hazard, wave height, wind speed, and bathymetry depth.
- **Determinism**: Identical inputs produce byte-equal profiles.
- **Artifacts Saved**:
  - `data/validation/risk/validation_report.json`
  - `data/validation/risk/sensitivity_report.json`
  - `data/validation/risk/benchmark_report.json`
  - `data/validation/risk/real_data_examples.parquet`
