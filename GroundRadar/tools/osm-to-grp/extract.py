"""
OSM-to-GRP extractor.

Pulls airport surface features from OpenStreetMap via Overpass, buffers
centerlines into polygons, and emits a GRP-compatible GRpluginMaps.txt
plus a per-airport block for GRpluginSettings.txt.

Usage:
    python extract.py config/cyhz.yaml

The output files are written relative to the repo root (the parent of
the GroundRadar/ folder containing this tool). Re-running is idempotent
within a given OSM snapshot; if data/<icao>_raw.json exists it's used
unless --refresh is passed.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml
from shapely.geometry import LineString, MultiPolygon, Polygon, mapping
from shapely.ops import unary_union

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

TOOL_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOL_DIR.parent.parent.parent          # tools/osm-to-grp -> GroundRadar -> repo
DATA_DIR = TOOL_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

OVERPASS_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]


# --------------------------------------------------------------------------
# Geometry helpers — flat-earth at airport latitude
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Projection:
    origin_lat: float
    m_per_deg_lat: float
    m_per_deg_lon: float

    @classmethod
    def at(cls, lat: float) -> "Projection":
        return cls(
            origin_lat=lat,
            m_per_deg_lat=111111.0,
            m_per_deg_lon=111111.0 * math.cos(math.radians(lat)),
        )

    def to_xy(self, lat: float, lon: float, origin_lon: float) -> tuple[float, float]:
        x = (lon - origin_lon) * self.m_per_deg_lon
        y = (lat - self.origin_lat) * self.m_per_deg_lat
        return x, y

    def from_xy(self, x: float, y: float, origin_lon: float) -> tuple[float, float]:
        lat = self.origin_lat + y / self.m_per_deg_lat
        lon = origin_lon + x / self.m_per_deg_lon
        return lat, lon


def fmt_coord(lat: float, lon: float) -> str:
    """Emit decimal degrees with colon separator, 6 places."""
    return f"{lat:.6f}:{lon:.6f}"


def parse_dms(s: str) -> float:
    """Parse 'N044.51.55.807' or 'W063.31.36.968' to signed decimal degrees."""
    direction = s[0]
    parts = s[1:].split(".", 3)
    deg = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2] + ("." + parts[3] if len(parts) > 3 else ""))
    dec = deg + minutes / 60.0 + seconds / 3600.0
    if direction in ("S", "W"):
        dec = -dec
    return dec


def fmt_dms(value: float, is_lat: bool) -> str:
    """Convert decimal degrees back to 'N044.51.55.807'-style."""
    direction = ("N" if value >= 0 else "S") if is_lat else ("E" if value >= 0 else "W")
    v = abs(value)
    deg = int(v)
    mm_dec = (v - deg) * 60
    mm = int(mm_dec)
    ss = (mm_dec - mm) * 60
    return f"{direction}{deg:03d}.{mm:02d}.{ss:06.3f}"


# --------------------------------------------------------------------------
# Overpass fetch
# --------------------------------------------------------------------------

def overpass_query(bbox: dict) -> str:
    return f"""
[out:json][timeout:90];
(
  way["aeroway"]({bbox['lat_min']},{bbox['lon_min']},{bbox['lat_max']},{bbox['lon_max']});
  node["aeroway"]({bbox['lat_min']},{bbox['lon_min']},{bbox['lat_max']},{bbox['lon_max']});
  relation["aeroway"]({bbox['lat_min']},{bbox['lon_min']},{bbox['lat_max']},{bbox['lon_max']});
);
out geom;
""".strip()


def fetch_or_cache(bbox: dict, cache_path: Path, refresh: bool) -> dict:
    if cache_path.exists() and not refresh:
        print(f"  using cached {cache_path.name} ({cache_path.stat().st_size} bytes)")
        return json.loads(cache_path.read_text(encoding="utf-8"))

    query = overpass_query(bbox)
    data = query.encode("utf-8")
    last_err: Exception | None = None
    for url in OVERPASS_ENDPOINTS:
        print(f"  POST {url}")
        req = urllib.request.Request(
            url, data=data,
            headers={
                "Content-Type": "text/plain; charset=utf-8",
                "User-Agent": "CZQM-vACC-GroundRadar-OSM/0.1 (joel@joelmorin.com)",
            },
        )
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read()
            print(f"    {resp.status} in {time.time() - t0:.1f}s ({len(raw)} bytes)")
            cache_path.write_text(raw.decode("utf-8"), encoding="utf-8")
            return json.loads(raw)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            print(f"    failed: {e}")
            last_err = e
            time.sleep(2)
    raise RuntimeError(f"All Overpass endpoints failed: {last_err}")


# --------------------------------------------------------------------------
# Classification / grouping
# --------------------------------------------------------------------------

@dataclass
class ClassifiedFeatures:
    runways: list[dict]                       # ways, kept after vertex filter
    taxiways_by_ref: dict[str, list[dict]]    # ref -> list of ways
    taxiway_unnamed: list[dict]
    taxilanes: list[dict]
    parking_position_ways: list[dict]
    apron_polygons: list[dict]
    hangars: list[dict]
    gates: list[dict]                         # nodes
    holding_position_ways: list[dict]
    bbox_center: tuple[float, float]


def classify(payload: dict, cfg: dict) -> ClassifiedFeatures:
    runways, taxiways, taxiway_unnamed, taxilanes = [], defaultdict(list), [], []
    parking_ways = []
    aprons, hangars = [], []
    gates: list[dict] = []
    holdings_ways: list[dict] = []

    min_rw = cfg.get("min_runway_vertices", 5)

    for el in payload.get("elements", []):
        tags = el.get("tags", {}) or {}
        aw = tags.get("aeroway")
        if not aw:
            continue
        if el["type"] == "way":
            geom = el.get("geometry") or []
            if not geom:
                continue
            if aw == "runway":
                if len(geom) >= min_rw:
                    runways.append(el)
            elif aw == "taxiway":
                ref = (tags.get("ref") or "").strip()
                if ref:
                    taxiways[ref].append(el)
                else:
                    taxiway_unnamed.append(el)
            elif aw == "taxilane":
                taxilanes.append(el)
            elif aw == "parking_position":
                parking_ways.append(el)
            elif aw == "apron":
                if geom[0] == geom[-1]:
                    aprons.append(el)
            elif aw == "hangar":
                if geom[0] == geom[-1]:
                    hangars.append(el)
            elif aw == "holding_position":
                holdings_ways.append(el)
        elif el["type"] == "node":
            if aw == "gate":
                gates.append(el)

    center = (
        0.5 * (cfg["bbox"]["lat_min"] + cfg["bbox"]["lat_max"]),
        0.5 * (cfg["bbox"]["lon_min"] + cfg["bbox"]["lon_max"]),
    )

    return ClassifiedFeatures(
        runways=runways,
        taxiways_by_ref=dict(taxiways),
        taxiway_unnamed=taxiway_unnamed,
        taxilanes=taxilanes,
        parking_position_ways=parking_ways,
        apron_polygons=aprons,
        hangars=hangars,
        gates=gates,
        holding_position_ways=holdings_ways,
        bbox_center=center,
    )


# --------------------------------------------------------------------------
# Buffering centerlines to polygons
# --------------------------------------------------------------------------

def buffer_way_to_polygon(
    way: dict, width_m: float, proj: Projection, origin_lon: float
) -> Polygon | MultiPolygon | None:
    geom = way.get("geometry") or []
    if len(geom) < 2:
        return None
    coords = [proj.to_xy(p["lat"], p["lon"], origin_lon) for p in geom]
    line = LineString(coords)
    return line.buffer(width_m / 2.0, cap_style=2, join_style=2)


def buffer_ways(
    ways: list[dict], width_m: float, proj: Projection, origin_lon: float
) -> Polygon | MultiPolygon:
    polys = []
    for w in ways:
        tags = w.get("tags", {}) or {}
        try:
            w_override = float(tags.get("width") or "")
        except (TypeError, ValueError):
            w_override = width_m
        p = buffer_way_to_polygon(w, w_override, proj, origin_lon)
        if p is not None and not p.is_empty:
            polys.append(p)
    if not polys:
        return Polygon()
    return unary_union(polys)


def way_polygon_xy(way: dict, proj: Projection, origin_lon: float) -> Polygon | None:
    geom = way.get("geometry") or []
    if len(geom) < 3:
        return None
    coords = [proj.to_xy(p["lat"], p["lon"], origin_lon) for p in geom]
    poly = Polygon(coords)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly if not poly.is_empty else None


def polygon_to_latlon_rings(
    poly: Polygon | MultiPolygon, proj: Projection, origin_lon: float
) -> list[list[tuple[float, float]]]:
    """Return a list of rings (each ring = list of (lat, lon)). Holes are dropped with a warning."""
    rings: list[list[tuple[float, float]]] = []

    def _add(poly: Polygon) -> None:
        if poly.is_empty:
            return
        ext = list(poly.exterior.coords)
        ring = [proj.from_xy(x, y, origin_lon) for (x, y) in ext]
        rings.append(ring)
        if poly.interiors:
            print(f"  WARN: polygon has {len(poly.interiors)} hole(s); dropping (GRP does not support polygon holes)")

    if isinstance(poly, MultiPolygon):
        for p in poly.geoms:
            _add(p)
    else:
        _add(poly)

    return rings


# --------------------------------------------------------------------------
# MAP block emission
# --------------------------------------------------------------------------

def map_block(
    name: str,
    folder: str,
    icao: str,
    layers: list[tuple[str, str, list[list[tuple[float, float]]]]],
    active: str = "1",
    hidden: bool = False,
) -> str:
    """
    Emit a single MAP block.
    layers is a list of (color_name, coordtype, list-of-rings) tuples.
    Each ring is a list of (lat, lon).
    """
    out: list[str] = []
    out.append(f"MAP:{name}")
    out.append(f"FOLDER:{folder}")
    out.append(f"AIRPORT:{icao}")
    if hidden:
        out.append("HIDDEN")
    out.append(f"ACTIVE:{active}")
    for color, coordtype, rings in layers:
        for ring in rings:
            out.append(f"COLOR:{color}")
            out.append(f"COORDTYPE:{coordtype}")
            for (lat, lon) in ring:
                out.append(f"COORD:{fmt_coord(lat, lon)}")
            out.append("")
    out.append("")
    return "\n".join(out)


def text_label_block(
    name: str,
    folder: str,
    icao: str,
    color: str,
    labels: list[tuple[float, float, str]],
    active: str = "1",
) -> str:
    out: list[str] = []
    out.append(f"MAP:{name}")
    out.append(f"FOLDER:{folder}")
    out.append(f"AIRPORT:{icao}")
    out.append(f"ACTIVE:{active}")
    out.append(f"COLOR:{color}")
    for lat, lon, text in labels:
        out.append(f"TEXT:{fmt_coord(lat, lon)}:{text}")
    out.append("")
    return "\n".join(out)


def linestring_block(
    name: str,
    folder: str,
    icao: str,
    color: str,
    lines: list[list[tuple[float, float]]],
    active: str = "1",
) -> str:
    out: list[str] = []
    out.append(f"MAP:{name}")
    out.append(f"FOLDER:{folder}")
    out.append(f"AIRPORT:{icao}")
    out.append(f"ACTIVE:{active}")
    out.append(f"COLOR:{color}")
    out.append(f"COORDTYPE:OTHER:POLYLINE")
    for line in lines:
        for lat, lon in line:
            out.append(f"COORD:{fmt_coord(lat, lon)}")
        out.append("")
    out.append("")
    return "\n".join(out)


def color_defs_block(colors: dict) -> str:
    out = []
    for name, rgb in colors.items():
        r, g, b = rgb
        out.append(f"COLORDEF:{name}:{r}:{g}:{b}")
    out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Output composition
# --------------------------------------------------------------------------

HEADER = """\
// CYHZ Ground Radar maps — auto-generated by tools/osm-to-grp/extract.py
// Source: OpenStreetMap (ODbL) via Overpass API
// Pattern: derived from pinatacolada/topskylppc (LPPC) — GPL-3.0
//   in-repo reference at reference docs/portugal/
// DO NOT EDIT BY HAND — regenerate with `python extract.py config/<icao>.yaml`
// Hand edits will be lost on next run.

"""


def write_maps_file(features: ClassifiedFeatures, cfg: dict, out_path: Path) -> None:
    icao: str = cfg["icao"]
    folder: str = icao
    twy_folder: str = f"{icao} TWY DATA"
    widths = cfg["default_widths"]
    proj = Projection.at(cfg["projection_lat"])
    origin_lon = features.bbox_center[1]

    sections: list[str] = [HEADER, color_defs_block(cfg["colors"])]

    # --- Background pane ---
    bbox = cfg["bbox"]
    background_ring = [
        (bbox["lat_min"], bbox["lon_min"]),
        (bbox["lat_max"], bbox["lon_min"]),
        (bbox["lat_max"], bbox["lon_max"]),
        (bbox["lat_min"], bbox["lon_max"]),
    ]
    sections.append(
        map_block(
            "BACKGROUND",
            "DIV",
            icao,
            [("SMGS_BACKGROUND", "OTHER:REGION_FILLONLY", [background_ring])],
        )
    )

    # --- APRONS (already polygons) ---
    if features.apron_polygons:
        apron_rings: list[list[tuple[float, float]]] = []
        for w in features.apron_polygons:
            poly = way_polygon_xy(w, proj, origin_lon)
            if poly is None:
                continue
            apron_rings.extend(polygon_to_latlon_rings(poly, proj, origin_lon))
        sections.append(
            map_block(
                "APRON",
                folder,
                icao,
                [("SMGS_APRON", "OTHER:REGION_FILLONLY", apron_rings)],
            )
        )

    # --- RUNWAYS (buffered centerlines, merged) ---
    if features.runways:
        rwy_poly = buffer_ways(features.runways, widths["runway"], proj, origin_lon)
        rwy_rings = polygon_to_latlon_rings(rwy_poly, proj, origin_lon) if not rwy_poly.is_empty else []
        sections.append(
            map_block(
                "RUNWAY",
                folder,
                icao,
                [("SMGS_RWY", "OTHER:REGION_FILLONLY", rwy_rings)],
            )
        )

    # --- TAXIWAYS (named + unnamed, all buffered + merged) ---
    all_taxi_ways: list[dict] = []
    for ways in features.taxiways_by_ref.values():
        all_taxi_ways.extend(ways)
    all_taxi_ways.extend(features.taxiway_unnamed)
    if all_taxi_ways:
        tw_poly = buffer_ways(all_taxi_ways, widths["taxiway"], proj, origin_lon)
        tw_rings = polygon_to_latlon_rings(tw_poly, proj, origin_lon) if not tw_poly.is_empty else []
        sections.append(
            map_block(
                "TAXIWAY",
                folder,
                icao,
                [("SMGS_TWY", "OTHER:REGION_FILLONLY", tw_rings)],
            )
        )

    # --- TAXILANES (thinner) ---
    if features.taxilanes:
        tl_poly = buffer_ways(features.taxilanes, widths["taxilane"], proj, origin_lon)
        tl_rings = polygon_to_latlon_rings(tl_poly, proj, origin_lon) if not tl_poly.is_empty else []
        sections.append(
            map_block(
                "TAXILANE",
                folder,
                icao,
                [("SMGS_TWY", "OTHER:REGION_FILLONLY", tl_rings)],
            )
        )

    # --- PARKING POSITIONS (stand fill, buffered) ---
    if features.parking_position_ways:
        pp_poly = buffer_ways(features.parking_position_ways, widths["parking_position"], proj, origin_lon)
        pp_rings = polygon_to_latlon_rings(pp_poly, proj, origin_lon) if not pp_poly.is_empty else []
        sections.append(
            map_block(
                "PARKING",
                folder,
                icao,
                [("SMGS_PARKING", "OTHER:REGION_FILLONLY", pp_rings)],
            )
        )

    # --- HANGARS / BUILDINGS ---
    if features.hangars:
        bldg_rings: list[list[tuple[float, float]]] = []
        for w in features.hangars:
            poly = way_polygon_xy(w, proj, origin_lon)
            if poly is None:
                continue
            bldg_rings.extend(polygon_to_latlon_rings(poly, proj, origin_lon))
        sections.append(
            map_block(
                "BUILDINGS",
                folder,
                icao,
                [("SMGS_BUILDING", "OTHER:REGION_FILLONLY", bldg_rings)],
            )
        )

    # --- HOLDING POSITION marking lines ---
    if features.holding_position_ways:
        lines = []
        for w in features.holding_position_ways:
            geom = w.get("geometry") or []
            if len(geom) < 2:
                continue
            lines.append([(p["lat"], p["lon"]) for p in geom])
        if lines:
            sections.append(
                linestring_block(
                    "HOLDING POSITIONS",
                    folder,
                    icao,
                    "SMGS_HOLDING",
                    lines,
                )
            )

    # --- TEXT: stand numbers (gate nodes + parking_position way midpoints; gate nodes win on conflict) ---
    seen_refs: set[str] = set()
    labels: list[tuple[float, float, str]] = []
    for n in features.gates:
        ref = (n.get("tags", {}) or {}).get("ref") or ""
        if not ref or ref in seen_refs:
            continue
        seen_refs.add(ref)
        labels.append((n["lat"], n["lon"], ref))
    for w in features.parking_position_ways:
        ref = (w.get("tags", {}) or {}).get("ref") or ""
        if not ref or ref in seen_refs:
            continue
        geom = w.get("geometry") or []
        if not geom:
            continue
        mid = geom[len(geom) // 2]
        seen_refs.add(ref)
        labels.append((mid["lat"], mid["lon"], ref))
    labels.sort(key=lambda t: (len(t[2]), t[2]))
    if labels:
        sections.append(
            text_label_block(
                "STAND NUMBER",
                folder,
                icao,
                "SMGS_LABEL",
                labels,
            )
        )
        print(f"  STAND NUMBER: {len(labels)} labels ({len(features.gates)} from gate nodes + {len(labels) - len(features.gates)} from parking_position ways)")

    # --- TEXT: taxiway names (midpoint of longest way per ref) ---
    if features.taxiways_by_ref:
        labels = []
        for ref, ways in sorted(features.taxiways_by_ref.items()):
            longest = max(ways, key=lambda w: len(w.get("geometry") or []))
            geom = longest.get("geometry") or []
            if not geom:
                continue
            mid = geom[len(geom) // 2]
            labels.append((mid["lat"], mid["lon"], ref))
        if labels:
            sections.append(
                text_label_block(
                    "TAXIWAY NAME",
                    folder,
                    icao,
                    "SMGS_LABEL",
                    labels,
                )
            )

    # --- Hidden CYHZ TWY DATA blocks (per named taxiway), for CMAC tagging ---
    for ref, ways in sorted(features.taxiways_by_ref.items()):
        poly = buffer_ways(ways, widths["taxiway"], proj, origin_lon)
        if poly.is_empty:
            continue
        rings = polygon_to_latlon_rings(poly, proj, origin_lon)
        sections.append(
            map_block(
                f"TWY {ref}",
                twy_folder,
                icao,
                [("SMGS_TWY", "TWYTYPE:NONE", rings)],
                hidden=True,
            )
        )

    text = "\n".join(sections)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"  wrote {out_path} ({len(text):,} bytes, {text.count('MAP:')} MAP blocks)")


def write_settings_file(cfg: dict, out_path: Path) -> None:
    icao = cfg["icao"]
    apt = cfg["airport"]
    sn = cfg["safety_nets"]
    ra = cfg["runway_area"]

    lines: list[str] = []
    lines.append(f"// {icao} GRP plugin settings — generated block")
    lines.append(f"// Re-run extract.py to regenerate this section.")
    lines.append("")
    lines.append(f"[{icao}]")
    lines.append(f"Airport_Elevation={apt['elevation_ft']}")
    lines.append(f"Airport_Radius={apt['radius_nm']}")

    for rwy_name, info in cfg["runways"].items():
        for end_key in ("end_a", "end_b"):
            e = info[end_key]
            lines.append(f"Airport_Runway_End={e['id']}:{e['lat']}:{e['lon']}")

    lines.append("")
    lines.append("Airport_SMR_Raw=2")
    lines.append("Airport_SMR_Track=0")
    lines.append("Airport_ModeA=1")
    lines.append("Airport_ModeS=1")
    lines.append("")
    lines.append(f"System_RwyArea={ra['normal_m']}")
    lines.append(f"System_RwyBufferArea={ra['normal_buffer_m']}")
    lines.append(f"System_RwyArea_LVP={ra['lvp_m']}")
    lines.append(f"System_RwyBufferArea_LVP={ra['lvp_buffer_m']}")
    lines.append("")
    for flag, val in sn.items():
        lines.append(f"System_{flag}={val}")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  wrote {out_path}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path, help="Path to airport YAML config")
    ap.add_argument("--refresh", action="store_true", help="Force re-fetch from Overpass")
    args = ap.parse_args(argv)

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    icao = cfg["icao"]

    print(f"=== {icao} ({cfg.get('display_name', '')}) ===")
    print(f"Repo root: {REPO_ROOT}")
    print(f"Bbox: {cfg['bbox']}")

    print("\n1. Fetch / cache OSM payload")
    cache_path = DATA_DIR / f"{icao.lower()}_raw.json"
    payload = fetch_or_cache(cfg["bbox"], cache_path, refresh=args.refresh)
    print(f"  {len(payload.get('elements', []))} elements")

    print("\n2. Classify and group")
    features = classify(payload, cfg)
    print(f"  runways:                 {len(features.runways)} ways (after vertex filter)")
    print(f"  taxiways (named):        {len(features.taxiways_by_ref)} refs across {sum(len(v) for v in features.taxiways_by_ref.values())} ways")
    print(f"  taxiways (unnamed):      {len(features.taxiway_unnamed)} ways")
    print(f"  taxilanes:               {len(features.taxilanes)}")
    print(f"  aprons:                  {len(features.apron_polygons)} polygons")
    print(f"  hangars:                 {len(features.hangars)} polygons")
    print(f"  parking_position ways:   {len(features.parking_position_ways)}")
    print(f"  gate nodes:              {len(features.gates)}")
    print(f"  holding_position ways:   {len(features.holding_position_ways)}")

    print("\n3. Buffer + emit MAP blocks")
    maps_out = REPO_ROOT / cfg["output"]["maps"]
    write_maps_file(features, cfg, maps_out)

    print("\n4. Emit settings block")
    settings_out = REPO_ROOT / cfg["output"]["settings"]
    write_settings_file(cfg, settings_out)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
