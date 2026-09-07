import sys
sys.path.extend([
    'packages/core/src', 'packages/domain/src', 'packages/data_access/src',
    'packages/models/src', 'packages/risk_engine/src', '.'
])

import json
import math
import h3
from datetime import datetime, timezone
from data_access.environment_provider import default_environment_provider
from domain.coordinates import GeoPoint

# Load corridor_geojson.json
with open("frontend/src/data/corridor_geojson.json", "r", encoding="utf-8") as f:
    corridor_data = json.load(f)

# Load environment_by_horizon.json
with open("frontend/src/data/environment_by_horizon.json", "r", encoding="utf-8") as f:
    env_data = json.load(f)

# Load risk_by_horizon.json
with open("frontend/src/data/risk_by_horizon.json", "r", encoding="utf-8") as f:
    risk_data = json.load(f)

now_env = env_data.get("Now", {})
now_risk = risk_data.get("Now", {})

print(f"Corridor features: {len(corridor_data['features'])}")
print(f"Now environment entries: {len(now_env)}")
print(f"Now risk entries: {len(now_risk)}")

# Check sample values
sample_id = corridor_data['features'][0]['properties']['cell_id']
print(f"Sample cell {sample_id}:")
print("  env:", now_env.get(sample_id))
print("  risk:", now_risk.get(sample_id))
