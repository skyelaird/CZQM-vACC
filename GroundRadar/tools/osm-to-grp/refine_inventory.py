"""
Refined inventory pass — group OSM ways by their ref tag, deduplicate, and
compare against the authoritative list of CYHZ features from the existing
CYHZ-TWR_GRP.asr (parking labels + taxiway labels).

Goal: produce a more honest "what does OSM actually cover" picture than the
raw element counts, which include fragmentation (one taxiway letter split
across multiple ways at intersections) and stray tags.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(r"D:\GitHub\CZQM-vACC")
DATA = REPO / "GroundRadar" / "tools" / "osm-to-grp" / "data" / "cyhz_raw.json"
ASR = REPO / "GroundRadar" / "CYHZ" / "CYHZ-TWR_GRP.asr"


def load_osm() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def asr_labels() -> tuple[set[str], set[str]]:
    """Pull authoritative parking and taxiway labels from the existing ASR."""
    text = ASR.read_text(encoding="utf-8")
    parking = set()
    taxiway = set()
    for line in text.splitlines():
        m = re.match(r"Free Text:CYHZ CYHZ PARKING\\([^:]+):freetext", line)
        if m:
            label = m.group(1).strip()
            # strip annotation like "B    [9100]"
            label = re.split(r"\s+", label)[0]
            parking.add(label)
            continue
        m = re.match(r"Free Text:CYHZ CYHZ TAXIWAY\\([^:]+):freetext", line)
        if m:
            label = m.group(1).strip()
            label = re.split(r"\s+", label)[0]
            taxiway.add(label)
    return parking, taxiway


def main() -> None:
    payload = load_osm()
    elements = payload.get("elements", [])

    # Group ways by (aeroway, ref)
    ways_by_aw_ref: defaultdict[tuple[str, str], list[dict]] = defaultdict(list)
    nodes_by_aw_ref: defaultdict[tuple[str, str], list[dict]] = defaultdict(list)
    rel_by_id: dict[int, dict] = {}

    for el in elements:
        tags = el.get("tags", {}) or {}
        aw = tags.get("aeroway", "?")
        ref = (tags.get("ref") or "").strip()
        if el["type"] == "way":
            ways_by_aw_ref[(aw, ref)].append(el)
        elif el["type"] == "node":
            nodes_by_aw_ref[(aw, ref)].append(el)
        elif el["type"] == "relation":
            rel_by_id[el["id"]] = el

    # -- Runways
    print("=== RUNWAYS ===")
    rw_groups: defaultdict[str, list[dict]] = defaultdict(list)
    for (aw, ref), ws in ways_by_aw_ref.items():
        if aw == "runway":
            rw_groups[ref or "(no-ref)"].extend(ws)
    for ref, ws in sorted(rw_groups.items()):
        verts = [len(w.get("geometry") or []) for w in ws]
        ids = [w["id"] for w in ws]
        print(f"  ref={ref!r:10}  ways={len(ws)}  vertex-counts={verts}  ids={ids}")
        for w in ws:
            tags = w.get("tags", {}) or {}
            print(f"     id={w['id']}  surface={tags.get('surface')!r}  width={tags.get('width')!r}  length={tags.get('length')!r}")
    print(f"  ==> {len({k for k in rw_groups})} distinct runway ref(s) in OSM")

    # -- Taxiways
    print("\n=== TAXIWAYS ===")
    tw_groups: defaultdict[str, list[dict]] = defaultdict(list)
    for (aw, ref), ws in ways_by_aw_ref.items():
        if aw == "taxiway":
            tw_groups[ref or "(no-ref)"].extend(ws)
    named, unnamed = 0, 0
    for ref, ws in sorted(tw_groups.items()):
        if ref == "(no-ref)":
            unnamed = len(ws)
            continue
        named += 1
        verts_total = sum(len(w.get("geometry") or []) for w in ws)
        print(f"  ref={ref!r:6}  ways={len(ws)}  total-vertices={verts_total}")
    print(f"  ==> {named} distinct named taxiways + {unnamed} unnamed connector ways")

    # -- Aprons
    print("\n=== APRONS ===")
    ap_ways = [w for (aw, _), ws in ways_by_aw_ref.items() if aw == "apron" for w in ws]
    print(f"  {len(ap_ways)} apron polygons (mostly unnamed)")
    for w in ap_ways:
        tags = w.get("tags", {}) or {}
        ref = tags.get("ref") or tags.get("name") or ""
        n = tags.get("operator") or ""
        print(f"  id={w['id']:<12} vertices={len(w.get('geometry') or [])}  ref/name={ref!r}  operator={n!r}")

    # -- Parking positions (ways) vs gate nodes vs ASR-authoritative parking list
    print("\n=== PARKING / GATES vs ASR ===")
    asr_parking, asr_taxiways = asr_labels()
    print(f"  Authoritative (existing ASR FREETEXT): {len(asr_parking)} parking labels, {len(asr_taxiways)} taxiway labels")
    print(f"     ASR parking: {sorted(asr_parking, key=lambda s: (len(s), s))}")
    print(f"     ASR taxiway: {sorted(asr_taxiways)}")

    pp_ways = [w for (aw, _), ws in ways_by_aw_ref.items() if aw == "parking_position" for w in ws]
    pp_refs = {(w.get("tags", {}) or {}).get("ref", "") for w in pp_ways}
    pp_refs.discard("")
    gate_nodes = [n for (aw, _), ns in nodes_by_aw_ref.items() if aw == "gate" for n in ns]
    gate_refs = {(n.get("tags", {}) or {}).get("ref", "") for n in gate_nodes}
    gate_refs.discard("")

    osm_all = pp_refs | gate_refs
    print(f"  OSM parking_position ways: {len(pp_ways)} ways, {len(pp_refs)} distinct refs")
    print(f"  OSM gate nodes:           {len(gate_nodes)} nodes, {len(gate_refs)} distinct refs")
    print(f"  OSM union of parking refs: {len(osm_all)}")

    missing_in_osm = sorted(asr_parking - osm_all, key=lambda s: (len(s), s))
    missing_in_asr = sorted(osm_all - asr_parking, key=lambda s: (len(s), s))
    print(f"  Gates in ASR but missing from OSM ({len(missing_in_osm)}): {missing_in_osm}")
    print(f"  Gates in OSM but not in ASR ({len(missing_in_asr)}): {missing_in_asr}")

    # Taxiways: ASR vs OSM (by named ref)
    osm_tw_refs = {ref for ref in tw_groups if ref != "(no-ref)"}
    missing_tw_osm = sorted(asr_taxiways - osm_tw_refs)
    missing_tw_asr = sorted(osm_tw_refs - asr_taxiways)
    print(f"\n  Taxiways in ASR but missing from OSM ({len(missing_tw_osm)}): {missing_tw_osm}")
    print(f"  Taxiways in OSM but not in ASR ({len(missing_tw_asr)}): {missing_tw_asr}")

    # -- Holding positions
    print("\n=== HOLDING POSITIONS ===")
    hp_ways = [w for (aw, _), ws in ways_by_aw_ref.items() if aw == "holding_position" for w in ws]
    hp_nodes = [n for (aw, _), ns in nodes_by_aw_ref.items() if aw == "holding_position" for n in ns]
    print(f"  {len(hp_ways)} ways (line segments), {len(hp_nodes)} nodes")
    types = defaultdict(int)
    for el in hp_ways + hp_nodes:
        t = (el.get("tags", {}) or {}).get("holding_position:type", "(none)")
        types[t] += 1
    for t, n in sorted(types.items(), key=lambda kv: -kv[1]):
        print(f"     holding_position:type={t!r:20s}  {n}")

    # -- Navaids
    print("\n=== NAVAIDS ===")
    nv_ways = [w for (aw, _), ws in ways_by_aw_ref.items() if aw == "navigationaid" for w in ws]
    nv_nodes = [n for (aw, _), ns in nodes_by_aw_ref.items() if aw == "navigationaid" for n in ns]
    print(f"  {len(nv_ways)} ways, {len(nv_nodes)} nodes (each typically an ILS/PAPI component)")
    kinds = defaultdict(int)
    for el in nv_ways + nv_nodes:
        t = el.get("tags", {}) or {}
        kind = t.get("navigationaid") or "(unspecified)"
        kinds[kind] += 1
    for k, n in sorted(kinds.items(), key=lambda kv: -kv[1]):
        print(f"     navigationaid={k!r:20s}  {n}")


if __name__ == "__main__":
    main()
