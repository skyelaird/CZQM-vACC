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
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, mapping
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
    helipad_nodes: list[dict]                 # nodes (often from osm_overrides)
    helipad_ways: list[dict]                  # closed ways with aeroway=helipad
    bbox_center: tuple[float, float]


def classify(payload: dict, cfg: dict) -> ClassifiedFeatures:
    runways, taxiways, taxiway_unnamed, taxilanes = [], defaultdict(list), [], []
    parking_ways = []
    aprons, hangars = [], []
    gates: list[dict] = []
    holdings_ways: list[dict] = []
    helipads_n: list[dict] = []
    helipads_w: list[dict] = []

    min_rw = cfg.get("min_runway_vertices", 5)
    overrides: dict[int, str] = {int(k): v for k, v in (cfg.get("osm_overrides") or {}).items()}

    n_overridden = 0
    for el in payload.get("elements", []):
        tags = el.get("tags", {}) or {}
        # Apply OSM overrides (re-tag known-bad elements before bucketing)
        if el.get("id") in overrides:
            new_aw = overrides[el["id"]]
            tags = dict(tags)
            tags["aeroway"] = new_aw
            n_overridden += 1
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
            elif aw == "helipad":
                if geom[0] == geom[-1]:
                    helipads_w.append(el)
        elif el["type"] == "node":
            if aw == "gate":
                gates.append(el)
            elif aw == "helipad":
                helipads_n.append(el)

    if n_overridden:
        print(f"  applied {n_overridden} OSM tag override(s)")

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
        helipad_nodes=helipads_n,
        helipad_ways=helipads_w,
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
    extra_actives: list[str] | None = None,
) -> str:
    out: list[str] = []
    out.append(f"MAP:{name}")
    out.append(f"FOLDER:{folder}")
    out.append(f"AIRPORT:{icao}")
    out.append(f"ACTIVE:{active}")
    for a in (extra_actives or []):
        out.append(f"ACTIVE:{a}")
    out.append(f"COLOR:{color}")
    out.append(f"COORDTYPE:OTHER:POLYLINE")
    for line in lines:
        for lat, lon in line:
            out.append(f"COORD:{fmt_coord(lat, lon)}")
        out.append("")
    out.append("")
    return "\n".join(out)


def runway_arrows_block(cfg: dict, icao: str, folder: str) -> str:
    """Emit a single MAP block containing RWY_ARROWS lines for every runway end.
    GRP auto-colours each arrow based on the current arrival/departure state of
    that runway end (arrival colour, departure colour, mixed colour, or nothing
    if the runway end isn't in active use)."""
    out: list[str] = []
    out.append("MAP:RUNWAY ARROWS")
    out.append(f"FOLDER:{folder}")
    out.append(f"AIRPORT:{icao}")
    out.append("ACTIVE:1")
    for pair_name, info in cfg["runways"].items():
        width = float(info.get("width_m", 63.0))
        for from_end, to_end in (("end_a", "end_b"), ("end_b", "end_a")):
            e_from, e_to = info[from_end], info[to_end]
            # RWY_ARROWS:<IcaoRwy>:<startLat>:<startLon>:<endLat>:<endLon>:<width>
            # Arrows point from start toward end; auto-coloured by the state of <IcaoRwy>.
            out.append(
                f"RWY_ARROWS:{icao}{e_from['id']}:{e_from['lat']}:{e_from['lon']}:"
                f"{e_to['lat']}:{e_to['lon']}:{width}"
            )
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
// Surface fills + linework: SCTFILEDATA pulling from the AeroNav AIRAC sector file
//   (hand-drawn, sweatbox-validated, multi-coloured REGIONS for grass/apron/hard/helipad/building)
// Overlays + tagging: OpenStreetMap (ODbL) via Overpass API
// Pattern reference: pinatacolada/topskylppc (LPPC) — GPL-3.0, in reference docs/portugal/
// DO NOT EDIT BY HAND — regenerate with `python extract.py config/<icao>.yaml`
// Hand edits will be lost on next run.

"""


def sctfiledata_block(
    name: str,
    folder: str,
    icao: str,
    color: str,
    sct_type: str,
    sct_group: str,
    active: str = "1",
    hidden: bool = False,
    coordtype: str | None = None,
    extra_lines: list[str] | None = None,
) -> str:
    """Emit a MAP block whose contents come from SCTFILEDATA:<type>\\<group>."""
    out: list[str] = []
    out.append(f"MAP:{name}")
    out.append(f"FOLDER:{folder}")
    out.append(f"AIRPORT:{icao}")
    if hidden:
        out.append("HIDDEN")
    out.append(f"ACTIVE:{active}")
    if extra_lines:
        out.extend(extra_lines)
    out.append(f"COLOR:{color}")
    if coordtype:
        out.append(f"COORDTYPE:{coordtype}")
    out.append(f"SCTFILEDATA:{sct_type}\\{sct_group}")
    out.append("")
    return "\n".join(out)


def partition_holding_by_runway_pair(
    holding_ways: list[dict],
    runway_ways: list[dict],
    proj: Projection,
    origin_lon: float,
) -> dict[str, list[dict]]:
    """For each holding way, find the closest runway centerline and group by its 'ref' (e.g., '05/23')."""
    rwy_lines: list[tuple[str, LineString]] = []
    for w in runway_ways:
        ref = (w.get("tags", {}) or {}).get("ref") or ""
        if not ref:
            continue
        geom = w.get("geometry") or []
        if len(geom) < 2:
            continue
        coords = [proj.to_xy(p["lat"], p["lon"], origin_lon) for p in geom]
        rwy_lines.append((ref, LineString(coords)))

    out: dict[str, list[dict]] = defaultdict(list)
    for hw in holding_ways:
        geom = hw.get("geometry") or []
        if len(geom) < 2:
            continue
        midp = geom[len(geom) // 2]
        x, y = proj.to_xy(midp["lat"], midp["lon"], origin_lon)
        p = Point(x, y)
        best: tuple[float, str] | None = None
        for ref, line in rwy_lines:
            d = p.distance(line)
            if best is None or d < best[0]:
                best = (d, ref)
        if best is not None:
            out[best[1]].append(hw)
    return dict(out)


def write_maps_file(features: ClassifiedFeatures, cfg: dict, out_path: Path) -> None:
    icao: str = cfg["icao"]
    folder: str = icao
    twy_folder: str = f"{icao} TWY DATA"
    stopbar_folder: str = f"{icao} STOP BARS"
    proj = Projection.at(cfg["projection_lat"])
    origin_lon = features.bbox_center[1]
    sct_groups = cfg["sct_groups"]

    sections: list[str] = [HEADER, color_defs_block(cfg["colors"])]

    # --- SCTFILEPATH (anchors all SCTFILEDATA lines below) ---
    sct_path = cfg.get("sct_file_path", "").strip()
    if sct_path:
        sections.append(f"SCTFILEPATH:{sct_path}\n")

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

    # --- SURFACE FILLS from .sct REGIONS (grass + apron + hard surface + helipad + building, with their own colours) ---
    sections.append(
        sctfiledata_block(
            "SURFACE", folder, icao,
            color="SMGS_BACKGROUND",     # not used by SCTFILEDATA (regions carry own colour) but required by grammar
            sct_type="REGIONS",
            sct_group=sct_groups["regions"],
        )
    )

    # --- LINEWORK from .sct GEO (taxiway/runway edges, markings, etc.) ---
    sections.append(
        sctfiledata_block(
            "LINEWORK", folder, icao,
            color="SMGS_BACKGROUND",     # GEO entries in .sct carry their own colours per segment
            sct_type="GEO",
            sct_group=sct_groups["geo_surface"],
        )
    )

    # --- PARKING DETAIL from .sct GEO ---
    sections.append(
        sctfiledata_block(
            "PARKING DETAIL", folder, icao,
            color="SMGS_PARKING",
            sct_type="GEO",
            sct_group=sct_groups["geo_parking"],
        )
    )

    # --- APRON sub-categories (OSM polygons, painted over the .sct's default apron rendering) ---
    apron_cats = cfg.get("apron_categories") or {}
    for cat_name, cat in apron_cats.items():
        cat_color = cat.get("color")
        wanted_ids = set(cat.get("osm_ids") or [])
        if not (cat_color and wanted_ids):
            continue
        cat_rings: list[list[tuple[float, float]]] = []
        for w in features.apron_polygons:
            if w["id"] not in wanted_ids:
                continue
            poly = way_polygon_xy(w, proj, origin_lon)
            if poly is None:
                continue
            cat_rings.extend(polygon_to_latlon_rings(poly, proj, origin_lon))
        if cat_rings:
            sections.append(
                map_block(
                    f"APRON {cat_name.upper()}",
                    folder,
                    icao,
                    [(cat_color, "OTHER:REGION_FILLONLY", cat_rings)],
                )
            )

    # --- HANGARS / BUILDINGS (OSM — augments any in the .sct REGIONS) ---
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

    # --- HELIPADS (OSM overrides + closed helipad ways; supplements the .sct's HelipadSurface regions) ---
    if features.helipad_ways or features.helipad_nodes:
        heli_polys = []
        for w in features.helipad_ways:
            poly = way_polygon_xy(w, proj, origin_lon)
            if poly is not None:
                heli_polys.append(poly)
        node_radius = float(cfg.get("helipad", {}).get("radius_m", 12.0))
        for n in features.helipad_nodes:
            x, y = proj.to_xy(n["lat"], n["lon"], origin_lon)
            heli_polys.append(Point(x, y).buffer(node_radius))
        if heli_polys:
            merged = unary_union(heli_polys)
            rings = polygon_to_latlon_rings(merged, proj, origin_lon)
            sections.append(
                map_block(
                    "HELIPAD",
                    folder,
                    icao,
                    [("SMGS_HELI", "OTHER:REGION_FILLONLY", rings)],
                )
            )
        # "H" labels at helipad centers
        h_labels: list[tuple[float, float, str]] = []
        for n in features.helipad_nodes:
            h_labels.append((n["lat"], n["lon"], "H"))
        for w in features.helipad_ways:
            geom = w.get("geometry") or []
            if not geom:
                continue
            lat_mean = sum(p["lat"] for p in geom) / len(geom)
            lon_mean = sum(p["lon"] for p in geom) / len(geom)
            h_labels.append((lat_mean, lon_mean, "H"))
        if h_labels:
            sections.append(
                text_label_block(
                    "HELIPAD LABEL", folder, icao, "SMGS_LABEL", h_labels,
                )
            )

    # --- STOP BARS — one MAP per runway pair, visible only when that runway pair is in active use ---
    if features.holding_position_ways and features.runways:
        by_pair = partition_holding_by_runway_pair(
            features.holding_position_ways, features.runways, proj, origin_lon,
        )
        for pair_name, hws in sorted(by_pair.items()):
            lines = []
            for w in hws:
                geom = w.get("geometry") or []
                if len(geom) < 2:
                    continue
                lines.append([(p["lat"], p["lon"]) for p in geom])
            if lines:
                rwys_in_pair = pair_name.split("/")
                rwy_list = ",".join(f"{icao}{r}" for r in rwys_in_pair)
                sections.append(
                    linestring_block(
                        f"STOP BARS {pair_name}",
                        stopbar_folder, icao, "SMGS_HOLDING", lines,
                        active=f"RWY:ARR:{rwy_list}:DEP:*",
                        extra_actives=[f"RWY:ARR:*:DEP:{rwy_list}"],
                    )
                )
        print(f"  STOP BARS: partitioned {len(features.holding_position_ways)} holding lines into {len(by_pair)} runway pair(s)")

    # --- RUNWAY ARROWS — auto-coloured direction indicators per runway end ---
    sections.append(runway_arrows_block(cfg, icao, folder))

    # --- TEXT: stand numbers from .sct FREETEXT (authoritative AIRAC positions) ---
    sections.append(
        sctfiledata_block(
            "STAND NUMBER", folder, icao,
            color="SMGS_LABEL",
            sct_type="FREETEXT",
            sct_group=sct_groups["freetext_parking"],
        )
    )

    # --- TEXT: taxiway names from .sct FREETEXT ---
    sections.append(
        sctfiledata_block(
            "TAXIWAY NAME", folder, icao,
            color="SMGS_LABEL",
            sct_type="FREETEXT",
            sct_group=sct_groups["freetext_taxiway"],
        )
    )

    # --- LVP OVERLAY (visible-only; activates when LVP toggled on Global Menu) ---
    sections.append(
        sctfiledata_block(
            "LVP OVERLAY", folder, icao,
            color="SMGS_HOLDING",
            sct_type="GEO",
            sct_group=sct_groups["geo_surface_lvp"],
            active=f"LVP:{icao}:1",
        )
    )

    # --- Hidden TWY DATA blocks (scaffolding for future RVM RESTRICTION rules; harmless otherwise) ---
    for ref, ways in sorted(features.taxiways_by_ref.items()):
        poly = buffer_ways(ways, 23.0, proj, origin_lon)   # fixed width for tagging blob
        if poly.is_empty:
            continue
        rings = polygon_to_latlon_rings(poly, proj, origin_lon)
        sections.append(
            map_block(
                f"TWY {ref}",
                twy_folder,
                icao,
                [("SMGS_BACKGROUND", "TWYTYPE:NONE", rings)],
                hidden=True,
            )
        )

    text = "\n".join(sections)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"  wrote {out_path} ({len(text):,} bytes, {text.count('MAP:')} MAP blocks)")


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """True bearing from point 1 to point 2, degrees 0-360."""
    lat1r, lat2r = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    x = math.sin(dlon) * math.cos(lat2r)
    y = math.cos(lat1r) * math.sin(lat2r) - math.sin(lat1r) * math.cos(lat2r) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0


def write_stands_file(features: ClassifiedFeatures, cfg: dict, out_path: Path) -> None:
    """Emit GRpluginStands.txt with one minimal STAND line per OSM-known stand ref.
    Radius derived from ICAO ARC category via stand_categories + category_radius."""
    icao = cfg["icao"]
    stands_cfg = cfg.get("stands") or {}
    default_cat = stands_cfg.get("default_category", "C")
    cat_radius: dict[str, float] = {
        k.upper(): float(v) for k, v in (cfg.get("category_radius") or {}).items()
    }
    stand_categories: dict[str, str] = {
        str(k): str(v).upper() for k, v in (cfg.get("stand_categories") or {}).items()
    }

    if not cat_radius:
        # Fallback if category_radius missing
        cat_radius = {"A": 10.0, "B": 14.0, "C": 20.0, "D": 28.0, "E": 35.0, "F": 42.0}

    def radius_for(ref: str) -> tuple[float, str]:
        cat = stand_categories.get(ref, default_cat).upper()
        return cat_radius.get(cat, cat_radius.get(default_cat.upper(), 20.0)), cat

    # Heading sources: config stand_headings (one-off, manually populated) -> OSM bearing -> none.
    hdg_tol = float(stands_cfg.get("heading_tolerance_deg", 30))
    config_headings: dict[str, float] = {
        str(k): float(v) for k, v in (cfg.get("stand_headings") or {}).items()
    }

    osm_headings: dict[str, float] = {}
    for w in features.parking_position_ways:
        ref = (w.get("tags", {}) or {}).get("ref") or ""
        if not ref:
            continue
        geom = w.get("geometry") or []
        if len(geom) < 2:
            continue
        p_from, p_to = geom[-2], geom[-1]
        osm_headings[ref] = bearing_deg(
            float(p_from["lat"]), float(p_from["lon"]),
            float(p_to["lat"]), float(p_to["lon"]),
        )

    def heading_for(ref: str) -> tuple[float | None, str]:
        if ref in config_headings:
            return config_headings[ref], "config"
        if ref in osm_headings:
            return osm_headings[ref], "osm"
        return None, "none"

    seen_refs: set[str] = set()
    stands: list[tuple[str, float, float, str, str, float, float | None, str]] = []

    for n in features.gates:
        ref = (n.get("tags", {}) or {}).get("ref") or ""
        if not ref or ref in seen_refs:
            continue
        seen_refs.add(ref)
        r, cat = radius_for(ref)
        hdg, hsrc = heading_for(ref)
        stands.append((ref, float(n["lat"]), float(n["lon"]), "gate", cat, r, hdg, hsrc))

    for w in features.parking_position_ways:
        ref = (w.get("tags", {}) or {}).get("ref") or ""
        if not ref or ref in seen_refs:
            continue
        geom = w.get("geometry") or []
        if not geom:
            continue
        end = geom[-1]
        seen_refs.add(ref)
        r, cat = radius_for(ref)
        hdg, hsrc = heading_for(ref)
        stands.append((ref, float(end["lat"]), float(end["lon"]), "parking_position", cat, r, hdg, hsrc))

    stands.sort(key=lambda t: (len(t[0]), t[0]))

    lines: list[str] = []
    lines.append(f"// {icao} GRP stand definitions — generated by tools/osm-to-grp/extract.py")
    lines.append("// Position sources: OSM aeroway=gate nodes (ref present); parking_position way endpoints fill gaps.")
    lines.append("// Radius from per-stand ICAO ARC category (cyhz.yaml/stand_categories).")
    lines.append("// Heading: cyhz.yaml/stand_headings when populated, else OSM parking_position last-segment bearing.")
    lines.append("// Auto-assignment disabled via System_AutoAssignDist=0 in GRpluginSettings.txt.")
    lines.append("")
    cat_counts: dict[str, int] = defaultdict(int)
    hdg_counts: dict[str, int] = defaultdict(int)
    for ref, lat, lon, _src, cat, r, hdg, hsrc in stands:
        lat_dms = fmt_dms(lat, True)
        lon_dms = fmt_dms(lon, False)
        lines.append(f"STAND:{icao}:{ref}:{lat_dms}:{lon_dms}:{r}")
        if hdg is not None:
            lines.append(f"HEADING:{hdg:.1f}:{hdg_tol}")
        cat_counts[cat] += 1
        hdg_counts[hsrc] += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cat_summary = ", ".join(f"{k}={v}" for k, v in sorted(cat_counts.items()))
    hdg_summary = ", ".join(f"{k}={v}" for k, v in sorted(hdg_counts.items()))
    print(f"  wrote {out_path} ({len(stands)} stands; categories: {cat_summary}; heading source: {hdg_summary})")


def write_settings_file(cfg: dict, out_path: Path) -> None:
    icao = cfg["icao"]
    apt = cfg["airport"]
    sn = cfg["safety_nets"]
    ra = cfg["runway_area"]

    lines: list[str] = []
    lines.append(f"// {icao} GRP plugin settings — generated block")
    lines.append(f"// Re-run tools/osm-to-grp/extract.py config/{icao.lower()}.yaml to regenerate.")
    lines.append("")
    lines.append("// --- System-wide settings (must be outside any [icao] block per Developer Guide §3.5.1) ---")
    # Stand auto-assignment is disabled — stands exist only for occupancy detection.
    auto_dist = (cfg.get("stands") or {}).get("auto_assign_dist_nm", 0)
    lines.append(f"System_AutoAssignDist={auto_dist}")
    lines.append(f"System_RwyArea={ra['normal_m']}")
    lines.append(f"System_RwyBufferArea={ra['normal_buffer_m']}")
    lines.append(f"System_RwyArea_LVP={ra['lvp_m']}")
    lines.append(f"System_RwyBufferArea_LVP={ra['lvp_buffer_m']}")
    lines.append("")
    lines.append(f"// --- Airport-specific settings for {icao} ---")
    lines.append(f"[{icao}]")
    lines.append(f"Airport_Elevation={apt['elevation_ft']}")
    lines.append(f"Airport_Radius={apt['radius_nm']}")
    if apt.get("sct_arp_lat") and apt.get("sct_arp_lon"):
        lines.append(f"Airport_Refpoint={apt['sct_arp_lat']}:{apt['sct_arp_lon']}")

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
    for flag, val in sn.items():
        lines.append(f"System_{flag}={val}")
    lines.append("")

    # APM approach paths
    apps = cfg.get("app_paths") or []
    apm = cfg.get("apm") or {}
    if apps and apm:
        lines.append("// Approach Path Monitoring — straight-in 3deg approaches to each runway end")
        for a in apps:
            lines.append(
                f"AppPath={icao}:{a['name']}:{a['end_lat']}:{a['end_lon']}:"
                f"{a['course']:.1f}:{a['dir']}:{a['end_alt']}:{a['vert']:.1f}"
            )
            lines.append(f"AppPath_APM={apm['alerts']}:{apm['range_min_nm']}:{apm['range_max_nm']}")
            lines.append(
                f"AppPath_APM_Vert_Lim={apm['vert_join_alt']}:{apm['vert_overfly_alt']}"
            )
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
    print(f"  helipads:                {len(features.helipad_ways)} ways + {len(features.helipad_nodes)} nodes")

    print("\n3. Buffer + emit MAP blocks")
    maps_out = REPO_ROOT / cfg["output"]["maps"]
    write_maps_file(features, cfg, maps_out)

    print("\n4. Emit settings block")
    settings_out = REPO_ROOT / cfg["output"]["settings"]
    write_settings_file(cfg, settings_out)

    if cfg.get("output", {}).get("stands"):
        print("\n5. Emit stands file")
        stands_out = REPO_ROOT / cfg["output"]["stands"]
        write_stands_file(features, cfg, stands_out)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
