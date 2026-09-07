# Real H3 Environmental Conditions — ORV Sagar Kanya Performance Diagnostic Table

Evaluated using the canonical **Unified H3 × Time Environment** (`data/antarctica/environment/environment_cells.parquet`).
Reference vessel: **ORV Sagar Kanya** (LOA: 100.34m, Draft: 5.6m, Service Speed: 9.0 kn, Bunker: 433 m³ / 368 MT, Endurance: 45 days).

| Category | H3 Cell ID | Coordinates (Lat, Lon) | Geo Status | Depth (m) | SIC (%) | Hs (m) | Current (kn) | Ground Spd (kn) | Fuel Rate (MT/h) | Feasible | Blocking Reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Open Ocean (Baseline)** | `85bf668bfffffff` | -45.01°, 154.70° | OPEN_OCEAN | 4715.0m | 0.0% | 2.82m | 0.08 kn | 8.59 kn | 0.3627 | **YES** | — |
| **Coastal / Mixed** | `85df30a7fffffff` | -64.31°, -61.42° | MIXED | 315.4m | 0.0% | N/A | 0.28 kn | 9.04 kn | 0.34 | **YES** | — |
| **High SIC (Pack Ice)** | `85dd2087fffffff` | -66.03°, -16.29° | OPEN_OCEAN | 5037.7m | 62.0% | N/A | 0.12 kn | 1.6 kn | 0.76 | <span style='color:red'>**NO**</span> | Sea ice concentration 62.0% exceeds operational limit 15.0% (Ice Class: UNKNOWN) |
| **Low SIC (Marginal Pack)** | `85e70b07fffffff` | -68.88°, 25.30° | OPEN_OCEAN | 3201.7m | 19.0% | 2.1m | 0.33 kn | 1.17 kn | 0.76 | <span style='color:red'>**NO**</span> | Sea ice concentration 19.0% exceeds operational limit 15.0% (Ice Class: UNKNOWN) |
| **High Wave State (Rough)** | `85c48a53fffffff` | -44.83°, -44.78° | OPEN_OCEAN | N/A | 0.0% | 5.5m | 0.34 kn | 6.98 kn | 0.4203 | **YES** | — |
| **Low Wave State (Calm)** | `85c32b0ffffffff` | -41.12°, -64.37° | OPEN_OCEAN | N/A | 0.0% | 0.82m | 0.34 kn | 8.4 kn | 0.3556 | **YES** | — |
| **Strong Current** | `85c08e87fffffff` | -41.02°, -17.05° | OPEN_OCEAN | N/A | 0.0% | 3.36m | 1.1 kn | 8.26 kn | 0.4158 | **YES** | — |
| **Weak Current** | `85bba4c3fffffff` | -41.92°, -173.10° | OPEN_OCEAN | N/A | 0.0% | 3.13m | 0.1 kn | 7.9 kn | 0.3975 | **YES** | — |
| **Deep Bathymetry** | `85bf668bfffffff` | -45.01°, 154.70° | OPEN_OCEAN | 4715.0m | 0.0% | 2.82m | 0.08 kn | 8.59 kn | 0.3627 | **YES** | — |
| **Shallow Bathymetry** | `85ce348bfffffff` | -48.47°, -75.50° | OPEN_OCEAN | 24.0m | 0.0% | N/A | N/A | 9.0 kn | 0.3402 | **YES** | — |
| **Iceberg Hazard Exposure** | `85c458dbfffffff` | -46.25°, -29.85° | OPEN_OCEAN | 4896.1m | 0.0% | 2.9m | 0.79 kn | 8.56 kn | 0.3801 | **YES** | — |
| **Blocked SCAR ADD Mask** | `85e123c7fffffff` | -67.85°, 69.57° | LAND | 189.8m | 29.0% | N/A | N/A | 1.5 kn | 0.76 | <span style='color:red'>**NO**</span> | Traverses SCAR ADD blocked region (LAND); land or ice shelf |

## Performance Insights & Diagnostics

### Open Ocean (Baseline) (`85bf668bfffffff`)
- **Environmental Context**: Depth: 4715.0m, SIC: 0.0%, Hs: 2.82m, Current Assistance: 0.08 kn.
- **Vessel Response**: Achievable: 8.51 kn, Ground Speed: 8.59 kn, Fuel Burn: 0.3627 MT/h.
- **Feasibility**: Feasible (Reason: None).
- **Inspector Narrative**: Wave height Hs=2.8m imparts added hull resistance (loss ~5.4%).

### Coastal / Mixed (`85df30a7fffffff`)
- **Environmental Context**: Depth: 315.4m, SIC: 0.0%, Hs: Nonem, Current Assistance: 0.03 kn.
- **Vessel Response**: Achievable: 9.0 kn, Ground Speed: 9.04 kn, Fuel Burn: 0.34 MT/h.
- **Feasibility**: Feasible (Reason: None).
- **Inspector Narrative**: Near-baseline open ocean conditions with calm sea state.

### High SIC (Pack Ice) (`85dd2087fffffff`)
- **Environmental Context**: Depth: 5037.7m, SIC: 62.0%, Hs: Nonem, Current Assistance: 0.1 kn.
- **Vessel Response**: Achievable: 1.5 kn, Ground Speed: 1.6 kn, Fuel Burn: 0.76 MT/h.
- **Feasibility**: Infeasible (Reason: Sea ice concentration 62.0% exceeds operational limit 15.0% (Ice Class: UNKNOWN)).
- **Inspector Narrative**: Sea ice concentration of 62.0% degrades through-water speed and elevates propulsion power.

### Low SIC (Marginal Pack) (`85e70b07fffffff`)
- **Environmental Context**: Depth: 3201.7m, SIC: 19.0%, Hs: 2.1m, Current Assistance: -0.33 kn.
- **Vessel Response**: Achievable: 1.5 kn, Ground Speed: 1.17 kn, Fuel Burn: 0.76 MT/h.
- **Feasibility**: Infeasible (Reason: Sea ice concentration 19.0% exceeds operational limit 15.0% (Ice Class: UNKNOWN)).
- **Inspector Narrative**: Adverse head current reduces ground progression by 0.3 kn. Sea ice concentration of 19.0% degrades through-water speed and elevates propulsion power.

### High Wave State (Rough) (`85c48a53fffffff`)
- **Environmental Context**: Depth: Nonem, SIC: 0.0%, Hs: 5.5m, Current Assistance: -0.3 kn.
- **Vessel Response**: Achievable: 7.28 kn, Ground Speed: 6.98 kn, Fuel Burn: 0.4203 MT/h.
- **Feasibility**: Feasible (Reason: None).
- **Inspector Narrative**: Wave height Hs=5.5m imparts added hull resistance (loss ~19.1%).

### Low Wave State (Calm) (`85c32b0ffffffff`)
- **Environmental Context**: Depth: Nonem, SIC: 0.0%, Hs: 0.82m, Current Assistance: -0.3 kn.
- **Vessel Response**: Achievable: 8.7 kn, Ground Speed: 8.4 kn, Fuel Burn: 0.3556 MT/h.
- **Feasibility**: Feasible (Reason: None).
- **Inspector Narrative**: Near-baseline open ocean conditions with calm sea state.

### Strong Current (`85c08e87fffffff`)
- **Environmental Context**: Depth: Nonem, SIC: 0.0%, Hs: 3.36m, Current Assistance: 0.73 kn.
- **Vessel Response**: Achievable: 7.49 kn, Ground Speed: 8.26 kn, Fuel Burn: 0.4158 MT/h.
- **Feasibility**: Feasible (Reason: None).
- **Inspector Narrative**: Favorable ocean current increases ground progression by +0.7 kn. Wave height Hs=3.4m imparts added hull resistance (loss ~16.8%).

### Weak Current (`85bba4c3fffffff`)
- **Environmental Context**: Depth: Nonem, SIC: 0.0%, Hs: 3.13m, Current Assistance: 0.09 kn.
- **Vessel Response**: Achievable: 7.8 kn, Ground Speed: 7.9 kn, Fuel Burn: 0.3975 MT/h.
- **Feasibility**: Feasible (Reason: None).
- **Inspector Narrative**: Wave height Hs=3.1m imparts added hull resistance (loss ~13.3%).

### Deep Bathymetry (`85bf668bfffffff`)
- **Environmental Context**: Depth: 4715.0m, SIC: 0.0%, Hs: 2.82m, Current Assistance: 0.08 kn.
- **Vessel Response**: Achievable: 8.51 kn, Ground Speed: 8.59 kn, Fuel Burn: 0.3627 MT/h.
- **Feasibility**: Feasible (Reason: None).
- **Inspector Narrative**: Wave height Hs=2.8m imparts added hull resistance (loss ~5.4%).

### Shallow Bathymetry (`85ce348bfffffff`)
- **Environmental Context**: Depth: 24.0m, SIC: 0.0%, Hs: Nonem, Current Assistance: 0.0 kn.
- **Vessel Response**: Achievable: 9.0 kn, Ground Speed: 9.0 kn, Fuel Burn: 0.3402 MT/h.
- **Feasibility**: Feasible (Reason: None).
- **Inspector Narrative**: Near-baseline open ocean conditions with calm sea state.

### Iceberg Hazard Exposure (`85c458dbfffffff`)
- **Environmental Context**: Depth: 4896.1m, SIC: 0.0%, Hs: 2.9m, Current Assistance: 0.38 kn.
- **Vessel Response**: Achievable: 8.15 kn, Ground Speed: 8.56 kn, Fuel Burn: 0.3801 MT/h.
- **Feasibility**: Feasible (Reason: None).
- **Inspector Narrative**: Favorable ocean current increases ground progression by +0.4 kn. Wave height Hs=2.9m imparts added hull resistance (loss ~9.4%).

### Blocked SCAR ADD Mask (`85e123c7fffffff`)
- **Environmental Context**: Depth: 189.8m, SIC: 29.0%, Hs: Nonem, Current Assistance: 0.0 kn.
- **Vessel Response**: Achievable: 1.5 kn, Ground Speed: 1.5 kn, Fuel Burn: 0.76 MT/h.
- **Feasibility**: Infeasible (Reason: Traverses SCAR ADD blocked region (LAND); land or ice shelf).
- **Inspector Narrative**: Sea ice concentration of 29.0% degrades through-water speed and elevates propulsion power.
