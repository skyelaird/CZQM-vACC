#!/usr/bin/env python3
"""
TopSky RF Arc Generator
Analyzes RNAV approach procedures and generates TopSky map definitions with RF arcs.

Author: Joel Lavoie - VATCAN CZQM vACC
Based on analysis of CYHZ and CYFC RNAV approaches
"""

import math
import os
import sys
from typing import Dict, List, Tuple, Optional

# ============================================================================
# GEOMETRY FUNCTIONS
# ============================================================================

def dms_to_decimal(dms_string: str) -> float:
    """Convert sector file format (N044.53.13.919) to decimal degrees."""
    direction = dms_string[0]
    parts = dms_string[1:].split('.')
    
    degrees = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2] + '.' + parts[3])
    
    decimal = degrees + minutes/60.0 + seconds/3600.0
    
    if direction in ['W', 'S']:
        decimal = -decimal
    
    return decimal

def decimal_to_dms(decimal: float, is_latitude: bool) -> str:
    """Convert decimal degrees to sector file format."""
    if is_latitude:
        direction = 'N' if decimal >= 0 else 'S'
    else:
        direction = 'E' if decimal >= 0 else 'W'
    
    decimal_abs = abs(decimal)
    degrees = int(decimal_abs)
    minutes_decimal = (decimal_abs - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = (minutes_decimal - minutes) * 60
    
    return f"{direction}{degrees:03d}.{minutes:02d}.{seconds:06.3f}"

def bearing_between_points(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate true bearing from point 1 to point 2."""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)
    
    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - \
        math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
    
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360

def distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in nautical miles between two points."""
    R = 3440.065  # Earth radius in nautical miles
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat_rad = math.radians(lat2 - lat1)
    dlon_rad = math.radians(lon2 - lon1)
    
    a = math.sin(dlat_rad/2)**2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon_rad/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def point_at_bearing_distance(lat: float, lon: float, bearing: float, distance_nm: float) -> Tuple[float, float]:
    """Calculate a point at given bearing and distance from a starting point."""
    R = 3440.065  # Earth radius in nautical miles
    
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

# ============================================================================
# RF ARC DETECTION AND CALCULATION
# ============================================================================

def determine_turn_toward_airport(
    waypoint_lat: float, waypoint_lon: float,
    entry_track: float,
    airport_lat: float, airport_lon: float
) -> str:
    """
    Determine if turn should be LEFT or RIGHT to curve toward airport.
    
    KEY INSIGHT: RF arcs on approaches always curve TOWARD the airport!
    
    Logic: If airport is to the right of entry track, turn RIGHT.
           If airport is to the left of entry track, turn LEFT.
    """
    # Bearing from waypoint to airport
    bearing_to_airport = bearing_between_points(
        waypoint_lat, waypoint_lon,
        airport_lat, airport_lon
    )
    
    # Calculate relative bearing (where airport is relative to entry track)
    relative_bearing = (bearing_to_airport - entry_track) % 360
    
    # If airport is 0-180° to the right of track, turn RIGHT
    # If airport is 180-360° (i.e., to the left), turn LEFT
    if relative_bearing < 180:
        return 'R'
    else:
        return 'L'

def calculate_arc_center_fix(
    initial_fix_lat: float, initial_fix_lon: float,
    ending_fix_lat: float, ending_fix_lon: float,
    entry_track_bearing: float,
    turn_direction: str
) -> Dict:
    """
    Calculate the arc center fix for an RF leg using Transport Canada method.
    
    Per Transport Canada:
    "The RF leg is defined by the arc centre fix, the arc initial fix, the arc ending 
    fix and the turn direction. The radius is calculated by the navigation computer as 
    the distance from the arc centre fix to the arc ending fix."
    
    The center must be:
    1. Perpendicular to entry track from initial fix (tangency)
    2. Equidistant from both initial and ending fixes (both on circle)
    """
    
    if turn_direction == 'L':
        perpendicular_bearing = (entry_track_bearing - 90) % 360
        direction_symbol = '<'
    else:
        perpendicular_bearing = (entry_track_bearing + 90) % 360
        direction_symbol = '>'
    
    # Binary search for radius where center is equidistant from both points
    min_r = 0.1
    max_r = 50.0
    tolerance = 0.001  # 0.001 NM ≈ 6 feet
    
    best_r = None
    for iteration in range(100):
        mid_r = (min_r + max_r) / 2
        
        center_lat, center_lon = point_at_bearing_distance(
            initial_fix_lat, initial_fix_lon,
            perpendicular_bearing,
            mid_r
        )
        
        dist_to_ending = distance_nm(center_lat, center_lon, 
                                     ending_fix_lat, ending_fix_lon)
        error = dist_to_ending - mid_r
        
        if abs(error) < tolerance:
            best_r = mid_r
            break
        
        if dist_to_ending > mid_r:
            min_r = mid_r
        else:
            max_r = mid_r
    
    if best_r is None:
        best_r = (min_r + max_r) / 2
    
    # Calculate final center position
    center_lat, center_lon = point_at_bearing_distance(
        initial_fix_lat, initial_fix_lon,
        perpendicular_bearing,
        best_r
    )
    
    # Verify distances
    dist_to_initial = distance_nm(center_lat, center_lon,
                                 initial_fix_lat, initial_fix_lon)
    dist_to_ending = distance_nm(center_lat, center_lon,
                                ending_fix_lat, ending_fix_lon)
    
    # Calculate angles for TopSky COORD_AF
    start_angle = bearing_between_points(center_lat, center_lon,
                                        initial_fix_lat, initial_fix_lon)
    end_angle = bearing_between_points(center_lat, center_lon,
                                      ending_fix_lat, ending_fix_lon)
    
    # Calculate sweep angle
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
    
    # Calculate exit track (tangent to arc at ending fix)
    # From ending fix, center is at bearing (end_angle + 180°)
    # For LEFT turn, center is 90° left of track, so track is 90° right of center
    # For RIGHT turn, center is 90° right of track, so track is 90° left of center
    if turn_direction == 'L':
        exit_track = (end_angle + 180 + 90) % 360
    else:
        exit_track = (end_angle + 180 - 90) % 360
    
    return {
        'center_lat': center_lat,
        'center_lon': center_lon,
        'radius': best_r,
        'start_angle': start_angle,
        'end_angle': end_angle,
        'sweep': sweep,
        'direction': direction_symbol,
        'exit_track': exit_track,
        'error': max(abs(dist_to_initial - best_r), abs(dist_to_ending - best_r))
    }

# ============================================================================
# SCT FILE PARSING
# ============================================================================

def load_waypoints_from_sct(sct_path: str) -> Dict[str, Tuple[str, str]]:
    """Load all waypoints from [FIXES] section of .sct file."""
    waypoints = {}
    in_fixes_section = False
    
    try:
        with open(sct_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                
                if line.startswith('[FIXES]'):
                    in_fixes_section = True
                    continue
                
                if in_fixes_section:
                    if line.startswith('['):
                        break
                    
                    if line and not line.startswith(';'):
                        parts = line.split()
                        if len(parts) >= 3:
                            fix_name = parts[0]
                            lat = parts[1]
                            lon = parts[2]
                            waypoints[fix_name] = (lat, lon)
    
    except FileNotFoundError:
        print(f"ERROR: File not found: {sct_path}")
        return {}
    except Exception as e:
        print(f"ERROR reading file: {e}")
        return {}
    
    return waypoints

# ============================================================================
# TOPSKY OUTPUT GENERATION
# ============================================================================

def format_coord_af(arc_params: Dict, spacing: float = 1.0) -> str:
    """Format a COORD_AF line for TopSky."""
    lat_str = decimal_to_dms(arc_params['center_lat'], True)
    lon_str = decimal_to_dms(arc_params['center_lon'], False)
    
    line = f"COORD_AF:{lat_str}:{lon_str}:{arc_params['radius']:.1f}:{spacing}:"
    line += f"{arc_params['start_angle']:.1f}:{arc_params['direction']}:{arc_params['end_angle']:.1f}"
    
    return line

def analyze_transition(transition_name: str, waypoint_sequence: List[str],
                      waypoint_coords: Dict[str, Tuple[float, float]],
                      airport_coords: Tuple[float, float]) -> List[Dict]:
    """
    Analyze a transition sequence and identify RF arcs.
    Uses airport coordinates to determine turn direction.
    Properly chains consecutive arcs using exit tracks.
    Returns list of leg definitions with arc info.
    """
    
    legs = []
    entry_track = None  # Track entering current waypoint
    
    for i in range(len(waypoint_sequence) - 1):
        fix1 = waypoint_sequence[i]
        fix2 = waypoint_sequence[i + 1]
        
        if fix1 not in waypoint_coords or fix2 not in waypoint_coords:
            print(f"WARNING: Missing coordinates for {fix1} or {fix2}")
            continue
        
        lat1, lon1 = waypoint_coords[fix1]
        lat2, lon2 = waypoint_coords[fix2]
        
        # Calculate direct bearing (for reference)
        bearing = bearing_between_points(lat1, lon1, lat2, lon2)
        distance = distance_nm(lat1, lon1, lat2, lon2)
        
        leg = {
            'from': fix1,
            'to': fix2,
            'bearing': bearing,
            'distance': distance,
            'is_arc': False,
            'arc_params': None
        }
        
        # Determine if this leg should be an RF arc
        if i > 0:  # Not the first leg
            # Use entry track from previous leg
            if entry_track is None:
                # If no entry track yet, use bearing from previous leg
                prev_from = waypoint_sequence[i-1]
                entry_track = bearing_between_points(
                    *waypoint_coords[prev_from], lat1, lon1
                )
            
            # Determine turn direction toward airport
            turn_direction = determine_turn_toward_airport(
                lat1, lon1, entry_track, *airport_coords
            )
            
            # Calculate RF arc
            arc = calculate_arc_center_fix(
                lat1, lon1, lat2, lon2, entry_track, turn_direction
            )
            
            # Check if arc is reasonable (sweep angle between 10° and 270°)
            if arc and 10 < arc['sweep'] < 270 and arc['error'] < 0.5:
                leg['is_arc'] = True
                leg['arc_params'] = arc
                # Update entry track for next leg to be exit track from this arc
                entry_track = arc['exit_track']
            else:
                # Not an arc, just straight leg
                entry_track = bearing
        else:
            # First leg is always straight
            entry_track = bearing
        
        legs.append(leg)
    
    return legs

def generate_topsky_map_combined(airport: str, runway: str,
                                 transitions: Dict[str, List[str]], 
                                 all_legs: Dict[str, List[Dict]]) -> str:
    """Generate single TopSky map definition combining all transitions."""
    
    output = []
    output.append(f"MAP:RNAV-Y-{runway}")
    output.append(f"FOLDER:{airport}")
    output.append(f"ACTIVE:RWY:ARR:{airport}{runway}:DEP:*")
    output.append("COLOR:TEXTLABEL")
    
    # Collect all unique waypoints across all transitions
    all_waypoints = set()
    for waypoints in transitions.values():
        all_waypoints.update(waypoints)
    
    # Add SYMBOL lines for all waypoints
    for wpt in sorted(all_waypoints):
        output.append(f"SYMBOL:FIX:{wpt}")
    
    output.append("COLOR:RNPAR")
    
    # Add each transition's coordinates
    for transition_name, waypoint_sequence in transitions.items():
        legs = all_legs[transition_name]
        
        # Add comment for transition
        output.append(f"; Transition: {transition_name}")
        
        # Add COORD/COORD_AF lines for this transition
        for i, wpt in enumerate(waypoint_sequence[:-1]):
            output.append(f"COORD:{wpt}")
            
            # Check if next leg has an arc
            if i < len(legs) and legs[i]['is_arc']:
                arc_line = format_coord_af(legs[i]['arc_params'])
                output.append(arc_line)
        
        # Final waypoint of this transition
        output.append(f"COORD:{waypoint_sequence[-1]}")
        output.append("")  # Blank line between transitions
    
    output.append("COORDLINE")
    output.append("")
    
    return '\n'.join(output)

# ============================================================================
# MAIN INTERACTIVE PROGRAM
# ============================================================================

class RFArcGenerator:
    def __init__(self):
        self.sct_path = None
        self.waypoint_db = {}
        self.waypoint_coords = {}
    
    def set_sct_file(self, path: str) -> bool:
        """Load and cache waypoints from SCT file."""
        if not os.path.exists(path):
            print(f"ERROR: File not found: {path}")
            return False
        
        print(f"Loading waypoints from {path}...")
        self.waypoint_db = load_waypoints_from_sct(path)
        
        if not self.waypoint_db:
            print("ERROR: No waypoints loaded from file")
            return False
        
        # Convert to decimal for calculations
        self.waypoint_coords = {}
        for name, (lat_str, lon_str) in self.waypoint_db.items():
            lat = dms_to_decimal(lat_str)
            lon = dms_to_decimal(lon_str)
            self.waypoint_coords[name] = (lat, lon)
        
        self.sct_path = path
        print(f"Loaded {len(self.waypoint_db)} waypoints")
        return True
    
    def verify_waypoints(self, waypoint_list: List[str]) -> bool:
        """Verify all waypoints exist in database."""
        missing = [wpt for wpt in waypoint_list if wpt not in self.waypoint_db]
        if missing:
            print(f"ERROR: Missing waypoints: {', '.join(missing)}")
            return False
        return True
    
    def generate_approach(self, airport: str, runway: str, 
                         airport_lat: float, airport_lon: float,
                         transitions: Dict[str, List[str]]) -> str:
        """Generate complete TopSky maps for an approach with all transitions combined."""
        
        output = []
        output.append(";=" + "="*77)
        output.append(f"; {airport} RNAV Y Rwy {runway} Approach Procedures")
        output.append("; Generated by TopSky RF Arc Generator")
        output.append("; Uses airport-directed turn logic for smooth, continuous arcs")
        output.append(";=" + "="*77)
        output.append("")
        
        all_legs = {}
        
        for transition_name, waypoint_sequence in transitions.items():
            print(f"\nAnalyzing transition: {transition_name}")
            print(f"  Route: {' - '.join(waypoint_sequence)}")
            
            # Verify waypoints
            if not self.verify_waypoints(waypoint_sequence):
                continue
            
            # Analyze for RF arcs using airport coordinates
            legs = analyze_transition(transition_name, waypoint_sequence, 
                                    self.waypoint_coords,
                                    (airport_lat, airport_lon))
            
            all_legs[transition_name] = legs
            
            # Report findings
            rf_count = sum(1 for leg in legs if leg['is_arc'])
            if rf_count > 0:
                print(f"  Found {rf_count} RF arc(s):")
                for leg in legs:
                    if leg['is_arc']:
                        arc = leg['arc_params']
                        print(f"    {leg['from']} → {leg['to']}: "
                              f"R={arc['radius']:.2f} NM, "
                              f"sweep={arc['sweep']:.1f}°, "
                              f"dir={arc['direction']}, "
                              f"error={arc['error']:.4f} NM")
            else:
                print(f"  No RF arcs detected (all straight legs)")
        
        # Generate single combined map
        map_text = generate_topsky_map_combined(airport, runway, transitions, all_legs)
        output.append(map_text)
        
        return '\n'.join(output)
    
    def interactive_mode(self):
        """Run interactive session."""
        print("="*80)
        print("TopSky RF Arc Generator")
        print("="*80)
        print()
        
        # Show .sct files in current directory
        cwd_sct_files = [f for f in os.listdir('.') if f.endswith('.sct')]
        if cwd_sct_files:
            print("Found .sct file(s) in current directory:")
            for f in cwd_sct_files:
                print(f"  - {f}")
            print()
        
        # Get SCT file
        while not self.sct_path:
            if cwd_sct_files:
                print("Enter .sct filename or full path (or 'quit'):")
            else:
                print("Enter full path to .sct file (or 'quit'):")
            
            path = input("> ").strip('"').strip("'")
            
            if path.lower() == 'quit':
                return
            
            # If just a filename, check current directory
            if not os.path.dirname(path) and not os.path.exists(path):
                # Try in current directory
                if os.path.exists(os.path.join('.', path)):
                    path = os.path.join('.', path)
            
            if self.set_sct_file(path):
                break
        
        while True:
            print("\n" + "="*80)
            print("Generate new approach procedure (or 'quit' to exit)")
            print("="*80)
            
            # Get airport code
            airport = input("\nAirport code (e.g., CYFC): ").strip().upper()
            if airport.lower() == 'quit':
                break
            
            # Get runway
            runway = input("Runway (e.g., 09): ").strip()
            if runway.lower() == 'quit':
                break
            
            # Get airport coordinates (for turn direction detection)
            print("\nAirport coordinates (needed for turn direction detection)")
            print("You can find these in your .sct file or use approximate values")
            
            airport_lat_str = input("Airport latitude (e.g., N45.52.00.000): ").strip()
            if airport_lat_str.lower() == 'quit':
                break
            
            airport_lon_str = input("Airport longitude (e.g., W066.32.00.000): ").strip()
            if airport_lon_str.lower() == 'quit':
                break
            
            try:
                airport_lat = dms_to_decimal(airport_lat_str)
                airport_lon = dms_to_decimal(airport_lon_str)
            except:
                print("ERROR: Invalid coordinate format. Use format like N45.52.00.000")
                continue
            
            # Get transitions
            transitions = {}
            print("\nEnter transitions (one per line)")
            print("Format: IF_POINT waypoint1 waypoint2 ... FAP")
            print("Example: VESBI UKNUM URTIT VYSTA")
            print("Enter blank line when done")
            
            while True:
                line = input(f"Transition {len(transitions)+1}: ").strip()
                if not line:
                    break
                if line.lower() == 'quit':
                    return
                
                waypoints = line.split()
                if len(waypoints) < 2:
                    print("ERROR: Need at least 2 waypoints")
                    continue
                
                if_point = waypoints[0]
                transitions[if_point] = waypoints
            
            if not transitions:
                print("No transitions entered, skipping...")
                continue
            
            # Generate output
            print("\nGenerating TopSky maps...")
            output = self.generate_approach(airport, runway, airport_lat, airport_lon, transitions)
            
            # Save to file
            filename = f"{airport}_RNAV-Y-{runway}_TopSkyMaps.txt"
            filepath = os.path.join(os.getcwd(), filename)
            
            try:
                with open(filepath, 'w') as f:
                    f.write(output)
                print(f"\n✓ Saved to: {filepath}")
            except OSError:
                # If can't write to current directory, try /home/claude or user's home
                try:
                    alt_path = os.path.join(os.path.expanduser('~'), filename)
                    with open(alt_path, 'w') as f:
                        f.write(output)
                    print(f"\n✓ Saved to: {alt_path}")
                except:
                    print(f"\n✓ Generated (could not save file)")
                    print("\nOutput preview:")
                    print(output[:500] + "...")
            
            # Ask to continue
            cont = input("\nGenerate another approach? (y/n): ").strip().lower()
            if cont != 'y':
                break
        
        print("\nThank you for using TopSky RF Arc Generator!")

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    generator = RFArcGenerator()
    
    if len(sys.argv) > 1:
        # Command line mode with SCT file provided
        generator.set_sct_file(sys.argv[1])
    
    generator.interactive_mode()
