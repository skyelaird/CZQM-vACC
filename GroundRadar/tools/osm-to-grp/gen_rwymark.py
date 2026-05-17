"""Generate ICAO Annex 14 §5.2 compliant runway-surface markings for CYHZ 14/32.

Emitted as a series of inline SMGS_RWYMARK polygons in the LPPT style:
each marking is one filled rectangular polygon. Drop the output inside
the appropriate MAP block, after the runway-surface (SMGS_RWY) fill, so
markings paint on top.

CYHZ runway 14/32:
  - Length 2,347 m (per AIP; 2,340.7 m computed from threshold coords)
  - Width  61 m (200 ft)
  - Precision approach Cat I (ILS at both ends per Canada AIP)
  - Code number 4 (length >= 1,800 m)

Marking inventory and the Annex 14 reference for each:
  §5.2.3  Centre line   — 0.45 m wide (Cat I), dashed 30 m stripe + 30 m gap,
                          located between the designation markings
  §5.2.4  Threshold     — 16 stripes total (table at 5.2.4.5 for 60 m width),
                          30 m × 1.80 m, 1.80 m spacing, double-spaced 3.6 m
                          across CL, starting 6 m from threshold; outer edge
                          27 m from CL (3 m runway-edge clearance)
  §5.2.5  Aiming point  — 2 stripes, 300 m from threshold (Table 5-1 col 4
                          for LDA 1200-2400 m), 60 m × 9 m, 18 m lateral
                          spacing between inner sides
  §5.2.6  Touchdown zone — 4 pairs total (table at 5.2.6.3 for LDA
                          1500-2400 m) at 150 m intervals from threshold;
                          the pair at 300 m is deleted (within 50 m of
                          aiming point) per 5.2.6.4 last sentence, leaving
                          3 pairs at 150, 450, 600 m; each stripe basic
                          pattern (5-5 A) = 22.5 m × 3 m; lateral spacing
                          matches aiming point
  §5.2.7  Side stripes  — 0.9 m wide continuous, outer edge at runway edge
                          (i.e. 30 m from CL), threshold to threshold

Run: python gen_rwymark.py > data/cyhz_14_32_rwymark.txt
"""
from __future__ import annotations

import math
import sys

# Threshold coordinates (decimal degrees) from CZQQ AIRAC 2605/1 [RUNWAY] section.
THR_14 = (44.89372, -63.51743)   # N44.53.37.388 W63.31.02.769
THR_32 = (44.88158, -63.49313)   # N44.52.53.691 W63.29.35.278
RWY_WIDTH = 61.0                 # m (200 ft)

# Flat-earth projection at runway midpoint
LAT_ORIGIN = 0.5 * (THR_14[0] + THR_32[0])
LON_ORIGIN = 0.5 * (THR_14[1] + THR_32[1])
M_PER_DEG_LAT = 111111.0
M_PER_DEG_LON = 111111.0 * math.cos(math.radians(LAT_ORIGIN))


def to_xy(lat: float, lon: float) -> tuple[float, float]:
    return (lon - LON_ORIGIN) * M_PER_DEG_LON, (lat - LAT_ORIGIN) * M_PER_DEG_LAT


def from_xy(x: float, y: float) -> tuple[float, float]:
    return LAT_ORIGIN + y / M_PER_DEG_LAT, LON_ORIGIN + x / M_PER_DEG_LON


# Runway local frame:  u = unit vector along centreline 14 -> 32;  p = perpendicular (right of u)
x14, y14 = to_xy(*THR_14)
x32, y32 = to_xy(*THR_32)
dx, dy = x32 - x14, y32 - y14
LENGTH = math.hypot(dx, dy)
ux, uy = dx / LENGTH, dy / LENGTH
px, py = uy, -ux


def axis(t_along: float, t_lat: float) -> tuple[float, float]:
    """Convert (along-runway-from-THR14, perpendicular) offset to local x,y."""
    return x14 + ux * t_along + px * t_lat, y14 + uy * t_along + py * t_lat


def rect_corners(t_center: float, lat_center: float, half_len_along: float, half_wid_lat: float
                 ) -> list[tuple[float, float]]:
    """Rectangle in runway-aligned coords, four corners CCW."""
    return [
        axis(t_center - half_len_along, lat_center - half_wid_lat),
        axis(t_center + half_len_along, lat_center - half_wid_lat),
        axis(t_center + half_len_along, lat_center + half_wid_lat),
        axis(t_center - half_len_along, lat_center + half_wid_lat),
    ]


def emit_poly(corners: list[tuple[float, float]], comment: str = "") -> None:
    if comment:
        print(f"// {comment}")
    print("COLOR:SMGS_RWYMARK")
    print("COORDTYPE:OTHER:REGION")
    for (xx, yy) in corners:
        lat, lon = from_xy(xx, yy)
        print(f"COORD:{lat:.6f}:{lon:.6f}")
    lat, lon = from_xy(corners[0][0], corners[0][1])
    print(f"COORD:{lat:.6f}:{lon:.6f}")  # close back to first
    print()


# Counters for the run-summary on stderr
counts: dict[str, int] = {}


def count(category: str) -> None:
    counts[category] = counts.get(category, 0) + 1


# --- §5.2.7  Runway side-stripe markings ---------------------------------
# 0.9 m wide, outer edge at runway edge (30 m from CL), threshold to threshold.
SIDE_STRIPE_WID = 0.9
edge_offset = (RWY_WIDTH / 2) - (SIDE_STRIPE_WID / 2)
for side in (-1, 1):
    emit_poly(
        rect_corners(LENGTH / 2, side * edge_offset, LENGTH / 2, SIDE_STRIPE_WID / 2),
        comment=f"side stripe ({'right' if side > 0 else 'left'} of CL)",
    )
    count("side_stripe")


# --- §5.2.4  Threshold marking (piano keys) ------------------------------
# 16 stripes total for 60 m runway. Stripes 30 m long, 1.80 m wide, 1.80 m
# spacing, double-spacing (3.60 m) across the CL. Start 6 m from threshold.
N_KEYS_PER_SIDE = 8
KEY_LEN = 30.0
KEY_WID = 1.8
KEY_GAP = 1.8
THR_INSET = 6.0   # stripes begin 6 m inboard of threshold (5.2.4.4)


def piano_keys(t_threshold: float, direction: int) -> None:
    """direction = +1 for threshold 14 (extends inboard toward 32),
                  -1 for threshold 32 (extends inboard toward 14)."""
    t_center = t_threshold + direction * (THR_INSET + KEY_LEN / 2)
    for side in (-1, 1):
        for i in range(N_KEYS_PER_SIDE):
            # Inner edge of stripe i (from CL): 1.8 + i*3.6 m
            inner_edge = (KEY_GAP / 2) + i * (KEY_WID + KEY_GAP)
            lat_center = side * (inner_edge + KEY_WID / 2)
            emit_poly(
                rect_corners(t_center, lat_center, KEY_LEN / 2, KEY_WID / 2),
                comment=f"threshold key (THR {'14' if direction>0 else '32'}, "
                        f"{'right' if side>0 else 'left'} stripe {i+1})",
            )
            count("threshold_stripe")


piano_keys(0.0, +1)
piano_keys(LENGTH, -1)


# --- §5.2.5  Aiming point marking ----------------------------------------
# LDA 2,347 m falls in Table 5-1 column 4 (1200 - 2400 m):
#   distance from threshold 300 m, length 45-60 m, width 6-10 m, lateral 18-22.5 m
# Use 60 m × 9 m, 18 m between inner sides.
AIM_T = 300.0
AIM_LEN = 60.0
AIM_WID = 9.0
AIM_INNER_GAP = 18.0


def aiming_points(t_threshold: float, direction: int) -> None:
    t_center = t_threshold + direction * AIM_T + direction * (AIM_LEN / 2)
    # 'beginning of the marking' at AIM_T from threshold per 5.2.5.3
    inner_edge_lat = AIM_INNER_GAP / 2
    for side in (-1, 1):
        emit_poly(
            rect_corners(t_center, side * (inner_edge_lat + AIM_WID / 2),
                         AIM_LEN / 2, AIM_WID / 2),
            comment=f"aiming point (THR {'14' if direction>0 else '32'}, "
                    f"{'right' if side>0 else 'left'})",
        )
        count("aiming_point")


aiming_points(0.0, +1)
aiming_points(LENGTH, -1)


# --- §5.2.6  Touchdown zone marking (basic pattern A) --------------------
# LDA 2,347 m falls in 1500 - 2400 m range -> 4 pairs total per §5.2.6.3.
# Pairs at 150, 300, 450, 600 m from threshold; the 300 m pair is deleted
# (within 50 m of the 300 m aiming point) per 5.2.6.4 last sentence.
# Remaining pairs: 150, 450, 600 m. Stripe = 22.5 m × 3 m. Lateral spacing
# of the inner sides equals the aiming point's = 18 m, so each rectangle's
# inner edge is at 9 m from CL.
TDZ_DISTANCES = [150.0, 450.0, 600.0]   # 300 m pair suppressed (5.2.6.4)
TDZ_LEN = 22.5
TDZ_WID = 3.0
TDZ_INNER_LAT = 9.0   # matches half of AIM_INNER_GAP


def tdz_pairs(t_threshold: float, direction: int) -> None:
    for d_from_thr in TDZ_DISTANCES:
        t_center = t_threshold + direction * (d_from_thr + TDZ_LEN / 2)
        for side in (-1, 1):
            emit_poly(
                rect_corners(t_center, side * (TDZ_INNER_LAT + TDZ_WID / 2),
                             TDZ_LEN / 2, TDZ_WID / 2),
                comment=f"TDZ pair {d_from_thr:.0f} m (THR {'14' if direction>0 else '32'}, "
                        f"{'right' if side>0 else 'left'})",
            )
            count("tdz_stripe")


tdz_pairs(0.0, +1)
tdz_pairs(LENGTH, -1)


# --- §5.2.3  Centre line marking (dashed) --------------------------------
# Precision approach Cat I -> 0.45 m width. Stripe + gap cycle 50-75 m;
# common choice 30 m stripe + 30 m gap. Located between designation
# markings — i.e. inboard of the threshold marking + designator block.
# Threshold stripes end at THR_INSET + KEY_LEN = 36 m. Reserve another
# ~30 m for the designator block, so CL dashes start at ~72 m from threshold.
CL_WID = 0.45
CL_STRIPE = 30.0
CL_GAP = 30.0
CL_START_OFFSET = 72.0
cl_t_start = CL_START_OFFSET
cl_t_end = LENGTH - CL_START_OFFSET
t = cl_t_start
while t + CL_STRIPE <= cl_t_end:
    t_center = t + CL_STRIPE / 2
    emit_poly(
        rect_corners(t_center, 0.0, CL_STRIPE / 2, CL_WID / 2),
        comment=f"centre line dash @ t={t_center:.0f} m",
    )
    count("centerline_dash")
    t += CL_STRIPE + CL_GAP


# --- Summary on stderr ---------------------------------------------------
total = sum(counts.values())
print(f"// runway length: {LENGTH:.1f} m, bearing 14->32: "
      f"{(math.degrees(math.atan2(ux, uy)) + 360) % 360:.1f} deg true", file=sys.stderr)
print(f"// total polygons: {total}", file=sys.stderr)
for k in sorted(counts):
    print(f"//   {k}: {counts[k]}", file=sys.stderr)
print("// NOTE: runway designation markings (the '14' and '32' digits) are NOT", file=sys.stderr)
print("//       emitted — those require glyph-stroke geometry per Annex 14 Figure 5-3.", file=sys.stderr)
print("//       The 72 m gap before the centreline dashes leaves room for them if", file=sys.stderr)
print("//       authored separately.", file=sys.stderr)
