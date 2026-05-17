"""Extract the CYHZ THR-14 turn pad outline from the OSM grass polygon.

Joel's hint: OSM way 1016444425 (natural=grassland) is mapped so that the
paved area is the *negative space* within it. The polygon's boundary
detours around the runway and the turn pad. The turn pad outline is the
concave portion of that boundary at the THR 14 end of the runway.

Algorithm (cited, not winged):
  1. Project all polygon vertices into runway-aligned (t, p) coordinates,
     where t = metres along runway from THR 14 toward THR 32 and
     p = perpendicular metres (positive = right of u when looking 14->32).
  2. The runway south edge is at p = +RWY_HALF (= 30.5 m for 61 m runway).
     Detect consecutive vertices forming a "bulge" — they leave the
     runway edge band (|p - RWY_HALF| > 5 m, and |p| > RWY_HALF + 5)
     and come back to the same edge band within DEPTH_LIMIT m of CL.
  3. The bulge vertices plus a closing segment along the runway edge
     form the turn pad outline.

Emits the resulting polygon as a GRP MAP block (one COLOR + COORDTYPE +
COORDs list ready to paste into GRpluginMaps.txt).

Run: python gen_turnpad.py > data/cyhz_thr14_turnpad.txt
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

OSM_FILE = Path(r"D:\GitHub\CZQM-vACC\GroundRadar\tools\osm-to-grp\data\osm_1016444425.json")

THR_14 = (44.89372, -63.51743)
THR_32 = (44.88158, -63.49313)
RWY_WIDTH = 61.0
RWY_HALF = RWY_WIDTH / 2

CORRIDOR_HALF = 45.0     # m: vertices with |p| <= this are "in the runway corridor"
                         # (61 m runway → half = 30.5, plus 14.5 m slack for OSM edge offset)
DEPTH_LIMIT = 150.0      # m: turn pad outer p should be within this of CL
THR_BAND = 250.0         # m: turn pad must be within this t-range of a threshold


payload = json.loads(OSM_FILE.read_text(encoding="utf-8"))
nodes = {el["id"]: (el["lat"], el["lon"]) for el in payload["elements"] if el.get("type") == "node"}
way = next(el for el in payload["elements"] if el.get("type") == "way")
refs = way["nodes"]

# Build runway frame
M_LAT = 111111.0
M_LON = 111111.0 * math.cos(math.radians(THR_14[0]))
dx = (THR_32[1] - THR_14[1]) * M_LON
dy = (THR_32[0] - THR_14[0]) * M_LAT
LENGTH = math.hypot(dx, dy)
ux, uy = dx / LENGTH, dy / LENGTH
px, py = uy, -ux

# Project vertices
points: list[tuple[float, float, float, float]] = []   # (lat, lon, t, p)
for ref in refs:
    if ref not in nodes:
        continue
    lat, lon = nodes[ref]
    x = (lon - THR_14[1]) * M_LON
    y = (lat - THR_14[0]) * M_LAT
    t = x * ux + y * uy
    p = x * px + y * py
    points.append((lat, lon, t, p))

# Detect bulges (turn pad candidates) the simple way:
#   1. Mark each vertex INSIDE if |p| <= CORRIDOR_HALF, OUTSIDE otherwise.
#   2. Find maximal runs of OUTSIDE vertices.
#   3. For each run, include the last INSIDE vertex before the run and the
#      first INSIDE vertex after — those are the runway-edge attachment points.
#   4. Filter: run's t-extent must be within THR_BAND of a threshold and the
#      max |p| within the run must be <= DEPTH_LIMIT.
def is_outside(p: float) -> bool:
    return abs(p) > CORRIDOR_HALF


n = len(points)
bulges: list[tuple[int, int, str]] = []  # (start_idx, end_idx, side_label) inclusive
i = 0
while i < n:
    if is_outside(points[i][3]):
        j = i
        while j + 1 < n and is_outside(points[j + 1][3]):
            j += 1
        start = (i - 1) % n
        end = (j + 1) % n
        run_t = [points[k][2] for k in range(i, j + 1)]
        run_p = [points[k][3] for k in range(i, j + 1)]
        t_min, t_max = min(run_t), max(run_t)
        p_max_abs = max(abs(p) for p in run_p)
        near_thr14 = t_min < THR_BAND
        near_thr32 = t_max > LENGTH - THR_BAND
        if (near_thr14 or near_thr32) and p_max_abs <= DEPTH_LIMIT:
            side_label = "south" if max(run_p) > 0 else "north"
            bulges.append((start, end, side_label))
        i = j + 1
    else:
        i += 1


print(f"// Detected {len(bulges)} turn-pad-like bulge(s) in OSM way {way['id']} (natural=grassland)", file=sys.stderr)
for (start, end, side) in bulges:
    span = ((end - start) % n) + 1
    t_start, p_start = points[start][2], points[start][3]
    t_end, p_end = points[end][2], points[end][3]
    print(f"//   bulge v{start}->v{end} ({span} vertices) on {side} side: "
          f"t={t_start:.0f}->{t_end:.0f} m, p_attach=({p_start:.0f}, {p_end:.0f})", file=sys.stderr)


# Emit GRP block for each detected bulge
print("// CYHZ THR-14 runway turn pad — extracted from OSM grass polygon 1016444425")
print("// (paved area = negative space within natural=grassland)")
print()

for (start, end, side) in bulges:
    # Walk the polygon vertices from start to end inclusive (going through the bulge)
    poly_points: list[tuple[float, float]] = []
    k = start
    while True:
        poly_points.append((points[k][0], points[k][1]))
        if k == end:
            break
        k = (k + 1) % n

    print(f"// turn pad on {side} side of runway, "
          f"polygon vertex {start}..{end} ({len(poly_points)} corners)")
    print("COLOR:SMGS_TWY")
    print("COORDTYPE:OTHER:REGION_FILLONLY")
    for (lat, lon) in poly_points:
        print(f"COORD:{lat:.6f}:{lon:.6f}")
    # GRP convention: close polygon by repeating the first vertex
    print(f"COORD:{poly_points[0][0]:.6f}:{poly_points[0][1]:.6f}")
    print()
