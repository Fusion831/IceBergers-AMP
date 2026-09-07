import os
import json

# Let's inspect display_aggregate_h3.json first to verify fields
with open("frontend/src/data/display_aggregate_h3.json", "r", encoding="utf-8") as f:
    disp = json.load(f)

print("Display aggregate features count:", len(disp["features"]))
feat0 = disp["features"][0]
print("Sample feature properties:", json.dumps(feat0["properties"], indent=2))
