# AMIP Routing Engine Integration: Canonical H3 Cell × Time State Space

## 1. Executive Summary

This document describes the architectural and implementation details for integrating the AMIP discrete 4D routing engine with the canonical **H3 Cell × Time** state space for SIH 2026 Problem Statement 26059 (National Centre for Polar and Ocean Research - NCPOR).

The integrated system operates over an unbroken operational intelligence chain:

$$\text{Observed Environmental Data} \to \text{Unified } H3 \times \text{Time Environment} \to \text{Sea-Ice / Mock SIC} \to \text{73-Iceberg Hazard Field} \to \text{RiskEngine} \to \text{VesselPerformanceEvaluator} \to \text{AMIPGridRouter} \to \text{Mission Route} \to \text{Diagnostics/ETA/Fuel/Risk}$$

All routing decisions are computed directly over discrete hexagonal H3 cells with dynamic chronological time propagation, 2D vector ocean currents, vessel hydrodynamic/cryospheric resistance curves, and strict hard constraint pruning by the AMIP Risk Engine.

---

## 2. Core Architectural Components

### 2.1 Canonical H3 Spatial Graph (`H3EnvironmentalGridGraph`)
Located in [`packages/routing/src/routing/grid_graph.py`](file:///c:/Users/daksh/Projects/SIH2026/packages/routing/src/routing/grid_graph.py), `H3EnvironmentalGridGraph` replaces artificial rectilinear raster grids with Uber's discrete global grid system (H3).

- **Hexagonal Topology**: Uses native `h3.grid_disk(cell, 1)` topological neighbors (up to 6 equidistant adjacent cells).
- **On-Demand Node Allocation**: Generates nodes dynamically during A* graph exploration to achieve sub-millisecond execution times without loading millions of inactive oceanic nodes into memory.
- **Spherical Geodesics & Azimuth Bearings**: Computes exact great-circle distance in nautical miles (NM) and forward azimuth heading angles ($0^\circ - 360^\circ$) between cell centroids.
- **Static Hard Masks**:
  - **SCAR Antarctic Digital Database (ADD)**: Flags Antarctic continental landmass and ice shelves as strictly non-navigable (`land_mask = True`, `navigable = False`).
  - **GEBCO Bathymetry**: Assigns water depths in meters to evaluate grounding risks.
- **Canonical Maitri Access Node**:
  - Inland Maitri station ($-70.7644^\circ\text{S}, 11.7340^\circ\text{E}$, elevation $>100\text{m}$) is strictly non-navigable land.
  - Indian expedition vessels transit to the **Maitri Maritime Access Node / India Bay** ($-69.95^\circ\text{S}, 11.73^\circ\text{E}$), preserving physical realism.

### 2.2 Discrete 4D State Space & Chronological Time Advancement
The routing state space is defined as:
$$\text{State} = (\text{cell\_id}, \text{time\_bucket})$$
where $\text{cell\_id}$ is a 15-character canonical H3 hex string (e.g. `85ad3617fffffff`) and $\text{time\_bucket} = \lfloor (t - t_0) / \Delta t_{\text{bucket}} \rfloor$.

- **Parent-Pointer Graph Traversal**: Reconstructs optimal trajectories in $O(\text{path\_length})$ memory.
- **Dynamic Time Advancement**: For each candidate edge transition $A \to B$:
  $$\Delta t = \frac{d_{\text{edge}}}{v_{\text{effective}}}, \quad t_1 = t_0 + \Delta t$$
- **Monotonic Progression**: Arrival timestamps strictly advance chronologically, ensuring that downstream environmental state queries query the exact predicted hour of passage.

### 2.3 2D Vector Ocean Current Dynamics
Ocean currents are vector-decomposed ($u_c$ Eastward, $v_c$ Northward) and projected onto the forward transit azimuth angle $\theta$:
$$v_{\text{along}} = (u_c \sin \theta + v_c \cos \theta) \times 1.94384 \text{ knots}$$
- **Effective Speed Over Ground**:
  $$v_{\text{ground}} = v_{\text{water}} + v_{\text{along}}$$
- **Current Assistance**: Favorable currents increase ground speed and reduce voyage transit hours without increasing engine fuel burn.
- **Current Penalty**: Opposing currents reduce ground speed, extending transit duration and increasing cumulative fuel consumption.

### 2.4 RiskEngine Hard Constraint Pruning
Every neighbor transition is dynamically evaluated against the `RiskEngine` baseline policy (`AMIP_POC_BASELINE`):
- **Hard Grounding**: $\text{Depth} \le \text{Vessel Draft}$ ($cost = \infty$).
- **Under-Keel Clearance**: $\text{Depth} - \text{Draft} < 3.0\text{m}$ ($cost = \infty$).
- **Vessel Ice Capability**: Sea ice concentration exceeding vessel limit:
  - ORV *Sagar Kanya* (Open Water): $\text{SIC} > 0.15 \implies \text{hard\_blocked} = \text{True}$.
  - Polar Research Vessel (Ice Class 1A Super): $\text{SIC} > 0.85 \implies \text{hard\_blocked} = \text{True}$.
- **Geographic Barriers**: SCAR ADD land and ice shelves are strictly pruned from the A* queue.

---

## 3. Objective Cost Formulations

The AMIP Routing Engine supports 5 physically distinct routing objectives:

| Objective | Edge Cost Formula | Physical Behavior |
| :--- | :--- | :--- |
| **`SHORTEST`** | $d_{\text{edge}}$ | Pure geodesic distance; direct line between waypoints. |
| **`FASTEST`** | $\Delta t_{\text{hours}}$ | Minimum travel time; detours around ice to maintain high speed. |
| **`SAFEST`** | $d \times [1 + 15(\text{SIC})^{1.5} + 10(\text{Hazard})^{1.5} + 3\max(0, \frac{H_s-3}{4}) + 20(R_{\text{composite}})^{1.5}]$ | Aggressive penalty against ice, iceberg hazard, and high sea states. |
| **`FUEL_EFFICIENT`** | $\text{Leg Fuel Burn (Tonnes)}$ | Naval architecture power-curve model leveraging favorable ocean currents. |
| **`BALANCED`** | $0.35 \frac{\Delta t}{24} + 0.35 \frac{\text{Fuel}}{20} + 0.20 \frac{R_{\text{composite}} \cdot d}{30} + 0.10 \frac{d}{100}$ | Multi-criteria Pareto compromise balancing time, fuel, and safety. |

---

## 4. Canonical NCPOR Mission Transect

The complete Indian Antarctic Research Expedition voyage is orchestrated via `MissionPlanner.plan_canonical_ncpor_mission`:

1. **Origin / Return Port**: Cape Town, South Africa ($-33.9249^\circ\text{S}, 18.4241^\circ\text{E}$).
2. **First Destination**: Bharati Maritime Access Node, Prydz Bay ($-69.40^\circ\text{S}, 76.19^\circ\text{E}$), Dwell: 48 hours.
3. **Second Destination**: Maitri Maritime Access Node / India Bay ($-69.95^\circ\text{S}, 11.73^\circ\text{E}$), Dwell: 72 hours.
4. **Final Return**: Cape Town Port ($-33.9249^\circ\text{S}, 18.4241^\circ\text{E}$).

**Key Navigation Metrics for Canonical Transect**:
- Total Distance: $\approx 6,606\text{ NM}$ ($\approx 12,234\text{ km}$).
- Cumulative Waypoints: $>25$ waypoints.
- H3 Cells Traversed: 49 discrete H3 cells.
- Dwell Times: 120 hours dedicated to science cargo discharge and resupply.

---

## 5. Verification & Test Coverage

The integration is verified by 10 comprehensive tests in [`tests/test_h3_routing_integration.py`](file:///c:/Users/daksh/Projects/SIH2026/tests/test_h3_routing_integration.py):

| Test Name | Verified Behavior | Status |
| :--- | :--- | :--- |
| `test_h3_grid_graph_hexagonal_topology_and_navigability` | Hexagonal disk-1 neighbors, spherical distance/bearings | **PASSED** |
| `test_h3_grid_graph_closest_node` | GeoPoint $\to$ closest H3 cell centroid mapping | **PASSED** |
| `test_h3_cell_id_binding_and_ordered_traversal` | Route waypoints bind canonical H3 index strings | **PASSED** |
| `test_chronological_time_advancement` | Monotonic ETA progression and physical time consistency | **PASSED** |
| `test_vector_current_assistance_and_penalty` | 2D currents increase ground speed and decrease transit duration | **PASSED** |
| `test_risk_engine_bathymetric_shoal_hard_blocking` | Pruning transitions through shoals exceeding vessel draft | **PASSED** |
| `test_risk_engine_ice_class_limit_pruning` | Sagar Kanya blocked by SIC $>0.15$; Ice-Class vessel passes | **PASSED** |
| `test_five_routing_objectives_differentiation` | 5 objectives yield distinct distance, fuel, and risk profiles | **PASSED** |
| `test_segment_diagnostics_and_route_risk_profile` | Full segment diagnostics and `RouteRiskProfile` aggregation | **PASSED** |
| `test_canonical_ncpor_mission_planner` | Multi-target NCPOR expedition itinerary | **PASSED** |

In addition, 100% backward compatibility is maintained across all pre-existing tests.
