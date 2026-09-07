import urllib.request
import re

urls = [
    "https://www.scp.byu.edu/iceberg/",
    "https://www.scp.byu.edu/iceberg/database1.html"
]

for url in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            # Extract plain text
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text)
            print(f"=== {url} ===")
            print(text[:1500])
    except Exception as e:
        print(f"Error {url}: {e}")
