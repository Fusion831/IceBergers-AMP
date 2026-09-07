import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base = "https://usicecenter.gov"
pids = [134, 135, 228]

for pid in pids:
    url = f"{base}/File/DownloadCurrent?pId={pid}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            cd = resp.headers.get("Content-Disposition", "")
            ct = resp.headers.get("Content-Type", "")
            cl = resp.headers.get("Content-Length", "")
            print(f"pId={pid}: url={url}")
            print(f"  Content-Disposition: {cd}")
            print(f"  Content-Type: {ct}")
            print(f"  Content-Length: {cl}")
            content = resp.read(2048)
            print(f"  Preview (first 200 chars): {content[:200]}")
    except Exception as e:
        print(f"pId={pid} Error: {e}")
