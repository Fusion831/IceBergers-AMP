import urllib.request
import json

url = "http://127.0.0.1:8000/api/v1/routes/plan-voyage"
payload = {
    "origin_station_id": "cape-town",
    "destination_station_id": "bharati",
    "vessel_id": "sagar-kanya",
    "objectives": ["FASTEST", "SAFEST", "SHORTEST", "FUEL_EFFICIENT", "BALANCED"]
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(f"Origin: {data['origin']}")
        print(f"Destination: {data['destination']}")
        print(f"Routes returned: {len(data['routes'])}")
        for r in data["routes"]:
            wps = r.get("waypoints", [])
            print(f"\nObjective: {r['objective']}, Waypoints: {len(wps)}")
            pts = [wp.get("point") or wp.get("position") for wp in wps]
            coords = [[p["longitude"], p["latitude"]] for p in pts if p]
            print(f"  First 3 coords: {coords[:3]}")
            print(f"  Middle coord: {coords[len(coords)//2] if coords else None}")
            print(f"  Last 3 coords: {coords[-3:]}")
            print(f"  Metrics: {r.get('metrics')}")
except Exception as e:
    print(f"Error: {e}")
