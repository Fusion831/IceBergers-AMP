import urllib.request
import re
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    'https://usicecenter.gov/Products/AntarcIcebergs',
    'https://usicecenter.gov/Catalog/AntarcIceberg',
    'https://www.scp.byu.edu/current_icebergs.html'
]

for url in urls:
    print('========================================')
    print('Checking:', url)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            print(f"Fetched {len(html)} bytes")
            # Look for download links
            links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html, re.I)
            data_links = [l for l in set(links) if any(ext in l.lower() for ext in ['.csv', '.kml', '.kmz', '.shp', '.zip', '.json', '.geojson', '.txt', 'download', 'table', 'data'])]
            print("Data links:")
            for dl in sorted(data_links):
                print("  ", dl)
    except Exception as e:
        print("Error:", e)
