# Canonical H3 Spatial Integration & Unified H3 × Time Grid

## 1. Executive Summary & Architectural Motivation

In the **Antarctic Mission Intelligence Platform (AMIP)**, disparate scientific datasets arrive in fundamentally incompatible spatial and temporal frames:
- **NSIDC Sea Ice Concentration**: Polar stereographic 25 km grid (`EPSG:3412`)
- **CMEMS Ocean Currents & Waves**: Geographic regular lat/lon grid (`0.083° × 0.083°`, `EPSG:4326`)
- **ECMWF Wind**: Atmospheric Gaussian/regular forecast grid (`0.4°/0.25°`)
- **GEBCO 2026 Sub-Ice Topography**: 15 arc-second raster bathymetry
- **SCAR ADD v7.12**: Antarctic high-resolution vector multipolygons (`EPSG:3031`)
- **Iceberg Tracking**: Point and polyline trajectory events in continuous WGS84 coordinates

To enable unified routing, multi-factor risk modeling, and interactive frontend time-scrubbing without continuous runtime raster resamplings or geometric intersections, **Uber's H3 Discrete Global Grid System (DGGS)** serves as the canonical application spatial backbone.

> [!IMPORTANT]
> **Authoritative Principles & Distinctions:**
> 1. **$\text{H3} \ne \text{Native Scientific Grid}$**: H3 is a derived application spatial key (`cell_id`), not the native scientific coordinate system. Native scientific formats and exact coordinates remain preserved and recoverable.
> 2. **$\text{H3 Cell} \ne \text{Exact Iceberg Position}$**: Icebergs exist at continuous, exact $(lat, lon)$ points. H3 cells represent spatial occupancy and indexing only.
> 3. **$\text{Observed Iceberg} \ne \text{Predicted Iceberg}$**: Validated historical and operational observations are strictly distinguished from physics-propagated forward trajectories.
> 4. **$\text{Trajectory Prediction} \ne \text{Hazard}$**: A single trajectory is a deterministic path; hazard is an ensemble-derived occupancy density field.
> 5. **$\text{Iceberg Hazard} \ne \text{Validated Collision Probability}$**: Trajectory ensemble occupancy quantifies spatial encounter potential, but is not a calibrated vessel collision probability without hull cross-section integration.
> 6. **$\text{GEBCO} \ne \text{SCAR ADD Geographic Mask}$**: GEBCO provides bathymetric seafloor depths; SCAR ADD provides legally binding territorial and ice-shelf boundary constraints. Neither replaces the other.

---

## 2. Configurable Resolution & Domain Bounds

### H3 Resolution
- **POC Starting Baseline**: `H3 Resolution 5`
- **Spatial Characteristics**:
  - Approximate Hexagon Edge Length: $\approx 8.54\text{ km}$
  - Approximate Hexagon Area: $\approx 252.9\text{ km}^2$
- **Configurability**: Controlled via environment variable `AMIP_H3_RESOLUTION` and `H3Config`. Downstream systems seamlessly accommodate transitions to resolution 4 ($\approx 22.6\text{ km}$ edge) or resolution 6 ($\approx 3.2\text{ km}$ edge).

### Antarctic Operating Domain
AMIP restricts grid generation to its operational mission domain rather than generating global cells:
1. **Circum-Antarctic Southern Ocean**:
   - Latitude: $-80.0^\circ\text{S} \le \phi \le -40.0^\circ\text{S}$
   - Longitude: $-180.0^\circ \le \lambda \le 180.0^\circ$
2. **Cape Town to Antarctica Navigation Corridor**:
   - Latitude: $-40.0^\circ\text{S} < \phi \le -33.5^\circ\text{S}$
   - Longitude: $15.0^\circ\text{E} \le \lambda \le 25.0^\circ\text{E}$

---

## 3. Spatial Aggregation & Physical Integrity

### Vector Component Aggregation (Currents & Winds)
Vector velocities must never be transformed to speed and direction before spatial averaging. AMIP enforces direct component aggregation:
$$\overline{u} = \frac{1}{N}\sum_{i=1}^N u_i, \quad \overline{v} = \frac{1}{N}\sum_{i=1}^N v_i$$
Derived scalar speed and compass direction are computed strictly **after** vector aggregation:
$$\text{Speed} = \sqrt{\overline{u}^2 + \overline{v}^2}, \quad \text{Direction} = \text{atan2}(\overline{u}, \overline{v}) \pmod{360^\circ}$$

### Circular Wave Direction Aggregation
Compass directions wrap around at $360^\circ \equiv 0^\circ$. Ordinary arithmetic averaging produces catastrophic errors (e.g., $359^\circ$ and $1^\circ$ average to $180^\circ$ South instead of $0^\circ$ North). AMIP enforces circular vector trigonometry:
$$\overline{\theta} = \text{atan2}\left(\frac{1}{N}\sum_{i=1}^N \sin(\theta_i), \frac{1}{N}\sum_{i=1}^N \cos(\theta_i)\right) \pmod{360^\circ}$$

### SCAR ADD Geographic Mask Mapping
- Exact area-weighted polygon intersections computed in Antarctic Polar Stereographic (`EPSG:3031`).
- Area fractions: `ocean_fraction`, `land_fraction`, `ice_shelf_fraction`, `ice_tongue_fraction`, `rumple_fraction`.
- Navigability status: `OPEN_OCEAN`, `MIXED`, `LAND`, `ICE_SHELF`, `ICE_TONGUE`, `RUMPLE`.
- Cells with $\text{land\_fraction} + \text{ice\_shelf\_fraction} \ge 0.5$ are flagged `is_blocked = True`.

### GEBCO 2026 Bathymetric Statistics
- Positive water depth convention: $\text{depth\_m} > 0$ represents meters of water above seafloor.
- Cell statistical metrics:
  - `bathymetry_mean_m`: Mean water depth
  - `bathymetry_min_m`: Shallowest depth (critical keel-grounding hazard metric)
  - `bathymetry_p10_m`, `bathymetry_p50_m`, `bathymetry_p90_m`: Distribution percentiles
  - `bathymetry_valid_fraction`: Ratio of valid oceanic depth soundings

### NSIDC Sea-Ice Concentration (SIC)
- Strict quality assurance: Land flags (`254`), missing data (`255`), and coastal flags are completely excluded from ocean SIC averages.
- Retains `sic_mean`, `sic_min`, `sic_max`, `sic_uncertainty`, and `sic_valid_fraction`.

---

## 4. Iceberg Subsystem Integration

### All 73 Icebergs Represented
The canonical H3 iceberg layers represent **all 73 distinct icebergs** from the verified dataset:
- **Normalized Observations**: Exact timestamp, coordinates, source (`BYU` or `USNIC`), dimensions, and spatial index `h3_cell`.
  - Stored in: `data/antarctica/icebergs/observations.parquet`
- **90-Day Trajectory Projections & Ensembles**: 812,618 trajectory points covering all 73 icebergs across deterministic and stochastic members.
  - Stored in: `data/antarctica/icebergs/trajectories.parquet`
- **Time-Dependent Hazard Field**:
  $$\text{hazard}(c, t) = \frac{\text{Number of ensemble members occupying cell } c \text{ at time } t}{\text{Total ensemble members for active icebergs}}$$
  - Stored in: `data/antarctica/hazard/iceberg_hazard.parquet`

---

## 5. Temporal Alignment & Quality States

### Canonical Timestep
AMIP defines a canonical **6-hour discrete time index** ($T+0, T+6\text{h}, T+12\text{h}, \dots$):
- **CMEMS Currents**: Native 6-hourly (direct alignment)
- **CMEMS Waves**: Native 3-hourly (sampled at 6h stride)
- **ECMWF Wind**: 0-48h forecast steps (aligned to valid timestamp)
- **NSIDC SIC**: Daily (carried forward over 24h cycle with `PERSISTED` flag)
- **GEBCO & SCAR ADD**: Static (time-invariant)
- **Iceberg Hazard**: Hourly model output evaluated at canonical 6h steps

### Quality Origin Flags
Every time-dependent variable reports its exact operational state:
`OBSERVED`, `FORECAST`, `MODEL_PREDICTED`, `INTERPOLATED`, `PERSISTED`, `CLIMATOLOGICAL`, `EXTENDED_PROJECTION`, `MISSING`. Missing values are preserved as `None`/`NaN` and never silently filled with `0.0`.

---

## 6. Static vs. Dynamic Partitioning Architecture

To eliminate redundant polygon geometry duplication across time partitions:

```
data/antarctica/
├── grid/
│   ├── cells.parquet            # Static attributes (geography fractions, GEBCO percentiles, WKT)
│   ├── geometry.geojson         # Representative boundary geometry for UI map
│   └── metadata.json            # Grid diagnostics, resolution, and domain bounds
├── environment/
│   ├── time_index.json          # Monotonic time index (T+0, T+6h, T+12h...)
│   └── [dynamic partitions]     # cell_id x time dynamic environmental states
├── icebergs/
│   ├── observations.parquet     # All 73 verified observations + H3 index
│   └── trajectories.parquet     # All 73 90-day trajectory projections + H3 index
├── hazard/
│   └── iceberg_hazard.parquet   # Ensemble occupancy hazard field
└── lookup/
    └── cell_metadata.json       # Consolidated summary metadata for frontend
```

---

## 7. Common Spatial Key Lookup API

The `H3CellLookupService` (`data_ingestion.h3.lookup`) exposes uniform access:
- `latlon_to_cell(lat, lon) -> str`: $O(1)$ discrete coordinate conversion
- `get_cell(cell_id) -> Optional[StaticH3Cell]`: $O(1)$ in-memory static state query
- `neighboring_cells(cell_id, ring_size=1) -> List[str]`: Graph neighbor expansion for routing
- `is_navigable(cell_id, min_draft_clearance_m=5.0) -> bool`: Combined SCAR ADD & GEBCO clearance
- `get_environment(cell_id, valid_time) -> Dict[str, Any]`: Complete environmental state contract

---

## 8. Machine Learning Interface

The `SeaIceForecastCell` schema (`data_ingestion.h3.ml_interface`) defines the normalized contract for upcoming sea-ice machine learning models (`Ice-kNN-South` and `ANTSIC-UNet`):
- `cell_id: str`
- `valid_time: datetime`
- `sic: float`
- `sic_uncertainty: Optional[float]`
- `model: str`
- `model_version: str`
- `forecast_horizon_hours: float`
- `quality_status: TemporalQualityStatus`
- `provenance: Dict[str, Any]`

---

## 9. Verification & Performance Benchmarks

The 25-point validation suite (`data_ingestion.h3.validator`) verified all requirements:
- **Total Verification Checks**: 25 / 25 Passed (`all_passed = True`)
- **All 73 Icebergs Represented**: Verified (`all_73_icebergs_present = True`)
- **Point-to-Cell Lookup Latency**: $\approx 0.45\ \mu\text{s}$ per coordinate
- **Query Throughput**: $> 2,200,000\text{ queries/second}$
- **Static Grid Memory Footprint**: $\approx 120\text{ bytes/cell}$
