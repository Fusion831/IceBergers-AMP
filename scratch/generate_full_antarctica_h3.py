import json
import h3

# Generate H3 resolution 3 cells covering the circum-Antarctic Southern Ocean (lat -78 to -30, lon -180 to 180)
cells = set()
for lat in range(-78, -30, 2):
    for lon in range(-180, 180, 2):
        cell = h3.latlng_to_cell(lat, lon, 3)
        cells.add(cell)

print(f"Generated {len(cells)} unique Res-3 cells around entire Antarctica continent.")

features = []
for cell in sorted(cells):
    boundary = h3.cell_to_boundary(cell)
    # Convert (lat, lng) to (lng, lat) for GeoJSON
    coords = [[round(lng, 5), round(lat, 5)] for lat, lng in boundary]
    coords.append(coords[0]) # close loop
    
    center_lat, center_lon = h3.cell_to_latlng(cell)
    features.append({
        "type": "Feature",
        "id": cell,
        "properties": {
            "id": cell,
            "h3_index": cell,
            "res": 3,
            "lat": round(center_lat, 4),
            "lon": round(center_lon, 4)
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [coords]
        }
    })

geojson = {
    "type": "FeatureCollection",
    "features": features
}

output_path = "frontend/src/data/antarctica_full_h3.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(geojson, f)

print(f"Saved full circum-Antarctic H3 grid GeoJSON to {output_path} ({len(features)} cells)")
