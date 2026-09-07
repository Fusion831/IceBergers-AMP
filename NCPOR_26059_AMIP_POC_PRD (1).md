# Antarctic Mission Intelligence Platform (AMIP)

## Complete Proof-of-Concept Product Requirements Document

**SIH 2026 Problem Statement:** 26059\
**Organization:** National Centre for Polar and Ocean Research (NCPOR),
Ministry of Earth Sciences\
**Document scope:** Complete SIH POC implementation, including product
requirements, workflows, data, models, APIs, frontend, validation,
deployment, testing, and demonstration.

> This document defines the complete POC. It intentionally excludes the
> large research/operational product roadmap except where future
> interfaces are required for architectural compatibility.

# AI-Enabled Antarctic Sea-Ice, Iceberg Trajectory, and Navigation Decision Support System

## Unified Product, Research, AI/ML, Data, and System Architecture

**Smart India Hackathon 2026 --- Problem Statement 26059**\
**Organization:** Ministry of Earth Sciences (MoES)\
**Department:** National Centre for Polar and Ocean Research (NCPOR)\
**Category:** Software\
**Theme:** Transportation & Logistics

------------------------------------------------------------------------

## 0. Document Purpose

This document defines a unified solution for SIH 2026 Problem Statement
26059 by combining two independently developed architecture drafts with
external research and current verification of relevant open-source and
scientific systems.

The intended approach is not to assume that either draft is correct. The
first architecture established a strong product framing around NCPOR
mission planning, horizon-dependent forecasting, uncertainty,
environmental risk, and PolarRoute integration. The second architecture
added greater technical detail around datasets, ML approaches, data
structures, API contracts, frontend behavior, evaluation, and future
vessel integration.

The unified architecture retains the strongest elements of both while
removing or correcting assumptions that are weak, unnecessary, or
insufficiently supported.

The system is deliberately divided into:

1.  **Strategic mission planning**: months to weeks ahead.
2.  **Tactical route planning**: weeks to days ahead.
3.  **Future operational/on-vessel decision support**: live vessel state
    and continuous replanning.

The first POC is primarily the first two layers. It should still
demonstrate the complete causal chain:

> **Environmental data → AI/ML and physical prediction → uncertainty →
> risk → geographic/route analysis → mission decision**

The future product extends the same architecture with live vessel state
and actual fuel observations.

------------------------------------------------------------------------

# 1. Official Problem Statement

## 1.1 Statement

> **Develop an AI/ML-enabled decision support platform capable of
> forecasting Antarctic sea-ice concentration, predicting iceberg
> trajectories, and identifying safe and fuel-efficient navigation
> routes for research vessels using satellite, oceanographic and
> meteorological datasets.**

## 1.2 Interpretation

The problem is not three isolated ML tasks.

The intended system is a decision-support pipeline in which
environmental information is transformed into actionable
mission-planning information:

``` text
Satellite / Ocean / Weather / Geographic Data
                    ↓
          Spatiotemporal Data Fusion
                    ↓
       Environmental Forecast / Prediction
                    ↓
          Uncertainty Quantification
                    ↓
            Environmental Risk
                    ↓
       Geographic + Route Evaluation
                    ↓
        Safety / Time / Fuel Tradeoffs
                    ↓
             Human Decision
```

The product therefore has to answer a more useful question than:

> "Can we predict sea ice?"

The operational question is:

> **"Given the mission objective, time window, geography and vessel
> constraints, where and when is it preferable to operate, and which
> route provides the best safety/fuel/time tradeoff under the predicted
> environmental conditions?"**

This distinction should govern the entire architecture.

------------------------------------------------------------------------

# 2. Product Vision

## 2.1 Product Concept

Working name:

# Antarctic Mission Intelligence Platform (AMIP)

Alternative product-facing name:

# Antarctic Mission Planner (AMP)

The exact name is not technically important. The capability is.

AMIP is a web-based environmental intelligence and mission-planning
platform designed initially for NCPOR's Antarctic operations.

It combines:

-   Sea-ice observations
-   Sea-ice forecasting
-   Iceberg observations
-   Iceberg trajectory modelling
-   Weather forecasts
-   Ocean forecasts
-   Geographic constraints
-   AI/ML predictions
-   Statistical/climatological information
-   Uncertainty
-   Route optimization
-   Simplified vessel performance/fuel estimation

into one planning workflow.

## 2.2 The Core Value Proposition

The platform should allow a planner to move from fragmented
environmental information to a defensible mission decision.

Instead of separately checking:

-   sea-ice charts,
-   weather forecasts,
-   ocean currents,
-   iceberg information,
-   bathymetry,
-   station geography,
-   historical conditions,
-   route-planning tools,

the planner receives a spatial and temporal synthesis of these factors.

The product is not intended to replace expert judgment.

It is intended to improve the information available to that judgment.

------------------------------------------------------------------------

# 3. The Two-Tier Product Strategy

The strongest combined architecture is a deliberate two-tier system.

## 3.1 Tier 1 --- Strategic Mission Planning

Planning horizon:

-   Seasonal
-   Approximately 1--6 months where scientifically supported
-   Explicitly useful for approximately 3-month mission planning
-   Historical/climatological context beyond reliable forecast horizons

Core questions:

-   Which locations are likely to be accessible?
-   Which weeks are historically and seasonally favorable?
-   What environmental conditions are expected?
-   How uncertain are those expectations?
-   Which candidate destination or operating area is preferable?
-   What route options should be considered?

## 3.2 Tier 2 --- Tactical / Near-Term Planning

Planning horizon:

-   Days to weeks
-   Higher-resolution forecast products
-   Current observations
-   More specific route evaluation

Core questions:

-   Which route is currently preferable?
-   Which areas should be avoided?
-   What is the predicted iceberg exposure?
-   How do weather and currents affect travel time and fuel?
-   Does a planned route intersect elevated environmental risk?

## 3.3 Future Tier 3 --- On-Vessel Operations

Future inputs:

-   Live GPS
-   Vessel speed
-   Heading
-   Engine state
-   Fuel flow/consumption
-   Vessel draft/trim where available
-   Updated satellite observations
-   Updated weather
-   Updated ocean conditions
-   Updated iceberg detections

Future capabilities:

-   Dynamic route replanning
-   Actual-vs-predicted comparison
-   Fuel-aware routing
-   Live hazard updates
-   Updated iceberg trajectory ensembles
-   Continuously updated ETA
-   Vessel-specific learned performance models

The POC should not attempt to implement Tier 3.

------------------------------------------------------------------------

# 4. Independent Problem Analysis

## 4.1 Primary User

The primary product user should be treated as:

> **A member of the NCPOR expedition/mission planning function
> responsible for deciding when, where, and how a research-vessel
> mission should operate.**

This role should be validated with NCPOR/domain experts before
production deployment.

The system should be designed for a technically competent domain user
who understands Antarctic operations but does not need to understand the
internal mechanics of the ML models.

## 4.2 Secondary Users

Potential secondary users include:

-   Voyage planners
-   Marine operations personnel
-   Research-vessel masters/captains
-   Expedition/science leaders
-   Station logistics planners
-   Polar scientists
-   Operations management
-   MoES-level decision-makers

The POC should prioritize the mission planner.

## 4.3 Why the Primary User Matters

A captain planning a route tomorrow and a mission planner evaluating an
expedition several months ahead do not need the same information.

The system therefore must not expose the same "forecast" identically at
every horizon.

It should expose the strongest scientifically appropriate information
available for the selected horizon.

------------------------------------------------------------------------

# 5. Current-State Problem

The source architecture drafts converge on the existence of an
information-fragmentation problem.

Relevant environmental information may exist across:

-   NASA/NSIDC
-   Copernicus Marine
-   ECMWF
-   EUMETSAT/OSI SAF
-   U.S. National Ice Center
-   NCPOR data systems
-   Other scientific datasets
-   Commercial weather-routing products
-   Existing polar route planning software

The operational challenge is not necessarily that these datasets do not
exist.

It is that they must be:

1.  acquired,
2.  harmonized,
3.  interpreted,
4.  compared,
5.  translated into operational constraints,
6.  combined with vessel capabilities,
7.  and converted into a mission decision.

The proposed system should automate the computational part of this chain
while leaving decision authority with the expert.

------------------------------------------------------------------------

# 6. Current Workflow Model

The following should be treated as the working workflow hypothesis to
validate with NCPOR personnel.

## 6.1 Long-Range Planning

Months ahead:

-   Expedition objectives are established.
-   Station/logistics requirements are considered.
-   Candidate dates and operating areas are considered.
-   Historical knowledge and broad seasonal expectations influence
    decisions.

The core limitation at this stage is that high-resolution deterministic
forecasts do not exist for the selected future date.

Therefore the appropriate information is:

-   climatology,
-   seasonal outlook,
-   probability,
-   historical analogs,
-   and scenario distributions.

## 6.2 Pre-Departure Planning

Weeks ahead:

-   Weather forecasts become increasingly useful.
-   Sea-ice observations become more informative.
-   Iceberg products become more current.
-   Ocean conditions can be evaluated at higher resolution.
-   Candidate routes can be compared more specifically.

## 6.3 Near-Term / Voyage Planning

Days ahead:

-   Current environmental state matters heavily.
-   Weather forecasts have substantially higher value.
-   Satellite observations can detect changing ice conditions.
-   Iceberg information is updated.
-   Route alternatives can be reconsidered.

## 6.4 Future On-Vessel Planning

During the voyage:

-   The vessel becomes a moving state.
-   Actual fuel usage becomes measurable.
-   GPS provides actual trajectory.
-   Current environmental observations can be compared with forecasts.
-   Dynamic routing becomes meaningful.

------------------------------------------------------------------------

# 7. Core Pain Points the Product Should Address

## 7.1 Information Fragmentation

The planner must currently combine information from multiple systems and
formats.

**AMIP response:** unified spatiotemporal environmental view.

## 7.2 Forecast-Horizon Mismatch

A single deterministic forecast cannot reasonably answer questions three
months ahead.

**AMIP response:** horizon-dependent information architecture.

## 7.3 Lack of Integrated "What-If" Analysis

The planner needs to compare:

-   different dates,
-   destinations,
-   operating areas,
-   route sequences,
-   safety/fuel/time priorities.

**AMIP response:** scenario engine.

## 7.4 Iceberg Risk Is Difficult to Integrate

An iceberg observation tells us where the iceberg is observed.

The planning system additionally needs:

-   predicted movement,
-   uncertainty,
-   route-intersection probability.

**AMIP response:** physical drift ensemble producing probability fields.

## 7.5 Route Optimization and Environmental Intelligence Are Separated

Existing routing systems can optimize routes, but the novelty
opportunity is in feeding them better Antarctic-specific environmental
intelligence and mission-level analysis.

**AMIP response:** augment rather than unnecessarily replace mature
route-planning components.

## 7.6 Fuel Estimation Is Vessel-Specific

Without actual telemetry, a planning system can only estimate fuel.

**AMIP response:** use existing vessel-performance capabilities where
possible; otherwise use a transparent planning approximation and clearly
label it as an estimate.

------------------------------------------------------------------------

# 7A. Product Feature Map and Model/Service Blueprint

This section defines the complete product at a glance before the
detailed architecture, datasets, implementation decisions, and research
roadmap. It establishes what the system contains, what each component
does, what it consumes, what it produces, and how those outputs move
through the system.

The product is not a single AI model. It is a decision-support system
composed of environmental data services, specialized prediction models,
physics-based models, uncertainty estimation, risk fusion, route
optimization, mission analysis, and an interactive visualization layer.

The complete decision chain is:

``` text
MISSION CONFIGURATION
        ↓
DATA DISCOVERY + QUALITY CONTROL
        ↓
CURRENT ENVIRONMENTAL STATE
        ↓
FORECAST GENERATION
        ├── Sea-Ice Forecast
        ├── Weather Forecast
        ├── Ocean Forecast
        └── Iceberg Trajectory Ensemble
        ↓
UNCERTAINTY PROPAGATION
        ↓
ENVIRONMENTAL RISK ENGINE
        ↓
VESSEL-CONSTRAINED ENVIRONMENTAL MESH
        ↓
POLARROUTE
        ↓
MULTI-OBJECTIVE ROUTE SET
        ↓
MISSION ANALYSIS
        ↓
DECISION SUPPORT UI
```

The system therefore has five logical layers:

``` text
Layer 1: OBSERVE
Satellite, weather, ocean, iceberg, bathymetry and geographic data

Layer 2: PREDICT
Sea-ice ML, operational weather/ocean forecasts, iceberg physics

Layer 3: UNDERSTAND
Uncertainty, environmental risk and accessibility analysis

Layer 4: OPTIMIZE
PolarRoute and multi-objective mission routing

Layer 5: DECIDE
Interactive maps, comparisons, explanations, reports and human review
```

## 7A.1 Complete Feature Inventory

### A. Mission Configuration

The Mission Configuration module defines the planning problem.

Features:

1.  Create a new mission.
2.  Select vessel profile.
3.  Select origin.
4.  Select one or more destinations.
5.  Select station sequence.
6.  Specify departure date or departure window.
7.  Specify expected mission duration.
8.  Specify arrival deadlines.
9.  Specify fuel priority.
10. Specify safety priority.
11. Specify travel-time priority.
12. Configure acceptable environmental thresholds.
13. Configure vessel-specific constraints.
14. Save a mission scenario.
15. Duplicate a scenario for what-if comparison.
16. Compare multiple mission scenarios.

Core inputs:

``` text
Vessel
Origin
Destination(s)
Departure window
Arrival constraint
Mission duration
Objective weights
Environmental constraints
```

Core output:

``` text
Mission Scenario Object
```

This object becomes the root input for downstream environmental analysis
and route generation.

------------------------------------------------------------------------

### B. Environmental Data Explorer

The Environmental Data Explorer provides a unified view of the current
and historical environmental state.

Features:

1.  Antarctic interactive map.
2.  Time slider.
3.  Historical date selection.
4.  Forecast date selection.
5.  Layer toggles.
6.  Opacity controls.
7.  Legend and units.
8.  Data-source indicator.
9.  Data timestamp.
10. Forecast horizon indicator.
11. Data freshness indicator.
12. Missing-data indicator.
13. Spatial zoom.
14. Mission-corridor focus.
15. Station markers.
16. Coastline and ice-shelf boundaries.
17. Bathymetry visualization.

The time slider is a core interaction rather than a decorative
animation.

When the selected time changes from `T+7` to `T+14`, the system should
change the underlying environmental state:

``` text
T+7
  ↓
SIC(T+7)
Icebergs(T+7)
Weather(T+7)
Ocean(T+7)
Risk(T+7)
Routes(T+7)

T+14
  ↓
SIC(T+14)
Icebergs(T+14)
Weather(T+14)
Ocean(T+14)
Risk(T+14)
Routes(T+14)
```

Visual interpolation may be used to make the animation smooth, but
interpolated frames must not be represented as independently generated
forecasts.

------------------------------------------------------------------------

### C. Sea-Ice Concentration Forecasting

The sea-ice module is the principal custom AI/ML component of the POC.

Its job is:

> Estimate future Antarctic sea-ice concentration and its uncertainty
> for decision-relevant forecast horizons.

Input data can include:

-   Recent sea-ice concentration.
-   Historical sea-ice concentration.
-   Sea-surface temperature.
-   Atmospheric variables.
-   Wind.
-   Ocean variables.
-   Seasonal forecast information.
-   Climatological statistics.

POC model:

``` text
Temporal U-Net / lightweight spatiotemporal CNN
+
Quantile regression
```

Alternative lightweight benchmark:

``` text
Ice-kNN-South-style analog/kNN model
```

The exact model selected for the final POC should be determined by
validation performance and compute feasibility.

The model serves as the:

``` text
Sea-Ice Forecast Service
```

It does not directly produce a navigation route.

Its output is an environmental forecast consumed by the risk engine.

Expected output:

``` text
SIC forecast map
+
SIC quantiles
+
forecast confidence
+
ice-edge estimate
+
forecast metadata
```

Example output structure:

``` text
SIC:
  q10
  q25
  q50
  q75
  q90

Derived:
  ice-edge probability
  mean SIC
  uncertainty/spread
```

Forecast horizons:

``` text
7 days
14 days
30 days
60 days
90 days
```

The information architecture must distinguish these horizons. Shorter
horizons can use more deterministic information; longer horizons should
increasingly emphasize probabilistic and seasonal information.

------------------------------------------------------------------------

### D. Sea-Ice Confidence and Uncertainty

This is a separate product capability built around the sea-ice model.

Features:

1.  Quantile maps.
2.  Ensemble spread maps.
3.  Confidence maps.
4.  Forecast reliability indicators.
5.  Data freshness.
6.  Model validity horizon.
7.  Historical error statistics.
8.  Uncertainty inspection for selected locations.

The system should be able to answer:

``` text
What does the model predict?
How uncertain is the prediction?
Why is it uncertain?
How far into the future is this forecast?
```

The output should never be reduced to a single unexplained confidence
percentage.

------------------------------------------------------------------------

### E. Sea-Ice Edge Analysis

Sea-ice concentration is converted into operationally meaningful
ice-edge information.

Features:

1.  Predicted ice edge.
2.  Ice-edge movement.
3.  Ice-edge probability.
4.  Distance from route to predicted ice edge.
5.  Historical ice-edge position.
6.  Forecast vs historical comparison.
7.  Ice-edge uncertainty corridor.

The ice edge is derived from the SIC field according to the selected
operational threshold.

------------------------------------------------------------------------

### F. Iceberg Observation Layer

The iceberg observation layer represents known iceberg locations from
available validated sources.

Features:

1.  Current iceberg positions.
2.  Historical iceberg positions.
3.  Iceberg identifiers where available.
4.  Iceberg size attributes where available.
5.  Observation timestamp.
6.  Observation confidence.
7.  Source metadata.
8.  Iceberg clustering/density.

The POC should not depend on building a raw SAR iceberg detector.

Existing validated iceberg information should be used first.

The product distinction is:

``` text
Observed iceberg
        ≠
Predicted iceberg position
        ≠
Iceberg risk
```

These are separate concepts.

------------------------------------------------------------------------

### G. Iceberg Trajectory Prediction

The iceberg trajectory module predicts how known icebergs may move.

POC model:

``` text
Physics-based Lagrangian drift model
+
Monte Carlo ensemble
```

Its job is:

> Propagate observed iceberg states forward using environmental forcing
> and estimate the probability distribution of future positions.

Input:

``` text
Initial iceberg position
Iceberg dimensions
Estimated draft where available
Ocean currents
Wind
Sea-ice conditions
Initial-state uncertainty
Model parameters
```

For each iceberg:

``` text
Observed State
     ↓
50+ stochastic trajectory members
     ↓
Trajectory ensemble
     ↓
Probability density
     ↓
Grid-based iceberg risk
```

The physics model accounts for first-order effects such as:

-   ocean-current advection,
-   wind drag,
-   Coriolis influence,
-   stochastic unresolved motion,
-   and, as the model matures, sea-ice interaction and other relevant
    effects.

Output:

``` text
Trajectory members
+
Mean trajectory
+
Uncertainty envelope
+
Probability density field
+
Route-intersection probability
```

The POC should use physics because the available tracked-iceberg dataset
is not sufficient justification for a large pure-ML trajectory model.

Future enhancement:

``` text
Physics trajectory
        +
XGBoost residual correction
        ↓
Hybrid iceberg forecast
```

------------------------------------------------------------------------

### H. Iceberg Risk Field

The trajectory ensemble is converted into a spatial risk field.

The module estimates:

``` text
P(iceberg encounter | location, time)
```

or a suitable normalized proxy based on the available data.

Features:

1.  Iceberg probability-density map.
2.  High-probability corridors.
3.  Route intersection probability.
4.  Distance-to-trajectory analysis.
5.  Time-dependent iceberg risk.
6.  Ensemble visualization.
7.  High-risk hotspot identification.

Output:

``` text
R_iceberg(x, y, t)
```

This becomes an input to the environmental risk engine.

------------------------------------------------------------------------

### I. Weather Intelligence

The system consumes rather than recreates operational weather forecasts.

Weather variables may include:

-   wind speed,
-   wind direction,
-   pressure,
-   air temperature,
-   wave conditions,
-   and other relevant available variables.

Horizon-dependent source strategy:

``` text
0–10 days
    ↓
Operational deterministic forecast

10–15 days
    ↓
Ensemble forecast + spread

Longer horizon
    ↓
Seasonal anomaly + climatology
```

The weather service provides:

``` text
Wind field
Wave field
Forecast uncertainty
Forecast metadata
```

The system should not claim to have trained an Antarctic weather model
unless such a model is actually developed and validated.

------------------------------------------------------------------------

### J. Ocean Intelligence

The ocean module provides:

-   surface currents,
-   sea-surface temperature,
-   relevant ocean-state variables,
-   ocean forecast uncertainty where available.

Its primary downstream consumers are:

1.  Iceberg drift model.
2.  Sea-ice forecasting model.
3.  Fuel/routing model.
4.  Environmental risk engine.

The ocean module is therefore primarily a data and forecasting service
rather than a custom AI research model in the POC.

------------------------------------------------------------------------

### K. Bathymetry and Geographic Constraints

The geographic constraint layer provides:

-   coastline,
-   land mask,
-   bathymetry,
-   ice shelves,
-   station locations,
-   route boundaries,
-   navigational exclusion regions.

These constraints are not predictions.

They define where a vessel can or cannot travel.

Hard constraints should remain separate from soft risk:

``` text
Hard Constraint:
Route cannot pass.

Soft Constraint:
Route may pass, but incurs a higher cost.
```

This distinction is critical to preventing an optimizer from trading
away an absolute safety or navigational constraint for a small fuel
saving.

------------------------------------------------------------------------

### L. Environmental Risk Engine

The risk engine converts multiple environmental predictions into a
unified navigational risk representation.

Inputs:

``` text
Sea-ice risk
Iceberg risk
Wind risk
Wave risk
Current-related cost
Bathymetry
Vessel constraints
```

Output:

``` text
R_total(x, y, t)
```

The POC risk engine should be interpretable and rule-based.

Conceptually:

``` text
Risk =
    sea-ice contribution
  + iceberg contribution
  + weather contribution
  + wave contribution
  + vessel/environment interaction
```

However, critical hazards should not be hidden by averaging.

A high-risk hazard can impose a dominant or hard penalty.

The risk engine also propagates environmental uncertainty.

Outputs:

``` text
R_mean
R_p90
R_uncertainty
```

Where:

-   `R_mean` represents expected risk.
-   `R_p90` represents a high-risk plausible scenario.
-   `R_uncertainty` represents ensemble spread.

This allows the route optimizer to distinguish:

``` text
Low expected risk + high uncertainty
```

from:

``` text
Low expected risk + high confidence
```

------------------------------------------------------------------------

### M. Vessel Constraint Model

The vessel model represents physical operating constraints.

Configurable fields include:

-   vessel name,
-   maximum speed,
-   cruising speed,
-   draft,
-   displacement where available,
-   ice capability,
-   wave tolerance,
-   wind tolerance,
-   maximum permissible SIC,
-   fuel model,
-   operating limits.

The system must use configurable vessel profiles rather than permanently
hard-coding one vessel.

The official NCPOR vessel profile used for a demonstration must be
verified independently before being treated as operational truth.

The vessel model serves as the interface between environmental
conditions and route feasibility.

------------------------------------------------------------------------

### N. Fuel Estimation

The POC uses a transparent physics/performance-based estimate rather
than pretending to have learned actual fuel consumption from nonexistent
telemetry.

Conceptually:

``` text
Total propulsion requirement
=
Calm-water resistance
+
Wave resistance
+
Wind resistance
+
Ice-related penalty
```

Inputs:

``` text
Vessel parameters
Speed
Route geometry
Wind
Waves
Sea ice
Currents
```

Output:

``` text
Estimated fuel consumption
Estimated fuel per route
Fuel efficiency comparison
```

The output must be labeled:

``` text
Estimated
```

until validated against actual vessel telemetry.

Future model:

``` text
Historical telemetry
+
Engine state
+
Speed
+
Draft/loading
+
Wind
+
Waves
+
Currents
+
Ice
+
Route geometry
        ↓
Vessel-specific fuel model
```

A future gradient-boosting, neural or hybrid model may then estimate
route-specific fuel consumption.

------------------------------------------------------------------------

### O. PolarRoute Integration

PolarRoute is the route-optimization engine.

The system should not unnecessarily rebuild a mature polar routing
system.

AMIP supplies:

``` text
Environmental state
+
Risk field
+
Bathymetry
+
Vessel constraints
```

PolarRoute supplies:

``` text
Optimal path computation
+
Vessel/environment interaction
+
Travel-time estimation
+
Route optimization
```

The integration boundary is:

``` text
AMIP Environmental Intelligence
             ↓
       Environmental Mesh
             ↓
          PolarRoute
             ↓
       Candidate Routes
```

PolarRoute is therefore not the AI prediction component.

It is the optimization component.

------------------------------------------------------------------------

### P. Multi-Objective Route Generation

The route engine should produce multiple meaningful alternatives rather
than one arbitrary "best" route.

Minimum POC route set:

1.  Safest.
2.  Fastest.
3.  Fuel-efficient.
4.  Balanced.

Definitions:

``` text
Safest:
Minimize exposure to maximum/critical environmental risk.

Fastest:
Minimize travel time subject to hard constraints.

Fuel-efficient:
Minimize estimated fuel consumption.

Balanced:
Optimize a weighted combination of safety, fuel and time.
```

The system should expose objective weights:

``` text
Safety: 0–100
Fuel:   0–100
Time:   0–100
```

Changing these weights should produce a different optimization problem.

------------------------------------------------------------------------

### Q. Route Comparison

The route comparison module compares candidates using:

-   distance,
-   ETA,
-   estimated fuel,
-   sea-ice exposure,
-   iceberg exposure,
-   weather exposure,
-   maximum risk,
-   expected risk,
-   risk uncertainty,
-   constraint violations,
-   mission feasibility.

Example:

``` text
                 Safest   Balanced   Fastest
Distance            ↓         ↓          ↓
ETA                 ↓         ↓          ↓
Fuel                ↓         ↓          ↓
Ice exposure        ↓         ↓          ↓
Iceberg exposure    ↓         ↓          ↓
Max risk            ↓         ↓          ↓
Uncertainty         ↓         ↓          ↓
```

The UI should make tradeoffs visible instead of hiding them inside a
single composite score.

------------------------------------------------------------------------

### R. Mission-Level Analysis

The Mission Analysis module goes beyond route generation.

It answers:

``` text
Can the mission be completed?
When should departure occur?
Which station should be visited first?
Which route is most robust?
How much fuel should be budgeted?
How much environmental uncertainty exists?
```

Features:

1.  Destination comparison.
2.  Departure-window comparison.
3.  Station-order comparison.
4.  Route comparison.
5.  Fuel budget comparison.
6.  Accessibility probability.
7.  Mission-duration estimate.
8.  Risk summary.
9.  Uncertainty summary.
10. Scenario ranking.

------------------------------------------------------------------------

### S. Station Accessibility

For each station or operating location, calculate:

``` text
Accessibility probability
Expected accessibility window
Environmental risk
Sea-ice condition
Iceberg risk
Weather suitability
Forecast confidence
```

This allows a planner to compare:

``` text
Bharati:
High accessibility probability
Lower uncertainty

Maitri:
Moderate accessibility probability
Higher sea-ice uncertainty
```

The values above are illustrative only. Actual values must be computed
from the data.

------------------------------------------------------------------------

### T. Departure Window Optimization

Instead of selecting one departure date, the system can evaluate a
range.

Example:

``` text
Departure Week A
    ↓
Forecast + risk + routes

Departure Week B
    ↓
Forecast + risk + routes

Departure Week C
    ↓
Forecast + risk + routes
```

Output:

``` text
Recommended window
+
alternatives
+
reason
+
uncertainty
```

Future versions can jointly optimize:

``` text
Departure date
+
Station sequence
+
Route
+
Fuel
+
Mission deadline
```

------------------------------------------------------------------------

### U. What-If Scenario Engine

Users should be able to clone a mission and change one or more
variables.

Examples:

``` text
What if departure is 7 days later?

What if Bharati is visited before Maitri?

What if safety weight increases?

What if the vessel has lower ice capability?

What if the mission deadline becomes tighter?
```

The system recomputes affected outputs rather than simply changing UI
labels.

------------------------------------------------------------------------

### V. Historical Replay and Validation

A historical replay mode should allow the system to reconstruct a past
planning scenario.

Workflow:

``` text
Select historical date
        ↓
Restrict system to information available at that time
        ↓
Generate forecast
        ↓
Generate routes
        ↓
Advance through time
        ↓
Reveal actual observations
        ↓
Compare forecast vs actual
        ↓
Evaluate route decision
```

This is important for scientific credibility because it demonstrates
that the system can be evaluated without relying on invented future
results.

------------------------------------------------------------------------

### W. Explanation Layer

Every recommendation should be explainable in terms of measurable system
outputs.

Example structure:

``` text
Balanced Route selected because:

1. Avoids high-probability sea-ice concentration region.
2. Reduces iceberg encounter probability.
3. Maintains acceptable wave exposure.
4. Adds X estimated hours relative to fastest route.
5. Reduces estimated fuel exposure relative to safest route.
6. Forecast confidence is moderate/high.
```

The explanation must be generated from actual model outputs.

The system must not invent explanations after the route has already been
selected.

------------------------------------------------------------------------

### X. Uncertainty Inspector

A dedicated uncertainty interface should expose:

-   model ensemble spread,
-   SIC quantiles,
-   iceberg trajectory spread,
-   weather ensemble spread,
-   risk uncertainty,
-   data freshness,
-   historical model error.

The user can select:

``` text
Location
+
Date
+
Variable
```

and inspect:

``` text
Prediction
Confidence
Uncertainty
Data source
Forecast horizon
```

------------------------------------------------------------------------

### Y. Reports and Export

The system should support an expedition-planning report containing:

1.  Mission configuration.
2.  Selected departure window.
3.  Environmental overview.
4.  Sea-ice forecast.
5.  Iceberg assessment.
6.  Weather/ocean conditions.
7.  Risk assessment.
8.  Candidate routes.
9.  Fuel estimates.
10. ETA estimates.
11. Uncertainty.
12. Route recommendation.
13. Explanation.
14. Data timestamps.
15. Model versions.

------------------------------------------------------------------------

## 7A.2 Exact Model and Service Responsibility Matrix

  ------------------------------------------------------------------------------------------------------------------------------
  Component       POC implementation          Primary            Input                    Output                    Served to
                                              responsibility                                                        
  --------------- --------------------------- ------------------ ------------------------ ------------------------- ------------
  Data ingestion  Python/xarray pipelines     Acquire            Satellite, weather,      Normalized datasets       All
                                              environmental data ocean, iceberg                                     downstream
                                                                 files/APIs                                         services

  Data            xarray/Rasterio/GeoPandas   Align              Raw datasets             Common environmental cube Models
  harmonization                               spatial/temporal                                                      
                                              grids                                                                 

  Climatology     Statistical baseline        Historical         Historical SIC/weather   Climatological fields     Forecast +
                                              seasonal                                                              mission
                                              expectation                                                           analysis

  Sea-ice         Persistence + climatology   Establish          Historical/current SIC   Baseline forecasts        Evaluation
  baseline                                    benchmark                                                             

  Sea-ice ML      Temporal U-Net /            Forecast SIC       SIC history +            SIC quantiles             Risk
                  lightweight temporal CNN                       environmental predictors                           engine + UI

  Sea-ice         Ice-kNN-South-style model   Lightweight        Historical               SIC forecast              Evaluation
  alternative                                 benchmark/backup   SIC/environment                                    

  Sea-ice edge    Derived calculation         Convert SIC into   SIC forecast             Ice-edge                  UI + risk
                                              edge                                        probability/geometry      

  Weather service ECMWF/other operational     Provide            Forecast products        Wind/weather fields       Risk + route
                  products                    atmospheric                                                           
                                              forecast                                                              

  Ocean service   CMEMS/other operational     Provide ocean      Ocean products           Currents/SST/etc.         Iceberg +
                  products                    state/forcing                                                         sea-ice +
                                                                                                                    risk

  Iceberg         Validated iceberg source    Provide observed   Iceberg observations     Positions + attributes    Drift model
  observations                                iceberg state                                                         

  Iceberg drift   Lagrangian physics + Monte  Forecast iceberg   Iceberg state +          Trajectory ensemble       Iceberg risk
                  Carlo                       movement           currents + wind                                    

  Iceberg density KDE / gridding              Convert            Ensemble tracks          Probability density       Risk
                                              trajectories into                                                     
                                              field                                                                 

  Risk engine     Rule-based physics-informed Convert            SIC, iceberg, weather,   Risk grid + uncertainty   PolarRoute
                  fusion                      environment into   waves, vessel                                      
                                              navigation cost    constraints                                        

  Vessel model    Configurable profile        Represent vessel   Vessel parameters        Feasibility/performance   Risk +
                                              limits                                      constraints               PolarRoute

  Fuel model      Simplified physics          Estimate fuel      Vessel + route +         Fuel estimate             Route
                                                                 environment                                        comparison

  PolarRoute      Existing routing engine     Optimize path      Environmental mesh +     Candidate routes          Mission
                                                                 vessel                                             analysis

  Mission         Backend service             Compare mission    Routes + forecasts +     Scenario metrics          UI
  analyzer                                    scenarios          constraints                                        

  Uncertainty     Ensemble/quantile           Quantify           Model ensembles          Mean, quantiles, spread   UI + risk
  engine          aggregation                 confidence                                                            

  Historical      Backtesting pipeline        Validate           Historical               Metrics                   Research
  evaluator                                   predictions        forecasts/observations                             dashboard

  Explanation     Deterministic feature       Explain            Route/risk metrics       Structured explanation    UI/report
  engine          attribution/rules           recommendations                                                       
  ------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

## 7A.3 Exact Role of Each AI/ML Model

### Model 1: Sea-Ice Forecast Model

**Serves as:** the primary custom environmental prediction model.

**Does:** predict future sea-ice concentration over the Antarctic
planning domain.

**Does not:** generate routes, predict weather, or directly control the
vessel.

``` text
Recent environmental history
        ↓
Temporal U-Net
        ↓
Future SIC distribution
```

------------------------------------------------------------------------

### Model 2: Sea-Ice Benchmark Model

**Serves as:** scientific baseline and low-compute fallback.

Possible implementation:

``` text
Persistence
+
Climatology
+
Ice-kNN-South-style analog prediction
```

**Does:** establish whether the custom deep-learning model actually
improves prediction.

**Does not:** replace the final model automatically.

A complex model that cannot beat persistence or climatology is a very
expensive way to rediscover disappointment.

------------------------------------------------------------------------

### Model 3: Iceberg Physics Model

**Serves as:** the primary iceberg trajectory predictor.

**Does:** propagate observed iceberg states using environmental forcing.

**Does not:** detect icebergs from raw satellite imagery.

``` text
Observed iceberg
      +
Ocean current
      +
Wind
      +
Uncertainty
      ↓
Physics ensemble
      ↓
Future trajectory distribution
```

------------------------------------------------------------------------

### Model 4: Future Iceberg Residual ML Model

**Serves as:** a future correction layer.

Candidate:

``` text
XGBoost / Gradient Boosting
```

**Does:** learn systematic residual errors in the physics model from
historical tracked iceberg trajectories.

``` text
Physics prediction
      ↓
Physics error
      ↓
XGBoost residual
      ↓
Corrected trajectory
```

**Does not:** replace the physical drift model.

------------------------------------------------------------------------

### Model 5: Future Antarctic Environmental Foundation Model

**Serves as:** the long-term shared environmental intelligence layer.

**Does:** learn multimodal spatial and temporal representations of
Antarctic environmental state and predict probabilistic future states.

Potential inputs:

``` text
SIC
SST
Currents
Wind
Pressure
Waves
Ice motion
Seasonal forecast fields
Iceberg observations
Climatology
```

Potential outputs:

``` text
Future SIC
Ice edge
Ice motion
Environmental anomalies
Ocean/environmental state
Probabilistic environmental representations
```

**Does not:** directly replace PolarRoute or autonomously command a
vessel.

Its purpose is to improve the quality of environmental information
supplied to downstream decision systems.

------------------------------------------------------------------------

### Model 6: Future Vessel Fuel Model

**Serves as:** vessel-specific performance intelligence.

**Does:** predict fuel consumption under environmental and operational
conditions.

Potential inputs:

``` text
Engine state
Speed
Draft
Loading
Wind
Waves
Currents
Sea ice
Route geometry
Historical fuel
```

Output:

``` text
Fuel consumption distribution
```

This becomes substantially more valuable after real voyage telemetry is
available.

------------------------------------------------------------------------

### Model 7: Future Risk Learning Model

**Serves as:** a research enhancement to the interpretable risk engine.

**Does:** learn nonlinear relationships between environmental conditions
and observed operational outcomes, provided sufficient historical labels
exist.

Potential targets:

-   route difficulty,
-   delay probability,
-   hazardous exposure,
-   operational interruption,
-   iceberg encounter,
-   station accessibility.

The learned risk model should remain subordinate to hard safety
constraints and an interpretable risk layer.

------------------------------------------------------------------------

## 7A.4 What Is Not an AI Model

The following are deliberately not represented as AI models in the POC:

``` text
Weather forecasting
Ocean forecasting
Bathymetry
Coastline
Route search
Basic map rendering
Data ingestion
Mission configuration
```

These are services, scientific products, deterministic algorithms, or
existing systems.

This separation prevents the product from becoming an arbitrary
collection of machine-learning labels.

------------------------------------------------------------------------

## 7A.5 POC Feature Priority

### P0: Required End-to-End Demonstration

``` text
Mission creation
        ↓
Interactive Antarctic map
        ↓
Time slider
        ↓
Current environmental state
        ↓
Sea-ice forecast
        ↓
Sea-ice uncertainty
        ↓
Iceberg observations
        ↓
Iceberg physics trajectories
        ↓
Weather/ocean layers
        ↓
Dynamic risk map
        ↓
PolarRoute
        ↓
Safest route
Balanced route
Fastest route
Fuel-efficient route
        ↓
Route comparison
        ↓
Mission/location comparison
        ↓
Uncertainty inspection
        ↓
Explanation
```

### P1: Research and Product Enhancement

-   ML sea-ice bias correction.
-   Improved seasonal model.
-   SAR iceberg detection.
-   Iceberg physics residual correction.
-   Simplified vessel fuel calibration.
-   Historical archive.
-   Better uncertainty calibration.
-   User authentication and persistence.
-   More ensemble products.
-   Expanded vessels.
-   Expanded operating regions.

### P2: Advanced Research

-   Large multimodal environmental model.
-   Sea-ice motion forecasting.
-   Sea-ice thickness intelligence.
-   Iceberg melt/shape evolution.
-   Wave-ice interaction.
-   Learned risk model.
-   Advanced vessel performance model.
-   Automated mission reports.
-   More sophisticated mission optimization.

### Operational Future

-   Live satellite feeds.
-   Live weather/ocean feeds.
-   GPS/AIS.
-   Engine telemetry.
-   Actual fuel data.
-   Continuous data assimilation.
-   Dynamic route replanning.
-   Onboard display.
-   Offline inference.
-   Low-bandwidth synchronization.
-   Actual-vs-predicted feedback loop.

------------------------------------------------------------------------

## 7A.6 End-to-End User Workflow

### Step 1: Create Mission

The planner opens AMIP and specifies:

``` text
Vessel
Origin
Destination
Departure window
Mission deadline
Safety/Fuel/Time priorities
```

The system creates a mission scenario.

### Step 2: Build Mission Corridor

The system determines the relevant Antarctic operating region and loads
environmental datasets required for that corridor.

The system should avoid unnecessary computation over irrelevant global
areas.

### Step 3: Load Current State

The platform loads:

``` text
Current SIC
Current iceberg positions
Current weather
Current ocean
Bathymetry
Stations
Geographic constraints
```

Each layer carries timestamp and source metadata.

### Step 4: Generate Forecast

For each requested horizon:

``` text
SIC forecast
Weather forecast
Ocean forecast
Iceberg trajectory ensemble
```

The sea-ice model generates probabilistic SIC.

The iceberg model generates trajectory ensembles.

Operational weather/ocean products provide their corresponding
forecasts.

### Step 5: Quantify Uncertainty

The system calculates:

``` text
SIC uncertainty
Iceberg uncertainty
Weather uncertainty
Risk uncertainty
```

These remain attached to the environmental state.

### Step 6: Generate Risk

For each spatial cell and forecast time:

``` text
Sea-ice risk
+
Iceberg risk
+
Weather/wave risk
+
Vessel constraints
        ↓
Composite environmental risk
```

### Step 7: Generate Routes

The environmental risk field is converted into a routing mesh.

PolarRoute generates multiple candidates.

``` text
Safest
Fastest
Fuel-efficient
Balanced
```

### Step 8: Evaluate Routes

For every candidate:

``` text
Distance
ETA
Fuel
Sea-ice exposure
Iceberg exposure
Weather exposure
Maximum risk
Expected risk
Risk uncertainty
```

are calculated.

### Step 9: Compare Missions

The planner can compare:

``` text
Departure A vs Departure B
Bharati first vs Maitri first
Safest vs Balanced vs Fastest
```

### Step 10: Inspect Uncertainty

The planner selects a location or route segment and sees:

``` text
Predicted condition
Prediction interval
Confidence
Data source
Forecast horizon
```

### Step 11: Review Recommendation

The system explains the recommendation using the actual calculated route
metrics.

### Step 12: Export

The planner can export the mission analysis as a structured report.

------------------------------------------------------------------------

## 7A.7 Time-Slider Execution Model

The time slider is implemented as a state-selection mechanism.

If the selected time is `T`:

``` text
Frontend
   ↓
GET /environment?time=T
   ↓
Backend
   ↓
Retrieve environmental state at T
   ↓
SIC(T)
Icebergs(T)
Weather(T)
Ocean(T)
Risk(T)
   ↓
Frontend redraw
```

When the user requests a route for that time:

``` text
/environment?time=T
        ↓
Risk(T)
        ↓
Mesh(T)
        ↓
PolarRoute
        ↓
Routes(T)
```

For a moving vessel, the route should ultimately be treated as
time-dependent:

``` text
Route position x(t)
```

rather than merely a static geometric line.

------------------------------------------------------------------------

## 7A.8 Model-Service Dependency Graph

``` text
                       ┌────────────────────┐
                       │ Historical Data    │
                       └─────────┬──────────┘
                                 ↓
                       ┌────────────────────┐
                       │ Data Cube / Store  │
                       └─────────┬──────────┘
                                 ↓
              ┌──────────────────┼──────────────────┐
              ↓                  ↓                  ↓
       Sea-Ice Model       Weather Service    Ocean Service
              ↓                  ↓                  ↓
       SIC Distribution     Weather Fields     Ocean Fields
              │                  │                  │
              │                  │          ┌───────┘
              │                  │          ↓
              │                  │   Iceberg Drift Model
              │                  │          ↓
              │                  │   Trajectory Ensemble
              │                  │          ↓
              └──────────────┬───┴──────────┘
                             ↓
                    Environmental State
                             ↓
                    Uncertainty Engine
                             ↓
                       Risk Engine
                             ↓
                    Vessel Constraints
                             ↓
                    Environmental Mesh
                             ↓
                        PolarRoute
                             ↓
                     Candidate Routes
                             ↓
                     Mission Analyzer
                             ↓
                  ┌──────────┼──────────┐
                  ↓          ↓          ↓
               Map UI    Comparison   Reports
```

------------------------------------------------------------------------

## 7A.9 Data Contract Between Components

Each prediction service should return more than a raw array.

A prediction object should conceptually contain:

``` text
variable
forecast_initialization_time
forecast_valid_time
spatial_reference
resolution
value
uncertainty
source
model
model_version
data_quality
missingness
```

This allows downstream services to determine whether a value is:

``` text
Observed
Reanalyzed
Forecast
AI-predicted
Physics-simulated
Derived
Estimated
```

This provenance distinction is required throughout the system.

------------------------------------------------------------------------

## 7A.10 Real vs Simulated vs Estimated Data

The POC should clearly classify outputs.

### Real / Observed

Examples:

-   satellite observations,
-   historical environmental measurements,
-   observed iceberg positions,
-   bathymetry,
-   station locations.

### Forecast / Model Product

Examples:

-   operational weather forecasts,
-   ocean forecasts,
-   seasonal forecasts.

### AI-Predicted

Examples:

-   future sea-ice concentration from the custom ML model,
-   future environmental variables from a future multimodal model.

### Physics-Simulated

Examples:

-   iceberg trajectories generated by the drift model.

### Estimated

Examples:

-   POC fuel consumption without calibrated telemetry.

### Simulated for Demonstration

Any data intentionally created to demonstrate a UI or workflow without
being sourced from a real operational dataset must be explicitly marked
as simulated.

------------------------------------------------------------------------

## 7A.11 Product Architecture Principle

The complete architecture should remain modular even after the future
large model is developed.

The intended evolution is:

``` text
Current POC

Specialized models
      ↓
Risk
      ↓
Routing


Future

Large environmental model
      ↓
Specialized physics + AI
      ↓
Data assimilation
      ↓
Risk
      ↓
Vessel performance
      ↓
Routing
      ↓
Mission optimization
```

The large model improves environmental intelligence. It does not become
a single point of failure for every system function.

------------------------------------------------------------------------

## 7A.12 Success Criteria for the Complete Product

A successful POC must demonstrate that:

1.  Multiple environmental datasets can be unified.
2.  Future sea-ice conditions can be predicted with measurable
    validation.
3.  Uncertainty is explicitly represented.
4.  Iceberg trajectories can be propagated probabilistically.
5.  Environmental hazards can be fused into a time-dependent risk field.
6.  Routes change when environmental conditions change.
7.  Routes change when objective weights change.
8.  Candidate routes can be compared quantitatively.
9.  The system explains why routes differ.
10. Historical replay can evaluate prediction performance.
11. The architecture can accept future live data.
12. No subsystem claims capabilities that its data or validation cannot
    support.

The strongest demonstration is not a beautiful map alone.

It is the causal chain:

``` text
Environmental conditions change
        ↓
Forecast changes
        ↓
Uncertainty changes
        ↓
Risk field changes
        ↓
Optimal route changes
        ↓
Fuel/time/safety tradeoff changes
        ↓
Mission recommendation changes
```

That is the core product behavior.

------------------------------------------------------------------------

# 8. What the Independent Solution Contributes

The independent architecture identified several important principles.

## 8.1 ML Should Not Replace Physics

Sea-ice, ocean and iceberg systems have strong physical structure.

ML is most valuable where it can:

-   correct bias,
-   learn residuals,
-   fuse variables,
-   downscale,
-   recognize nonlinear relationships,
-   or provide efficient approximate forecasts.

It should not replace known physical mechanisms merely to increase the
number of AI components.

## 8.2 Weather and Ocean Forecasts Should Normally Be Consumed

Do not build a weather model simply because the system contains AI.

Use authoritative forecast products and use ML only where additional
correction/downscaling/fusion provides demonstrated value.

## 8.3 Iceberg Trajectory Prediction Should Start With Physics

Large Antarctic tabular icebergs can be strongly controlled by ocean
circulation, with other forces contributing depending on iceberg size
and conditions.

A physics-informed ensemble is therefore a better starting point than a
pure deep trajectory model.

## 8.4 PolarRoute Is a Major Reusable Component

The British Antarctic Survey's PolarRoute project already provides an
open-source long-distance polar route-planning package that:

-   constructs environmental meshes,
-   models vessel performance,
-   incorporates environmental conditions,
-   finds optimized paths,
-   and supports vessel/fuel-related calculations.

It is available under the MIT license and has both a core Python package
and associated server/pipeline repositories.

This is a major architectural finding.

**The project should not rebuild PolarRoute simply to say that it used
AI.**

------------------------------------------------------------------------

# 9. What Our Initial Concept Got Right

The original concept's strongest assumptions were:

1.  The POC should begin as strategic planning rather than live onboard
    navigation.
2.  An interactive Antarctic map should be the central user interface.
3.  The system should compare safety, fuel and time.
4.  The system should investigate approximately three months of
    planning.
5.  Geographic locations should be evaluated in addition to routes.
6.  Uncertainty should be visible.
7.  Future onboard integration should be part of the architectural
    direction.
8.  AI/ML should materially contribute to the system rather than being
    decorative.

These should remain.

------------------------------------------------------------------------

# 10. What Our Initial Concept Should Change

## 10.1 Do Not Build a New Route Optimizer First

PolarRoute already addresses a large portion of:

-   polar environmental routing,
-   environmental mesh generation,
-   vessel performance,
-   route optimization.

The development effort should therefore focus on the intelligence that
feeds the route engine.

## 10.2 Do Not Promise a Deterministic 90-Day Weather Forecast

At long horizons, weather information should be represented through:

-   seasonal outlooks,
-   ensemble probabilities,
-   climatology,
-   analogs,
-   or derived mission-level risk.

## 10.3 Do Not Force AI into Every Subsystem

The final system should include:

-   AI/ML where it adds predictive value,
-   physics where physics is better,
-   external numerical forecasts where they already outperform a
    student-built replacement,
-   optimization algorithms where deterministic graph optimization is
    appropriate.

## 10.4 Do Not Treat Iceberg Detection as the Only Iceberg AI Problem

For the POC, existing iceberg observation products can provide
detections.

The AI/physics contribution can instead be:

> **current iceberg observations → trajectory ensemble →
> route-intersection probability**

A future model can improve detection from raw SAR imagery.

## 10.5 Do Not Overclaim Fuel Optimization

The POC can estimate fuel.

Future vessel telemetry can learn vessel-specific consumption.

These are different capabilities and must be labeled differently.

------------------------------------------------------------------------

# 11. Unified Product Architecture

The final product should consist of seven major logical layers.

``` text
┌───────────────────────────────────────────────────────────┐
│                  1. DATA SOURCES                          │
│ Satellite | Sea Ice | Icebergs | Weather | Ocean | Geo   │
└─────────────────────────────┬─────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────┐
│                  2. DATA FUSION                           │
│ Spatial + temporal harmonization | QC | features | cube  │
└─────────────────────────────┬─────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────┐
│             3. FORECAST / PREDICTION LAYER               │
│ Sea-ice ML | Iceberg physics | Weather/Ocean forecasts   │
└─────────────────────────────┬─────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────┐
│              4. UNCERTAINTY + RISK ENGINE                │
│ Probability | ensemble spread | hazard fields | risk     │
└─────────────────────────────┬─────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────┐
│          5. MISSION + ROUTE INTELLIGENCE                 │
│ Location analysis | PolarRoute | route comparisons       │
└─────────────────────────────┬─────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────┐
│                6. DECISION INTERFACE                     │
│ Antarctic map | timeline | comparisons | explanations    │
└─────────────────────────────┬─────────────────────────────┘
                              ↓
                    HUMAN MISSION DECISION
```

------------------------------------------------------------------------

# 12. Dataset Architecture

## 12.1 Dataset Selection Principle

The project should distinguish four classes of information:

### A. Observation

What has actually been observed.

### B. Reanalysis / Historical Reconstruction

A consistent historical estimate used for training and climatology.

### C. Operational Forecast

A model-generated future state from a recognized forecasting system.

### D. AI/ML Prediction

A derived forecast or correction generated by AMIP.

This distinction must be preserved in the data model and frontend.

------------------------------------------------------------------------

# 13. Sea-Ice Datasets

## 13.1 NSIDC AMSR-E/AMSR2 Unified L3 Daily 12.5 km

**Provider:** NASA National Snow and Ice Data Center

**Dataset:** AU_SI12

**Useful variables:**

-   Sea-ice concentration
-   Brightness temperatures
-   Snow depth over sea ice
-   Supporting polar products

**Temporal resolution:** daily

**Spatial resolution:** 12.5 km

**Antarctic grid:** polar stereographic

**Use in AMIP:**

-   Historical training target
-   Validation
-   Recent observation layer
-   Climatology
-   Anomaly generation

**Official source:**

https://nsidc.org/data/au_si12/versions/1

**Important note:** NSIDC currently documents the record as covering
AMSR-E from 2002--2011 and AMSR2 from 2012 onward. A single
uninterrupted "AMSR2 from 1989" training series should therefore not be
claimed. Earlier passive-microwave datasets may be used to extend
historical coverage if required.

## 13.2 Copernicus Marine Sea-Ice Products

Use Copernicus Marine products for:

-   Sea-ice concentration
-   Sea-ice edge
-   Sea-ice drift
-   Ice type
-   Related ice variables
-   Operational/forecast baselines where available

Official portal:

https://data.marine.copernicus.eu/

The exact product, resolution and forecast horizon should be recorded
from the selected product metadata at implementation time rather than
hard-coded in the architecture.

## 13.3 EUMETSAT / OSI SAF

Potential role:

-   Independent SIC source
-   Ice-edge validation
-   Near-real-time environmental state

Official resource:

https://osi-saf.eumetsat.int/

## 13.4 Sea-Ice Dataset Role Matrix

  --------------------------------------------------------------------------------------
  Dataset          Historical    NRT            Forecast   Training   Validation     POC
  -------------- ------------ ------ ------------------- ---------- ------------ -------
  NSIDC AU_SI12           Yes    Yes                  No        Yes          Yes     Yes

  Copernicus              Yes    Yes   Product-dependent        Yes          Yes     Yes
  Marine ice                                                                     
  products                                                                       

  EUMETSAT/OSI            Yes    Yes   Product-dependent   Optional          Yes     Yes
  SAF                                                                            
  --------------------------------------------------------------------------------------

------------------------------------------------------------------------

# 14. Iceberg Data

## 14.1 Copernicus Marine Iceberg Product

The Copernicus Marine product:

**SAR Sea Ice Berg Concentration and Individual Icebergs Observed with
Sentinel-1 & RCM**

provides:

-   Individual iceberg observations
-   Iceberg concentration
-   Satellite-derived detections
-   Gridded products
-   Sentinel-1/RCM-derived information
-   CFAR-based detection products

Official source:

https://data.marine.copernicus.eu/product/SEAICE_ARC_SEAICE_L4_NRT_OBSERVATIONS_011_007/description

This is highly valuable because the POC does not need to solve raw-SAR
iceberg detection before it can solve the actual operational question of
iceberg risk.

## 14.2 U.S. National Ice Center

Potential use:

-   Larger iceberg tracking
-   Historical/reference tracks
-   Independent validation

Official resource:

https://www.natice.noaa.gov/

Use availability and licensing according to the current source.

## 14.3 Historical Iceberg Tracks

Historical iceberg trajectories can be used to validate the physical
drift model.

Potential sources identified in the architecture research include
public/research tracking datasets.

Every specific historical dataset should be checked for:

-   licensing,
-   track continuity,
-   spatial coverage,
-   temporal frequency,
-   iceberg size,
-   and whether the tracks are appropriate for Antarctic operations.

------------------------------------------------------------------------

# 15. Oceanographic Datasets

## 15.1 Copernicus Marine

Potential variables:

-   Surface currents
-   Ocean temperature
-   Salinity
-   Sea level
-   Ocean velocity
-   Waves
-   SST

Official portal:

https://data.marine.copernicus.eu/

Primary uses:

-   Iceberg drift forcing
-   Route current assistance
-   Fuel model inputs
-   Environmental risk
-   ML predictors

## 15.2 HYCOM

Potential use:

-   Alternative or comparison ocean current field
-   3D ocean-state information
-   Drift-model forcing

Official resource:

https://www.hycom.org/

Use as an alternative or ensemble input where coverage and access are
appropriate.

## 15.3 GEBCO

Variables:

-   Bathymetry
-   Elevation

Official resource:

https://www.gebco.net/

Use:

-   Grounding constraints
-   Shallow-water avoidance
-   Route graph masking
-   Environmental context

------------------------------------------------------------------------

# 16. Meteorological Data

## 16.1 ERA5

Provider:

ECMWF / Copernicus Climate Data Store

Uses:

-   Historical wind
-   Temperature
-   Pressure
-   Atmospheric fields
-   Climatology
-   Model training features

Official source:

https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels

## 16.2 ECMWF Operational Forecasts

Use operational ECMWF forecasts rather than attempting to train a
weather model.

Potential variables:

-   Wind
-   Pressure
-   Temperature
-   Precipitation
-   Waves where available through the relevant product
-   Other relevant meteorological parameters

The frontend should expose the product's actual forecast horizon and
update time.

## 16.3 ECMWF Seasonal Forecasts

ECMWF states that its seasonal forecasts provide information up to seven
months ahead and are produced as ensembles. The system should therefore
use seasonal forecasts as one input to long-range planning rather than
pretending they are deterministic weather predictions.

Official source:

https://www.ecmwf.int/en/forecasts/documentation-and-support/seasonal

------------------------------------------------------------------------

# 17. NCPOR-Specific Data

An important addition to the two original architectures is the NCPOR
data ecosystem itself.

NCPOR publicly exposes polar data and station observations, including
meteorological information from Indian polar stations.

Relevant resources include:

https://data.ncpor.res.in/

https://npdc.ncpor.res.in/

These can become strategically valuable for an eventual NCPOR-specific
model because they provide Indian station observations for validation
and regional calibration.

Potential future use:

-   Station weather verification
-   Forecast bias correction
-   Local operating-condition models
-   Mission archive
-   Indian expedition feedback loop

NCPOR observations should not automatically be treated as sufficient
training data. Coverage, variables, quality and historical length must
be assessed first.

------------------------------------------------------------------------

# 18. Geographic Datasets

Use:

-   SCAR Antarctic Digital Database
-   GEBCO
-   NCPOR station coordinates
-   Research station databases
-   Relevant marine boundaries
-   Relevant protected/restricted areas if required by the mission

Core geographic objects:

-   Coastline
-   Ice shelves
-   Stations
-   Candidate operating areas
-   Bathymetry
-   Water mask
-   Transit corridors

The geographic layer is not merely a basemap.

It defines where the optimization problem is legally/geographically
valid.

------------------------------------------------------------------------

# 19. Open-Source and Adjacent Systems to Reuse

One of the strongest findings from comparing the architectures is that
AMIP should be an **intelligence layer around proven open-source
components**, not a reinvention project.

## 19.1 PolarRoute

GitHub:

https://github.com/bas-logist/PolarRoute

PolarRoute provides:

-   Environmental mesh construction
-   Vessel performance modelling
-   Route planning
-   Environmental constraint handling
-   Physics-informed route smoothing
-   Route optimization

The repository currently describes the package as an open-source
long-distance maritime polar route planner and is licensed under MIT.

The related research paper is:

Jonathan D. Smith et al. (2025), "Path-Planning on a Spherical Surface
with Disturbances and Exclusion Zones."

DOI:

https://doi.org/10.1613/jair.1.16746

## 19.2 MeshiPhi

MeshiPhi is the environmental mesh component associated with PolarRoute.

It creates structured environmental representations used by the
route-planning stack.

Reuse rather than rebuild.

## 19.3 PolarRoute-server

Repository:

https://github.com/bas-logist/PolarRoute-server

This provides a server-side integration option around PolarRoute and
MeshiPhi.

The current repository includes Django, Celery and PostgreSQL
components.

Architecture recommendation:

-   Prefer direct library integration during early development.
-   Move to a PolarRoute-server-backed service if the project needs
    independent route jobs or a stable service boundary.
-   Do not invent an API contract that is not supported by the current
    PolarRoute-server implementation.
-   Pin the exact upstream commit/version used by the project.

## 19.4 PolarRoute-pipeline

Repository:

https://github.com/bas-logist/PolarRoute-pipeline

This is particularly relevant because it demonstrates that operational
polar routing can be organized as a data pipeline:

-   retrieve environmental data,
-   store it,
-   construct meshes,
-   generate routes,
-   produce outputs.

It is a valuable adjacent reference architecture.

## 19.5 Frontend/Open Geospatial Components

Potential open-source stack:

-   MapLibre GL JS
-   Deck.gl where high-volume visualization is required
-   Apache ECharts for analytics
-   xarray
-   Dask
-   Rasterio
-   GeoPandas
-   GDAL
-   PostGIS
-   Zarr

These components should be selected according to the POC's actual
workload.

------------------------------------------------------------------------

# 20. Final AI/ML Architecture

The AI architecture should be modular.

``` text
                  ┌───────────────────────────┐
                  │ Historical observations   │
                  └─────────────┬─────────────┘
                                ↓
                  ┌───────────────────────────┐
                  │ Sea-Ice Forecast Model    │
                  │ Statistical + ML ensemble │
                  └─────────────┬─────────────┘
                                ↓
                  ┌───────────────────────────┐
                  │ Probabilistic SIC fields  │
                  └─────────────┬─────────────┘

Iceberg observations ─────────→ Physics Drift Model
                                     ↓
                           Trajectory Ensemble

ECMWF forecast ─────────────────────→ Environmental State
CMEMS forecast ─────────────────────→ Environmental State

All predictions
     ↓
Uncertainty / Scenario Engine
     ↓
Environmental Risk Field
     ↓
PolarRoute + Mission Analytics
```

------------------------------------------------------------------------

# 21. Sea-Ice Forecasting: Core AI Capability

## 21.1 Why Sea Ice Is the Most Important AI Research Component

Sea-ice concentration directly influences:

-   vessel accessibility,
-   route feasibility,
-   route risk,
-   fuel consumption,
-   schedule,
-   station access.

It is also a problem where existing research demonstrates meaningful ML
value.

The research should not assume that a deep network is automatically
superior.

## 21.2 Research Evidence

### Ice-kNN-South

A 2025 Journal of Geophysical Research: Machine Learning and Computation
paper introduced Ice-kNN-South for Antarctic sea-ice concentration
anomaly prediction up to 90 days.

The study reports improved performance against anomaly persistence,
climatology and ECMWF predictions over much of the lead period while
using relatively little computational resource.

Source:

https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024JH000433

This is highly relevant because the intended POC does not need a giant
deep-learning system to establish value.

### ANTSIC-UNet

A 2025 The Cryosphere paper presents ANTSIC-UNet for extended seasonal
Antarctic sea-ice concentration prediction using multiple climate
variables.

The study evaluates forecasts up to six months ahead against statistical
baselines and SEAS5 and reports skill that varies by region, season and
event type.

Source:

https://tc.copernicus.org/articles/19/6381/2025/

This supports investigating a multi-variable spatial deep-learning model
for a later research version.

### ConvLSTM Antarctic Forecasting

A 2024 Ocean Modelling study used ConvLSTM for daily Antarctic sea-ice
prediction and reported useful skill over approximately 30 days.

Source:

https://www.sciencedirect.com/science/article/pii/S1463500324000738

This is useful as a model family comparison, not a mandate to use
ConvLSTM.

------------------------------------------------------------------------

# 22. Unified Sea-Ice Model Strategy

The best architecture is not one model for all horizons.

## 22.1 Horizon A: 0--10 Days

Use operational forecast products as the primary source.

AI role:

-   bias correction,
-   local correction,
-   uncertainty calibration,
-   data fusion.

Do not replace the operational numerical forecast unless validation
proves an ML replacement is better.

## 22.2 Horizon B: 10--30/45 Days

Candidate models:

-   Ice-kNN-South-style method
-   lightweight U-Net
-   ConvLSTM baseline
-   anomaly-persistence baseline

The final selection should be empirical.

At this horizon a POC can reasonably demonstrate:

-   current observation,
-   model prediction,
-   baseline prediction,
-   comparison,
-   error evaluation.

## 22.3 Horizon C: 30--90 Days

Use a seasonal/extended forecast architecture.

Candidates:

-   Ice-kNN-South
-   ANTSIC-UNet-style model
-   anomaly persistence
-   climatology
-   SEAS5-derived outlook
-   model ensemble

The important design choice is:

> Output a probability distribution or expected anomaly, not a
> false-precision deterministic map.

## 22.4 Horizon D: Beyond 90 Days

Do not promise fine-scale deterministic prediction.

Use:

-   climatology,
-   seasonal outlook,
-   historical analogs,
-   scenario analysis,
-   probability of favorable conditions.

This can still be operationally useful for strategic planning.

------------------------------------------------------------------------

# 23. Recommended Sea-Ice Model Stack

The most defensible development strategy is:

### Baseline 1

Persistence.

### Baseline 2

Seasonal climatology.

### Baseline 3

SEAS5 or another relevant operational forecast.

### Candidate AI 1

Ice-kNN-South-style lightweight prediction.

### Candidate AI 2

Multi-variable U-Net/ANTSIC-UNet-style model.

### Candidate AI 3

ConvLSTM baseline for comparison.

Then select based on actual validation.

This avoids prematurely locking the project to Temporal U-Net merely
because it looks suitably AI-ish in a slide deck.

------------------------------------------------------------------------

# 24. Sea-Ice Inputs

Potential input variables:

### Sea-ice

-   Recent SIC
-   SIC anomaly
-   Ice edge
-   Ice drift
-   Ice concentration history

### Ocean

-   SST
-   Surface current
-   Sea-surface height where useful
-   Ocean temperature
-   Salinity where useful

### Atmosphere

-   Wind u/v
-   Air temperature
-   Pressure
-   Radiation where useful

### Forecast information

-   Seasonal ensemble mean
-   Seasonal anomaly
-   Ensemble spread

### Derived features

-   Distance to ice edge
-   SIC gradient
-   Recent SIC trend
-   Historical percentile
-   Seasonal phase

------------------------------------------------------------------------

# 25. Sea-Ice Outputs

Each prediction should produce:

-   Median/mean SIC
-   Lower quantile
-   Upper quantile
-   Probability SIC exceeds an operational threshold
-   Ice-edge probability
-   Anomaly
-   Model confidence
-   Baseline comparison

Useful output:

``` text
Probability(SIC > threshold)
```

is often more operationally meaningful than:

``` text
SIC = 0.37
```

because the route engine ultimately needs to reason about navigability.

------------------------------------------------------------------------

# 26. Iceberg Detection Strategy

## 26.1 POC Decision

Use an existing operational/research iceberg detection product.

Primary candidate:

Copernicus Marine Sentinel-1/RCM iceberg product.

Do not make raw-SAR detection a POC dependency.

This keeps the project focused on the actual SIH problem:

> **predicting iceberg trajectories and using them for navigation
> decision support.**

## 26.2 Future Detection Model

Later, develop an ML detector using:

-   Sentinel-1 SAR
-   labeled iceberg observations
-   existing CFAR detections as weak labels
-   human validation
-   historical tracks

Candidate architectures:

-   CNN classifier
-   U-Net
-   segmentation transformer
-   object detector

Model choice should depend on the labeling structure.

------------------------------------------------------------------------

# 27. Iceberg Trajectory Prediction

## 27.1 Physics First

The trajectory model should represent:

-   Ocean-current advection
-   Wind drag
-   Coriolis effects
-   Wave-related effects where relevant
-   Sea-ice interaction
-   Iceberg size and geometry
-   Possible grounding

Research on large Antarctic tabular icebergs supports strong coupling to
ocean currents in relevant regimes.

Reference:

Wagner, T. J. W. et al. (2017), "An Analytical Model of Iceberg Drift."

https://journals.ametsoc.org/view/journals/phoc/47/7/jpo-d-16-0262.1.xml

## 27.2 Model

Use a Lagrangian drift framework.

Conceptually:

``` text
Initial iceberg state
        +
Ocean current
        +
Wind
        +
Coriolis / physical terms
        +
Sea-ice interaction
        +
Stochastic uncertainty
        ↓
Future iceberg position
```

Run this as an ensemble.

## 27.3 Ensemble Generation

For each iceberg:

1.  Start from observed position and dimensions.
2.  Sample uncertainty in the initial state.
3.  Sample/perturb forcing fields.
4.  Vary uncertain physical coefficients.
5.  Integrate forward.
6.  Produce multiple possible tracks.

Output:

-   Mean/median trajectory
-   50% region
-   90% region
-   probability density
-   probability of entering route buffer
-   closest approach
-   time of closest approach

## 27.4 Why Not Pure ML Initially?

Pure ML trajectory models require:

-   substantial high-quality track histories,
-   consistent inputs,
-   well-defined labels,
-   enough variation across conditions.

The physics-based system already provides an interpretable prior.

The future architecture can learn the residual:

``` text
Observed trajectory
-
Physics trajectory
=
Physics-model residual
```

Then ML can learn the residual correction.

This is a better research direction than throwing LSTMs at sparse
tracks.

------------------------------------------------------------------------

# 28. Iceberg ML Enhancement

Future model:

``` text
Physics Drift Prediction
          ↓
Residual Features
          ↓
XGBoost / small neural model
          ↓
Residual Correction
          ↓
Hybrid Trajectory
```

Candidate features:

-   current velocity
-   wind velocity
-   iceberg dimensions
-   latitude
-   longitude
-   sea-ice concentration
-   wave state
-   time since initialization
-   bathymetric context

Output:

-   residual displacement
-   confidence-adjusted trajectory

Validation must compare:

1.  persistence,
2.  physics-only,
3.  physics + ML.

The ML model must demonstrate improvement before being adopted.

------------------------------------------------------------------------

# 29. Weather and Ocean Integration

## 29.1 Rule

Do not train a replacement global weather model.

Use authoritative operational products.

The architecture should ingest:

-   atmospheric forecast,
-   ocean forecast,
-   wave forecast,
-   seasonal products.

## 29.2 Where AI Helps

AI can be used for:

-   bias correction,
-   downscaling,
-   multi-source blending,
-   uncertainty calibration,
-   route-impact prediction.

Example:

``` text
ECMWF forecast
+
Historical observation error
↓
ML residual correction
↓
AMIP-adjusted local forecast
```

This should only be activated after demonstrating that correction
improves validation skill.

------------------------------------------------------------------------

# 30. Environmental State Cube

The unified system should represent environmental state as a
spatiotemporal cube.

Conceptually:

``` text
Dimensions:
(time, y, x, variable)
```

For probabilistic/ensemble products:

``` text
(time, ensemble, y, x, variable)
```

Potential variables:

``` text
sic
sic_anomaly
ice_edge_distance
ice_drift_u
ice_drift_v
sst
ocean_u
ocean_v
wave_height
wave_period
wind_u
wind_v
pressure
temperature
iceberg_density
iceberg_probability
bathymetry
```

------------------------------------------------------------------------

# 31. Spatial Reference Strategy

Use:

### Internal scientific analysis

Antarctic Polar Stereographic where appropriate.

This is appropriate for Antarctic spatial analysis because distance and
area behavior are more suitable for the region than a naive lat/lon
grid.

### Web display

WGS84/web-map coordinates as required by the selected frontend mapping
system.

### Routing

Use the coordinate representation required by PolarRoute/MeshiPhi and
preserve the correct geodesic/geospatial transformations.

Do not assume that the web map's projection should become the scientific
computation grid.

------------------------------------------------------------------------

# 32. Spatial Resolution Strategy

Do not force all data to the same resolution prematurely.

Use a multi-resolution approach:

``` text
Native Data
    ↓
Quality Control
    ↓
Scientific Processing at native/appropriate resolution
    ↓
Analysis Grid
    ↓
Route-resolution environmental mesh
    ↓
Web visualization tiles
```

The architecture drafts suggested approximately 10 km as an important
fusion/routing resolution.

That is a reasonable POC candidate, but the exact resolution must be
based on:

-   input resolution,
-   route-engine requirements,
-   computational cost,
-   vessel-scale hazards,
-   and forecast reliability.

Fine-resolution visualization should not be confused with
fine-resolution prediction skill.

------------------------------------------------------------------------

# 33. Data Fusion Pipeline

``` text
SOURCE INGESTION
      ↓
Metadata validation
      ↓
Quality-control flags
      ↓
Coordinate transformation
      ↓
Temporal normalization
      ↓
Spatial resampling/regridding
      ↓
Missing-data handling
      ↓
Feature engineering
      ↓
Historical climatology
      ↓
Forecast/observation alignment
      ↓
Unified environmental cube
      ↓
Model inputs
```

------------------------------------------------------------------------

# 34. Data Processing Requirements

## 34.1 Quality Control

Every dataset should preserve:

-   source,
-   acquisition time,
-   valid time,
-   processing version,
-   quality flag,
-   units,
-   spatial resolution,
-   temporal resolution.

## 34.2 Temporal Alignment

Forecast products must distinguish:

-   forecast initialization time,
-   lead time,
-   valid time.

Example:

``` text
Forecast issued:
2026-09-06 00:00 UTC

Valid:
2026-09-10 12:00 UTC

Lead:
4.5 days
```

This is essential for honest model evaluation.

## 34.3 Avoid Leakage

Training features must only use information that would actually have
been available at the simulated forecast issuance time.

For example, a model evaluated as a "30-day forecast" cannot
accidentally use observations from day +5 through day +30.

------------------------------------------------------------------------

# 35. Historical Training Dataset Construction

Construct forecast-style samples.

For each initialization time:

``` text
INPUT:
[t-30 ... t]

TARGET:
[t+1 ... t+H]

AVAILABLE_AT_T:
Only data that would have existed at t
```

Generate separate samples for:

-   short lead,
-   medium lead,
-   seasonal lead.

Use walk-forward temporal validation.

Do not random-shuffle the entire time series.

------------------------------------------------------------------------

# 36. Risk Engine

The environmental risk engine converts predictions into a
route-consumable representation.

Potential dimensions:

-   sea-ice risk,
-   iceberg risk,
-   weather risk,
-   wave risk,
-   current/fuel penalty,
-   bathymetric constraint,
-   uncertainty.

The central output is:

``` text
R(x, y, t)
```

where risk is spatially and temporally varying.

------------------------------------------------------------------------

# 37. Risk Engine Design Principle

The final implementation should separate:

### Hard constraints

Conditions under which a route cell should be:

-   inaccessible,
-   excluded,
-   or explicitly flagged.

### Soft costs

Conditions that increase:

-   risk,
-   time,
-   fuel,
-   or preference penalty.

This is preferable to collapsing everything into one arbitrary score.

Example:

``` text
Bathymetry < safe threshold
→ hard constraint

High adverse current
→ soft fuel penalty

High uncertainty
→ soft risk penalty

Extreme weather
→ hard or near-hard operational constraint
```

Exact operational thresholds require domain validation.

------------------------------------------------------------------------

# 38. Sea-Ice Risk

Do not assume a universal SIC threshold represents "unsafe."

Instead define:

``` text
R_ice =
f(
  SIC,
  ice type,
  thickness where available,
  vessel capability,
  operational policy
)
```

For the POC, configurable thresholds can be used.

The UI must label them as:

> planning assumptions / demonstration thresholds

until validated by NCPOR and vessel operators.

------------------------------------------------------------------------

# 39. Iceberg Risk

The most useful route-planning variable is not simply:

``` text
number of icebergs
```

but:

``` text
P(iceberg intersects route corridor during time window)
```

Possible calculation:

1.  Generate trajectory ensemble.
2.  Convert tracks into probability density.
3.  Buffer the proposed route.
4.  Calculate intersection probability.
5.  Incorporate uncertainty.
6.  Convert to route risk.

Output:

``` text
Iceberg intersection probability:
12%

Expected closest approach:
38 km

90% trajectory region:
Displayed as corridor
```

These values are illustrative outputs, not predetermined performance
claims.

------------------------------------------------------------------------

# 40. Weather Risk

Weather risk can be derived from variables relevant to vessel
operations.

Potential factors:

-   wind speed,
-   wind direction,
-   wave height,
-   wave period,
-   visibility proxies where available,
-   pressure gradients/storm indicators.

The exact operational thresholds should be configurable rather than
baked permanently into the product.

------------------------------------------------------------------------

# 41. Ocean Current Contribution

Current should have two distinct effects.

### Safety

In some contexts currents may influence navigation conditions and drift,
but this should be handled only where domain evidence supports it.

### Efficiency

Current directly matters to transit time and propulsion/fuel
requirements.

Therefore:

``` text
favorable current → lower route cost

adverse current → higher route cost
```

This is one of the variables that can turn a route optimizer from
"shortest path" into a real environmental route planner.

------------------------------------------------------------------------

# 42. Uncertainty Architecture

Uncertainty must propagate from upstream predictions into downstream
decisions.

``` text
Forecast uncertainty
        ↓
Prediction uncertainty
        ↓
Risk uncertainty
        ↓
Route uncertainty
        ↓
Mission decision confidence
```

## 42.1 Sea Ice

Potential:

-   quantile regression,
-   ensemble predictions,
-   analog spread,
-   climatological distribution.

## 42.2 Iceberg

Potential:

-   Monte Carlo trajectory ensemble,
-   forcing perturbation,
-   initial-state uncertainty.

## 42.3 Weather

Use native ensemble information where available.

## 42.4 Route

Run route evaluation across multiple environmental realizations where
computationally practical.

Instead of:

> "Route A is safest."

Display:

> "Route A has the lowest median risk and remains feasible across 87% of
> evaluated environmental scenarios."

Only use a percentage like this when it has actually been computed.

------------------------------------------------------------------------

# 43. Strategic Three-Month Planning

## 43.1 Core Concept

The three-month planning interface should be a **scenario explorer**,
not a 90-day weather oracle.

A planner selects:

``` text
Planning window:
December 1 → February 28
```

The system shows:

-   seasonal expectation,
-   historical distribution,
-   available seasonal ensemble information,
-   ML sea-ice outlook,
-   uncertainty,
-   weekly accessibility,
-   candidate locations,
-   route options where forecasts are valid.

## 43.2 Example Timeline

``` text
90 days
│
├── Seasonal outlook
│
├── Historical probability
│
├── AI sea-ice seasonal outlook
│
├── Weekly environmental scenarios
│
├── Medium-range forecast when available
│
└── Short-range operational forecast
```

As the mission date gets closer, the information should become more
specific.

------------------------------------------------------------------------

# 44. Location Intelligence

The product should not only evaluate routes.

It should evaluate:

> "Which location is operationally preferable during this period?"

## 44.1 Candidate Location Inputs

A location may be:

-   station,
-   research site,
-   sampling area,
-   coastal access point,
-   scientific region,
-   temporary operating area.

## 44.2 Location Metrics

Potential metrics:

-   probability of favorable sea-ice conditions,
-   mean/median SIC,
-   probability SIC exceeds a threshold,
-   iceberg exposure,
-   weather exposure,
-   wave conditions,
-   accessibility,
-   route distance,
-   estimated fuel,
-   uncertainty,
-   number of favorable operating days.

## 44.3 Output

Example conceptual result:

``` text
Location A
Favorable days: 31/45
Ice risk: Low
Weather exposure: Moderate
Access confidence: High

Location B
Favorable days: 22/45
Ice risk: Moderate
Weather exposure: Low
Access confidence: Medium
```

The platform should expose the underlying factors.

------------------------------------------------------------------------

# 45. Route Optimization

## 45.1 Use PolarRoute

The preferred architecture is:

``` text
AMIP Environmental Intelligence
             ↓
Mission-specific environmental mesh
             ↓
PolarRoute / MeshiPhi
             ↓
Optimized Route
```

PolarRoute should be treated as a reusable route-planning engine.

## 45.2 Why This Is Stronger

This gives the project two distinct areas of value:

### Existing capability

PolarRoute already provides polar path optimization.

### Our contribution

AMIP contributes:

-   mission-level planning,
-   ML sea-ice prediction,
-   uncertainty,
-   iceberg trajectory probability,
-   environmental risk fusion,
-   geographic comparison,
-   what-if analysis,
-   NCPOR-specific decision support.

That is a much cleaner system boundary.

------------------------------------------------------------------------

# 46. Route Objectives

Generate several useful alternatives rather than one supposedly perfect
route.

## 46.1 Safest

Minimize exposure to hard/soft hazard cost.

## 46.2 Fastest Feasible

Minimize predicted travel time while satisfying safety constraints.

## 46.3 Fuel-Efficient

Minimize predicted energy/fuel cost.

## 46.4 Balanced

Produce a Pareto/weighted compromise.

The user should see the tradeoff rather than have it hidden.

------------------------------------------------------------------------

# 47. Route Cost Formulation

Conceptually:

``` text
Total route cost =
    travel_time_cost
  + fuel_cost
  + sea_ice_risk_cost
  + iceberg_risk_cost
  + weather_risk_cost
  + uncertainty_penalty
```

However, safety-critical constraints should not simply be represented as
numerical weights.

The final architecture should distinguish:

``` text
INVALID ROUTE
```

from:

``` text
VALID BUT LESS PREFERRED ROUTE
```

This avoids a mathematically elegant optimizer selecting a route through
something that should have been impossible to cross.

------------------------------------------------------------------------

# 48. Route Comparison

For every route display:

-   distance,
-   estimated travel time,
-   estimated fuel,
-   maximum risk,
-   mean risk,
-   sea-ice exposure,
-   iceberg intersection probability,
-   weather exposure,
-   uncertainty,
-   major hazards,
-   explanation of tradeoffs.

Example:

``` text
ROUTE A — SAFEST
Distance: 4,180 NM
Time: 19.2 days
Fuel estimate: 1,430 MT
Median risk: 0.22
P95 risk: 0.41
Iceberg intersection: 4%

ROUTE B — FUEL EFFICIENT
Distance: 4,050 NM
Time: 18.8 days
Fuel estimate: 1,365 MT
Median risk: 0.29
P95 risk: 0.55
Iceberg intersection: 7%
```

These numbers are schematic and must not appear in the actual product
until generated by the system.

------------------------------------------------------------------------

# 49. Fuel Model

## 49.1 POC

Fuel should be treated as an estimated planning cost.

Potential inputs:

-   vessel displacement,
-   hull characteristics,
-   speed,
-   wind,
-   waves,
-   current,
-   sea-ice conditions.

Where PolarRoute's vessel-performance model provides appropriate
capabilities, reuse it.

## 49.2 Simplified Physics Model

A simplified model may use:

``` text
Fuel Rate =
Base vessel resistance
× speed relationship
× environmental correction
```

The exact implementation should be derived from:

-   available vessel specifications,
-   the selected route engine,
-   naval-architecture literature.

Do not make the POC dependent on unavailable proprietary telemetry.

## 49.3 Future Fuel Model

Once vessel telemetry exists:

``` text
GPS
+
speed
+
heading
+
engine RPM
+
fuel flow
+
draft
+
wind
+
wave
+
current
+
ice
        ↓
ML / hybrid vessel-performance model
        ↓
Actual fuel prediction
```

Candidate models:

-   gradient boosting,
-   neural networks,
-   Gaussian processes,
-   hybrid physics + ML.

The model should be calibrated on actual voyage data.

------------------------------------------------------------------------

# 50. Future On-Vessel Extension

The strategic architecture naturally evolves into an operational system.

## 50.1 Live State

``` text
Current vessel position
Current heading
Current speed
Current fuel
Current environmental state
```

## 50.2 Rolling Forecast

``` text
Latest satellite
+
Latest weather
+
Latest ocean
+
Latest iceberg observations
+
latest model predictions
```

## 50.3 Dynamic Route

``` text
Current state
→ forecast
→ risk
→ route
→ compare
→ update
```

The route is no longer static.

It becomes a rolling optimization problem.

------------------------------------------------------------------------

# 51. Closed-Loop Future Architecture

``` text
Prediction
    ↓
Vessel operation
    ↓
Actual observation
    ↓
Prediction error
    ↓
Data archive
    ↓
Model evaluation
    ↓
Model improvement
```

Potential feedback variables:

-   actual GPS trajectory,
-   observed ice,
-   actual sea state,
-   fuel consumed,
-   speed achieved,
-   route changes.

This feedback loop should be treated as a future research capability
rather than assumed to be automatically beneficial.

------------------------------------------------------------------------

# 52. Backend Architecture

The POC backend should remain modular without becoming unnecessarily
enterprise-heavy.

``` text
                 FastAPI
                    │
       ┌────────────┼────────────┐
       │            │            │
   Mission      Environment    Routing
   Service        Service      Service
       │            │            │
       │       ┌────┴────┐      │
       │       │         │      │
       │    Sea-Ice   Iceberg   │
       │      ML       Drift    │
       │                │       │
       └──────────┬─────┴───────┘
                  │
              Risk Engine
                  │
          Data Access Layer
            │           │
         PostGIS      Zarr
```

No security/authentication layer is defined in this document beyond what
is necessary to operate the POC.

------------------------------------------------------------------------

# 53. Backend Responsibilities

## Mission Service

Responsible for:

-   mission definitions,
-   origin,
-   destinations,
-   time windows,
-   vessel profile,
-   objectives,
-   generated assessments.

## Environment Service

Responsible for:

-   current environmental fields,
-   forecast retrieval,
-   raster metadata,
-   time slices.

## Sea-Ice Model Service

Responsible for:

-   ML inference,
-   model selection,
-   forecast generation,
-   confidence outputs.

## Iceberg Service

Responsible for:

-   observations,
-   trajectory ensembles,
-   trajectory probability fields.

## Risk Service

Responsible for:

-   environmental risk maps,
-   scenario aggregation,
-   uncertainty propagation.

## Routing Service

Responsible for:

-   preparing the route environment,
-   invoking PolarRoute,
-   collecting route alternatives,
-   calculating comparison metrics.

------------------------------------------------------------------------

# 54. Suggested Technology Stack

## Backend

-   Python
-   FastAPI
-   Pydantic
-   PostgreSQL
-   PostGIS

## Scientific Processing

-   NumPy
-   SciPy
-   xarray
-   Dask where necessary
-   Rasterio
-   rioxarray
-   GeoPandas
-   GDAL

## ML

-   PyTorch
-   scikit-learn
-   XGBoost where useful

## Data Storage

-   Zarr for multi-dimensional scientific data
-   GeoParquet for vector archives
-   Object storage for raw/processed datasets
-   PostGIS for mission and geospatial metadata

## Routing

-   PolarRoute
-   MeshiPhi

## Frontend

-   React
-   TypeScript
-   MapLibre GL JS
-   Apache ECharts or equivalent analytical charting library

The exact framework versions should be pinned during implementation.

------------------------------------------------------------------------

# 55. Storage Architecture

``` text
OBJECT STORAGE
│
├── raw/
│   ├── sea_ice/
│   ├── weather/
│   ├── ocean/
│   ├── iceberg/
│   └── geography/
│
├── processed/
│   ├── fused_environment.zarr
│   ├── climatology.zarr
│   ├── forecast.zarr
│   └── risk.zarr
│
└── models/
    ├── sea_ice/
    ├── iceberg/
    └── calibration/

POSTGIS
│
├── missions
├── locations
├── vessels
├── routes
├── iceberg metadata
└── dataset metadata
```

------------------------------------------------------------------------

# 56. API Design

The APIs should represent user actions rather than expose raw
implementation details unnecessarily.

## 56.1 Mission

``` http
POST /api/v1/missions
```

Create a mission.

``` http
GET /api/v1/missions/{mission_id}
```

Retrieve mission.

``` http
POST /api/v1/missions/{mission_id}/analyze
```

Run complete environmental/location/route analysis.

## 56.2 Environment

``` http
GET /api/v1/environment/current
```

Current environmental state.

``` http
GET /api/v1/environment/forecast
```

Forecast state.

``` http
GET /api/v1/sea-ice/forecast
```

Sea-ice forecast with uncertainty.

``` http
GET /api/v1/risk/map
```

Environmental risk field for a selected valid time.

## 56.3 Icebergs

``` http
GET /api/v1/icebergs
```

Current observed iceberg data.

``` http
GET /api/v1/icebergs/{iceberg_id}
```

Individual iceberg.

``` http
GET /api/v1/icebergs/{iceberg_id}/trajectory
```

Trajectory ensemble and probability field.

## 56.4 Locations

``` http
POST /api/v1/locations/analyze
```

Analyze one or more candidate locations.

``` http
POST /api/v1/locations/compare
```

Compare candidate locations.

## 56.5 Routes

``` http
POST /api/v1/routes/optimize
```

Generate route alternatives.

``` http
GET /api/v1/routes/{route_id}
```

Retrieve route and metrics.

------------------------------------------------------------------------

# 57. Mission Analysis Request

Example:

``` json
{
  "origin": {
    "name": "Cape Town",
    "lat": -33.9249,
    "lon": 18.4241
  },
  "destinations": [
    {
      "name": "Bharati",
      "lat": -69.4068,
      "lon": 76.1953
    },
    {
      "name": "Maitri",
      "lat": -70.7644,
      "lon": 11.7340
    }
  ],
  "planning_window": {
    "start": "2027-01-01",
    "end": "2027-02-28"
  },
  "vessel_profile": "configured-vessel",
  "priorities": {
    "safety": 0.5,
    "fuel": 0.3,
    "time": 0.2
  }
}
```

The exact coordinates and vessel profile should come from a validated
mission configuration rather than being hard-coded.

------------------------------------------------------------------------

# 58. Mission Analysis Internal Flow

When:

``` http
POST /api/v1/missions/{id}/analyze
```

is called:

``` text
1. Validate mission
        ↓
2. Resolve dates and locations
        ↓
3. Load environmental data
        ↓
4. Determine forecast horizon available
        ↓
5. Generate / retrieve sea-ice forecast
        ↓
6. Retrieve iceberg observations
        ↓
7. Generate iceberg trajectory ensemble
        ↓
8. Retrieve weather/ocean fields
        ↓
9. Generate environmental risk
        ↓
10. Evaluate candidate locations
        ↓
11. Prepare route environment
        ↓
12. Invoke PolarRoute
        ↓
13. Calculate route metrics
        ↓
14. Aggregate uncertainty
        ↓
15. Rank alternatives
        ↓
16. Return decision-support result
```

------------------------------------------------------------------------

# 59. Route Optimization API Flow

``` http
POST /api/v1/routes/optimize
```

Input:

-   origin,
-   destination/waypoints,
-   departure date/time,
-   vessel profile,
-   objective.

Internal:

``` text
Origin/Destination validation
        ↓
Environmental forecast retrieval
        ↓
Risk field retrieval
        ↓
Time-dependent environmental mesh
        ↓
Vessel performance model
        ↓
PolarRoute
        ↓
Route candidates
        ↓
Route metrics
        ↓
Risk intersection analysis
        ↓
Fuel estimate
        ↓
Uncertainty evaluation
        ↓
Final route alternatives
```

------------------------------------------------------------------------

# 60. Database Model

## Mission

``` text
mission_id
name
planning_start
planning_end
origin
destinations
vessel_id
priority_profile
created_at
```

## Vessel

``` text
vessel_id
name
length
beam
draft
speed_profile
ice_class
environmental_limits
fuel_model
```

## Location

``` text
location_id
mission_id
name
geometry
type
priority
```

## Route

``` text
route_id
mission_id
route_type
geometry
distance_nm
estimated_duration
estimated_fuel
mean_risk
p95_risk
ice_exposure
iceberg_intersection_probability
weather_exposure
```

## Environmental Layer Metadata

``` text
layer_id
variable
source
model
initialization_time
valid_time
lead_time
resolution
units
data_path
quality_status
```

## Sea-Ice Forecast Metadata

``` text
forecast_id
initialization_time
valid_time
lead_time
model
quantile
source
data_path
validation_metrics
```

## Iceberg Observation

``` text
iceberg_id
source
observation_time
geometry
size_if_available
quality
```

## Trajectory

``` text
trajectory_id
iceberg_id
initialization_time
ensemble_member
lead_time
geometry
probability_density_reference
```

------------------------------------------------------------------------

# 61. Frontend Product Architecture

The frontend should feel like a scientific mission-planning workstation,
not a generic startup dashboard.

## Core views

### 1. Mission Setup

-   Mission name
-   Date window
-   Origin
-   Destinations
-   Vessel
-   Objective priorities

### 2. Antarctic Map

Central analytical workspace.

### 3. Environmental Timeline

Shows how conditions change over time.

### 4. Location Comparison

Compares candidate operating areas.

### 5. Route Comparison

Compares candidate routes.

### 6. Prediction Inspector

Explains one forecast at a selected point.

------------------------------------------------------------------------

# 62. Main Map

Map layers:

### Geography

-   Coastline
-   Ice shelves
-   Bathymetry
-   Stations

### Sea Ice

-   Current SIC
-   Forecast SIC
-   Ice edge
-   SIC anomaly
-   Probability SIC exceeds threshold
-   Uncertainty

### Icebergs

-   Observed locations
-   Size where available
-   Predicted mean trajectories
-   50% trajectory region
-   90% trajectory region
-   Density/probability field

### Weather

-   Wind vectors
-   Wave height
-   Pressure or storm indicators

### Ocean

-   Current vectors
-   SST
-   Other relevant fields

### Decision Layer

-   Risk field
-   Candidate locations
-   Route alternatives
-   Restricted areas

------------------------------------------------------------------------

# 63. Time Slider

The time slider is one of the core product interactions.

It should support the time horizons actually supported by the data.

Conceptual controls:

``` text
Now
+1d
+3d
+7d
+14d
+30d
+60d
+90d
```

But a disabled/unavailable horizon should say:

> "No forecast of this class is available at this lead time. Showing
> seasonal probability/climatology."

Do not render a smooth animation of invented values between legitimate
forecast points.

------------------------------------------------------------------------

# 64. Location Comparison Interface

Example:

  Metric                              Bharati   Maitri   Candidate C
  --------------------------------- --------- -------- -------------
  Favorable operating probability         ---      ---           ---
  Median SIC                              ---      ---           ---
  P90 SIC                                 ---      ---           ---
  Iceberg exposure                        ---      ---           ---
  Weather exposure                        ---      ---           ---
  Accessibility confidence                ---      ---           ---
  Route distance                          ---      ---           ---
  Estimated fuel                          ---      ---           ---
  Best operating window                   ---      ---           ---

The UI should allow the user to inspect the underlying time series.

------------------------------------------------------------------------

# 65. Route Comparison Interface

Use a comparison panel rather than showing only one route.

``` text
              Safest     Fastest     Fuel Efficient     Balanced

Distance        —           —              —                —
Time            —           —              —                —
Fuel            —           —              —                —
Ice exposure    —           —              —                —
Iceberg risk    —           —              —                —
Weather         —           —              —                —
Median risk     —           —              —                —
P95 risk        —           —              —                —
Confidence      —           —              —                —
```

Also display the routes simultaneously on the map.

------------------------------------------------------------------------

# 66. "Why This Recommendation?" Interface

Every recommendation should be explainable.

Example structure:

``` text
Recommended:
Bharati-first, Balanced Route

Primary factors:
• Lower projected sea-ice exposure
• Lower iceberg-route intersection probability
• Favorable ocean-current component
• Acceptable weather exposure

Tradeoff:
• 4% longer predicted transit than the fastest alternative
• Slightly higher estimated fuel than the minimum-fuel route

Confidence:
MEDIUM

Main uncertainty:
Sea-ice forecast spread increases after the selected medium-range horizon.
```

This explanation should be generated from actual metrics, not a generic
LLM paragraph hallucinated over a map.

An LLM can later help phrase the explanation, but the quantitative facts
should come from the structured decision engine.

------------------------------------------------------------------------

# 67. Three-Month Planning Experience

The user selects:

``` text
Mission:
Antarctic Summer Expedition

Planning window:
01 Dec → 28 Feb

Objective:
Station resupply + scientific operations
```

The system provides:

### Seasonal panel

-   historical probability,
-   seasonal outlook,
-   AI sea-ice outlook,
-   confidence.

### Weekly panel

-   expected accessibility,
-   risk,
-   route feasibility.

### Location panel

-   candidate-location ranking.

### Route panel

-   route options for selected planning dates.

This makes the three-month horizon a planning product rather than a
dubious forecasting claim.

------------------------------------------------------------------------

# 68. Model Evaluation

## 68.1 Sea-Ice

Required:

-   MAE
-   RMSE
-   Anomaly correlation coefficient
-   Integrated ice-edge error
-   Brier score for probabilistic threshold events
-   Comparison against persistence
-   Comparison against climatology
-   Comparison against operational forecast

## 68.2 Iceberg Trajectory

Required:

-   Average displacement error
-   Final displacement error
-   Track overlap
-   Closest-approach error
-   Probability calibration

## 68.3 Route

Required:

-   feasibility,
-   route length,
-   time,
-   estimated fuel,
-   risk exposure,
-   robustness across environmental scenarios.

------------------------------------------------------------------------

# 69. Evaluation Philosophy

The strongest proof is not:

> "Our AI achieved 94% accuracy."

The strongest proof is:

``` text
Baseline
    ↓
AI / hybrid model
    ↓
Better forecast
    ↓
Different risk field
    ↓
Better route decision
```

A model should not be considered successful merely because a statistical
metric improved if the improvement does not affect a decision.

------------------------------------------------------------------------

# 70. Baseline Framework

Every learned component must have a baseline.

## Sea Ice

-   Persistence
-   Climatology
-   Operational forecast
-   Ice-kNN-South-style model
-   Deep model candidate

## Iceberg

-   Persistence
-   Current-only drift
-   Physics ensemble
-   Physics + ML residual

## Route

-   Great-circle / basic shortest feasible route
-   PolarRoute environmental route
-   AMIP risk-augmented PolarRoute

The comparison should establish the value added by each layer.

------------------------------------------------------------------------

# 71. Research Evidence and Case Studies

## 71.1 PolarRoute

PolarRoute provides a direct example of using environmental conditions,
vessel performance and route planning in polar waters.

It demonstrates that route optimization can be modularized around an
environmental mesh and vessel model.

Sources:

-   GitHub: https://github.com/bas-logist/PolarRoute
-   Paper: https://doi.org/10.1613/jair.1.16746

## 71.2 PolarRoute Pipeline

BAS also provides a separate pipeline for automating environmental mesh
and route-generation workflows.

Source:

https://github.com/bas-logist/PolarRoute-pipeline

This is highly relevant to the proposed architecture because it
illustrates how recurring environmental ingestion can support
operational route planning.

## 71.3 Ice-kNN-South

The Ice-kNN-South paper demonstrates a computationally lightweight
Antarctic sea-ice ML approach with skill reported up to 90 days.

Source:

https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024JH000433

Important implication:

The POC should benchmark lightweight ML rather than assuming
transformer-scale architectures are required.

## 71.4 ANTSIC-UNet

ANTSIC-UNet provides evidence that multi-variable deep learning can be
relevant to extended seasonal Antarctic SIC prediction.

Source:

https://tc.copernicus.org/articles/19/6381/2025/

Important implication:

A deeper spatial model is a legitimate research direction if the
project's own validation demonstrates value.

## 71.5 Antarctic ConvLSTM

A ConvLSTM study provides evidence for useful short/subseasonal
Antarctic SIC prediction.

Source:

https://www.sciencedirect.com/science/article/pii/S1463500324000738

## 71.6 Iceberg Physics

Wagner et al. provide analytical treatment of iceberg drift and identify
regimes where large Antarctic tabular icebergs are strongly linked to
ocean current behavior.

Source:

https://journals.ametsoc.org/view/journals/phoc/47/7/jpo-d-16-0262.1.xml

## 71.7 Operational Iceberg Observation

Copernicus Marine provides a Sentinel-1/RCM iceberg product with gridded
concentration and individual detections.

Source:

https://data.marine.copernicus.eu/product/SEAICE_ARC_SEAICE_L4_NRT_OBSERVATIONS_011_007/description

This supports the decision to use existing detection products in the
POC.

------------------------------------------------------------------------

# 72. Existing-System Landscape

The system should explicitly acknowledge that parts of the problem are
already solved elsewhere.

  -----------------------------------------------------------------------
  Capability              Existing Example        AMIP Role
  ----------------------- ----------------------- -----------------------
  Sea-ice observations    NSIDC / OSI SAF / CMEMS Integrate

  Operational weather     ECMWF                   Integrate

  Ocean forecasts         CMEMS / other systems   Integrate

  Iceberg detections      CMEMS / NIC             Integrate

  Polar route             PolarRoute              Reuse / augment
  optimization                                    

  Environmental mesh      MeshiPhi                Reuse

  Data pipeline pattern   PolarRoute-pipeline     Adapt

  Seasonal sea-ice ML     Ice-kNN-South /         Benchmark / adapt
                          ANTSIC-UNet research    

  Mission-level planning  Gap/combination         AMIP's primary
                                                  contribution
  -----------------------------------------------------------------------

This is more defensible than claiming the project invents all of these
capabilities.

------------------------------------------------------------------------

# 73. Actual Differentiation

The strongest potential differentiation is the combination:

``` text
Seasonal Antarctic intelligence
+
Probabilistic sea ice
+
Predictive iceberg risk
+
Environmental fusion
+
Mission-level location planning
+
Polar route optimization
+
Explicit uncertainty
+
NCPOR-specific workflow
```

The key product innovation is therefore not necessarily a single new
neural-network architecture.

It is the decision-support layer connecting scientific information to
mission planning.

------------------------------------------------------------------------

# 74. NCPOR-Specific Opportunity

NCPOR has an unusual advantage for eventual system development:

the organization can potentially provide domain knowledge and future
operational observations that generic global systems do not have.

Potential feedback:

``` text
AMIP prediction
      ↓
NCPOR mission
      ↓
Actual conditions
      ↓
Vessel observations
      ↓
Model validation
      ↓
Indian Antarctic operational model
```

This could eventually create a system increasingly tailored to:

-   Indian station access,
-   Indian expedition timing,
-   Indian vessel characteristics,
-   Indian operational constraints,
-   and Antarctic regions relevant to NCPOR.

This is a long-term opportunity, not a POC assumption.

------------------------------------------------------------------------

# 75. NCPOR Station Geography

Current NCPOR public sources identify:

-   Maitri as an Indian Antarctic research station in the Schirmacher
    Oasis.
-   Bharati in the Larsemann Hills region near the coast.

NCPOR also publishes station and polar observation information through
its data systems.

Sources:

https://ncpor.res.in/pages/display/376-maitri-

https://ncpor.res.in/pages/view/260/257-bharti

https://data.ncpor.res.in/

A current NCPOR expedition advertisement also describes shipboard
operations along a Cape Town--Bharati--Maitri--Cape Town transect.

Source:

https://ncpor.res.in/files/39ISEA/39-ISEA-Advt-24-01-19.pdf

The product can use these as default demonstration locations while
remaining configurable for future missions.

------------------------------------------------------------------------

# 76. Vessel Data: Important Source Discrepancy

The two architecture drafts use both **Sagar Kanya** and **Sagar Nidhi**
in different places.

This should not be silently resolved by copying one name into
production.

Current NCPOR's public page clearly identifies **ORV Sagar Kanya** and
publishes:

-   Length overall: 100.34 m
-   Maximum draft: 5.6 m
-   Cruising speed: 8--10 knots
-   Endurance: 45 days

Source:

https://ncpor.res.in/pages/view/260/257-bharti

The dedicated NCPOR ORV Sagar Kanya page is:

https://ncpor.res.in/pages/view/260/167-orv-sagar-kanya

Therefore:

> **Do not hard-code Sagar Nidhi as the POC vessel without operational
> confirmation.**

The system should instead use a configurable vessel profile.

For the demo, Sagar Kanya can be used as the currently publicly
documented NCPOR reference vessel, subject to confirmation by the
relevant operational team.

This is exactly the sort of small detail that becomes embarrassing when
someone in the judging room actually knows ships.

------------------------------------------------------------------------

# 77. Failure and Limitation Analysis

## 77.1 Satellite Gap

Cause:

-   missing observations,
-   processing delay,
-   sensor limitation.

Response:

-   fallback to previous observation,
-   alternate satellite source,
-   climatology/model,
-   confidence downgrade.

## 77.2 Cloud / Optical Data Limitation

Optical data may be unusable under cloud or illumination conditions.

Response:

-   prioritize microwave/SAR products where appropriate,
-   mark observation confidence,
-   do not interpolate blindly.

## 77.3 Iceberg Detection Error

Response:

-   retain source confidence,
-   combine multiple products,
-   avoid navigation-grade claims,
-   propagate detection uncertainty into trajectory risk.

## 77.4 Sparse Iceberg Labels

Response:

-   physics-first trajectory,
-   weak supervision for future detector,
-   historical validation.

## 77.5 Model Distribution Shift

A model trained on historical Antarctic conditions may encounter
conditions outside its training distribution.

Response:

-   confidence degradation,
-   analog fallback,
-   climatology,
-   operational forecast,
-   out-of-distribution checks in future versions.

## 77.6 Long-Horizon Forecast Uncertainty

Response:

Do not force deterministic outputs.

Show:

-   probability,
-   ensemble spread,
-   historical variability.

## 77.7 Incorrect Fuel Estimate

Response:

Label all POC fuel numbers as estimates.

Future solution:

calibrate using actual telemetry.

## 77.8 Route Appears Mathematically Optimal but Operationally Poor

Response:

Use:

-   hard constraints,
-   vessel limits,
-   safety thresholds,
-   domain rules,
-   reviewable route explanations.

------------------------------------------------------------------------

# 78. Data Quality and Provenance

Every displayed prediction should be traceable to:

-   data source,
-   model,
-   initialization time,
-   valid time,
-   lead time,
-   model version,
-   input dataset version.

For example:

``` text
SIC Prediction

Model:
AMIP-SEAICE-0.3

Initialized:
2026-09-06 00:00 UTC

Valid:
2026-10-06 00:00 UTC

Lead:
30 days

Inputs:
NSIDC AU_SI12
ERA5
CMEMS ocean
SEAS5 ensemble

Validation skill:
Stored separately by region/season
```

This is essential for scientific credibility.

------------------------------------------------------------------------

# 79. Model Selection Policy

The project should adopt a formal model-selection rule:

> **A complex model is not accepted merely because it is more advanced.
> It is accepted only if it demonstrates meaningful improvement over a
> simpler baseline on temporally held-out data and improves downstream
> decisions.**

This provides a principled way to choose between:

-   kNN,
-   U-Net,
-   ConvLSTM,
-   Transformer,
-   physics model,
-   hybrid model.

------------------------------------------------------------------------

# 80. Proposed Final Model Stack

The synthesized architecture should begin with:

## Sea Ice

### Base information

Operational forecast + observations + climatology.

### AI candidate

Ice-kNN-South-style model or lightweight multi-variable spatial ML.

### Research candidate

ANTSIC-UNet-style model.

### Selection

Empirical validation.

## Iceberg Detection

Existing Copernicus/NIC product.

## Iceberg Trajectory

Physics-based Lagrangian ensemble.

## Iceberg Future Enhancement

Physics + ML residual correction.

## Weather

ECMWF / relevant operational forecast.

## Ocean

CMEMS / appropriate ocean forecast.

## Risk

Transparent hybrid physical/statistical risk engine.

## Routing

PolarRoute + MeshiPhi.

This is the strongest combined architecture.

------------------------------------------------------------------------

# 81. Why This Architecture Is Better Than a Giant AI Model

A monolithic architecture might look like:

``` text
all datasets
    ↓
huge neural network
    ↓
recommended route
```

That creates several problems:

-   difficult scientific interpretation,
-   difficult validation,
-   difficult debugging,
-   insufficient labels for some components,
-   unclear failure handling,
-   hard-to-explain decisions,
-   unnecessarily large compute requirements.

The modular architecture instead provides:

``` text
Specialized scientific problem
        ↓
Best available physical/ML method
        ↓
Explicit uncertainty
        ↓
Structured decision layer
```

This is more appropriate for a research decision-support system.

------------------------------------------------------------------------

# 82. Product Decision Flow

The final product should support four levels of decisions.

## Level 1 --- When?

Compare potential departure/operation windows.

## Level 2 --- Where?

Compare candidate geographic locations.

## Level 3 --- How?

Compare route alternatives.

## Level 4 --- Why?

Explain the factors causing the recommendation.

This is a stronger framing than "show environmental data on a map."

------------------------------------------------------------------------

# 83. Future On-Vessel Fuel and Navigation System

The future system should evolve from:

``` text
Static vessel profile
+
environmental forecasts
```

to:

``` text
Live vessel state
+
actual measured fuel
+
environmental observations
+
forecast
```

The future fuel model becomes:

``` text
Predicted Fuel
    ↓
Actual Fuel
    ↓
Prediction Error
    ↓
Model Recalibration
```

This creates the possibility of vessel-specific performance estimation.

------------------------------------------------------------------------

# 84. Future Dynamic Routing

The future route problem becomes:

``` text
At time t:
Current vessel state
+
future environmental scenarios
+
mission objectives
↓
best route
```

At time:

``` text
t + Δt
```

recompute:

``` text
Current state
+
new observations
+
updated forecasts
+
updated iceberg trajectories
↓
new best route
```

This is fundamentally different from the static POC.

------------------------------------------------------------------------

# 85. POC Philosophy

The POC must prove the entire core pipeline, not merely demonstrate
isolated components.

It should be possible to run a complete scenario from one screen:

``` text
Choose mission period
       ↓
Choose locations
       ↓
View environmental prediction
       ↓
View sea-ice forecast
       ↓
View iceberg observations
       ↓
View iceberg trajectory probability
       ↓
View weather/ocean fields
       ↓
Generate risk field
       ↓
Generate routes
       ↓
Compare routes
       ↓
See fuel/time/risk tradeoffs
       ↓
Inspect uncertainty
       ↓
Receive recommendation
```

That is the minimum meaningful POC.

------------------------------------------------------------------------

# 86. What the POC Should Demonstrate

The POC should show **all three official capabilities**.

## Capability 1 --- Sea-Ice Forecasting

Demonstrate:

-   observed SIC,
-   historical baseline,
-   ML prediction,
-   forecast horizon,
-   spatial map,
-   uncertainty,
-   comparison against baseline.

The model can be a lightweight research model or adapted/open
implementation initially.

The important point is that the prediction must be real and evaluated.

## Capability 2 --- Iceberg Trajectory Prediction

Demonstrate:

-   observed iceberg position,
-   environmental forcing,
-   physics-based trajectory,
-   ensemble paths,
-   probability corridor,
-   route intersection analysis.

This should be real computation, not a hand-drawn simulated trajectory.

## Capability 3 --- Safe and Fuel-Efficient Navigation

Demonstrate:

-   environmental risk field,
-   route optimization,
-   multiple route objectives,
-   fuel estimate,
-   time,
-   risk,
-   uncertainty,
-   recommendation.

PolarRoute should be reused rather than a new routing engine being built
unnecessarily.

------------------------------------------------------------------------

# 87. What Can Be Open-Source / Reused in the POC

The POC is explicitly allowed to use adjacent/open-source systems.

Potential reusable components:

  Component                     Reuse
  ----------------------------- -------------------------
  Polar routing                 PolarRoute
  Environmental mesh            MeshiPhi
  Routing data pipeline ideas   PolarRoute-pipeline
  SIC data                      NSIDC
  Operational sea ice           Copernicus / OSI SAF
  Iceberg observations          Copernicus Marine / NIC
  Weather                       ECMWF products
  Ocean                         Copernicus Marine
  Scientific arrays             xarray/Zarr
  Geoprocessing                 Rasterio/GDAL/GeoPandas
  Map                           MapLibre
  Charts                        ECharts

The team's custom work should concentrate on:

-   Antarctic mission intelligence,
-   AI sea-ice prediction,
-   iceberg trajectory ensemble,
-   uncertainty,
-   risk fusion,
-   location analysis,
-   route integration,
-   and the product workflow.

------------------------------------------------------------------------

# 88. What Should Be Custom Later

Once the POC is proven, custom research can improve:

### Sea ice

-   better regional model,
-   multimodel ensembles,
-   physics-informed ML,
-   improved extreme-event prediction.

### Icebergs

-   raw Sentinel-1 detection,
-   better size estimation,
-   melt prediction,
-   sea-ice interaction,
-   ML residual correction.

### Vessel performance

-   vessel-specific resistance model,
-   actual fuel-consumption model,
-   learned speed-power curve.

### Risk

-   expert-calibrated hazard thresholds,
-   probabilistic collision risk,
-   vessel-specific risk models.

### Planning

-   learned mission success probability,
-   expedition-level scheduling optimization.

------------------------------------------------------------------------

# 89. POC Data Mode

The POC can operate on a **historical replay / frozen-date mode**.

For example:

``` text
Simulated planning date:
01 September 2026

Mission period:
01 December 2026 → 28 February 2027
```

The system uses only information that would have been available at the
chosen simulated planning date wherever forecast realism is being
demonstrated.

This prevents the demo from secretly using future observations.

A second "historical replay" can compare predictions against what
actually happened later.

That makes the demo much more scientifically credible.

------------------------------------------------------------------------

# 90. POC Should Have Two Modes

## Mode A --- Planning

Input:

-   future mission dates,
-   locations,
-   route objectives.

Output:

-   environmental outlook,
-   accessibility,
-   route options,
-   uncertainty.

## Mode B --- Historical Validation

Input:

-   historical date,
-   region,
-   known later observations.

Output:

-   predicted vs observed,
-   model error,
-   baseline comparison.

Mode B is exceptionally useful for judges because it demonstrates that
the AI component is not simply producing attractive colors on an
Antarctic map.

------------------------------------------------------------------------

# 91. Final Unified Architecture

``` text
                       ┌────────────────────┐
                       │ DATA PROVIDERS      │
                       ├────────────────────┤
                       │ NSIDC              │
                       │ CMEMS              │
                       │ ECMWF              │
                       │ OSI SAF            │
                       │ Copernicus iceberg │
                       │ NIC                │
                       │ NCPOR              │
                       │ GEBCO / SCAR       │
                       └─────────┬──────────┘
                                 │
                                 ↓
                  ┌────────────────────────────┐
                  │ DATA INGESTION & QC        │
                  │ metadata / time / CRS      │
                  └─────────────┬──────────────┘
                                ↓
                  ┌────────────────────────────┐
                  │ SPATIOTEMPORAL DATA CUBE  │
                  │ xarray / Zarr / PostGIS    │
                  └─────────────┬──────────────┘
                                │
             ┌──────────────────┼───────────────────┐
             ↓                  ↓                   ↓
   ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐
   │ SEA-ICE        │  │ ICEBERG          │  │ WEATHER/OCEAN  │
   │ AI/ML          │  │ PHYSICS          │  │ FORECASTS      │
   │                │  │ DRIFT ENSEMBLE   │  │ + optional ML  │
   └───────┬────────┘  └─────────┬────────┘  └───────┬─────────┘
           │                     │                   │
           └─────────────────────┼───────────────────┘
                                 ↓
                    ┌────────────────────────┐
                    │ UNCERTAINTY ENGINE     │
                    │ ensembles / quantiles  │
                    │ probability fields     │
                    └────────────┬───────────┘
                                 ↓
                    ┌────────────────────────┐
                    │ ENVIRONMENTAL RISK     │
                    │ hard constraints       │
                    │ soft costs             │
                    │ scenario fields        │
                    └────────────┬───────────┘
                                 ↓
                  ┌────────────────────────────┐
                  │ MISSION INTELLIGENCE      │
                  │ location analysis         │
                  │ date-window analysis      │
                  └─────────────┬──────────────┘
                                ↓
                  ┌────────────────────────────┐
                  │ POLAR ROUTE ENGINE        │
                  │ PolarRoute + MeshiPhi     │
                  └─────────────┬──────────────┘
                                ↓
                  ┌────────────────────────────┐
                  │ ROUTE COMPARISON          │
                  │ safety / fuel / time      │
                  │ risk / uncertainty        │
                  └─────────────┬──────────────┘
                                ↓
                  ┌────────────────────────────┐
                  │ FRONTEND                  │
                  │ Antarctic map             │
                  │ timeline                  │
                  │ locations                 │
                  │ routes                    │
                  │ explanations              │
                  └─────────────┬──────────────┘
                                ↓
                       MISSION PLANNER
                                ↓
                    FUTURE OPERATIONAL LOOP
```

------------------------------------------------------------------------

# 92. Final Architectural Decisions

  -------------------------------------------------------------------------
  Decision              Final Recommendation           Reason
  --------------------- ------------------------------ --------------------
  Product focus         Strategic mission planning     Matches POC scope
                        first                          and long-horizon
                                                       planning problem

  Three-month planning  Probabilistic/scenario-based   Avoid false
                                                       deterministic
                                                       precision

  Weather               External operational forecasts Rebuilding weather
                                                       models is
                                                       unnecessary

  Ocean                 External operational forecasts Use established
                                                       numerical models

  Sea ice               Hybrid baseline + ML           Strongest
                                                       demonstrated AI
                                                       opportunity

  Sea-ice model         Benchmark lightweight + deep   Avoid premature
                        models                         architecture lock-in

  Iceberg detection     Existing product in POC        Detection is not the
                                                       core bottleneck

  Iceberg trajectory    Physics ensemble               Strong scientific
                                                       foundation, sparse
                                                       labels

  Iceberg ML            Residual correction later      More defensible than
                                                       pure ML initially

  Risk                  Hybrid transparent model       Explainable and
                                                       configurable

  Routing               PolarRoute/MeshiPhi            Reuse mature
                                                       open-source
                                                       capability

  Custom router         Do not build first             Duplicates existing
                                                       work

  Fuel                  Existing route/vessel model +  No telemetry
                        planning estimate              initially

  Future fuel           ML from telemetry              Requires actual
                                                       vessel data

  Frontend              2D interactive Antarctic map   Best fit for spatial
                                                       planning

  Data architecture     Zarr + PostGIS + object        Fits scientific
                        storage                        multidimensional
                                                       data and mission
                                                       metadata

  POC                   Historical replay + planning   Demonstrates
                        scenario                       capability and
                                                       validation

  Security/enterprise   Deferred                       Outside current core
  stack                                                objective
  -------------------------------------------------------------------------

------------------------------------------------------------------------

# 93. Final Product Definition

## AMIP is:

A strategic Antarctic environmental-intelligence and mission-planning
platform that:

1.  aggregates Antarctic environmental datasets;
2.  uses AI/ML where it adds measurable predictive value;
3.  uses physics-based models where physical knowledge is stronger;
4.  represents uncertainty explicitly;
5.  converts predictions into environmental risk;
6.  evaluates candidate locations and mission windows;
7.  integrates PolarRoute for route optimization;
8.  compares safety, time and fuel;
9.  explains the reasons behind route and location recommendations;
10. provides a clear path toward future live, vessel-integrated
    operations.

------------------------------------------------------------------------

# 94. What This System Is Not

It is not initially:

-   an autonomous ship controller,
-   an autopilot,
-   a replacement for maritime navigation systems,
-   a weather model,
-   a universal Antarctic digital twin,
-   a guaranteed iceberg-collision prevention system,
-   a deterministic three-month forecasting oracle,
-   a fully autonomous route decision-maker.

Those distinctions are important.

The platform is a decision-support system.

------------------------------------------------------------------------

# 95. Future Expansion Architecture

## Stage 1

``` text
Historical + current environmental data
→ prediction
→ risk
→ route
→ planning
```

## Stage 2

``` text
Higher-frequency forecast updates
→ better prediction
→ operational route planning
```

## Stage 3

``` text
Live vessel
+
environment
+
fuel
→ dynamic risk
→ dynamic routing
```

## Stage 4

``` text
Actual voyage data
→ learned vessel model
→ improved environmental models
→ better route decisions
```

------------------------------------------------------------------------

# 96. Research Roadmap

## Research Track A --- Sea Ice

Questions:

-   Does Ice-kNN-South outperform our selected baselines in the target
    region?
-   Does adding CMEMS/ERA5/seasonal information improve it?
-   Where does a U-Net outperform kNN?
-   How does skill vary by region and season?
-   How does performance behave during anomalous Antarctic sea-ice
    years?

## Research Track B --- Icebergs

Questions:

-   How accurate is the physics-only trajectory model?
-   How much does sea-ice interaction affect the prediction?
-   How much residual error remains?
-   Is enough historical data available to justify ML correction?

## Research Track C --- Route

Questions:

-   Does adding AMIP's predicted risk materially alter route choice?
-   Are route recommendations robust to uncertainty?
-   How much fuel/time tradeoff exists between candidate paths?

## Research Track D --- Mission Planning

Questions:

-   Does the system actually change planning decisions?
-   Which outputs are most useful to planners?
-   What uncertainty representation is understandable?

------------------------------------------------------------------------

# 97. Recommended Development Sequence

The development should follow the dependency graph, not the glamour
graph.

``` text
1. Acquire/understand real datasets
            ↓
2. Build unified historical slice
            ↓
3. Build environmental map
            ↓
4. Establish sea-ice baselines
            ↓
5. Implement sea-ice AI candidate
            ↓
6. Implement iceberg observation ingestion
            ↓
7. Implement iceberg physics ensemble
            ↓
8. Build risk engine
            ↓
9. Integrate PolarRoute
            ↓
10. Build route comparison
            ↓
11. Build mission/location analysis
            ↓
12. Add uncertainty visualization
            ↓
13. Historical replay validation
            ↓
14. Final end-to-end demonstration
```

Do not spend the majority of the project training a sophisticated
sea-ice model before a planner can actually see the output on a map and
use it to change a route.

------------------------------------------------------------------------

# 98. Final POC Definition

The POC should be considered successful if one evaluator can complete
the following sequence without leaving the platform:

> **Select an Antarctic mission window → select candidate locations →
> inspect current and future environmental conditions → see an AI/ML
> sea-ice prediction → see its uncertainty → see observed icebergs → see
> predicted iceberg trajectories → see integrated environmental risk →
> generate multiple routes → compare safety/fuel/time → inspect why a
> route is preferred → change the date or destination → observe the
> recommendation change.**

That is the core vertical slice.

The POC does not need to prove that every component is production-grade.

It does need to prove that the **entire decision chain works**.

A strong implementation can therefore reuse:

-   open-source route planning,
-   existing satellite products,
-   operational weather/ocean forecasts,
-   existing iceberg detection,
-   published ML approaches,

while investing custom engineering and research effort where the project
actually creates differentiated value:

> **Antarctic environmental prediction + uncertainty + mission-level
> decision intelligence + route integration.**

------------------------------------------------------------------------

# 99. POC Capability Checklist

The final POC should visibly demonstrate all of the following.

### Environmental Intelligence

-   [ ] Antarctic map
-   [ ] Sea-ice observation
-   [ ] Sea-ice forecast
-   [ ] Sea-ice uncertainty
-   [ ] Weather forecast
-   [ ] Ocean current information
-   [ ] Wave information
-   [ ] Iceberg observations
-   [ ] Iceberg trajectory ensemble

### AI/ML

-   [ ] Real sea-ice prediction model
-   [ ] Baseline comparison
-   [ ] Forecast validation
-   [ ] Probabilistic output
-   [ ] Model uncertainty

### Physics

-   [ ] Iceberg drift model
-   [ ] Ensemble trajectory
-   [ ] Environmental forcing

### Decision Support

-   [ ] Risk map
-   [ ] Candidate location comparison
-   [ ] Date-window analysis
-   [ ] Route alternatives
-   [ ] Safety/time/fuel comparison
-   [ ] Recommendation explanation
-   [ ] Uncertainty inspection

### Routing

-   [ ] PolarRoute/MeshiPhi integration
-   [ ] Environmental constraints
-   [ ] Vessel profile
-   [ ] Multiple route objectives

### Validation

-   [ ] Historical replay
-   [ ] Prediction vs observation
-   [ ] Baseline vs AI
-   [ ] Route comparison

------------------------------------------------------------------------

# 100. Bottom-Line Architecture

The final recommendation is:

``` text
                NCPOR MISSION
                     │
                     ▼
          ┌────────────────────┐
          │ Mission Planner UI │
          └──────────┬─────────┘
                     │
                     ▼
          ┌────────────────────┐
          │ Scenario Engine    │
          │ Date / Location    │
          │ Vessel / Objective │
          └──────────┬─────────┘
                     │
                     ▼
       ┌─────────────────────────────┐
       │ Antarctic Environmental Cube │
       │ NSIDC + CMEMS + ECMWF +     │
       │ Iceberg + NCPOR + Geography │
       └──────────────┬──────────────┘
                      │
       ┌──────────────┼───────────────┐
       ▼              ▼               ▼
┌────────────┐ ┌──────────────┐ ┌─────────────┐
│ Sea-Ice AI │ │ Iceberg Drift│ │ Weather/    │
│ Forecast   │ │ Physics      │ │ Ocean       │
│            │ │ Ensemble     │ │ Forecasts   │
└─────┬──────┘ └──────┬───────┘ └──────┬──────┘
      │               │                │
      └───────────────┼────────────────┘
                      ▼
             ┌─────────────────┐
             │ Uncertainty     │
             │ + Risk Engine   │
             └────────┬────────┘
                      ▼
          ┌────────────────────────┐
          │ Location Intelligence │
          └───────────┬────────────┘
                      ▼
          ┌────────────────────────┐
          │ PolarRoute + MeshiPhi │
          └───────────┬────────────┘
                      ▼
          ┌────────────────────────┐
          │ Route Alternatives     │
          │ Safe / Fast / Fuel /   │
          │ Balanced               │
          └───────────┬────────────┘
                      ▼
             ┌────────────────┐
             │ Decision View  │
             │ Why + Tradeoff │
             │ + Uncertainty  │
             └────────────────┘
```

This architecture combines the strongest ideas from both source designs
while preserving a disciplined boundary between what should be built,
what should be reused, and what should remain future research.

The most important design principle is:

> **Use open-source and established scientific systems for what they
> already solve well. Build custom intelligence where the existing
> systems stop: long-horizon Antarctic prediction, uncertainty-aware
> environmental fusion, iceberg trajectory risk, mission-level
> geographic analysis, and the translation of those predictions into a
> coherent planning decision.**

------------------------------------------------------------------------

# 101. Primary References and Implementation Links

## Problem / NCPOR

NCPOR official site:

https://ncpor.res.in/

NCPOR Bharati:

https://ncpor.res.in/pages/view/260/257-bharti

NCPOR Maitri:

https://ncpor.res.in/pages/display/376-maitri-

NCPOR data:

https://data.ncpor.res.in/

NCPOR Polar Data Centre:

https://npdc.ncpor.res.in/

## Sea Ice

NSIDC AU_SI12:

https://nsidc.org/data/au_si12/versions/1

Copernicus Marine:

https://data.marine.copernicus.eu/

EUMETSAT OSI SAF:

https://osi-saf.eumetsat.int/

Ice-kNN-South:

https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024JH000433

ANTSIC-UNet:

https://tc.copernicus.org/articles/19/6381/2025/

Antarctic ConvLSTM:

https://www.sciencedirect.com/science/article/pii/S1463500324000738

## Icebergs

Copernicus Marine iceberg product:

https://data.marine.copernicus.eu/product/SEAICE_ARC_SEAICE_L4_NRT_OBSERVATIONS_011_007/description

U.S. National Ice Center:

https://www.natice.noaa.gov/

Wagner et al. iceberg drift model:

https://journals.ametsoc.org/view/journals/phoc/47/7/jpo-d-16-0262.1.xml

## Weather / Ocean

ECMWF seasonal forecasting:

https://www.ecmwf.int/en/forecasts/documentation-and-support/seasonal

Copernicus Climate Data Store:

https://cds.climate.copernicus.eu/

HYCOM:

https://www.hycom.org/

GEBCO:

https://www.gebco.net/

## Open-Source Routing

PolarRoute:

https://github.com/bas-logist/PolarRoute

PolarRoute-server:

https://github.com/bas-logist/PolarRoute-server

PolarRoute-pipeline:

https://github.com/bas-logist/PolarRoute-pipeline

PolarRoute paper:

https://doi.org/10.1613/jair.1.16746

------------------------------------------------------------------------

# 102. Source and Verification Notes

This unified architecture was synthesized from the two provided
architecture drafts, with their technical detail retained where useful
and their conflicting assumptions explicitly reviewed.

The supplied drafts independently converged on:

-   strategic mission planning as the appropriate initial product,
-   uncertainty-aware long-horizon planning,
-   hybrid physics + ML,
-   the value of existing PolarRoute infrastructure,
-   an interactive Antarctic map,
-   candidate-location analysis,
-   route comparison,
-   future on-vessel extension.

The current official/web checks used for this synthesis additionally
confirm:

-   NSIDC's current AU_SI12 dataset description and coverage,
-   ECMWF seasonal-forecast capability,
-   current Copernicus Marine iceberg-product availability,
-   current BAS PolarRoute and associated server/pipeline repositories,
-   current NCPOR public station information,
-   current NCPOR public ORV Sagar Kanya specifications.

Where a source-draft claim could not be established as current fact, it
has been reframed as a hypothesis, implementation assumption, or item
requiring NCPOR/domain validation.

------------------------------------------------------------------------

# 103. Final Recommendation

The system should be built as an **AI-enhanced Antarctic Mission
Intelligence Platform**, not as an isolated sea-ice model and not as
another route planner.

Its core computational contribution is:

``` text
OBSERVATIONS
     +
FORECASTS
     +
PHYSICS
     +
AI/ML
     ↓
PROBABILISTIC ENVIRONMENTAL STATE
     ↓
RISK
     ↓
LOCATION + ROUTE OPTIONS
     ↓
SAFETY / FUEL / TIME TRADEOFF
     ↓
MISSION DECISION
```

The POC should prove every link in that chain using real datasets
wherever practical, existing open-source systems where appropriate, and
clearly identified simulation only where necessary.

The future system can then replace static assumptions with:

``` text
LIVE VESSEL
+
LIVE ENVIRONMENT
+
ACTUAL FUEL
+
UPDATED MODELS
     ↓
DYNAMIC DECISION SUPPORT
```

## That is the coherent path from a hackathon POC to a credible research-grade NCPOR platform.

------------------------------------------------------------------------

# POC Scope Boundary

The POC ends at the validated strategic-planning workflow:

``` text
Environmental Data
      ↓
Forecast / Simulation
      ↓
Uncertainty
      ↓
Risk
      ↓
PolarRoute
      ↓
Candidate Routes
      ↓
Mission Comparison
      ↓
Human Decision Support
```

Live vessel telemetry, autonomous onboard navigation, continuous dynamic
replanning, and the large multimodal Antarctic Environmental Foundation
Model are future-product capabilities. Their interfaces may be
anticipated in the POC architecture, but they are not dependencies for
POC completion.
