import json

path = "frontend/src/data/canonical_routes.json"
with open(path, "r", encoding="utf-8") as f:
    d = json.load(f)

print(f"Routes in frontend/src/data/canonical_routes.json: {list(d.keys())}")
for k, v in d.items():
    wps = v.get("waypoints", [])
    print(f"\n--- {k}: {v.get('name')} ({len(wps)} waypoints) ---")
    print(f"Start: {wps[0] if wps else 'none'}")
    print(f"Mid:   {wps[len(wps)//2] if wps else 'none'}")
    print(f"End:   {wps[-1] if wps else 'none'}")
