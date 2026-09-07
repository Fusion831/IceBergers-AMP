# AMIP: Next Implementation Context
## Environmental Data Pipeline, Unified Grid, and Earth Map Visualization

### Purpose

The next implementation phase is the **AMIP Environmental Data Pipeline and Unified Computational Grid**. The purpose is to take environmental datasets from different scientific sources, normalize them, align them spatially and temporally, and expose one consistent environmental state for every AMIP computational grid cell and time.

The pipeline must support two consumers:

1. **AMIP backend computation:** risk, vessel performance, iceberg physics, and 4D routing.
2. **Earth-map visualization:** displaying the same environmental layers on the real geographic map in the web application, with a time slider and zoom-dependent detail.

The backend remains the computational source of truth. Google Earth Engine (GEE) is intended as a geospatial visualization/serving layer for map visualization, not as the routing engine.

---

## 1. Unified Environmental Representation

AMIP should treat the environment as a function of location and time:

```text
Environment(latitude, longitude, time)
```

The AMIP computational grid is the common representation into which the external datasets are transformed.

Each grid cell should have a stable identifier and geographic boundaries, for example:

```text
cell_id
latitude
longitude
lat_min
lat_max
lon_min
lon_max
```

The environmental state for a cell/time should be able to contain:

```text
sea_ice_concentration
sea_ice_uncertainty
current_u_ms
current_v_ms
wind_u_ms
wind_v_ms
wave_height_m
wave_direction_deg
wave_period_s
iceberg_hazard
bathymetry_depth_m
is_land
is_ice_shelf
is_navigable
provenance
```

Future sea-ice forecasts from Ice-kNN-South and ANTSIC-UNet will eventually populate the future SIC fields. Until those models are handed off, a placeholder or observed/reanalysis SIC layer can be used to develop the rest of the system.

---

## 2. Important Grid Principle

All external datasets do **not** necessarily use the same grid.

Examples include:

- NSIDC Antarctic SIC: polar-stereographic projected grid.
- Copernicus Marine: regular geographic ocean grid.
- ECMWF/ERA5: regular geographic atmospheric grid.
- GEBCO: high-resolution geographic bathymetry grid.
- Iceberg observations: point/vector observations rather than a raster grid.

Therefore, the pipeline must first normalize coordinate systems where necessary and then transform each source onto the AMIP computational grid.

Do not assume that every source arrives as a simple latitude/longitude array.

Do not blindly average every variable. Aggregation must depend on variable type.

Examples:

- Current `u/v`: spatially appropriate, preferably area-weighted aggregation/regridding.
- Wind `u/v`: spatially appropriate aggregation/regridding.
- Wave variables: appropriate interpolation/regridding.
- SIC: spatial aggregation with correct missing-data and land-mask handling.
- Bathymetry: appropriate spatial statistic for navigation use.
- Land/ice-shelf masks: categorical logic, not numerical averaging.
- Icebergs: retain point tracks first; later convert them into a time-dependent hazard/probability field.

The goal is not to make every source grid identical. The goal is to create one reliable AMIP representation.

---

## 3. Data Sources

### 3.1 Antarctic Sea Ice: NSIDC G02202 v6

Primary historical SIC dataset:

https://nsidc.org/data/g02202/versions/6

Use it to provide historical Antarctic sea-ice concentration. Preserve the native source grid, metadata, dates, masks, and missing values before regridding.

Near-real-time continuation to investigate/use separately:

https://nsidc.org/data/g10016/versions/4

Do not blindly concatenate the two products without verifying continuity and source-specific semantics.

Later, the trained AMIP ML models will produce future SIC fields using the shared model interface.

---

### 3.2 Ocean Currents: Copernicus Marine Global Ocean Physics

Product:

https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024

For the POC, use the **6-hourly currents** dataset as the primary navigation current source.

Required information:

```text
current_u
current_v
valid_time
latitude
longitude
```

Copernicus Marine provides an official Python/CLI Toolbox and programmatic subsetting capability. The implementation should query/subset by:

```text
bounding box
variable(s)
time range
```

rather than downloading full global files unnecessarily.

Official Toolbox information:

https://help.marine.copernicus.eu/en/articles/7949409-copernicus-marine-toolbox-introduction

Subset API:

https://help.marine.copernicus.eu/en/articles/8283072-copernicus-marine-toolbox-api-subset

The system should support automated retrieval of the latest available forecast data, while wording this as near-real-time/latest-available rather than promising zero-latency live data.

---

### 3.3 Waves: Copernicus Marine Global Ocean Waves

Product:

https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_WAV_001_027

Required variables for AMIP:

```text
significant wave height
wave direction
wave period
```

Only the variables required by the vessel-performance and risk layers should be ingested.

Subset geographically and temporally, then regrid onto the AMIP computational grid.

---

### 3.4 Weather/Wind: ECMWF ERA5 and Forecast Data

Historical/reanalysis dataset:

https://www.ecmwf.int/en/forecasts/datasets/era5-hourly-data-single-levels-1940-present

Operational/open forecast information:

https://www.ecmwf.int/en/forecasts/datasets/open-data

For routing, begin with:

```text
u10
v10
```

and derive wind speed and direction as needed.

For ML training, use the specific atmospheric variables required by the Ice-kNN-South and ANTSIC-UNet input schemas. Do not ingest every available ERA5 variable without a reason.

ERA5 should be treated as historical/reanalysis data. Future navigation uses the appropriate forecast source.

---

### 3.5 Bathymetry: GEBCO 2026

Dataset:

https://www.gebco.net/data-products/gridded-bathymetry-data

Use the appropriate Antarctic/under-ice bathymetry product for the mission region.

Convert the source into a clear positive water-depth representation:

```text
depth_m
```

Keep bathymetry separate from the land/ice-shelf geographic mask.

---

### 3.6 Geographic / Navigability Mask

Use an authoritative Antarctic coastline/ice-shelf/geographic dataset, or a verified existing project dataset if one is already present.

The output should distinguish at least:

```text
is_land
is_ice_shelf
is_navigable
```

Do not infer all geography from bathymetry alone.

User-defined avoidance zones remain runtime constraints and should not be permanently baked into the static mask.

---

### 3.7 Icebergs

USNIC Antarctic iceberg products:

https://usicecenter.gov/Products/Antarcicebergs

BYU Antarctic iceberg database:

https://www.scp.byu.edu/iceberg/database1.html

Ingestion should preserve iceberg observations as vector/time-series data:

```text
iceberg_id
latitude
longitude
observation_time
dimensions_if_available
source
```

These observations will later feed a physics-based iceberg trajectory model using currents, wind, sea ice, and uncertainty.

The trajectory model will produce a derived field such as:

```text
iceberg_hazard(cell, time)
```

The raw iceberg datasets should not be treated as a complete census of every iceberg.

---

## 4. AMIP Computational Grid

Create a fixed, configurable AMIP grid for the POC.

The grid must be able to support:

- a coarse trans-oceanic routing resolution;
- finer regional/science-area resolution;
- stable cell identifiers;
- cell boundaries and centroid coordinates;
- efficient spatial lookup;
- route-cell visualization;
- environmental attribution.

Do not make the grid ID dependent on fragile floating-point string formatting. Prefer stable row/column or equivalent grid indexing while keeping geographic coordinates separately.

Conceptually:

```text
AMIPGrid
    cell_id
    geometry / bounds
    centroid_lat
    centroid_lon
    row
    col
```

Every environmental source is transformed/regridded into this grid.

---

## 5. Recommended Python Geospatial/Data Stack

Use a stack that works both for scientific processing and for producing web-map-compatible outputs.

Primary tools:

```text
xarray       multidimensional scientific arrays
xESMF        structured-grid regridding
pyproj       coordinate/reference-system transformations
rasterio     raster processing and GeoTIFF/COG creation
GDAL         geospatial raster/vector utilities where required
GeoPandas    vector geospatial data
Shapely      geometry operations
NumPy        numerical processing
Pandas       tabular metadata/time-series handling
```

For storage of large time × latitude × longitude arrays, Zarr is a strong backend format. NetCDF remains useful for scientific interchange and validating source files.

For the map-visualization path, create **Cloud Optimized GeoTIFF (COG)** representations of raster layers so they can later be uploaded/registered as Earth Engine assets.

---

## 6. Storage Architecture

Maintain two representations where useful:

```text
Scientific / computational master
    ↓
Zarr / NetCDF / database-backed grid

Visualization representation
    ↓
Cloud Optimized GeoTIFF (COG)
```

The scientific master remains the source for risk, vessel performance, routing, and analysis.

COGs are the web-map/visualization representation.

Do not make Earth Engine the authoritative data store for routing.

---

## 7. Earth Map / Google Earth Engine Integration

The web application should ultimately display the AMIP layers **on the actual Earth map**, rather than rendering Antarctica as an isolated custom diagram.

Google Earth Engine can be used as the geospatial visualization/serving layer for raster environmental fields. AMIP should create georeferenced raster products, preferably COGs, with explicit geographic metadata and timestamps.

The visualization path is:

```text
Raw scientific datasets
        ↓
Normalization / regridding
        ↓
AMIP computational grid
        ↓
Raster export
        ↓
Cloud Optimized GeoTIFFs
        ↓
Google Cloud Storage / Earth Engine assets
        ↓
Earth Engine Image / ImageCollection
        ↓
Web map
```

For time-varying layers, use an Earth Engine ImageCollection conceptually corresponding to timestamped environmental states.

Examples:

```text
AMIP/SIC/
    timestamp_1
    timestamp_2
    timestamp_3

AMIP/CURRENTS/
    timestamp_1
    timestamp_2
    timestamp_3

AMIP/WAVES/
    timestamp_1
    timestamp_2
    timestamp_3
```

Each image should carry temporal metadata so the frontend/time slider can select the appropriate state.

Earth Engine can be used to visualize:

```text
sea-ice concentration
sea-ice uncertainty
ice edge
current-related layers
wind
waves
bathymetry
risk
```

Vector layers such as iceberg tracks can remain vector features and be rendered separately. An `iceberg_hazard` raster can be produced for routing/heatmap use.

Google's COG asset documentation:

https://developers.google.com/earth-engine/Earth_Engine_asset_from_cloud_geotiff

Earth Engine REST reference:

https://developers.google.com/earth-engine/reference/rest

Important: Earth Engine should not be responsible for running AMIP's A*/Dijkstra routing, vessel performance calculations, or dynamic risk logic. The backend remains responsible for those calculations.

---

## 8. Frontend Map Architecture

The frontend should operate on a real geographic basemap and progressively reveal AMIP information as the user zooms in.

Conceptually:

```text
Global Earth
    ↓ zoom
Southern Ocean
    ↓ zoom
Antarctic region
    ↓ zoom
Mission corridor / science region
    ↓ zoom
AMIP computational cells
```

The map should support:

```text
sea-ice layer
ice edge
sea-ice uncertainty
iceberg observations
iceberg trajectories
current vectors
wind vectors
wave conditions
risk heatmap
route alternatives
route-cell inspection
```

The time slider should change the actual environmental layers, not just animate iceberg markers.

For example:

```text
T+0
    SIC_0
    currents_0
    wind_0
    waves_0
    iceberg_hazard_0
    risk_0

T+30
    SIC_30
    currents_30
    wind_30
    waves_30
    iceberg_hazard_30
    risk_30
```

When a route is selected, the exact traversed grid cells should be visible. Clicking a cell should expose the environmental attributes used by the router.

---

## 9. Environment API Contract

The backend should expose a consistent environmental interface regardless of source dataset.

Conceptually:

```python
environment = get_environment(
    cell_id=cell_id,
    valid_time=timestamp,
)
```

or for a map region:

```python
cells = get_cells(
    bbox=bbox,
    valid_time=timestamp,
    resolution=resolution,
)
```

Every returned cell should carry provenance for its values where practical.

Example:

```text
Cell: grid_02341
Time: 2026-09-15T12:00:00Z

SIC: 67.4 %
SIC uncertainty: 8.1 %
Current U: 0.18 m/s
Current V: -0.04 m/s
Wind U: 7.2 m/s
Wind V: -3.1 m/s
Wave height: 2.8 m
Wave direction: 214°
Wave period: 8.0 s
Iceberg hazard: 0.14
Depth: 1840 m
Land: false
Ice shelf: false
Navigable: true

Provenance:
SIC -> model/source/version
Currents -> CMEMS product/version
Wind -> ECMWF product/version
Waves -> CMEMS product/version
Bathymetry -> GEBCO version
Icebergs -> USNIC/BYU + trajectory model version
```

---

## 10. What Happens When the ML Models Arrive

The sea-ice models are separate from the raw-data ingestion layer.

The ML teams will deliver:

```text
Ice-kNN-South
    ↓
future SIC grid + uncertainty

ANTSIC-UNet
    ↓
future SIC grid + uncertainty
```

Their outputs must plug into the same AMIP environment interface.

The routing and risk layers should not care whether the SIC came from:

```text
observed SIC
operational SIC forecast
Ice-kNN-South
ANTSIC-UNet
```

The model selection can be controlled by configuration, and the resulting forecast must retain provenance.

---

## 11. Work to Build After Data Ingestion

Once the unified grid can reliably serve environmental states, implement the remaining system in this sequence:

```text
1. Unified environmental data layer
2. Iceberg observation + physics trajectory layer
3. Risk engine
4. Vessel performance + fuel model
5. True grid-based 4D A*/Dijkstra router
6. Mission planner / multi-target legs
7. Backend REST APIs
8. Earth-map frontend + environmental layers
9. ML sea-ice model integration
10. End-to-end validation and benchmarking
```

Development of these layers can happen in parallel after the common environment interface exists. Risk, vessel, and routing code can use synthetic/mock environmental data while real ingestion is still being completed.

---

## 12. Core End-to-End Architecture

```text
              EXTERNAL DATA

NSIDC ─────── Sea Ice
CMEMS ─────── Currents + Waves
ECMWF ─────── Weather
GEBCO ─────── Bathymetry
USNIC/BYU ─── Icebergs

                    │
                    ▼
           Data Ingestion Layer
                    │
        normalization / validation
                    │
        spatial + temporal alignment
                    │
                    ▼
              AMIP Grid
                    │
         Environment(cell, time)
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
    ML SIC      Iceberg       Static
    Forecast    Physics       Geography
        │           │            │
        └───────────┼────────────┘
                    ▼
              Risk Engine
                    │
                    ▼
           Vessel Performance
                    │
                    ▼
             4D Grid Router
                    │
                    ▼
             Mission Planner
                    │
             ┌──────┴───────┐
             ▼              ▼
        Backend APIs     Visualization
                              │
                       COG / Earth Engine
                              │
                              ▼
                         Real Earth Map
```

## Core Principle

**The AMIP grid is the common language of the system.** External datasets remain scientifically traceable at their native resolution and coordinate systems, but are transformed into a unified, time-aware AMIP representation before being consumed by risk, vessel performance, routing, or visualization.

The web map should visualize the **same environmental reality that the router uses**. This allows the user to see the actual SIC, currents, wind, waves, iceberg hazard, risk, and route cells behind a navigation decision, while keeping computation and routing under AMIP's backend control.
