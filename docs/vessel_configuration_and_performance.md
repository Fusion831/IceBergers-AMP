# AMIP Vessel Configuration & Vessel Performance Subsystem

## 1. Executive Summary & Architecture

The **Antarctic Mission Intelligence Platform (AMIP)** couples multi-source Earth Observation and numerical weather prediction datasets with vessel naval architectural constraints to generate safe, energy-efficient routes.

The overall operational architecture is:

```
Native Datasets (CMEMS, ECMWF, NSIDC, GEBCO, SCAR ADD)
          ↓
H3 Spatial Integration (Resolution 5 Canonical DGGS)
          ↓
Unified H3 × Time Environment (EnvironmentCell / UnifiedEnvironmentCell)
          ↓
Vessel Configuration (Generic VesselProfile + Provenance Tracking)
          ↓
Vessel Performance Evaluator (Hydrodynamics, Metocean, Cryosphere)
          ↓
Vessel Routing Cost Adapter (FASTEST, SAFEST, FUEL_EFFICIENT, SHORTEST, BALANCED)
          ↓
Existing Routing & Mission Planning Engine
```

> [!IMPORTANT]
> **Architectural Non-Negotiables:**
> 1. **Vessel as Configuration**: The system contains no hardcoded `if vessel == "Sagar Kanya"` logic. All behavior is driven by typed Pydantic models loaded dynamically from configuration (`data/config/vessels/<vessel_id>.json`).
> 2. **Normalized Environment Ingestion**: The vessel subsystem consumes only normalized environment interfaces (`EnvironmentCell`, `UnifiedEnvironmentCell`, or mapped dictionary states). It never loads raw CMEMS NetCDF, ECMWF GRIB, NSIDC GeoTIFF, GEBCO raster, or SCAR ADD shapefiles directly.
> 3. **Cell/Transition-Specific Performance**: Performance is never evaluated as a static speed or scalar cost for an entire region. Every edge transition $A \to B$ is individually evaluated against the environment of the target cell at the transition timestamp.
> 4. **Dynamic Time Propagation**: Transit time across segment $i$ advances the simulation clock ($t_{\text{arrival}} = t_{\text{departure}} + \Delta t$), ensuring that cell $i+1$ is evaluated against dynamic forecast conditions at $t_{\text{arrival}}$.

---

## 2. Reference Vessel Profile: ORV Sagar Kanya

The initial reference vessel for Indian Antarctic research expeditions is the **Oceanographic Research Vessel (ORV) Sagar Kanya**, owned by the Ministry of Earth Sciences (MoES) / National Centre for Polar and Ocean Research (NCPOR) and operated by the Shipping Corporation of India (SCI).

### Authoritative Reference Parameters

| Parameter | Published / Configured Value | Unit | Provenance Classification | Primary Source |
|---|---|---|---|---|
| **Vessel ID** | `orv_sagar_kanya` | — | SYSTEM | Configuration Key |
| **Vessel Name** | `ORV Sagar Kanya` | — | PUBLISHED | NCPOR Fleet Register |
| **Callsign** | `ATSK` | — | PUBLISHED | NCPOR Tender / SCI Registry |
| **Length Overall (LOA)** | `100.34` | m | **PUBLISHED** | NCPOR Fleet Specification |
| **Length BP (LBP)** | `89.00` | m | **PUBLISHED** | NCPOR 2026 Tender Spec |
| **Breadth Extreme** | `16.39` | m | **PUBLISHED** | NCPOR Fleet Specification |
| **Breadth Moulded** | `16.30` | m | **PUBLISHED** | NCPOR 2026 Tender Spec |
| **Maximum Draft** | `5.60` | m | **PUBLISHED** | NCPOR Fleet Spec & Tender |
| **Gross Tonnage (GT)** | `4888` | GT | **PUBLISHED** | NCPOR 2026 Tender Spec |
| **Deadweight (DWT)** | `796.0` | MT | **PUBLISHED** | NCPOR 2026 Tender Spec |
| **Displacement** | `4180.0` | MT | **DERIVED** | Naval Arch. ($C_b \approx 0.51$ at $5.6\text{m}$ draft) |
| **Propulsion Plant** | Twin Screw Diesel-Electric | — | **PUBLISHED** | NCPOR Fleet Specification |
| **Engine Output** | `2460.0` ($2 \times 1230\text{ kW}$) | kW | **PUBLISHED** | NCPOR 2026 Tender Spec |
| **Cruising Speed** | `9.0` (range 8–10) | kn | **USER_CONFIGURED** | Nominal point from published range |
| **Minimum Speed** | `4.0` | kn | **ASSUMED** | Southern Ocean steerageway minimum |
| **Maximum Sprint Speed** | `12.0` | kn | **ASSUMED** | Calm water full-ahead limit |
| **Endurance** | `45` | days | **PUBLISHED** | NCPOR Fleet Spec & Tender |
| **Bunker Capacity (MGO)** | `433.0` ($368.05\text{ MT}$) | $\text{m}^3$ | **PUBLISHED** | NCPOR 2026 Tender Spec |
| **Ice Class / Polar Class** | `UNKNOWN` | — | **UNKNOWN** | NCPOR Fleet Register (No certified rating) |

### Discrepancy Documentation

Where authoritative sources cite divergent specifications, both values are preserved with notes:
1. **Gross Tonnage**: NCPOR historical website lists `4209 GRT` (pre-modification); 2026 tender specifies `4888 GT`. The 2026 tender value is retained as modern registered tonnage while logging the historical value.
2. **Breadth**: `16.39 m` extreme breadth vs `16.30 m` moulded breadth. Both preserved in `VesselGeometry`.
3. **Length**: `100.34 m` LOA vs `89.00 m` LBP. Both preserved in `VesselGeometry`.

---

## 3. Parameter Provenance & Classification System

Every parameter in AMIP is assigned a strict provenance tier (`vessel.provenance.ParameterClassification`):

1. **`PUBLISHED`**: Directly extracted from official, published government or institutional literature (e.g., NCPOR vessel specification page, NCPOR 2026 tender document).
2. **`DERIVED`**: Mathematically computed from published parameters without speculative external assumptions (e.g., fuel capacity in MT from $\text{volume} \times \text{density}$, displacement from hull dimensions and block coefficient).
3. **`ASSUMED`**: Engineering approximations where authoritative naval architectural drawings or sea-trial telemetry are not publicly disclosed (e.g., minimum steerage speed, gale wind thresholds, wave resistance curves).
4. **`USER_CONFIGURED`**: Operational policies and safety margins intentionally adjustable by the voyage planner (e.g., nominal cruise speed, maximum permissible SIC, safety under-keel margin).
5. **`UNKNOWN`**: Explicitly documented as uncertified or missing from authoritative records (e.g., Sagar Kanya Polar/Ice Class).

---

## 4. Sea Ice Capability & Policy

> [!CAUTION]
> **No Fabricated Ice Class:**
> Official NCPOR records do not cite an IACS Polar Class (PC1–PC7) or Finnish-Swedish Ice Class rating for ORV Sagar Kanya. Her ice capability is formally cataloged as `UNKNOWN`.
> While she has completed Southern Ocean scientific expeditions, she is an open-ocean research vessel, not an icebreaker.

Operational sea-ice handling is governed by configurable user policy:
- **`max_operational_sic`**: Default `0.15` (15% SIC). Transitions exceeding this threshold are flagged `is_feasible = False` with the blocking reason: `"Sea ice concentration X% exceeds operational limit 15.0% (Ice Class: UNKNOWN)"`.
- **`preferred_max_sic`**: Default `0.05` (5% SIC). Concentrations between 5% and 15% permit transit but emit operational soft warnings (`"Navigating in ice pack: SIC X% > preferred 5.0%"`).
- **Ice Resistance Model**: For non-zero SIC within operational limits, through-water speed is degraded non-linearly:
  $$f_{\text{ice}} = \max\left(0.20, 1.0 - 0.65 \times \left(\frac{\text{SIC}}{\text{max\_sic}}\right)^2\right)$$
  and added ice resistance multiplier $\text{ice\_res\_factor} = 0.80 \times (\text{SIC} / \text{max\_sic})^2$ scales fuel burn.

---

## 5. Hydrodynamic & Metocean Resistance Models

### 2D Vector Ocean Currents
Ocean current vectors $(u_{\text{current}}, v_{\text{current}})$ from CMEMS are added vectorially to the vessel's heading-dependent through-water velocity:
$$\vec{V}_{\text{ground}} = \vec{V}_{\text{vessel}} + \vec{V}_{\text{current}}$$
- **Along-Track Progression**: Ground velocity projected onto the planned transit track:
  $$V_{\text{along-track}} = V_{\text{ground}, e} \sin(\theta_{\text{hdg}}) + V_{\text{ground}, n} \cos(\theta_{\text{hdg}})$$
- **Favorable Current**: Increases ground speed, reduces transit time, and lowers total leg fuel.
- **Opposing Current**: Decreases ground speed, increases transit time, and raises total leg fuel.
- **Cross-Current**: Deflects course over ground ($\theta_{\text{ground}} \ne \theta_{\text{hdg}}$).
- **Steerage / Stall Protection**: If opposing current exceeds through-water speed ($V_{\text{along-track}} \le 0$), a soft warning is raised for vessel stall risk.

### Wave Resistance
Using significant wave height $H_s$, mean wave direction $\theta_{\text{wave}}$, and encounter angle $\theta_{\text{enc}} = |\theta_{\text{hdg}} - \theta_{\text{wave}}| \pmod{360^\circ}$:
$$C_{\text{enc}} = 0.5 \times (1.0 + \cos(\theta_{\text{enc}}))$$
$$\text{wave\_loss} = 0.08 \times \left(\frac{H_s}{2.5}\right)^2 \times (0.4 + 0.6 C_{\text{enc}})$$
$$f_{\text{wave}} = \max(0.35, 1.0 - \text{wave\_loss})$$
Wave resistance factor scales hourly fuel demand:
$$\text{wave\_res\_factor} = 0.12 \times \left(\frac{H_s}{2.5}\right)^2 \times (0.4 + 0.6 C_{\text{enc}})$$
Performance monotonically degrades with increasing wave height; wave height never improves speed or fuel economy.

### Aerodynamic Wind Resistance
Using ECMWF 10m wind velocity $(u_{\text{wind}}, v_{\text{wind}})$:
- Relative apparent wind vector: $\vec{V}_{\text{rel}} = \vec{V}_{\text{wind}} - \vec{V}_{\text{vessel}}$
- Relative wind speed $V_{\text{rel}} = |\vec{V}_{\text{rel}}|$ and apparent angle $\theta_{\text{rel}}$ are computed.
- Headwind component opposing forward motion induces speed loss and fuel resistance:
  $$f_{\text{wind}} = \max\left(0.70, 1.0 - 0.03 \times \left(\frac{w_{\text{head}}}{10.0}\right)^{1.5}\right) \quad \text{for } w_{\text{head}} > 0$$
- Wind is treated as aerodynamic hull drag on a powered vessel, never as direct passive advection.

---

## 6. Bathymetry, Grounding & SCAR ADD Constraints

### Bathymetry & Keel Grounding
- Water depth is obtained from GEBCO 2026 sub-ice bathymetry ($\text{depth\_m} > 0$).
- Vessel operating draft is $5.6\text{ m}$.
- Under-keel clearance: $\text{clearance} = \text{depth} - \text{draft}$.
- Policy distinguishes 4 clearance states:
  1. **`SAFE`**: $\text{clearance} \ge \text{required\_margin}$ (default $3.0\text{ m}$).
  2. **`WARNING`**: $\text{clearance} < 3.0\text{ m}$ (when UKC rule is set to `WARNING`).
  3. **`CRITICAL`**: $\text{depth} \le 5.6\text{ m}$ (direct hull grounding) or $\text{clearance} < 1.5\text{ m}$.
  4. **`HARD_BLOCK`**: $\text{clearance} < 3.0\text{ m}$ (default policy, marking transition infeasible).

### Authoritative SCAR ADD Geographic Mask
- Continental land, permanent ice shelves, and ice tongues defined by SCAR ADD v7.12 are strictly non-navigable (`is_blocked = True`).
- The router is never permitted to trade land or ice-shelf crossings for lower distance or fuel.

---

## 7. Fuel Consumption & Endurance Model

### Fuel Model Specification
- Labeled explicitly as: `"POC estimate (reduced-order cubic propulsion model + auxiliary hotel load)"`.
- **Propulsion Power**: Evaluated using cubic speed-power scaling at commanded cruising speed:
  $$P_{\text{prop}} = P_{\text{base}} \times \left(\frac{V_{\text{requested}}}{V_{\text{ref}}}\right)^3 \times (1 + f_{\text{wave\_res}} + f_{\text{wind\_res}} + f_{\text{ice\_res}})$$
- **Auxiliary Hotel Load**: Constant $0.06\text{ MT/h}$ ($1.44\text{ MT/day}$) for scientific laboratories, HVAC, and service generators.
- **Calibrated Baseline**: At nominal 9.0 knots, propulsion consumes $0.28\text{ MT/h}$ ($6.72\text{ MT/day}$), totaling $8.16\text{ MT/day}$. Over 45 days, this totals $367.2\text{ MT}$ ($\approx 99.8\%$ of $368.05\text{ MT}$ bunker capacity).
- **Leg Fuel**: $\text{Fuel (MT)} = \text{fuel\_rate} \times \text{travel\_time\_hours}$.
- **Cumulative Margin**: $\text{Margin (\%)} = \frac{\text{Capacity} - \text{Cumulative Fuel}}{\text{Capacity}} \times 100\%$.

### Endurance Tracking
- Published endurance is **45 days**.
- Cumulative route duration is tracked in decimal days.
- If cumulative voyage time exceeds 45 days, the route is flagged as exceeding unassisted endurance.

---

## 8. Transition Evaluator Contract (`EdgeEvaluation`)

The transition evaluator computes:

```python
EdgeEvaluation(
    feasible=True/False,
    reason=Optional[str],
    warnings=List[str],
    heading=float,                       # Degrees [0, 360)
    distance_m=float,                    # Great-circle meters
    distance_nm=float,                   # Nautical miles
    requested_speed_kn=float,            # Commanded speed
    achievable_speed_kn=float,           # After wave/wind/ice resistance
    ground_speed_kn=float,               # After 2D vector current addition
    ground_direction_deg=float,          # Course over ground
    along_track_speed_kn=float,          # Velocity along planned track
    current_u=Optional[float],           # Eastward current (m/s)
    current_v=Optional[float],           # Northward current (m/s)
    current_speed_kn=Optional[float],    # Magnitude
    current_assistance_kn=float,         # Along-track component (+ fwd, - opposing)
    wind_u=Optional[float],              # Eastward wind (m/s)
    wind_v=Optional[float],              # Northward wind (m/s)
    wind_speed_ms=Optional[float],       # Wind magnitude
    relative_wind_speed_ms=Optional[float],
    relative_wind_direction_deg=Optional[float],
    wave_height=Optional[float],         # Significant wave height Hs (m)
    wave_direction=Optional[float],      # Mean direction
    wave_period=Optional[float],         # Peak period Tp (s)
    wave_encounter_deg=Optional[float],
    sic=Optional[float],                 # Sea ice concentration fraction [0, 1]
    sic_uncertainty=Optional[float],     # SIC uncertainty fraction [0, 1]
    bathymetry_depth=Optional[float],    # Depth (m)
    draft=float,                         # Operating draft (5.6m)
    clearance=Optional[float],           # Under-keel clearance (m)
    clearance_status=str,                # SAFE, WARNING, CRITICAL, HARD_BLOCK
    travel_time_hours=float,             # Segment duration
    departure_time=str,                  # ISO 8601 UTC
    arrival_time=str,                    # ISO 8601 UTC
    fuel_rate=float,                     # MT/h
    fuel_used=float,                     # Leg total MT
    fuel_used_m3=float,                  # Leg total m3
    cumulative_fuel_mt=float,            # Cumulative MT
    fuel_capacity_margin_pct=float,      # Remaining bunker margin %
    fuel_capacity_exceeded=bool,
    cumulative_time_hours=float,         # Cumulative hours
    endurance_margin_days=float,         # Remaining endurance days
    endurance_exceeded=bool,
    constraint_state=dict,
    model_version="AMIP-VesselPerf-2026.1 (ORV Sagar Kanya POC Model)",
)
```

---

## 9. Mission-Ready Nodes & The Maitri Inland Distinction

The canonical Indian Antarctic Expedition transect consists of 4 nodes (`vessel.mission_nodes`):
1. **Cape Town Port**: $(-33.9188^\circ, 18.4233^\circ)$
2. **Bharati Maritime Access Node**: $(-69.3800^\circ, 76.1900^\circ)$ (Larsemann Hills / Prydz Bay coastal node)
3. **Maitri Maritime Access Node**: $(-69.9500^\circ, 11.7300^\circ)$ (India Bay / Princess Astrid Coast fast ice edge)
4. **Cape Town Port**: $(-33.9188^\circ, 18.4233^\circ)$

> [!WARNING]
> **Why Maitri Station Itself Cannot Be a Vessel Waypoint:**
> Maitri Research Station $(-70.7644^\circ\text{S}, 11.7340^\circ\text{E})$ is situated $\approx 100\text{ km}$ inland in the Schirmacher Oasis on ice-free rock and continental ice sheet.
> Routing directly to Maitri station coordinates results in an immediate `HARD_BLOCK` constraint violation against the SCAR ADD land mask.
> The vessel routes to the **India Bay Maritime Access Node** $(-69.95^\circ\text{S}, 11.73^\circ\text{E})$, from which resupply proceeds overland via tracked vehicle convoy or helicopter.

---

## 10. Frontend Inspector & Configuration Contract

### Performance Inspector Payload (`vessel.inspector.format_transition_inspector`)
When an operator clicks any route waypoint or candidate H3 transition on the map, the frontend inspector receives a structured diagnostic card containing:
- Vessel identity and current draft
- Cell ID, timestamps, transit duration, heading, and distance
- Commanded vs Achievable vs Ground speed with along-track component
- Detailed metocean forcings (currents, winds, waves, encounter angles)
- Cryosphere & bathymetry (SIC, uncertainty, depth, clearance, status)
- Fuel burn rate, leg fuel, cumulative fuel, and endurance margins
- Feasibility status and warnings
- An automated plain-language **performance narrative** explaining why the vessel accelerates, decelerates, or burns excess fuel in that specific cell.

### User Configuration Panel (`VesselProfile.to_frontend_config`)
The configuration UI groups parameters into logical cards (Hull Dimensions, Tonnage & Power, Speed Preferences, Fuel & Endurance, Ice Policy, Metocean Limits) and tags every field with its authoritative provenance badge (`PUBLISHED`, `DERIVED`, `ASSUMED`, `USER_CONFIGURED`, `UNKNOWN`). User-editable operational assumptions are clearly distinguished from fixed naval architectural specifications.
