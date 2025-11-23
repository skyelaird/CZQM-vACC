#!/usr/bin/env python3
"""
CZQX Class G Airspace Calculator
Subtracts controlled airspace from CZQX FIR boundary (13,000-18,000 feet)
Outputs TopSky-formatted COORD lists
"""

from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
import math
import re


def parse_aviation_coord(coord_str):
    """
    Parse aviation coordinate format to decimal degrees.
    Examples:
        N052.57.36.381 W066.51.14.000
        N49°13'57.010" W057°12'46.890"
    """
    # Remove quotes and normalize separators
    coord_str = coord_str.replace('"', '').replace("'", '.')
    coord_str = coord_str.replace('°', '.')
    
    # Pattern: matches N/S followed by degrees.minutes.seconds(.fraction)
    # Handles both N45.00.00.00 and N52.57.36.381 formats
    lat_pattern = r'([NS])(\d+)\.(\d+)\.(\d+)\.?(\d*)'
    lon_pattern = r'([EW])(\d+)\.(\d+)\.(\d+)\.?(\d*)'
    
    lat_match = re.search(lat_pattern, coord_str)
    lon_match = re.search(lon_pattern, coord_str)
    
    if not lat_match or not lon_match:
        raise ValueError(f"Cannot parse coordinate: {coord_str}")
    
    # Parse latitude
    lat_dir = lat_match.group(1)
    lat_deg = int(lat_match.group(2))
    lat_min = int(lat_match.group(3))
    lat_sec_str = lat_match.group(4)
    lat_frac = lat_match.group(5) if lat_match.group(5) else '0'
    
    # Handle fractional seconds
    if lat_frac:
        lat_sec = float(f"{lat_sec_str}.{lat_frac}")
    else:
        lat_sec = float(lat_sec_str)
    
    lat = lat_deg + lat_min/60 + lat_sec/3600
    if lat_dir == 'S':
        lat = -lat
    
    # Parse longitude
    lon_dir = lon_match.group(1)
    lon_deg = int(lon_match.group(2))
    lon_min = int(lon_match.group(3))
    lon_sec_str = lon_match.group(4)
    lon_frac = lon_match.group(5) if lon_match.group(5) else '0'
    
    # Handle fractional seconds
    if lon_frac:
        lon_sec = float(f"{lon_sec_str}.{lon_frac}")
    else:
        lon_sec = float(lon_sec_str)
    
    lon = lon_deg + lon_min/60 + lon_sec/3600
    if lon_dir == 'W':
        lon = -lon
    
    return (lat, lon)


def decimal_to_topsky(lat, lon):
    """Convert decimal degrees to TopSky format: N052.57.36.381 W066.51.14.000"""
    # Latitude
    lat_dir = 'N' if lat >= 0 else 'S'
    lat_abs = abs(lat)
    lat_deg = int(lat_abs)
    lat_min = int((lat_abs - lat_deg) * 60)
    lat_sec = ((lat_abs - lat_deg) * 60 - lat_min) * 60
    
    # Longitude
    lon_dir = 'E' if lon >= 0 else 'W'
    lon_abs = abs(lon)
    lon_deg = int(lon_abs)
    lon_min = int((lon_abs - lon_deg) * 60)
    lon_sec = ((lon_abs - lon_deg) * 60 - lon_min) * 60
    
    return f"{lat_dir}{lat_deg:03d}.{lat_min:02d}.{lat_sec:06.3f}:{lon_dir}{lon_deg:03d}.{lon_min:02d}.{lon_sec:06.3f}"


def create_arc_points(center_lat, center_lon, radius_nm, start_bearing, end_bearing, num_points=20):
    """
    Create points along a circular arc.
    
    Args:
        center_lat, center_lon: Center point in decimal degrees
        radius_nm: Radius in nautical miles
        start_bearing: Starting bearing in degrees (clockwise from north)
        end_bearing: Ending bearing in degrees
        num_points: Number of points to generate along the arc
    
    Returns:
        List of (lat, lon) tuples
    """
    points = []
    
    # Normalize bearings to 0-360
    start_bearing = start_bearing % 360
    end_bearing = end_bearing % 360
    
    # Determine if we go clockwise or counter-clockwise
    if end_bearing > start_bearing:
        # Clockwise
        bearing_range = end_bearing - start_bearing
        bearings = [start_bearing + (bearing_range * i / (num_points - 1)) for i in range(num_points)]
    else:
        # Counter-clockwise (crosses 0)
        bearing_range = (360 - start_bearing) + end_bearing
        bearings = [(start_bearing + (bearing_range * i / (num_points - 1))) % 360 for i in range(num_points)]
    
    for bearing in bearings:
        # Convert to radians
        lat_rad = math.radians(center_lat)
        lon_rad = math.radians(center_lon)
        bearing_rad = math.radians(bearing)
        
        # Distance in radians (1 nm ≈ 1.852 km, Earth radius ≈ 6371 km)
        distance_rad = (radius_nm * 1.852) / 6371
        
        # Calculate new point
        new_lat = math.asin(
            math.sin(lat_rad) * math.cos(distance_rad) +
            math.cos(lat_rad) * math.sin(distance_rad) * math.cos(bearing_rad)
        )
        
        new_lon = lon_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(distance_rad) * math.cos(lat_rad),
            math.cos(distance_rad) - math.sin(lat_rad) * math.sin(new_lat)
        )
        
        points.append((math.degrees(new_lat), math.degrees(new_lon)))
    
    return points


def create_circle_polygon(center_lat, center_lon, radius_nm, num_points=36):
    """Create a circular polygon."""
    return create_arc_points(center_lat, center_lon, radius_nm, 0, 360, num_points)


def create_airway_corridor(waypoints, corridor_width_nm=5):
    """
    Create a corridor polygon around an airway centerline.
    
    Args:
        waypoints: List of (lat, lon) tuples defining the airway
        corridor_width_nm: Half-width of corridor in nautical miles (5nm = 10nm total width)
    
    Returns:
        Shapely Polygon
    """
    if len(waypoints) < 2:
        raise ValueError("Need at least 2 waypoints for airway")
    
    # Create LineString for the airway centerline
    line = LineString([(lon, lat) for lat, lon in waypoints])
    
    # Buffer the line (approximate: 1 degree ≈ 60 nm at equator, adjust for latitude)
    avg_lat = sum(lat for lat, lon in waypoints) / len(waypoints)
    km_per_degree = 111.32  # at equator
    nm_per_degree = km_per_degree / 1.852
    buffer_degrees = corridor_width_nm / (nm_per_degree * math.cos(math.radians(avg_lat)))
    
    buffered = line.buffer(buffer_degrees)
    return buffered


def main():
    print("CZQX Class G Airspace Calculator")
    print("=" * 60)
    
    # ========================================================================
    # 1. CZQX FIR BOUNDARY (from DAH Section 3.7.2-1)
    # ========================================================================
    print("\n1. Loading CZQX Gander Domestic FIR boundary...")
    
    fir_coords_raw = [
        "N45°00'00.00\" W051°00'00.00\"",
        "N45°00'00.00\" W053°00'00.00\"",
        "N44°26'48.00\" W056°03'06.00\"",
        "N45°36'43.00\" W056°28'25.00\"",
        "N48°30'00.00\" W062°00'00.00\"",
        "N49°18'00.00\" W061°00'00.00\"",
        "N49°32'00.00\" W061°00'00.00\"",
        "N51°00'00.00\" W058°00'00.00\"",
        "N51°17'00.00\" W057°00'00.00\"",
        "N51°44'06.00\" W057°00'00.00\"",
        "N52°11'47.00\" W058°08'34.00\"",
        "N51°38'00.00\" W059°30'00.00\"",
        "N51°20'00.00\" W059°30'00.00\"",
        "N50°50'00.00\" W060°00'00.00\"",
        "N50°50'00.00\" W062°05'00.00\"",
        "N51°25'00.00\" W064°00'00.00\"",
        "N53°42'00.00\" W064°55'00.00\"",
        "N54°25'00.00\" W065°20'00.00\"",
        "N55°05'00.00\" W065°05'00.00\"",
        "N55°21'20.00\" W064°00'00.00\"",
        "N57°33'00.00\" W064°00'00.00\"",
        "N58°28'16.00\" W060°21'04.00\"",
        "N57°00'00.00\" W059°00'00.00\"",
        "N53°00'00.00\" W054°00'00.00\"",
        "N49°00'00.00\" W051°00'00.00\"",
        "N45°00'00.00\" W051°00'00.00\"",
    ]
    
    fir_coords = [parse_aviation_coord(c) for c in fir_coords_raw]
    fir_polygon = Polygon([(lon, lat) for lat, lon in fir_coords])
    print(f"   FIR polygon: {len(fir_coords)} vertices")
    
    # ========================================================================
    # 2. CONTROLLED AIRSPACE TO SUBTRACT
    # ========================================================================
    controlled_polygons = []
    
    # CAE Number One (DAH 3.7.4-4)
    print("\n2. Creating CAE Number One...")
    cae1_coords_raw = [
        "N47°29'07.00\" W052°51'08.00\"",  # Torbay VOR
        "N46°00'00.00\" W051°00'00.00\"",
        "N52°00'00.00\" W053°12'00.00\"",
        "N48°53'59.00\" W054°32'06.00\"",  # Gander VOR
        "N47°29'07.00\" W052°51'08.00\"",  # Close polygon
    ]
    cae1_coords = [parse_aviation_coord(c) for c in cae1_coords_raw]
    cae1_polygon = Polygon([(lon, lat) for lat, lon in cae1_coords])
    controlled_polygons.append(cae1_polygon)
    print(f"   CAE #1: {len(cae1_coords)} vertices")
    
    # CAE Number Thirteen (DAH 3.7.4-6) - 7 vertices + 3 arcs
    print("\n3. Creating CAE Number Thirteen...")
    cae13_vertices = [
        parse_aviation_coord("N53°58'47.00\" W062°32'58.00\""),
        parse_aviation_coord("N57°19'13.00\" W059°35'11.00\""),
    ]
    
    # Arc 1: 15nm radius centered on Prawn (clockwise)
    prawn_center = parse_aviation_coord("N57°12'12.00\" W059°10'48.00\"")
    arc1_end = parse_aviation_coord("N57°21'14.52\" W058°48'43.28\"")
    arc1_points = create_arc_points(prawn_center[0], prawn_center[1], 15, 
                                     calculate_bearing(prawn_center, cae13_vertices[-1]),
                                     calculate_bearing(prawn_center, arc1_end), 10)
    
    cae13_coords = cae13_vertices + arc1_points + [
        parse_aviation_coord("N54°00'18.27\" W054°36'50.15\""),
    ]
    
    # Arc 2: 15nm radius (clockwise)
    arc2_center = parse_aviation_coord("N53°52'00.00\" W054°58'00.00\"")
    arc2_end = parse_aviation_coord("N53°38'52.35\" W054°45'49.12\"")
    arc2_points = create_arc_points(arc2_center[0], arc2_center[1], 15,
                                     calculate_bearing(arc2_center, cae13_coords[-1]),
                                     calculate_bearing(arc2_center, arc2_end), 10)
    cae13_coords.extend(arc2_points)
    cae13_coords.append(parse_aviation_coord("N52°07'07.82\" W059°04'51.74\""))
    
    # Arc 3: 87nm radius centered on Goose Bay NDB (counter-clockwise)
    goose_center = parse_aviation_coord("N53°20'16.00\" W060°21'57.00\"")
    arc3_points = create_arc_points(goose_center[0], goose_center[1], 87,
                                     calculate_bearing(goose_center, cae13_coords[-1]),
                                     calculate_bearing(goose_center, cae13_vertices[0]), 20)
    cae13_coords.extend(arc3_points)
    
    cae13_polygon = Polygon([(lon, lat) for lat, lon in cae13_coords])
    controlled_polygons.append(cae13_polygon)
    print(f"   CAE #13: {len(cae13_coords)} vertices (with discretized arcs)")
    
    # NEWFOUNDLAND CAE (DAH 3.7.4-8) - 9 vertices + 3 arcs
    print("\n4. Creating NEWFOUNDLAND CAE...")
    nfld_vertices = [
        parse_aviation_coord("N48°30'00.00\" W062°00'00.00\""),
        parse_aviation_coord("N50°02'00.22\" W058°15'24.06\""),
    ]
    
    # Arc 1: 60nm radius (clockwise)
    nfld_arc1_center = parse_aviation_coord("N49°10'48.00\" W057°27'26.00\"")
    nfld_arc1_end = parse_aviation_coord("N50°10'15.81\" W057°15'45.25\"")
    nfld_arc1_points = create_arc_points(nfld_arc1_center[0], nfld_arc1_center[1], 60,
                                          calculate_bearing(nfld_arc1_center, nfld_vertices[-1]),
                                          calculate_bearing(nfld_arc1_center, nfld_arc1_end), 15)
    nfld_coords = nfld_vertices + nfld_arc1_points
    nfld_coords.append(parse_aviation_coord("N49°53'06.49\" W054°16'56.19\""))
    
    # Arc 2: 60nm radius centered on Gander VOR (clockwise)
    gander_vor = parse_aviation_coord("N48°53'59.00\" W054°32'06.00\"")
    nfld_arc2_end = parse_aviation_coord("N49°35'09.00\" W053°25'32.17\"")
    nfld_arc2_points = create_arc_points(gander_vor[0], gander_vor[1], 60,
                                          calculate_bearing(gander_vor, nfld_coords[-1]),
                                          calculate_bearing(gander_vor, nfld_arc2_end), 15)
    nfld_coords.extend(nfld_arc2_points)
    nfld_coords.append(parse_aviation_coord("N48°20'22.01\" W051°42'10.78\""))
    
    # Arc 3: 60nm radius (clockwise)
    nfld_arc3_center = parse_aviation_coord("N47°40'11.00\" W052°48'30.00\"")
    nfld_arc3_end = parse_aviation_coord("N46°41'28.30\" W052°30'34.21\"")
    nfld_arc3_points = create_arc_points(nfld_arc3_center[0], nfld_arc3_center[1], 60,
                                          calculate_bearing(nfld_arc3_center, nfld_coords[-1]),
                                          calculate_bearing(nfld_arc3_center, nfld_arc3_end), 15)
    nfld_coords.extend(nfld_arc3_points)
    nfld_coords.extend([
        parse_aviation_coord("N45°56'43.45\" W057°03'28.92\""),
        parse_aviation_coord("N48°30'00.00\" W062°00'00.00\""),
    ])
    
    nfld_polygon = Polygon([(lon, lat) for lat, lon in nfld_coords])
    controlled_polygons.append(nfld_polygon)
    print(f"   NFLD CAE: {len(nfld_coords)} vertices (with discretized arcs)")
    
    # St. Anthony CAE (DAH 3.7.4-10) - 3 vertices + 1 arc
    print("\n5. Creating St. Anthony CAE...")
    st_anthony_ad = parse_aviation_coord("N51°23'30.00\" W056°05'04.00\"")
    sta_vertices = [
        parse_aviation_coord("N51°44'05.00\" W056°40'00.00\""),
    ]
    
    # 30nm arc (clockwise)
    sta_arc_end = parse_aviation_coord("N51°03'05.00\" W056°40'00.00\"")
    sta_arc_points = create_arc_points(st_anthony_ad[0], st_anthony_ad[1], 30,
                                        calculate_bearing(st_anthony_ad, sta_vertices[0]),
                                        calculate_bearing(st_anthony_ad, sta_arc_end), 20)
    sta_coords = sta_vertices + sta_arc_points + [
        sta_arc_end,
        sta_vertices[0],  # Close polygon
    ]
    
    sta_polygon = Polygon([(lon, lat) for lat, lon in sta_coords])
    controlled_polygons.append(sta_polygon)
    print(f"   St. Anthony CAE: {len(sta_coords)} vertices (with discretized arc)")
    
    # Goose Bay MTCA (DAH 3.7.5-8) - 87nm circle
    print("\n6. Creating Goose Bay MTCA (87nm circle)...")
    goose_circle_coords = create_circle_polygon(goose_center[0], goose_center[1], 87, 36)
    goose_polygon = Polygon([(lon, lat) for lat, lon in goose_circle_coords])
    controlled_polygons.append(goose_polygon)
    print(f"   Goose Bay MTCA: {len(goose_circle_coords)} vertices")
    
    # ========================================================================
    # 3. AIRWAYS (5nm corridors each side)
    # ========================================================================
    print("\n7. Creating airway corridors (5nm each side)...")
    
    waypoints = {
        'YWK': parse_aviation_coord("N052.57.36.381 W066.51.14.000"),
        'DENSO': parse_aviation_coord("N053.35.26.001 W064.14.08.001"),
        'YYR': parse_aviation_coord("N053.19.10.628 W060.17.38.389"),
        'YAY': parse_aviation_coord("N051.23.38.108 W056.05.01.500"),
        'YDF': parse_aviation_coord("N049.13.57.010 W057.12.46.890"),
        'YQX': parse_aviation_coord("N048.53.58.920 W054.32.05.578"),
        'PEKRO': parse_aviation_coord("N53°09'23\" W064°06'09\""),
    }
    
    airways = {
        'V381': [waypoints['YAY'], waypoints['YDF']],
        'V315': [waypoints['YAY'], waypoints['YQX']],
        'T604': [waypoints['YWK'], waypoints['PEKRO'], waypoints['YYR']],
        'T697': [waypoints['YWK'], waypoints['DENSO'], waypoints['YYR']],
    }
    
    for airway_name, airway_waypoints in airways.items():
        airway_polygon = create_airway_corridor(airway_waypoints, corridor_width_nm=5)
        controlled_polygons.append(airway_polygon)
        print(f"   {airway_name}: {len(airway_waypoints)} waypoints")
    
    # ========================================================================
    # 4. UNION ALL CONTROLLED AIRSPACE
    # ========================================================================
    print("\n8. Computing union of all controlled airspace...")
    controlled_union = unary_union(controlled_polygons)
    print(f"   Union complete: {type(controlled_union).__name__}")
    
    # ========================================================================
    # 5. SUBTRACT FROM FIR
    # ========================================================================
    print("\n9. Computing Class G = FIR - Controlled...")
    class_g = fir_polygon.difference(controlled_union)
    print(f"   Result: {type(class_g).__name__}")
    
    # ========================================================================
    # 6. EXPORT TO TOPSKY FORMAT
    # ========================================================================
    print("\n10. Exporting to TopSky format...")
    
    output_lines = []
    output_lines.append("; CZQX Class G Airspace (13,000-18,000 feet)")
    output_lines.append("; Generated by czqx_class_g_calculator.py")
    output_lines.append("; Subtract controlled airspace from CZQX Gander Domestic FIR")
    output_lines.append("")
    
    # Handle MultiPolygon (if result is fragmented) or Polygon
    if class_g.geom_type == 'Polygon':
        polygons_to_export = [class_g]
    elif class_g.geom_type == 'MultiPolygon':
        polygons_to_export = list(class_g.geoms)
        print(f"   Result is MultiPolygon with {len(polygons_to_export)} parts")
    else:
        print(f"   WARNING: Unexpected geometry type: {class_g.geom_type}")
        polygons_to_export = []
    
    for idx, poly in enumerate(polygons_to_export):
        output_lines.append(f"MAP:CZQX-CLASS-G-PART{idx+1}")
        output_lines.append("FOLDER:CLASS-G")
        output_lines.append("LAYER:0")
        output_lines.append("COLOR:UNCONTROLLED_STATIC")
        output_lines.append("ACTIVE:ID::")
        
        # Get exterior coordinates (Shapely stores as (x, y) = (lon, lat))
        coords = list(poly.exterior.coords)
        for lon, lat in coords[:-1]:  # Skip last point (same as first)
            output_lines.append(f"COORD:{decimal_to_topsky(lat, lon)}")
        
        output_lines.append("COORDPOLY:0")
        output_lines.append("")
    
    # Write to file
    output_file = "/home/claude/czqx_class_g_output.txt"
    with open(output_file, 'w') as f:
        f.write('\n'.join(output_lines))
    
    print(f"\n✓ Output written to: {output_file}")
    print(f"✓ Total polygons: {len(polygons_to_export)}")
    print(f"✓ Ready for TopSkyMaps.txt integration")
    
    return output_file


def calculate_bearing(point1, point2):
    """Calculate initial bearing from point1 to point2 in degrees."""
    lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
    lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])
    
    dlon = lon2 - lon1
    
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    
    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing


if __name__ == "__main__":
    try:
        output_file = main()
        print("\n" + "=" * 60)
        print("SUCCESS: Class G airspace calculation complete!")
        print("=" * 60)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
