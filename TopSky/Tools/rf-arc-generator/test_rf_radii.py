#!/usr/bin/env python3
"""
Calculate RF (Radius to Fix) arc parameters for RNAV approaches using standard radii.
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
    """Calculate distance in nautical miles between two points."""
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

def test_rf_arc_radius(start_fix_name, start_lat, start_lon,
                       end_fix_name, end_lat, end_lon,
                       entry_bearing, turn_direction, radius_nm):
    """Test an RF arc with a specific radius."""
    
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
    
    # Check how close the end point is to the arc
    dist_center_to_end = distance_nm(center_lat, center_lon, end_lat, end_lon)
    error = abs(dist_center_to_end - radius_nm)
    
    # Calculate angles
    start_angle = bearing_between_points(center_lat, center_lon, start_lat, start_lon)
    end_angle = bearing_between_points(center_lat, center_lon, end_lat, end_lon)
    
    # Calculate sweep
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
        'radius': radius_nm,
        'center_lat': center_lat,
        'center_lon': center_lon,
        'error': error,
        'start_angle': start_angle,
        'end_angle': end_angle,
        'sweep': sweep,
        'direction': direction_symbol,
        'dist_to_end': dist_center_to_end
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

# ===== MAIN PROCESSING =====

waypoints = {
    'GOSUG': ('N044.53.13.919', 'W063.45.00.619'),
    'ETMEP': ('N044.48.38.919', 'W063.40.44.270'),
    'LOPMA': ('N044.48.35.661', 'W063.34.55.930'),
    'PEPTA': ('N044.47.36.211', 'W063.27.19.731'),
    'AVIGU': ('N044.45.43.329', 'W063.29.11.140'),
}

coords = {}
for name, (lat_str, lon_str) in waypoints.items():
    lat = dms_to_decimal(lat_str)
    lon = dms_to_decimal(lon_str)
    coords[name] = (lat, lon)

print("="*80)
print("TESTING STANDARD RF ARC RADII")
print("="*80)

# Test radii in NM (typical values for RNAV procedures)
test_radii = [1.0, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0]

# ===== GOSUG - ETMEP - LOPMA =====
gosug_lat, gosug_lon = coords['GOSUG']
etmep_lat, etmep_lon = coords['ETMEP']
lopma_lat, lopma_lon = coords['LOPMA']

gosug_etmep_track = bearing_between_points(gosug_lat, gosug_lon, etmep_lat, etmep_lon)
etmep_lopma_direct = bearing_between_points(etmep_lat, etmep_lon, lopma_lat, lopma_lon)
etmep_lopma_dist = distance_nm(etmep_lat, etmep_lon, lopma_lat, lopma_lon)

print(f"\n{'='*80}")
print("ETMEP to LOPMA RF Arc")
print(f"{'='*80}")
print(f"Entry track (GOSUG-ETMEP): {gosug_etmep_track:.2f}°")
print(f"Direct bearing ETMEP-LOPMA: {etmep_lopma_direct:.2f}°")
print(f"Direct distance: {etmep_lopma_dist:.2f} NM")
print(f"\nTesting different radii (Turn direction: LEFT):\n")

print(f"{'Radius':>7} {'Error':>8} {'Sweep':>7} {'Center Lat':>12} {'Center Lon':>13} {'Dist to End':>12}")
print("-"*80)

etmep_results = []
for radius in test_radii:
    result = test_rf_arc_radius(
        'ETMEP', etmep_lat, etmep_lon,
        'LOPMA', lopma_lat, lopma_lon,
        gosug_etmep_track, 'L', radius
    )
    etmep_results.append(result)
    print(f"{radius:7.1f} {result['error']:8.3f} {result['sweep']:7.2f}° "
          f"{result['center_lat']:12.6f} {result['center_lon']:13.6f} {result['dist_to_end']:12.3f}")

# Find best radius
best_etmep = min(etmep_results, key=lambda x: x['error'])
print(f"\nBest fit: {best_etmep['radius']:.1f} NM (error: {best_etmep['error']:.3f} NM)")
print(f"\nTopSky COORD_AF command:")
print(format_topsky_coord_af(best_etmep))

# ===== PEPTA - AVIGU - LOPMA =====
pepta_lat, pepta_lon = coords['PEPTA']
avigu_lat, avigu_lon = coords['AVIGU']

pepta_avigu_track = bearing_between_points(pepta_lat, pepta_lon, avigu_lat, avigu_lon)
avigu_lopma_direct = bearing_between_points(avigu_lat, avigu_lon, lopma_lat, lopma_lon)
avigu_lopma_dist = distance_nm(avigu_lat, avigu_lon, lopma_lat, lopma_lon)

print(f"\n{'='*80}")
print("AVIGU to LOPMA RF Arc")
print(f"{'='*80}")
print(f"Entry track (PEPTA-AVIGU): {pepta_avigu_track:.2f}°")
print(f"Direct bearing AVIGU-LOPMA: {avigu_lopma_direct:.2f}°")
print(f"Direct distance: {avigu_lopma_dist:.2f} NM")

# Test both LEFT and RIGHT turns
for turn_dir in ['L', 'R']:
    print(f"\nTesting different radii (Turn direction: {turn_dir}):\n")
    print(f"{'Radius':>7} {'Error':>8} {'Sweep':>7} {'Center Lat':>12} {'Center Lon':>13} {'Dist to End':>12}")
    print("-"*80)
    
    avigu_results = []
    for radius in test_radii:
        result = test_rf_arc_radius(
            'AVIGU', avigu_lat, avigu_lon,
            'LOPMA', lopma_lat, lopma_lon,
            pepta_avigu_track, turn_dir, radius
        )
        avigu_results.append(result)
        print(f"{radius:7.1f} {result['error']:8.3f} {result['sweep']:7.2f}° "
              f"{result['center_lat']:12.6f} {result['center_lon']:13.6f} {result['dist_to_end']:12.3f}")
    
    best_avigu = min(avigu_results, key=lambda x: x['error'])
    print(f"\nBest fit ({turn_dir}): {best_avigu['radius']:.1f} NM (error: {best_avigu['error']:.3f} NM, sweep: {best_avigu['sweep']:.1f}°)")
    if turn_dir == 'R' or (turn_dir == 'L' and best_avigu['sweep'] < 180):  # Only show reasonable arcs
        print(f"\nTopSky COORD_AF command:")
        print(format_topsky_coord_af(best_avigu))

print(f"\n{'='*80}")
