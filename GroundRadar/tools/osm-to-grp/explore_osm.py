"""
Exploration script — pull CYHZ aeroway features from OpenStreetMap via Overpass API,
save the raw JSON, and print a summary breakdown.

Not yet a real tool. Goal: validate that OSM coverage of CYHZ is good enough to base
the GRP rebuild on, and decide whether to build a proper reusable extractor.

Usage:
    python explore_osm.py
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

# CYHZ bounding box — slightly wider than spec, matching the existing CYHZ-TWR_GRP.asr WINDOWAREA
LAT_MIN, LAT_MAX = 44.846, 44.906
LON_MIN, LON_MAX = -63.617, -63.458

OVERPASS_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

QUERY = f"""
[out:json][timeout:90];
(
  way["aeroway"]({LAT_MIN},{LON_MIN},{LAT_MAX},{LON_MAX});
  node["aeroway"]({LAT_MIN},{LON_MIN},{LAT_MAX},{LON_MAX});
  relation["aeroway"]({LAT_MIN},{LON_MIN},{LAT_MAX},{LON_MAX});
);
out geom;
""".strip()


def fetch_overpass() -> dict:
    data = QUERY.encode("utf-8")
    last_err: Exception | None = None
    for url in OVERPASS_ENDPOINTS:
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "text/plain; charset=utf-8",
                "User-Agent": "CZQM-vACC-GroundRadar-OSM-Explorer/0.1 (joel@joelmorin.com)",
            },
        )
        print(f"POST {url} ({len(data)} bytes)")
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read()
            print(f"Response: {resp.status} in {time.time() - t0:.1f}s, {len(raw)} bytes")
            return json.loads(raw.decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            print(f"  failed: {e}")
            last_err = e
            time.sleep(2)
    raise RuntimeError(f"All Overpass endpoints failed; last error: {last_err}")


def summarize(payload: dict) -> None:
    elements = payload.get("elements", [])
    print(f"\nTotal elements: {len(elements)}")

    by_kind: Counter = Counter()
    by_aeroway: Counter = Counter()
    nodes_with_aeroway: list[dict] = []
    ways_by_aeroway: defaultdict[str, list[dict]] = defaultdict(list)
    relations: list[dict] = []
    interesting_tag_keys: Counter = Counter()

    for el in elements:
        kind = el.get("type", "?")
        by_kind[kind] += 1
        tags = el.get("tags", {}) or {}
        aw = tags.get("aeroway", "?")
        by_aeroway[aw] += 1
        for k in tags:
            interesting_tag_keys[k] += 1
        if kind == "node":
            nodes_with_aeroway.append(el)
        elif kind == "way":
            ways_by_aeroway[aw].append(el)
        elif kind == "relation":
            relations.append(el)

    print("\nBy element kind:")
    for kind, n in by_kind.most_common():
        print(f"  {kind:10s} {n}")

    print("\nBy aeroway tag:")
    for aw, n in by_aeroway.most_common():
        print(f"  {aw:25s} {n}")

    print("\nTop tag keys present (across all elements):")
    for k, n in interesting_tag_keys.most_common(25):
        print(f"  {k:25s} {n}")

    # Show a handful of representative ways
    print("\nRepresentative ways (first of each aeroway tag, geometry vertex count):")
    for aw, ws in sorted(ways_by_aeroway.items()):
        w = ws[0]
        geom = w.get("geometry") or []
        ref = w.get("tags", {}).get("ref") or w.get("tags", {}).get("name") or ""
        print(f"  {aw:20s} id={w['id']:<12} vertices={len(geom):<4} ref/name={ref!r}")

    # Show all nodes with aeroway (likely holding_position / parking_position / windsock / etc.)
    print(f"\nNodes ({len(nodes_with_aeroway)} total) — first 30:")
    for n in nodes_with_aeroway[:30]:
        tags = n.get("tags", {}) or {}
        aw = tags.get("aeroway", "?")
        ref = tags.get("ref") or tags.get("name") or ""
        print(f"  node id={n['id']:<12} aeroway={aw:20s} ref/name={ref!r}")

    if relations:
        print(f"\nRelations ({len(relations)} total):")
        for r in relations[:20]:
            tags = r.get("tags", {}) or {}
            print(f"  rel id={r['id']:<12} tags={tags}")


def main() -> int:
    out_dir = Path(__file__).parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "cyhz_raw.json"

    try:
        payload = fetch_overpass()
    except urllib.error.HTTPError as e:
        print(f"HTTP error: {e.code} {e.reason}", file=sys.stderr)
        print(e.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"URL error: {e}", file=sys.stderr)
        return 1

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved raw payload to {out_path}")

    summarize(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
