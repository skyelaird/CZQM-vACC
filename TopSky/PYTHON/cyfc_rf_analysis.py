#!/usr/bin/env python3
"""
Analyze CYFC RNAV Y Rwy 09 RF arc transitions.
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

def test_rf_arc_radius(start_lat, start_lon, end_lat, end_lon,
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
    
    dist_center_to_end = distance_nm(center_lat, center_lon, end_lat, end_lon)
    error = abs(dist_center_to_end - radius_nm)
    
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

def analyze_transition(waypoints_list, coords_dict, transition_name):
    """Analyze a complete transition to identify potential RF arcs."""
    print(f"\n{'='*80}")
    print(f"{transition_name}")
    print(f"{'='*80}")
    
    test_radii = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0]
    
    for i in range(len(waypoints_list) - 1):
        fix1 = waypoints_list[i]
        fix2 = waypoints_list[i + 1]
        
        lat1, lon1 = coords_dict[fix1]
        lat2, lon2 = coords_dict[fix2]
        
        bearing = bearing_between_points(lat1, lon1, lat2, lon2)
        distance = distance_nm(lat1, lon1, lat2, lon2)
        
        print(f"\n{fix1} to {fix2}:")
        print(f"  Bearing: {bearing:.2f}°")
        print(f"  Distance: {distance:.2f} NM")
        
        # Check if this might be an RF arc by looking at the next leg
        if i < len(waypoints_list) - 2:
            fix3 = waypoints_list[i + 2]
            lat3, lon3 = coords_dict[fix3]
            
            # Calculate track change
            next_bearing = bearing_between_points(lat2, lon2, lat3, lon3)
            track_change = (next_bearing - bearing) % 360
            if track_change > 180:
                track_change = 360 - track_change
                turn_dir = 'L'
            else:
                turn_dir = 'R'
            
            print(f"  Next leg {fix2}-{fix3}: {next_bearing:.2f}°")
            print(f"  Track change: {track_change:.2f}° ({turn_dir} turn)")
            
            # If significant track change, this might be an RF arc
            if track_change > 10:
                print(f"\n  Possible RF arc from {fix2} to {fix3}:")
                print(f"  Testing radii (Turn direction: L and R):\n")
                
                for turn_direction in ['L', 'R']:
                    results = []
                    for radius in test_radii:
                        result = test_rf_arc_radius(
                            lat2, lon2, lat3, lon3,
                            bearing, turn_direction, radius
                        )
                        results.append(result)
                    
                    best = min(results, key=lambda x: x['error'])
                    if best['error'] < 0.5 and best['sweep'] < 270:  # Reasonable arc
                        print(f"    {turn_direction} turn: Best radius = {best['radius']:.1f} NM, "
                              f"error = {best['error']:.3f} NM, sweep = {best['sweep']:.1f}°")

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
    print(f"{name}: {lat:.6f}, {lon:.6f}")

# Analyze transitions
analyze_transition(['VESBI', 'UKNUM', 'URTIT', 'VYSTA'], coords, 
                   "Transition 1: VESBI - UKNUM - URTIT - VYSTA")
analyze_transition(['ANERA', 'URPUS', 'VYSTA'], coords,
                   "Transition 2: ANERA - URPUS - VYSTA")

print("\n" + "="*80)
print("DETAILED RF ARC ANALYSIS")
print("="*80)

# Now do detailed analysis of confirmed RF arcs
# Based on the preliminary scan, identify which legs are likely RF

# Transition 1: Check UKNUM-URTIT-VYSTA
vesbi_lat, vesbi_lon = coords['VESBI']
uknum_lat, uknum_lon = coords['UKNUM']
urtit_lat, urtit_lon = coords['URTIT']
vysta_lat, vysta_lon = coords['VYSTA']

vesbi_uknum_track = bearing_between_points(vesbi_lat, vesbi_lon, uknum_lat, uknum_lon)
uknum_urtit_track = bearing_between_points(uknum_lat, uknum_lon, urtit_lat, urtit_lon)
urtit_vysta_track = bearing_between_points(urtit_lat, urtit_lon, vysta_lat, vysta_lon)

print(f"\nTransition 1 Track Analysis:")
print(f"  VESBI-UKNUM: {vesbi_uknum_track:.2f}°")
print(f"  UKNUM-URTIT: {uknum_urtit_track:.2f}°")
print(f"  URTIT-VYSTA: {urtit_vysta_track:.2f}°")

# Transition 2: Check ANERA-URPUS-VYSTA
anera_lat, anera_lon = coords['ANERA']
urpus_lat, urpus_lon = coords['URPUS']

anera_urpus_track = bearing_between_points(anera_lat, anera_lon, urpus_lat, urpus_lon)
urpus_vysta_track = bearing_between_points(urpus_lat, urpus_lon, vysta_lat, vysta_lon)

print(f"\nTransition 2 Track Analysis:")
print(f"  ANERA-URPUS: {anera_urpus_track:.2f}°")
print(f"  URPUS-VYSTA: {urpus_vysta_track:.2f}°")

print("\n" + "="*80)
