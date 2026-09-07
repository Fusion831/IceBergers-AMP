# AMIP: FULL PRODUCT VISION + REAL DATA ARCHITECTURE

**Antarctic Mission Intelligence Platform (AMIP)**  
*SIH 2026 Problem Statement 26059 (NCPOR / MoES)*  
*Architectural Reference & Master Specification*

---

## 1. Core Vision: Environmental Intelligence + Mission Planning + Decision Support

AMIP is **not** a simple route planner or a static map viewer. It is an end-to-end environmental intelligence, mission planning, and navigation decision-support system for Antarctic research-vessel operations.

The fundamental computational representation of the platform is:
$$\text{Environment}(\text{latitude}, \text{longitude}, \text{time})$$

Every physical, operational, and navigational attribute that varies with space and time is evaluated through this 4D state.

---

## 2. Multi-Scale Geographic & Grid Experience

The user interacts with a continuous geographic canvas with progressive Level-of-Detail (LoD):

$$\text{Global Earth} \longrightarrow \text{Southern Ocean} \longrightarrow \text{Antarctica} \longrightarrow \text{Mission Corridor} \longrightarrow \text{Detailed Grid} \longrightarrow \text{Individual Cells}$$

* **Global Earth View:** Planners start from departure ports (e.g., Cape Town, Goa, Punta Arenas, Hobart) and trace transits down into the high polar latitudes.
* **Hierarchical Zoom:** Broad environmental patterns (e.g., Antarctic Circumpolar Current jet, Roaring Forties storm tracks) transition seamlessly into regional sea-ice marginal zones, and down to individual computational grid cells upon zooming in.
* **Computational Grid Cells:** A grid cell is not merely a visual raster; it is the fundamental discrete computational unit of the system containing:
  * Sea-ice concentration ($q_{10}, q_{50}, q_{90}$) and thickness
  * Ocean current velocity vector ($\mathbf{u}_{\text{ocean}} = [u_o, v_o]$)
  * 10-meter wind velocity vector ($\mathbf{u}_{\text{wind}} = [u_{10}, v_{10}]$)
  * Significant wave height ($H_s$) and peak period ($T_p$)
  * Seabed depth / bathymetry
  * Iceberg encounter density ($R_{\text{iceberg}}$)
  * Composite navigational risk ($R_{\text{composite}}$)
* **Cell Inspection:** Clicking any cell displays its exact multi-variable state, timestamp, and data provenance (e.g. `Observed`, `Predicted`, `Synthetic/Mock`, `Estimated`).

---

## 3. Time as a Core Computational Dimension ($T+0$ to $T+90$ Days)

The temporal slider is **not** a video animation bar; it is an active query driver:

$$\text{Time Slider Move } (T_1 \to T_2) \implies \text{Environment}(\text{cell}, T_1) \neq \text{Environment}(\text{cell}, T_2)$$

* As time advances:
  * Sea-ice edge advances or retreats; concentration changes.
  * Monte Carlo iceberg trajectory ensembles propagate along currents and winds with expanding uncertainty cones.
  * Weather fronts and wave heights evolve.
  * Spatial risk distribution shifts dynamically.
* **Recomputation Workflow:** Planners can select departure dates, inspect the forecast field, generate routes, advance the slider, and immediately observe if route feasibility or recommended alternatives change.

---

## 4. Multi-Target Expedition Planning

Expeditions are complex multi-stop scientific campaigns, not single-origin/destination queries:
* **Supported Nodes:**
  * Starting departure ports (e.g. Cape Town)
  * Official Antarctic research stations (e.g. Bharati, Maitri)
  * User-selected science survey polygons and arbitrary oceanographic coordinates
  * Selected environmental grid cells designated as mission targets (e.g. `Grid Cell S17`, `Grid Cell S42`)
  * User-defined dynamic avoidance zones (e.g., iceberg calving fronts, shallow shoals, restricted marine zones)
* **Operational Scheduling:** Dwell times at each node advance the mission's running temporal clock, adjusting environmental conditions for subsequent legs.

---

## 5. Clean Decoupled Data Ecosystem

The platform enforces a strict boundary between external scientific sources and internal computation:

```
[Real Data Feeds]   OR   [Deterministic Synthetic Provider]
        │                                │
        └───────────────┬────────────────┘
                        ▼
       EnvironmentalDataProviderInterface
                        ▼
             Environment(x, y, t)
                        ▼
       [Models] ── [Risk] ── [4D Router]
                        ▼
              [Frontend / Decision UI]
```

### Data Sources & Roles
1. **Sea Ice:**
   * *NSIDC AMSR-E / AMSR2 L3 Daily 12.5 km (AU_SI12):* Ground-truth target for ML training, climatology, and validation.
   * *Copernicus Marine (CMEMS):* Operational near-real-time SIC, ice edge, and drift vectors.
   * *EUMETSAT OSI SAF:* Long-term Climate Data Record (CDR) for anomaly calibration.
2. **Ocean Currents (Vector Field):**
   * *Copernicus Marine Global Ocean Physics:* Eastward current ($u_o$) and northward current ($v_o$) vectors for vessel heading assistance/opposition and iceberg drift forcing.
3. **Waves & Swell:**
   * *Copernicus Marine Global Ocean Waves:* Significant wave height ($H_s$) and period ($T_p$) for hydrodynamic speed loss, fuel penalties, and safety constraints.
4. **Weather & Atmosphere:**
   * *ECMWF ERA5 & IFS (HRES / SEAS5):* Tactical 10-meter wind vectors ($u_{10}, v_{10}$), air temperature, pressure, and seasonal ensemble trends.
5. **Icebergs:**
   * *USNIC Antarctic Iceberg Tracking & CMEMS SAR Products:* Observed initial coordinates, dimensions, and hazard fronts propagated via Lagrangian physics into 50-member Monte Carlo trajectory ensembles.
6. **Bathymetry & Coastlines:**
   * *GEBCO 2024 & SCAR Antarctic Digital Database (ADD):* Water depth, vessel draft grounding checks, continental shelf gradients, and land/ice-shelf exclusion masks.
7. **Mission Logistics:**
   * *NCPOR NPDC:* Station coordinates, approach corridors, and Indian polar expedition records stored as configurable database entities.

---

## 6. Vessel Hydrodynamics & 4D Spatiotemporal Routing

* **Configurable Vessel Profiles:** Accounts for Polar Class (PC1–PC7 / unstrengthened), length, beam, draft, displacement, service speed, and fuel burn curves.
* **Physics-Derived Speed:** Speed is not constant:
  $$V_{\text{effective}} = f(\text{Vessel}, \text{Heading}, \mathbf{u}_{\text{current}}, \mathbf{u}_{\text{wind}}, H_s, \text{SIC})$$
* **Naval Architecture Fuel Consumption:** Modeled using the cubic admiralty power law modulated by icebreaking resistance multipliers.
* **5 Distinct Pareto Objectives:**
  1. `SHORTEST`: Minimum geographic distance.
  2. `FASTEST`: Minimum total transit duration (flank speed open-water bypass).
  3. `SAFEST`: Minimum cumulative exposure to high risk, icebergs, and heavy sea states.
  4. `FUEL_EFFICIENT`: Optimal engine RPM along favorable ocean current jets.
  5. `BALANCED`: Multi-criteria compromise based on mission priority weights.
* **Spatiotemporal Trajectory:** The output is a full 4D path:
  $$\text{Path}(x, y, t)$$
  Allowing segment-by-segment inspection of why each waypoint was selected.

---

## 7. Strategic Architecture & Future PolarRoute Integration

* **AMIP Platform Responsibility:** Owns the environmental data ingestion, AI sea-ice forecasting, Lagrangian iceberg drift physics, multi-criteria risk engine, mission planning, and decision visualization.
* **Navigation Router Abstraction:**
  ```text
  NavigationRouter
      ├── AMIPCustomRouter (Native 4D Dijkstra/A* - Active)
      └── PolarRouteAdapter (Future integration with British Antarctic Survey PolarRoute)
  ```

---

*Document permanently stored for architectural guidance and product roadmap alignment.*
