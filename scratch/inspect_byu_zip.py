import urllib.request
import zipfile
import io
from pathlib import Path

url = "https://www.scp.byu.edu/iceberg/consolidated_database_v8.0.zip"
print("Downloading BYU zip...")
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = resp.read()
    print(f"Downloaded {len(data)} bytes")

z = zipfile.ZipFile(io.BytesIO(data))
print("Files in zip:")
file_list = z.namelist()
for name in file_list[:25]:
    info = z.getinfo(name)
    print(f"  {name} ({info.file_size} bytes)")
if len(file_list) > 25:
    print(f"  ... and {len(file_list) - 25} more files")

# Inspect a text or csv file inside
for name in file_list:
    if name.endswith(('.csv', '.txt', '.dat')):
        print(f"\n--- Preview of {name} ---")
        content = z.read(name).decode('utf-8', errors='ignore')
        lines = content.splitlines()[:15]
        for l in lines:
            print(l)
        break
