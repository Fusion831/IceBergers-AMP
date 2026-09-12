# IceBergers-AMP: Antarctic Maritime Intelligence Platform (AMIP)

> **Advanced AI-powered dynamic routing, polar maritime risk assessment, and environmental intelligence for Antarctic navigation.** Developed for polar vessels operating under the IMO Polar Code and POLARIS system.

---

## 🧭 Project Overview

AMIP (**Antarctic Maritime Intelligence Platform**) is a decision-support system designed to empower Antarctic expedition planning and safe vessel navigation. By fusing multi-modal environmental observations—including sea ice concentration (NSIDC), wind & ocean currents (ECMWF), bathymetry (GEBCO), and iceberg tracking (USNIC / BYU)—AMIP generates multi-objective, risk-mitigated routes tailored to vessel ice classes (PC1–PC7).

### Key Features
- **Hexagonal Discrete Spatial Indexing (Uber H3)**: Unified spatial grid at polar latitudes for unified environmental representation and fast graph traversal.
- **Iceberg Hazard & Drift Modeling**: Physics-based kinematic drift simulations accounting for ocean currents, Coriolis force, and thermodynamic degradation.
- **Fast Sea Ice Spatial Interpolation (Ice-kNN)**: Sub-second spatial prediction of ice concentration across the Southern Ocean.
- **POLARIS Risk Engine**: Standardized Risk Index Outcome (RIO) calculation conforming to IMO guidelines for polar ship operations.
- **Multi-Objective Polar Pathfinder**: Pareto-optimal route generation balancing Fuel Consumption, Travel Time, Iceberg Proximity, and Bathymetric Safety.
- **Interactive Antarctic Command HUD**: Real-time Polar Stereographic map visualizer, route explainability drawer, dynamic voyage simulator, and station telemetry.

---

## 📂 Repository Structure

```text
IceBergers-AMP/
├── apps/
│   └── backend/                    # FastAPI backend service & REST API endpoints
│       └── src/
│           ├── api/                # Route handlers (routes, hazards, telemetry)
│           └── main.py             # Application entrypoint
├── data/                           # Processed polar datasets & static configurations
│   ├── antarctica/                 # Antarctic environmental layers & H3 grid lookups
│   ├── config/                     # Risk matrices & vessel performance profiles
│   └── validation/                 # Ground-truth validation benchmarks
├── data_ingestion/                 # Multi-source polar data ingestion pipelines
│   ├── ecmwf/                      # Wind & ocean surface current ingestion
│   ├── gebco/                      # Bathymetry & depth processing
│   ├── geographic_mask/            # Land & ice-shelf boundary masks
│   ├── grid/                       # AMIP unified environmental spatial grid
│   ├── h3/                         # Uber H3 hexagonal discrete global grid system
│   ├── iceberg/                    # USNIC / BYU iceberg detection & drift pipeline
│   └── nsidc/                      # NSIDC sea ice concentration (SIC) ingestion
├── docker/                         # Containerization & deployment
│   ├── Dockerfile                  # Production container definition
│   ├── docker-compose.yml          # Multi-service stack (PostGIS + backend)
│   └── postgis-init.sql            # Spatial database initialization
├── docs/                           # Architecture, PRD specifications & technical notes
│   ├── AMIP_FULL_PRODUCT_VISION.md
│   ├── AMIP_TECHNICAL_VIVA_QA.md
│   ├── iceberg_trajectory_model.md
│   ├── risk_profile_and_risk_engine.md
│   └── routing_engine_integration.md
├── frontend/                       # Vite + React + TypeScript interactive UI
│   ├── public/                     # Public assets & static geoJSON/data
│   └── src/
│       ├── components/             # Polar map, navigation controls, telemetry cards
│       ├── context/                # Global mission & layer state providers
│       ├── views/                  # Mission planner & risk dashboard views
│       ├── App.tsx
│       └── main.tsx
├── ice_knn/                        # Fast k-NN spatial inference for ice conditions
│   ├── inference.py                # Online spatial interpolation
│   └── model.py                    # Model definitions
├── model/                          # Offline training routines & model checkpoints
│   └── ice_knn_south/              # Southern Ocean specialized weights & training
├── packages/                       # Core modular Python packages
│   ├── core/                       # Shared utilities, logging & math primitives
│   ├── data_access/                # PostGIS / parquet storage access layer
│   ├── domain/                     # Pydantic domain models & contracts
│   ├── iceberg_physics/            # Thermodynamic decay & kinematic drift models
│   ├── models/                     # ML / statistical model wrappers
│   ├── risk_engine/                # Dynamic polar maritime risk calculator
│   ├── routing/                    # Multi-objective Pareto / A* polar pathfinder
│   └── services/                   # Business logic orchestrating data & routing
├── scripts/                        # Automation, benchmarks & data precomputation
│   ├── build_full_backend_h3_grid.py
│   ├── cli_route_visualizer.py
│   ├── run_nsidc_pipeline.py
│   └── seed_demo_data.py
├── tests/                          # Unit, integration & E2E polar test suite
│   ├── test_amip_unified_grid.py
│   ├── test_e2e_mission.py
│   ├── test_iceberg_drift_and_hazard.py
│   ├── test_risk_engine.py
│   └── test_routing.py
├── vessel/                         # Vessel polar specifications & performance
│   ├── config.py                   # Polar class parameters (PC4, PC6, etc.)
│   ├── constraints.py              # POLARIS regulatory limits & safety boundaries
│   ├── evaluator.py                # Speed reduction & engine workload curves
│   └── fuel.py                     # Heavy fuel oil / MGO consumption modeling
├── .env.example                    # Environment variable configuration template
├── .gitignore                      # Git exclusion rules
├── pyproject.toml                  # Python build & dependency metadata
└── README.md                       # Project documentation
```

---

## 🚀 Quickstart

### 1. Prerequisites
- Python >= 3.11
- Node.js >= 18 & npm
- Docker & Docker Compose (Optional, for PostGIS storage)

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/Fusion831/IceBergers-AMP.git
cd IceBergers-AMP

# Set up Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies in editable mode
pip install -e .

# Launch FastAPI backend
uvicorn apps.backend.src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173` to explore the interactive polar stereographic navigation dashboard.

---

## 📊 Evaluation & Verification
Run the comprehensive test suite:
```bash
pytest tests/
```