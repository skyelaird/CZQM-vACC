"""One-off generator: emit a CYHZ 14/32 SMGS_RWYMARK block in the LPPT style.

LPPT authors runway markings as many small filled rectangular polygons painted
on top of the runway surface (all inside the big MAP:SURFACE block, prefaced
with COLOR:SMGS_RWYMARK + COORDTYPE:OTHER:REGION).

This script generates an equivalent set for CYHZ runway 14/32:
  - 1 continuous centerline strip
  - 12 piano-key threshold bars at threshold 14 (per ICAO Annex 14 for 60m runway)
  - 12 piano-key threshold bars at threshold 32
  - Aiming-point markings (2 per end, 300m from threshold)
  - Designator-area outlines (1 per end, where the 14/32 numbers paint)

Output goes to stdout. Copy/paste into GRpluginMaps.txt inside the appropriate
MAP block (e.g. between the runway-surface polygon and the next feature).

Run: python gen_rwymark.py > /tmp/cyhz_rwymark.txt
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

# Threshold coordinates (decimal degrees) from AeroNav AIRAC 2605/1 [RUNWAY] section
THR_14 = (44.89372, -63.51743)   # N44.53.37.388 W63.31.02.769
THR_32 = (44.88158, -63.49313)   # N44.52.53.691 W63.29.35.278

# Flat-earth projection at CYHZ runway midpoint
LAT_ORIGIN = 0.5 * (THR_14[0] + THR_32[0])
LON_ORIGIN = 0.5 * (THR_14[1] + THR_32[1])
M_PER_DEG_LAT = 111111.0
M_PER_DEG_LON = 111111.0 * math.cos(math.radians(LAT_ORIGIN))


def to_xy(lat: float, lon: float) -> tuple[float, float]:
    return (lon - LON_ORIGIN) * M_PER_DEG_LON, (lat - LAT_ORIGIN) * M_PER_DEG_LAT


def from_xy(x: float, y: float) -> tuple[float, float]:
    return LAT_ORIGIN + y / M_PER_DEG_LAT, LON_ORIGIN + x / M_PER_DEG_LON


# Runway local frame: u = unit vector along centerline (14 -> 32), p = perpendicular (right of u)
x14, y14 = to_xy(*THR_14)
x32, y32 = to_xy(*THR_32)
dx, dy = x32 - x14, y32 - y14
length = math.hypot(dx, dy)
ux, uy = dx / length, dy / length
px, py = uy, -ux   # right-of-u perpendicular


def axis_offset(t_along: float, t_lateral: float) -> tuple[float, float]:
    """Convert (along-runway, perpendicular) offset from threshold 14 to local x,y."""
    return x14 + ux * t_along + px * t_lateral, y14 + uy * t_along + py * t_lateral


def rect(t_center: float, lat_center: float, half_len: float, half_wid: float) -> list[tuple[float, float]]:
    """Rectangle centered at (t_center along runway, lat_center perpendicular), aligned with runway.
    Returns 4 corner (x,y) tuples in local frame, going counterclockwise."""
    corners_local = [
        (-half_len, -half_wid),
        ( half_len, -half_wid),
        ( half_len,  half_wid),
        (-half_len,  half_wid),
    ]
    out = []
    for (cl, cw) in corners_local:
        out.append(axis_offset(t_center + cl, lat_center + cw))
    return out


def emit_polygon(corners: list[tuple[float, float]]) -> None:
    print("COLOR:SMGS_RWYMARK")
    print("COORDTYPE:OTHER:REGION")
    for (xx, yy) in corners:
        lat, lon = from_xy(xx, yy)
        print(f"COORD:{lat:.6f}:{lon:.6f}")
    # Close back to first vertex (LPPT convention)
    lat, lon = from_xy(corners[0][0], corners[0][1])
    print(f"COORD:{lat:.6f}:{lon:.6f}")
    print()


# --- Generate markings ---

print(f"// CYHZ 14/32 runway surface markings — SMGS_RWYMARK polygons", file=sys.stderr)
print(f"// Runway length (computed from thresholds): {length:.1f} m", file=sys.stderr)
print(f"// Runway bearing 14->32: {(math.degrees(math.atan2(ux, uy)) + 360) % 360:.1f}° true", file=sys.stderr)

count = 0

# 1) Centerline — one continuous strip, 0.9m wide.
# ICAO: centerline starts 6m before/after the threshold bars (so ~36m from threshold edge).
# Practical: just offset 30m from each threshold to keep clear of the piano keys.
CENTERLINE_OFFSET = 36.0  # m, from threshold
cl_t_start = CENTERLINE_OFFSET
cl_t_end = length - CENTERLINE_OFFSET
cl_t_center = 0.5 * (cl_t_start + cl_t_end)
cl_half_len = 0.5 * (cl_t_end - cl_t_start)
emit_polygon(rect(cl_t_center, 0.0, cl_half_len, 0.45))   # 0.9 m wide -> half=0.45
count += 1

# 2) Piano-key threshold bars at each end.
# ICAO Annex 14 for 60m-wide runway: 16 stripes total, 8 each side.
# Each stripe: 30m long (along runway), 1.8m wide (across runway), 1.8m gap between adjacent stripes.
# Innermost stripe edge is 1.8m off the centerline. They start at the threshold and extend inboard 30m.
N_KEYS_PER_SIDE = 8
KEY_LEN = 30.0
KEY_WID = 1.8
KEY_GAP = 1.8

def piano_keys_at(t_threshold: float, direction: int) -> None:
    """direction +1: keys extend inboard from threshold 14. -1: inboard from threshold 32."""
    global count
    t_center = t_threshold + direction * (KEY_LEN / 2)
    for side in (-1, 1):
        for i in range(N_KEYS_PER_SIDE):
            inner_edge = (KEY_GAP / 2) + i * (KEY_WID + KEY_GAP)
            lat_center = side * (inner_edge + KEY_WID / 2)
            emit_polygon(rect(t_center, lat_center, KEY_LEN / 2, KEY_WID / 2))
            count += 1

piano_keys_at(0.0, +1)        # at threshold 14
piano_keys_at(length, -1)     # at threshold 32

# 3) Aiming-point markings — two thick rectangles at 300m from each threshold.
# ICAO: 30-60m long, 6-10m wide, 9-22.5m from CL. Pick 60m × 6m, 18m off CL.
AIM_T_FROM_THR = 300.0
AIM_LEN = 60.0
AIM_WID = 6.0
AIM_LATERAL = 18.0

def aiming_point(t_threshold: float, direction: int) -> None:
    global count
    t_center = t_threshold + direction * AIM_T_FROM_THR
    for side in (-1, 1):
        emit_polygon(rect(t_center, side * AIM_LATERAL, AIM_LEN / 2, AIM_WID / 2))
        count += 1

aiming_point(0.0, +1)         # 300m from 14, inboard
aiming_point(length, -1)      # 300m from 32, inboard

# 4) Designator-area outline — a single rectangle where the "14" and "32" numbers would paint.
# ICAO: designator about 60m from threshold, ~9m × 20m (representing the painted digits as a block).
DES_T_FROM_THR = 90.0
DES_LEN = 20.0
DES_WID = 9.0

def designator_block(t_threshold: float, direction: int) -> None:
    global count
    t_center = t_threshold + direction * DES_T_FROM_THR
    emit_polygon(rect(t_center, 0.0, DES_LEN / 2, DES_WID / 2))
    count += 1

designator_block(0.0, +1)     # "14" area
designator_block(length, -1)  # "32" area

print(f"\n// Total polygons emitted: {count}", file=sys.stderr)
