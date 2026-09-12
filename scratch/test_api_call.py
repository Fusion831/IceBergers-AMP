import urllib.request
import json

for orig, dest in [('mcmurdo', 'punta-arenas'), ('cape-town', 'bharati'), ('hobart', 'mcmurdo')]:
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/v1/routes/plan-voyage',
        data=json.dumps({
            'origin_station_id': orig,
            'destination_station_id': dest,
            'objectives': ['FASTEST', 'SHORTEST', 'SAFEST', 'FUEL_EFFICIENT', 'BALANCED']
        }).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"\n=== Voyage: {orig} -> {dest} ===")
        for r in data.get('routes', []):
            obj = r['objective']
            m = r['metrics']
            wps = r['waypoints']
            fuel = m.get('estimated_fuel_mt') or m.get('estimated_fuel_tonnes')
            print(f"{obj:15s}: Dist={m['distance_nm']} NM, Days={m['duration_days']}d, Fuel={fuel} MT, Wps={len(wps)}")
