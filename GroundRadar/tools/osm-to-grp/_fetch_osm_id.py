"""Fetch a specific OSM element by id (way or relation) via Overpass, including
all member ways for relations (so we can see inner rings of a multipolygon)."""
from __future__ import annotations
import json
import sys
import time
import urllib.error
import urllib.request

OVERPASS_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
]

osm_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1016444425

# Query both as way and as relation; relations get their members recursively.
query = f"""
[out:json][timeout:60];
(
  way({osm_id});
  relation({osm_id});
);
out body;
>;
out geom;
""".strip()

data = query.encode("utf-8")
last_err = None
for url in OVERPASS_ENDPOINTS:
    print(f"POST {url}", file=sys.stderr)
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "text/plain; charset=utf-8",
                 "User-Agent": "CZQM-vACC-GroundRadar-OSM/0.1 (joel@joelmorin.com)"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
        print(f"  {resp.status} in {time.time()-t0:.1f}s ({len(raw)} bytes)", file=sys.stderr)
        payload = json.loads(raw)
        break
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        print(f"  failed: {e}", file=sys.stderr)
        last_err = e
        time.sleep(2)
else:
    raise RuntimeError(f"All Overpass endpoints failed: {last_err}")

print(json.dumps(payload, indent=2))
