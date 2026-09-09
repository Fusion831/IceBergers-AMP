# AMIP Technical Viva & Judge Q&A Document
**Antarctic Mission Intelligence Platform (AMIP) | NCPOR / MoES — SIH 2026**
*Authoritative Architectural Audit & Technical Defense Reference*

---

## Provenance & Classification Guide
To maintain absolute scientific and engineering integrity, all technical answers in this document are labeled with their authoritative system classification:
- `[OFFICIAL]`: Published in government, institutional, or scientific documentation (NCPOR, SCAR ADD, GEBCO, NSIDC, CMEMS).
- `[DERIVED]`: Directly calculated from official parameters via standard mathematical or physical laws.
- `[USER_CONFIGURED]`: Configurable operational parameters adjustable by voyage planners or policy files.
- `[ASSUMED]`: Engineering approximations where authoritative sea-trial or proprietary telemetry is undisclosed.
- `[POC SIMPLIFICATION]`: Simplified architecture implemented specifically for the prototype demonstration.
- `[FUTURE]`: Planned for subsequent operational deployment phases.

---

# Spoken Architecture Pitch (60–75 Seconds)

> **Instructions for Speaker:** Speak clearly, with a conversational and confident cadence. Do not rush. This single paragraph connects the entire technical pipeline into one coherent story without technical jargon.

"Planning an expedition in the Southern Ocean is uniquely difficult because critical data—satellite sea ice, ocean currents, storm waves, seabed depths, and drifting icebergs—comes from fragmented scientific sources in completely different formats. In our offline pipeline, we standardize these datasets onto a unified, time-dependent H3 hexagonal map, forecasting sea-ice changes and iceberg drift across a ninety-day mission window. Once everything shares this common grid, the platform can evaluate any location across time: is this water physically usable, and how risky is it? When we combine this with a vessel like ORV Sagar Kanya, our Risk Engine immediately eliminates impassable areas like land, permanent ice shelves, and shallow grounding zones, while scoring navigable waters against operational risks like sea ice, iceberg encounters, and rough seas. Our routing engine then searches through the grid to calculate five distinct, optimal routes—such as fastest, safest, or fuel-efficient—so expedition leaders have real operational alternatives. Powered by Python, FastAPI, React, MapLibre, and Uber H3, the platform lets navigators scrub through time, inspect every cell, and understand the exact environmental reasoning behind every nautical mile."

---

## 1. Data Ingestion & Normalization

### Q: How do you normalize the different Antarctic datasets?
`[DERIVED]` We convert all disparate scientific formats (polar stereographic satellite rasters, NetCDF ocean grids, atmospheric GRIB files, and vector bathymetry) into a standardized internal data model. Coordinates are projected to WGS84 and indexed to discrete H3 hexagonal cells; timestamps are binned into canonical 6-hour intervals; and scalar values are clamped, quality-checked, and converted to uniform SI and nautical units.

### Q: What exact spatial aggregation formulas are used for vector fields like wind and ocean currents?
`[DERIVED]` Vector fields are never averaged using scalar speed and direction, as that causes catastrophic cancellation. Instead, the orthogonal zonal ($u$, Eastward) and meridional ($v$, Northward) components are averaged independently:
$$\bar{u} = \frac{1}{N}\sum_{i=1}^N u_i, \quad \bar{v} = \frac{1}{N}\sum_{i=1}^N v_i$$
Derived speed and compass direction are computed strictly after vector aggregation:
$$\text{Speed} = \sqrt{\bar{u}^2 + \bar{v}^2}, \quad \text{Direction} = \text{atan2}(\bar{u}, \bar{v}) \pmod{360^\circ}$$
*Say it simply:* We average the East-West and North-South push separately before figuring out the final speed and heading.

### Q: How do you handle circular wave directions during spatial aggregation?
`[DERIVED]` Ordinary arithmetic averaging of circular compass angles produces severe errors near the $0^\circ / 360^\circ$ boundary (for example, $359^\circ$ and $1^\circ$ average to $180^\circ$ South instead of $0^\circ$ North). We enforce circular trigonometric vector summation:
$$\bar{\theta} = \text{atan2}\left(\frac{1}{N}\sum_{i=1}^N \sin(\theta_i), \frac{1}{N}\sum_{i=1}^N \cos(\theta_i)\right) \pmod{360^\circ}$$
*Say it simply:* We convert angles into trigonometry coordinates so North wraps around seamlessly.

### Q: Why can't you simply average all data across a cell?
`[DERIVED]` Environmental data represents fundamentally different physical categories. Averaging categorical terrain masks destroys coastlines; averaging bathymetric depth obscures minimum shallow pinnacles that cause ship grounding; and averaging vector winds as raw speeds ignores whether gusts oppose each other.

### Q: How do you handle different spatial resolutions?
`[DERIVED]` We use Uber's H3 discrete global grid system as our canonical spatial integration canvas. Continuous vector coastlines (SCAR ADD) are sampled via exact polygon-area intersections; coarse raster data (such as 25 km NSIDC sea ice or 0.25° ECMWF wind) is resampled to cell centroids with area-weighted interpolation.

### Q: How do you handle different time resolutions?
`[USER_CONFIGURED]` We establish a canonical 6-hour discrete time step ($T+0, T+6\text{h}, T+12\text{h}, \dots$). Fast-updating ocean physics and wave models (3–6 hourly) align directly to these bins, while daily satellite sea ice is held constant across each 24-hour cycle tagged with a `PERSISTED` quality flag.

### Q: How do you handle missing values or sensor dropouts?
`[DERIVED]` Missing values are detected during ingestion and flagged with a degraded `data_quality_risk` score (a penalty of $-0.15$ confidence per missing physical parameter). The platform fills missing transient fields with seasonal climatological baselines rather than failing silently.

### Q: How do you handle land, coast, and ice-shelf cells?
`[OFFICIAL]` We ingest the authoritative SCAR Antarctic Digital Database (ADD v7.12) in Antarctic Polar Stereographic projection (`EPSG:3031`). Each cell calculates exact area fractions for ocean, continental land, ice shelves, and ice tongues. Any cell with $(\text{land\_fraction} + \text{ice\_shelf\_fraction}) \ge 0.5$ is flagged `is_blocked = True`.

### Q: How do you prevent invalid scientific values from entering the routing system?
`[DERIVED]` Every ingestion pipeline applies strict Pydantic boundary schemas with validation gates. Negative wave heights, sea-ice concentrations outside $[0.0, 1.0]$, sensor error flags (such as NSIDC 254 for land and 255 for missing), and negative water depths are sanitized and logged before graph ingestion.

---

## 2. Discrete Global Grid System (Uber H3)

### Q: What is H3?
`[OFFICIAL]` H3 is an open-source Discrete Global Grid System (DGGS) developed by Uber that partitions the surface of the Earth into a hierarchical hexagonal grid mapped onto a spherical icosahedron.

### Q: Why did you choose H3 over a traditional latitude/longitude raster grid?
`[DERIVED]` Latitude/longitude grids suffer from severe meridian convergence at the poles, compressing longitude lines into microscopic slivers near Antarctica and distorting distance and area calculations. H3 minimizes area distortion and provides uniform adjacency across the Southern Ocean.

### Q: Why hexagons instead of squares or triangles?
`[DERIVED]` Hexagons have a single, uniform neighbor distance: every adjacent cell centroid is equidistant (sharing 6 identical edge-adjacent neighbors). In square grids, diagonal neighbors are $\sqrt{2} \approx 1.414\times$ further away, creating artificial directional bias and zigzag path artifacts during graph routing.

### Q: What H3 resolution are you using?
`[USER_CONFIGURED]` We use **H3 Resolution 5** as our primary operational baseline for the mission corridor.

### Q: Why Resolution 5?
`[DERIVED]` Resolution 5 hexagons have an average edge length of $\approx 8.54\text{ km}$ and an area of $\approx 252.9\text{ km}^2$. For a 6,600-nautical-mile polar voyage, this provides sufficient detail to navigate coastal access corridors while keeping the graph search small enough to execute in sub-second response times.

### Q: How do you map iceberg observations onto H3?
`[DERIVED]` Exact $(lat, lon)$ points from iceberg tracking databases are mapped to their containing H3 cell using `h3.latlng_to_cell(lat, lon, resolution=5)`. The exact geographical coordinates are retained in metadata, while the H3 cell serves as the spatial indexing key.

### Q: How does H3 become a routing graph?
`[DERIVED]` Each navigable H3 cell represents a graph node. The routing graph evaluates candidate directed edges between topological neighbor cells using `h3.grid_disk(cell, 1)`, computing great-circle distances and forward azimuth bearings between centroids.

### Q: How many neighboring cells does each cell have?
`[OFFICIAL]` In H3, regular hexagonal cells have exactly **6 neighbors**. (Only 12 pentagonal cells exist globally across the entire planet to close the icosahedron, none of which disrupt our Southern Ocean mission corridor).

---

## 3. Sea-Ice Machine Learning & Forecasting

### Q: Where exactly is the AI in the platform?
`[DERIVED]` The AI component is our **Ice-kNN-South** model, located in `ice_knn/`. It performs analog spatiotemporal forecasting of Antarctic Sea Ice Concentration (SIC) and concentration anomalies up to 90 days into the future.

### Q: What model architecture are you using?
`[DERIVED]` Ice-kNN-South uses a combined **Principal Component Analysis (PCA) and k-Nearest Neighbors ($k=30$) analog forecasting** architecture. It projects high-dimensional environmental fields into low-dimensional latent spaces and retrieves historical analog evolution states.

### Q: Why did you choose an analog k-NN approach instead of a deep-learning U-Net or ConvLSTM?
`[DERIVED]` Deep neural networks require massive training datasets, heavy GPU clusters, and frequently hallucinate physically impossible sea-ice dynamics in data-sparse polar regimes. The k-NN analog approach is physically constrained: every forecasted state is a weighted blend of observed historical Antarctic evolutions, ensuring physically realistic sea-ice growth and retreat without runtime GPU dependencies.

### Q: What input data does the model use?
`[OFFICIAL]` The model uses historical NSIDC daily Sea Ice Concentration, ERA5 atmospheric reanalysis (2-meter air temperature, 10-meter wind vectors, and geopotential height), and CMEMS ocean physics (Sea Surface Temperature and surface currents).

### Q: What is the prediction horizon?
`[USER_CONFIGURED]` The model produces forecasts up to **90 days (T+0 to T+90)**, matching the operational duration of an Indian Antarctic Scientific Expedition.

### Q: Is the model retrained live during route planning?
`[POC SIMPLIFICATION]` No. The model weights and analog indices are precomputed and frozen offline. Runtime route planning queries precomputed forecast fields to guarantee sub-second routing performance and deterministic mission planning.

### Q: What is "synthetic SIC" and why is it used in the POC?
`[POC SIMPLIFICATION]` In the POC, runtime route planning utilizes a deterministic synthetic SIC pathway that mathematically replicates the historical seasonal summer retreat (SIC decreasing from December through February). This allows judges to verify real-time routing responsiveness and seasonal ice avoidance without waiting for external multi-gigabyte satellite NetCDF downloads.

---

## 4. Iceberg Physics & Drift Modeling

### Q: How do you predict iceberg movement?
`[DERIVED]` Iceberg drift is computed using a **physics-based Lagrangian momentum conservation model** that integrates hydrodynamic and aerodynamic drag forces forward in time using spherical geodesic kinematics.

### Q: Why use physics instead of machine learning for icebergs?
`[DERIVED]` There are only ~73 major tracked icebergs in the entire Antarctic database, providing far too few samples for deep learning models to generalize without severe overfitting. In contrast, fluid dynamic momentum equations reliably govern iceberg motion regardless of location.

### Q: What forces are included in the iceberg drift model?
`[DERIVED]` The governing force balance per unit mass is:
$$\frac{d\mathbf{V}_i}{dt} = \mathbf{a}_{\text{ocean}} + \mathbf{a}_{\text{air}} + \mathbf{a}_{\text{coriolis}} + \mathbf{a}_{\text{seaice}} + \mathbf{a}_{\text{boundary}}$$
- $\mathbf{a}_{\text{ocean}}$: Quadratic hydrodynamic drag from relative ocean currents:
  $$\mathbf{a}_{\text{ocean}} = \frac{1}{2}\rho_w C_w \frac{A_w}{M} |\mathbf{U}_o - \mathbf{V}_i|(\mathbf{U}_o - \mathbf{V}_i)$$
- $\mathbf{a}_{\text{air}}$: Quadratic aerodynamic drag from 10m surface winds:
  $$\mathbf{a}_{\text{air}} = \frac{1}{2}\rho_a C_a \frac{A_a}{M} |\mathbf{U}_a - \mathbf{V}_i|(\mathbf{U}_a - \mathbf{V}_i)$$
- $\mathbf{a}_{\text{coriolis}}$: Planetary rotational deflection: $\mathbf{a}_{\text{coriolis}} = [f v_i, -f u_i]^T$
- $\mathbf{a}_{\text{seaice}}$: Drag dampening from surrounding pack ice: $\mathbf{a}_{\text{seaice}} = -\gamma_{\text{ice}} C_{\text{ice}}^{1.8} (\mathbf{V}_i - \mathbf{U}_{\text{ice}})$
- $\mathbf{a}_{\text{boundary}}$: Grounding against bathymetric shoals or SCAR ADD coastlines.

### Q: How do you calculate the Coriolis acceleration?
`[DERIVED]` The Coriolis parameter is calculated as:
$$f = 2\Omega \sin(\phi)$$
where $\Omega = 7.292115 \times 10^{-5}\text{ rad/s}$ and $\phi$ is latitude. In the Southern Hemisphere ($\phi < 0$), $f$ is strictly negative, correctly deflecting moving icebergs to the **left** of their velocity vector.

### Q: Do ocean currents or winds have a bigger effect on icebergs?
`[DERIVED]` Ocean currents dominate tabular iceberg motion by approximately **60 to 1**. Because tabular icebergs have 89% of their mass submerged ($H_{\text{draft}} = 0.89 H_{\text{total}}$) and seawater is ~820 times denser than air, current drag completely outweighs surface windage.

### Q: Why do you generate an ensemble of trajectories?
`[DERIVED]` Environmental forecasts contain uncertainty, and iceberg drag coefficients vary with underwater melting. We run **50-member Monte Carlo ensembles** per iceberg, perturbing drag coefficients ($\pm 15\%$) and wind encounter angles ($\pm 10^\circ$) to produce a realistic spatial dispersion cone over 90 days.

### Q: What does "Iceberg Hazard" actually mean? Is it collision probability?
`[DERIVED]` **No, iceberg hazard is NOT certified collision probability.** It is a normalized spatial occupancy density:
$$\text{Hazard}(c, t) = \frac{\text{Ensemble members occupying cell } c \text{ at time } t}{\text{Total ensemble members}}$$
It quantifies the relative likelihood of encountering an iceberg in that cell, but does not model fine-grained ship hull collision cross-sections.

---

## 5. Environmental Risk Engine

### Q: What does the Risk Engine do?
`[DERIVED]` The Risk Engine evaluates H3 cells, transit segments, and complete routes against vessel capabilities and authoritative boundaries. It outputs a structured `RiskProfile` separating absolute non-negotiable blocks (`hard_blocked = True`) from relative operational penalties (`composite_risk`).

### Q: What is the difference between a hard constraint and a soft penalty?
`[DERIVED]`
- **Hard Constraints**: Physical or legal impossibilities that immediately prune an edge from the routing graph (cost = $\infty$). The ship cannot physically exist there.
- **Soft Penalties**: Navigable environmental conditions (such as 4-meter waves or 8% sea ice) that degrade speed, increase fuel burn, and add a weighted cost to guide the route planner around danger when a safer bypass exists.

### Q: What are your hard constraints?
`[OFFICIAL]`
1. **Continental Land & Permanent Ice Shelves**: SCAR ADD v7.12 mask (`LAND`, `ICE_SHELF`, `ICE_TONGUE`).
2. **Bathymetric Grounding**: Seafloor depth $\le$ vessel draft ($5.6\text{ m}$).
3. **Under-Keel Clearance Margin**: Depth $-$ Draft $< 3.0\text{ m}$.
4. **Vessel Sea-Ice Limit**: Sea-ice concentration exceeding vessel certified limit (SIC $> 15\%$ for ORV Sagar Kanya).

### Q: How is Composite Risk calculated?
`[USER_CONFIGURED]` Composite risk is a normalized weighted sum of 7 decomposed risk factors:
$$R_{\text{composite}} = w_{\text{ice}} R_{\text{ice}} + w_{\text{berg}} R_{\text{berg}} + w_{\text{wave}} R_{\text{wave}} + w_{\text{wind}} R_{\text{wind}} + w_{\text{bathy}} R_{\text{bathy}} + w_{\text{curr}} R_{\text{curr}} + w_{\text{conf}} R_{\text{conf}}$$
Where the baseline weights defined in `data/config/risk/risk_policy.json` are:
- Sea Ice ($w_{\text{ice}}$): **0.35**
- Iceberg Hazard ($w_{\text{berg}}$): **0.25**
- Waves ($w_{\text{wave}}$): **0.15**
- Wind ($w_{\text{wind}}$): **0.10**
- Bathymetry ($w_{\text{bathy}}$): **0.05**
- Current ($w_{\text{curr}}$): **0.05**
- Data Quality / Confidence ($w_{\text{conf}}$): **0.05**
The weights strictly sum to $1.0$.

### Q: Where did the risk weights come from? Are they learned by AI?
`[USER_CONFIGURED]` No, the weights are **not learned by AI**. They are configured operational policy parameters derived from standard polar navigation practice (where sea ice and icebergs represent primary catastrophic hull hazards, while wind and current represent secondary efficiency concerns). NCPOR voyage planners can adjust these weights via configuration.

---

## 6. Vessel Configuration & Bathymetry

### Q: What vessel are you modeling?
`[OFFICIAL]` We model the **ORV Sagar Kanya**, India's premier oceanographic research vessel owned by MoES/NCPOR and operated by the Shipping Corporation of India (SCI).

### Q: What are her official parameters versus assumptions?
`[OFFICIAL]` Length Overall ($100.34\text{ m}$), Beam ($16.39\text{ m}$), Maximum Draft ($5.60\text{ m}$), Gross Tonnage ($4888\text{ GT}$), Propulsion Power ($2 \times 1230\text{ kW}$ twin diesel-electric), Bunker Capacity ($433\text{ m}^3 \approx 368\text{ MT}$), and Endurance ($45\text{ days}$) are **official published specifications**.
`[ASSUMED]` Hull wave drag coefficients, fuel hotel load ($1.44\text{ MT/day}$), and minimum steerageway speed ($4.0\text{ knots}$) are engineering assumptions.

### Q: What is Sagar Kanya's Ice Class rating?
`[OFFICIAL]` Official NCPOR records do not cite a certified IACS Polar Class (PC1–PC7) or Finnish-Swedish rating; her ice class is formally documented as `UNKNOWN`. She is an open-ocean research vessel, not an icebreaker.
`[USER_CONFIGURED]` We configure a conservative operational ceiling of **15% Sea Ice Concentration (SIC $\le 0.15$)**. Any cell exceeding 15% SIC is strictly pruned from Sagar Kanya's routing network.

### Q: How do you calculate Under-Keel Clearance (UKC)?
`[DERIVED]` Using GEBCO 2026 positive water depth $D_{\text{depth}}$ and operating draft $T = 5.6\text{ m}$:
$$\text{UKC} = D_{\text{depth}} - T$$
If $\text{UKC} < 3.0\text{ m}$, the transition is hard-blocked.

---

## 7. Speed, Ocean Currents, and Travel Time

### Q: What is the difference between STW and SOG?
`[DERIVED]`
- **Speed Through Water (STW)**: The speed at which the vessel moves through the surrounding water mass, determined by engine power minus wave and ice drag.
- **Speed Over Ground (SOG)**: The actual speed of the vessel relative to the seabed, calculated by adding the along-track ocean current to STW:
  $$\text{SOG} = \text{STW} + V_{\text{along-track}}$$

### Q: How do you calculate along-track ocean current?
`[DERIVED]` Using zonal current $u$ (Eastward) and meridional current $v$ (Northward) projected onto ship true heading $\theta$ ($0^\circ = \text{North}, 90^\circ = \text{East}$):
$$V_{\text{along-track}} = (u \sin\theta + v \cos\theta) \times 1.94384 \text{ [knots]}$$
- If $V_{\text{along-track}} > 0$: Favorable tail current (increases SOG, saves fuel and time).
- If $V_{\text{along-track}} < 0$: Opposing head current (decreases SOG, increases travel time).

### Q: How do you calculate segment travel time and total route duration?
`[DERIVED]` Leg duration is calculated strictly from distance and SOG:
$$\Delta t_i = \frac{d_i}{\text{SOG}_i} \quad [\text{hours}]$$
Total sailing time is the sum of leg durations: $T_{\text{sailing}} = \sum_{i} \Delta t_i$. Total expedition mission duration adds the configured scientific station dwell times ($48\text{ h}$ at Bharati, $72\text{ h}$ at Maitri).

### Q: Why did earlier prototype versions produce erroneous 50–80 day transit times?
`[DERIVED]` Auditing revealed two critical bugs in the early prototype router:
1. **Silent 1.5-Knot Ice Crawl Fallback**: When an edge touched ice exceeding limits, instead of pruning the edge, the router silently assigned a 1.5-knot crawl speed. Over thousands of miles, traveling at 1.5 knots artificially inflated transit times to 50–80 days.
2. **Current Double-Counting**: Ocean currents were subtracted from STW and then re-penalized in leg duration formulas.
Both bugs were eliminated: hard constraints strictly prune impassable ice, and `VesselSpeedModel` rigorously calculates $\text{SOG} = \text{STW} + V_{\text{along-track}}$, producing reconciled, realistic 28–35 day sailing times for the 6,600 NM circuit.

---

## 8. Routing Algorithm & State Space

### Q: What routing algorithm are you using?
`[DERIVED]` We use a **4D time-dependent A* heuristic graph search algorithm** implemented in `packages/routing/src/routing/grid_router.py`.

### Q: What is the 4D state space?
`[DERIVED]` The routing state is:
$$\text{State} = (\text{cell\_id}, \text{time\_bucket})$$
where $\text{cell\_id}$ is the 15-character canonical H3 hexagon index (e.g. `85ad3617fffffff`) and $\text{time\_bucket} = \lfloor (t - t_0) / 12\text{ hours} \rfloor$. This allows the router to evaluate environmental conditions at the exact predicted hour the ship arrives at that cell.

### Q: What happens if no feasible route exists?
`[DERIVED]` If severe weather or pack ice blocks all forward paths under Sagar Kanya's limits, the A* search returns failure (`is_feasible = False`) with clear diagnostics identifying the blocking barrier (e.g., "Prydz Bay approach blocked by SIC > 15%"). It does not fabricate a path through land or impenetrable ice.

---

## 9. Route Objectives & Pareto Optimization

### Q: How are the 5 routing objectives defined mathematically?
`[DERIVED]`
1. **`SHORTEST`**: Minimizes geographic distance:
   $$\text{Cost} = d_{\text{edge}} \quad [\text{NM}]$$
2. **`FASTEST`**: Minimizes transit duration:
   $$\text{Cost} = \Delta t_{\text{hours}} = \frac{d_{\text{edge}}}{\text{SOG}} \quad [\text{hours}]$$
3. **`SAFEST`**: Heavily penalizes environmental risks:
   $$\text{Cost} = d_{\text{edge}} \times \left[1.0 + 15(\text{SIC})^{1.5} + 10(H_{\text{berg}})^{1.5} + 3\max\left(0, \frac{H_s-3}{4}\right) + 20(R_{\text{composite}})^{1.5}\right]$$
4. **`FUEL_EFFICIENT`**: Minimizes total fuel consumption using the naval architecture power curve:
   $$\text{Cost} = \text{Leg Fuel Burn} \quad [\text{Metric Tons}]$$
5. **`BALANCED`**: Multi-criteria compromise:
   $$\text{Cost} = 0.35\left(\frac{\Delta t}{24}\right) + 0.35\left(\frac{\text{Fuel}}{20}\right) + 0.20\left(\frac{R_{\text{composite}} \cdot d}{30}\right) + 0.10\left(\frac{d}{100}\right)$$

### Q: Are the five routes guaranteed to be completely different?
`[DERIVED]` Not necessarily. In open, benign deep water, the shortest, fastest, and fuel-efficient paths often coincide. However, when storm waves, currents, or sea-ice margins appear, the routes diverge significantly: `SAFEST` steers wide around ice and storms, `FASTEST` detours to pick up tail currents, and `SHORTEST` hugs the direct geodesic line.

---

## 10. Multi-Objective Normalization

### Q: How do you combine distance, time, fuel, and risk when they have different units?
`[DERIVED]` We use dimensional scaling factors that normalize each term into a comparable daily dimensionless magnitude:
- Time is normalized by $24\text{ hours}$ ($1\text{ day}$).
- Fuel is normalized by $20\text{ Metric Tons}$ (nominal full-power daily consumption).
- Risk is weighted by distance and normalized by $30\text{ risk-NM}$.
- Distance is normalized by $100\text{ NM}$.
This prevents any single variable (like distance in thousands of miles) from overpowering time or risk.

---

## 11. Fuel Consumption Modeling

### Q: How do you estimate fuel consumption?
`[DERIVED]` We use a reduced-order naval architecture power model based on the admiralty speed-power cubic law:
$$P_{\text{prop}} = P_{\text{base}} \times \left(\frac{V_{\text{effective}}}{V_{\text{cruise}}}\right)^3 \times \left(1 + f_{\text{wave\_res}} + f_{\text{ice\_res}}\right) + P_{\text{hotel}}$$
- Propulsion power scales with the cube of speed through water.
- Added drag from waves ($H_s > 3.0\text{m}$) and ice concentration increases required engine torque.
- Auxiliary hotel load is constant at $1.44\text{ MT/day}$ ($0.06\text{ MT/h}$) for science labs and life support.

### Q: Is fuel consumption measured or estimated?
`[POC SIMPLIFICATION]` It is an engineering estimate based on standard naval architectural power curves and Sagar Kanya's published fuel rate ($8.16\text{ MT/day}$ cruising at 9 knots). It has not yet been calibrated against live engine-room telemetry.

---

## 12. Route Visualization & Frontend Integrity

### Q: Are the routes on the map manually drawn or approximate lines?
`[DERIVED]` **No. Every route rendered on the map is the exact sequence of H3 cells produced by the routing algorithm.** The backend stores every traversed H3 cell ID in the GeoJSON response (`route.cells`), and the frontend MapLibre layer renders those exact centroid coordinates.

### Q: Can an operator inspect individual route segments?
`[DERIVED]` Yes. Clicking any route segment opens the Segment Inspector, showing the exact from-cell, to-cell, SOG, STW, along-track current, wave height, fuel consumption, and risk breakdown for that specific leg.

---

## 13. System Validation & Verification

### Q: How do you validate the entire system?
`[DERIVED]` Validation is conducted across 5 layers:
1. **Scientific Validation**: Validating sea-ice predictions against satellite observations using RMSE.
2. **Physics Validation**: Verifying that iceberg drift conserves momentum and deflects left under Southern Hemisphere Coriolis.
3. **Reconciliation Auditing**: Verifying that $\text{Average SOG} \times \text{Sailing Time} \equiv \text{Total Distance}$ within $\pm 0.1\%$.
4. **Automated Unit & Integration Tests**: 10 comprehensive tests in `tests/test_h3_routing_integration.py` verifying graph topology, non-navigability of land, and monotonic ETA progression.
5. **Visual Verification**: Verifying that rendered map routes never cross SCAR ADD land boundaries.

---

## 14. "Why Not Just Use X?"

### Q: Why not use Google Maps or standard marine AIS routers?
`[DERIVED]` Commercial navigation systems assume static coastlines and open water. They do not model dynamic 90-day sea-ice freeze/thaw cycles, 73 drifting tabular icebergs, polar-class ice capability thresholds, or high-latitude geodesic convergence.

### Q: Why not use a straight-line great-circle route?
`[DERIVED]` A straight-line route from Cape Town to Bharati cuts directly through heavy Antarctic pack ice and grounded iceberg fields in Prydz Bay, which would trap or crush a non-icebreaker like Sagar Kanya.

### Q: Why not calculate everything live instead of precomputing?
`[DERIVED]` Simulating 50 ensemble tracks for 73 icebergs over 90 days requires calculating over 800,000 trajectory steps, which takes minutes of CPU time. Precomputing environmental grids allows the interactive dashboard to respond in milliseconds during live mission briefings.

---

## 15. Known Limitations & Product Boundaries

### Q: What are the biggest limitations of the current prototype?
`[POC SIMPLIFICATION]`
1. **Coarse Nearshore Bathymetry**: 15-arc-second GEBCO bathymetry lacks fine multibeam hydrographic soundings in unchartered Antarctic bays.
2. **Lack of Live Telemetry**: Fuel burn curves use naval architecture estimates rather than real-time engine-room torque sensors.
3. **Discrete Horizon Approximations**: Metocean forecasts beyond 7 days rely on seasonal climatology rather than coupled atmosphere-ice-ocean models.

### Q: Is this certified for autonomous ship navigation?
`[OFFICIAL]` **No.** AMIP is explicitly a **decision-support platform** for human expedition leaders, captains, and NCPOR operations planners. It is not an autonomous autopilot.

---

## 16. Rapid-Fire Exam (25 One-Sentence Answers)

1. **What is H3?** Uber's discrete global grid system that divides the Earth into hexagonal spatial cells.
2. **What is SIC?** Sea Ice Concentration, the fraction of an ocean cell covered by sea ice from 0.0 to 1.0.
3. **What is SOG?** Speed Over Ground, the actual forward speed of the ship relative to the seabed.
4. **What is STW?** Speed Through Water, the ship's speed relative to the water mass before current assistance.
5. **What is UKC?** Under-Keel Clearance, the water depth remaining between the vessel's lowest hull point and the seabed.
6. **What is an ensemble?** A collection of Monte Carlo simulations run with slightly perturbed physics to map trajectory uncertainty.
7. **What is Iceberg Hazard?** The normalized spatial occupancy density of simulated iceberg trajectories in a cell.
8. **Is Iceberg Hazard collision probability?** No, it is a spatial encounter likelihood proxy, not a calibrated hull collision probability.
9. **What is a hard constraint?** A non-negotiable physical or regulatory barrier, such as land or grounding, that sets edge cost to infinity.
10. **What is a soft penalty?** A navigable environmental hazard, such as waves or ice, that adds a weighted cost to guide the route away from danger.
11. **Where is the AI?** In the Ice-kNN-South model that forecasts 90-day sea-ice concentration anomalies.
12. **Why physics for icebergs instead of ML?** Because 73 historical icebergs are too few to train deep learning, whereas fluid dynamics equations govern drift universally.
13. **Why precompute data?** To deliver sub-second interactive route planning during live operational briefings.
14. **Why five route alternatives?** To give mission commanders explicit trade-offs between distance, speed, safety, and fuel economy.
15. **Why hexagons instead of squares?** Hexagons have equidistant neighbors in all six directions, eliminating directional path distortion.
16. **Does the frontend calculate routes?** No, the backend A* router computes the route, and the frontend faithfully renders the resulting H3 cells.
17. **Is fuel consumption exact?** No, it is a reduced-order naval architecture estimate based on the cubic speed-power law.
18. **Can Sagar Kanya break ice?** No, she is an uncertified open-water research vessel restricted to a maximum of 15% sea ice concentration.
19. **What caused the 50-80 day bug in early prototypes?** A silent 1.5-knot ice crawl fallback and double-counted ocean currents.
20. **How was it fixed?** By pruning impassable ice with hard constraints and calculating SOG strictly as STW plus along-track current.
21. **What is the canonical expedition circuit?** Cape Town to Bharati (48h dwell), to Maitri/India Bay (72h dwell), returning to Cape Town (~6,606 NM).
22. **What is SCAR ADD?** The Scientific Committee on Antarctic Research Antarctic Digital Database, the authoritative coastline boundary.
23. **How does current affect SOG?** Currents parallel to heading are added to STW; opposing currents subtract from SOG.
24. **Can risk weights be changed?** Yes, NCPOR operators can modify the weights in `data/config/risk/risk_policy.json`.
25. **Is this system production-ready?** It is an advanced proof-of-concept decision-support platform ready for operational validation with NCPOR.

---

## 17. Formula Cheat Sheet

| Parameter | Formula | Code Implementation | Spoken Explanation |
|---|---|---|---|
| **Vector Current Along Track** | $V_{\text{along}} = (u \sin\theta + v \cos\theta) \times 1.94384$ | `speed_model.py:100` | Current projected onto ship heading and converted to knots. |
| **Speed Over Ground** | $\text{SOG} = \text{STW} + V_{\text{along}}$ | `speed_model.py:122` | Speed through water plus along-track current push. |
| **Leg Travel Time** | $\Delta t = \frac{d}{\text{SOG}}$ | `speed_model.py:128` | Leg distance divided by actual speed over ground. |
| **Under-Keel Clearance** | $\text{UKC} = \text{Depth} - \text{Draft}$ | `engine.py:315` | Water depth minus ship operating draft. |
| **Coriolis Parameter** | $f = 2\Omega \sin(\phi)$ | `iceberg_trajectory_model.md:63` | Earth rotational frequency modulated by latitude. |
| **Circular Angle Average** | $\bar{\theta} = \text{atan2}(\sum \sin\theta, \sum \cos\theta)$ | `h3_spatial_integration.md:56` | Trigonometric angle averaging that wraps around 360°. |
| **Composite Risk** | $R_{\text{comp}} = \sum_{i=1}^7 w_i R_i$ | `engine.py:263` | Weighted sum of 7 normalized environmental risk factors. |
| **Cubic Propulsion Power** | $P = P_{\text{base}} (V/V_{\text{cruise}})^3 (1 + f_{\text{env}}) + P_{\text{hotel}}$ | `fuel_model.py:64` | Naval architecture cubic speed-power relationship. |
| **Balanced Edge Cost** | $0.35\frac{\Delta t}{24} + 0.35\frac{\text{Fuel}}{20} + 0.20\frac{R \cdot d}{30} + 0.10\frac{d}{100}$ | `grid_router.py:121` | Dimensionless Pareto trade-off between time, fuel, risk, and distance. |
| **Iceberg Hazard Density** | $H(c, t) = \frac{N_{\text{active members in cell}}}{N_{\text{total ensemble members}}}$ | `h3_spatial_integration.md:87` | Spatial density of simulated ensemble tracks in a cell. |
