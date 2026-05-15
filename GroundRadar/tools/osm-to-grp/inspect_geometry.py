"""
Second-pass inspection — for each aeroway type, check whether OSM ways are:
  - closed (polygon-like: first vertex == last vertex), or
  - open (centerline-like: distinct endpoints).

This determines how much OSM coverage maps directly to LPPT's polygon-fill approach
vs how much we'd need to buffer centerlines into polygons ourselves.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    data_path = Path(__file__).parent / "data" / "cyhz_raw.json"
    payload = json.loads(data_path.read_text(encoding="utf-8"))

    by_aeroway: defaultdict[str, dict] = defaultdict(lambda: {"closed": [], "open": []})

    for el in payload.get("elements", []):
        if el.get("type") != "way":
            continue
        tags = el.get("tags", {}) or {}
        aw = tags.get("aeroway", "?")
        geom = el.get("geometry") or []
        if not geom:
            continue
        first, last = geom[0], geom[-1]
        is_closed = first == last
        entry = {
            "id": el["id"],
            "ref": tags.get("ref") or tags.get("name") or "",
            "vertices": len(geom),
            "surface": tags.get("surface", ""),
            "width": tags.get("width", ""),
        }
        bucket = "closed" if is_closed else "open"
        by_aeroway[aw][bucket].append(entry)

    print(f"{'aeroway':25s} closed   open    total")
    print(f"{'-'*25} {'-'*7} {'-'*7} {'-'*7}")
    for aw in sorted(by_aeroway):
        c, o = by_aeroway[aw]["closed"], by_aeroway[aw]["open"]
        print(f"{aw:25s} {len(c):7d} {len(o):7d} {len(c)+len(o):7d}")

    print("\n--- runways (detail) ---")
    for entry in by_aeroway["runway"]["closed"] + by_aeroway["runway"]["open"]:
        kind = "polygon" if entry in by_aeroway["runway"]["closed"] else "line"
        print(f"  id={entry['id']:<12} ref={entry['ref']!r:>10}  {kind:7s}  v={entry['vertices']:3d}  surface={entry['surface']!r}  width={entry['width']!r}")

    print("\n--- taxiways (detail) ---")
    for entry in by_aeroway["taxiway"]["closed"] + by_aeroway["taxiway"]["open"]:
        kind = "polygon" if entry in by_aeroway["taxiway"]["closed"] else "line"
        print(f"  id={entry['id']:<12} ref={entry['ref']!r:>6}  {kind:7s}  v={entry['vertices']:3d}  surface={entry['surface']!r}  width={entry['width']!r}")

    print("\n--- aprons (detail) ---")
    for entry in by_aeroway["apron"]["closed"] + by_aeroway["apron"]["open"]:
        kind = "polygon" if entry in by_aeroway["apron"]["closed"] else "line"
        print(f"  id={entry['id']:<12} ref={entry['ref']!r:>20}  {kind:7s}  v={entry['vertices']:3d}")

    print("\n--- helipad/heliport (detail) ---")
    for aw in ("heliport", "helipad"):
        for entry in by_aeroway[aw]["closed"] + by_aeroway[aw]["open"]:
            kind = "polygon" if entry in by_aeroway[aw]["closed"] else "line"
            print(f"  {aw:10s} id={entry['id']:<12} ref={entry['ref']!r:>20}  {kind:7s}  v={entry['vertices']:3d}")

    print("\n--- holding_position (detail, all) ---")
    for entry in by_aeroway["holding_position"]["closed"] + by_aeroway["holding_position"]["open"]:
        kind = "polygon" if entry in by_aeroway["holding_position"]["closed"] else "line"
        print(f"  id={entry['id']:<12} ref={entry['ref']!r:>15}  {kind:7s}  v={entry['vertices']:3d}")


if __name__ == "__main__":
    main()
