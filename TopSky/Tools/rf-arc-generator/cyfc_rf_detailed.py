#!/usr/bin/env python3
"""
Calculate detailed RF arc parameters for CYFC RNAV Y Rwy 09.
"""

import math

def dms_to_decimal(dms_string):
    """Convert sector file format to decimal degrees."""
    direction = dms_string[0]
    parts = dms_string[1:].split('.')
    
    degrees = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2] + '.' + parts[3])
    
    decimal = degrees + minutes/60.0 + seconds/3600.0
    
    if direction in ['W', 'S']:
        decimal = -decimal
    
    return decimal

def bearing_between_points(lat1, lon1, lat2, lon2):
    """Calculate true bearing from point 1 to point 2."""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)
    
    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - \
        math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
    
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360

def distance_nm(lat1, lon1, lat2, lon2):
    """Calculate distance in nautical miles."""
    R = 3440.065
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat_rad = math.radians(lat2 - lat1)
    dlon_rad = math.radians(lon2 - lon1)
    
    a = math.sin(dlat_rad/2)**2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon_rad/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def point_at_bearing_distance(lat, lon, bearing, distance_nm):
    """Calculate a point at given bearing and distance."""
    R = 3440.065
    
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing)
    
    lat2_rad = math.asin(
        math.sin(lat_rad) * math.cos(distance_nm/R) +
        math.cos(lat_rad) * math.sin(distance_nm/R) * math.cos(bearing_rad)
    )
    
    lon2_rad = lon_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(distance_nm/R) * math.cos(lat_rad),
        math.cos(distance_nm/R) - math.sin(lat_rad) * math.sin(lat2_rad)
    )
    
    return math.degrees(lat2_rad), math.degrees(lon2_rad)

def calculate_rf_arc_details(start_name, start_lat, start_lon,
                             end_name, end_lat, end_lon,
                             entry_bearing, turn_direction, radius_nm):
    """Calculate complete RF arc parameters."""
    
    if turn_direction == 'L':
        direction_symbol = '<'
        perpendicular_offset = -90
    else:
        direction_symbol = '>'
        perpendicular_offset = +90
    
    center_bearing = (entry_bearing + perpendicular_offset) % 360
    center_lat, center_lon = point_at_bearing_distance(
        start_lat, start_lon, center_bearing, radius_nm
    )
    
    dist_center_to_start = distance_nm(center_lat, center_lon, start_lat, start_lon)
    dist_center_to_end = distance_nm(center_lat, center_lon, end_lat, end_lon)
    
    start_angle = bearing_between_points(center_lat, center_lon, start_lat, start_lon)
    end_angle = bearing_between_points(center_lat, center_lon, end_lat, end_lon)
    
    if turn_direction == 'L':
        if end_angle > start_angle:
            sweep = start_angle + (360 - end_angle)
        else:
            sweep = start_angle - end_angle
    else:
        if end_angle < start_angle:
            sweep = (360 - start_angle) + end_angle
        else:
            sweep = end_angle - start_angle
    
    return {
        'start_fix': start_name,
        'end_fix': end_name,
        'center_lat': center_lat,
        'center_lon': center_lon,
        'radius': radius_nm,
        'start_angle': start_angle,
        'end_angle': end_angle,
        'sweep': sweep,
        'direction': direction_symbol,
        'error_start': abs(dist_center_to_start - radius_nm),
        'error_end': abs(dist_center_to_end - radius_nm)
    }

def format_topsky_coord_af(arc_params, spacing=1.0):
    """Format a COORD_AF line for TopSky."""
    lat = arc_params['center_lat']
    lon = arc_params['center_lon']
    
    lat_ns = 'N' if lat >= 0 else 'S'
    lon_ew = 'E' if lon >= 0 else 'W'
    
    lat_abs = abs(lat)
    lon_abs = abs(lon)
    
    lat_d = int(lat_abs)
    lat_m = int((lat_abs - lat_d) * 60)
    lat_s = ((lat_abs - lat_d) * 60 - lat_m) * 60
    
    lon_d = int(lon_abs)
    lon_m = int((lon_abs - lon_d) * 60)
    lon_s = ((lon_abs - lon_d) * 60 - lon_m) * 60
    
    lat_str = f"{lat_ns}{lat_d:03d}.{lat_m:02d}.{lat_s:06.3f}"
    lon_str = f"{lon_ew}{lon_d:03d}.{lon_m:02d}.{lon_s:06.3f}"
    
    line = f"COORD_AF:{lat_str}:{lon_str}:{arc_params['radius']:.1f}:{spacing}:"
    line += f"{arc_params['start_angle']:.1f}:{arc_params['direction']}:{arc_params['end_angle']:.1f}"
    
    return line

# ===== MAIN =====

waypoints = {
    'ANERA': ('N045.39.40.611', 'W066.44.52.800'),
    'UKNUM': ('N045.55.20.308', 'W066.40.01.801'),
    'URPUS': ('N045.49.11.870', 'W066.39.39.819'),
    'URTIT': ('N045.50.44.368', 'W066.40.20.539'),
    'VESBI': ('N045.56.53.361', 'W066.33.58.651'),
    'VYSTA': ('N045.50.38.810', 'W066.37.33.610'),
}

coords = {}
for name, (lat_str, lon_str) in waypoints.items():
    lat = dms_to_decimal(lat_str)
    lon = dms_to_decimal(lon_str)
    coords[name] = (lat, lon)

print("="*80)
print("CYFC RNAV Y RWY 09 - RF ARC CALCULATIONS")
print("="*80)

# Arc 1: UKNUM to URTIT
print("\n" + "="*80)
print("Arc 1: UKNUM to URTIT")
print("="*80)

vesbi_lat, vesbi_lon = coords['VESBI']
uknum_lat, uknum_lon = coords['UKNUM']
urtit_lat, urtit_lon = coords['URTIT']

vesbi_uknum_track = bearing_between_points(vesbi_lat, vesbi_lon, uknum_lat, uknum_lon)

arc1 = calculate_rf_arc_details(
    'UKNUM', uknum_lat, uknum_lon,
    'URTIT', urtit_lat, urtit_lon,
    vesbi_uknum_track, 'L', 2.5
)

print(f"Entry track (VESBI-UKNUM): {vesbi_uknum_track:.2f}°")
print(f"Arc radius: {arc1['radius']} NM")
print(f"Arc center: {arc1['center_lat']:.6f}, {arc1['center_lon']:.6f}")
print(f"Start angle: {arc1['start_angle']:.2f}°")
print(f"End angle: {arc1['end_angle']:.2f}°")
print(f"Sweep: {arc1['sweep']:.2f}°")
print(f"Direction: {arc1['direction']} (counterclockwise)")
print(f"Verification - Start error: {arc1['error_start']:.3f} NM")
print(f"Verification - End error: {arc1['error_end']:.3f} NM")
print(f"\nTopSky COORD_AF:")
print(format_topsky_coord_af(arc1))

# Arc 2: URTIT to VYSTA
print("\n" + "="*80)
print("Arc 2: URTIT to VYSTA")
print("="*80)

vysta_lat, vysta_lon = coords['VYSTA']
uknum_urtit_track = bearing_between_points(uknum_lat, uknum_lon, urtit_lat, urtit_lon)

arc2 = calculate_rf_arc_details(
    'URTIT', urtit_lat, urtit_lon,
    'VYSTA', vysta_lat, vysta_lon,
    uknum_urtit_track, 'L', 1.0
)

print(f"Entry track (UKNUM-URTIT): {uknum_urtit_track:.2f}°")
print(f"Arc radius: {arc2['radius']} NM")
print(f"Arc center: {arc2['center_lat']:.6f}, {arc2['center_lon']:.6f}")
print(f"Start angle: {arc2['start_angle']:.2f}°")
print(f"End angle: {arc2['end_angle']:.2f}°")
print(f"Sweep: {arc2['sweep']:.2f}°")
print(f"Direction: {arc2['direction']} (counterclockwise)")
print(f"Verification - Start error: {arc2['error_start']:.3f} NM")
print(f"Verification - End error: {arc2['error_end']:.3f} NM")
print(f"\nTopSky COORD_AF:")
print(format_topsky_coord_af(arc2))

# Arc 3: URPUS to VYSTA
print("\n" + "="*80)
print("Arc 3: URPUS to VYSTA")
print("="*80)

anera_lat, anera_lon = coords['ANERA']
urpus_lat, urpus_lon = coords['URPUS']

anera_urpus_track = bearing_between_points(anera_lat, anera_lon, urpus_lat, urpus_lon)

arc3 = calculate_rf_arc_details(
    'URPUS', urpus_lat, urpus_lon,
    'VYSTA', vysta_lat, vysta_lon,
    anera_urpus_track, 'R', 2.5
)

print(f"Entry track (ANERA-URPUS): {anera_urpus_track:.2f}°")
print(f"Arc radius: {arc3['radius']} NM")
print(f"Arc center: {arc3['center_lat']:.6f}, {arc3['center_lon']:.6f}")
print(f"Start angle: {arc3['start_angle']:.2f}°")
print(f"End angle: {arc3['end_angle']:.2f}°")
print(f"Sweep: {arc3['sweep']:.2f}°")
print(f"Direction: {arc3['direction']} (clockwise)")
print(f"Verification - Start error: {arc3['error_start']:.3f} NM")
print(f"Verification - End error: {arc3['error_end']:.3f} NM")
print(f"\nTopSky COORD_AF:")
print(format_topsky_coord_af(arc3))

print("\n" + "="*80)
