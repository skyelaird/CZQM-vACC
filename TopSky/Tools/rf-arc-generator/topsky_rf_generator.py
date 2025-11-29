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
# VALIDATION FUNCTIONS
# ============================================================================

def validate_waypoint_format(waypoint: str) -> bool:
    """
    Validate waypoint is in 5LNC format (5 letters/numbers).
    Returns True if valid, False otherwise.
    """
    if len(waypoint) != 5:
        return False
    
    # Must be alphanumeric
    if not waypoint.isalnum():
        return False
    
    return True

def validate_runway_format(runway: str) -> bool:
    """
    Validate runway format.
    Must be 2-3 characters: 2 digits + optional L/R/C suffix
    Examples: 05, 23, 24L, 09R, 14C
    """
    if len(runway) < 2 or len(runway) > 3:
        return False
    
    # First two characters must be digits
    if not runway[:2].isdigit():
        return False
    
    # Runway number must be 01-36
    rwy_num = int(runway[:2])
    if rwy_num < 1 or rwy_num > 36:
        return False
    
    # If 3 characters, third must be L, R, or C
    if len(runway) == 3:
        if runway[2] not in ['L', 'R', 'C']:
            return False
    
    return True

def validate_coordinate_range(lat: float, lon: float) -> bool:
    """
    Validate coordinates are in reasonable range.
    Lat: -90 to +90
    Lon: -180 to +180
    """
    if lat < -90 or lat > 90:
        return False
    if lon < -180 or lon > 180:
        return False
    return True

def parse_waypoint_sequence(input_str: str, known_waypoints: set) -> Tuple[List[str], List[str]]:
    """
    Parse waypoint sequence and detect errors.
    Returns: (valid_waypoints, error_messages)
    
    Handles common errors:
    - Missing spaces between waypoints (VESBIUMNUM → VESBI UKNUM)
    - Typos (detected by not found in waypoint database)
    - Invalid format (not 5 characters)
    """
    tokens = input_str.split()
    valid_waypoints = []
    errors = []
    
    for token in tokens:
        token = token.upper().strip()
        
        # Check if token is valid length
        if len(token) == 5:
            if validate_waypoint_format(token):
                if token in known_waypoints:
                    valid_waypoints.append(token)
                else:
                    errors.append(f"Waypoint '{token}' not found in .sct file - check spelling")
            else:
                errors.append(f"'{token}' has invalid format (must be 5 alphanumeric characters)")
        
        # Check if token might be multiple waypoints concatenated
        elif len(token) % 5 == 0 and len(token) > 5:
            # Could be missing spaces: VESBIUMNUM = VESBI + UKNUM
            possible_split = []
            for i in range(0, len(token), 5):
                wpt = token[i:i+5]
                if wpt in known_waypoints:
                    possible_split.append(wpt)
                else:
                    break
            
            if len(possible_split) == len(token) // 5:
                errors.append(f"Missing spaces? '{token}' could be: {' '.join(possible_split)}")
                # Add them anyway with a note
                valid_waypoints.extend(possible_split)
            else:
                errors.append(f"'{token}' is wrong length ({len(token)} chars) - waypoints must be 5 characters")
        
        else:
            errors.append(f"'{token}' is wrong length ({len(token)} chars) - waypoints must be 5 characters")
    
    return valid_waypoints, errors

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

def load_airports_from_sct(sct_path: str) -> Dict[str, Tuple[str, str]]:
    """Load all airports from [AIRPORT] section of .sct file."""
    airports = {}
    in_airport_section = False
    
    try:
        with open(sct_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                
                if line.startswith('[AIRPORT]'):
                    in_airport_section = True
                    continue
                
                if in_airport_section:
                    if line.startswith('['):
                        break
                    
                    if line and not line.startswith(';'):
                        parts = line.split()
                        if len(parts) >= 4:
                            # Format: ICAO Frequency Lat Lon [Letter]
                            icao = parts[0]
                            lat = parts[2]
                            lon = parts[3]
                            airports[icao] = (lat, lon)
    
    except Exception as e:
        print(f"WARNING: Could not read airports: {e}")
        return {}
    
    return airports

def load_runways_from_sct(sct_path: str) -> Dict[str, List[str]]:
    """
    Load all runways from [RUNWAY] section of .sct file.
    Returns dict: {airport: [list of runway identifiers]}
    
    Format: RWY1 RWY2 Heading1 Heading2 Lat1 Lon1 Lat2 Lon2 Airport
    Example: 05 23 053 233 N044.51.56.318 W063.31.38.110 N044.53.18.250 W063.30.17.200 CYHZ
    """
    runways = {}
    in_runway_section = False
    
    try:
        with open(sct_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                
                if line.startswith('[RUNWAY]'):
                    in_runway_section = True
                    continue
                
                if in_runway_section:
                    if line.startswith('['):
                        break
                    
                    if line and not line.startswith(';'):
                        parts = line.split()
                        if len(parts) >= 9:
                            # Format: RWY1 RWY2 HDG1 HDG2 LAT1 LON1 LAT2 LON2 AIRPORT
                            rwy1 = parts[0]
                            rwy2 = parts[1]
                            airport = parts[8]
                            
                            if airport not in runways:
                                runways[airport] = []
                            
                            # Add both runway ends (e.g., 05 and 23)
                            if rwy1 not in runways[airport]:
                                runways[airport].append(rwy1)
                            if rwy2 not in runways[airport]:
                                runways[airport].append(rwy2)
    
    except Exception as e:
        print(f"WARNING: Could not read runways: {e}")
        return {}
    
    return runways

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
        
        # COORDLINE after each transition
        output.append("COORDLINE")
        output.append("")  # Blank line between transitions
    
    return '\n'.join(output)

# ============================================================================
# MAIN INTERACTIVE PROGRAM
# ============================================================================

class RFArcGenerator:
    def __init__(self):
        self.sct_path = None
        self.waypoint_db = {}
        self.waypoint_coords = {}
        self.airport_db = {}
        self.airport_coords = {}
        self.runway_db = {}
    
    def set_sct_file(self, path: str) -> bool:
        """Load and cache waypoints, airports, and runways from SCT file."""
        if not os.path.exists(path):
            print(f"ERROR: File not found: {path}")
            return False
        
        print(f"Loading data from {path}...")
        
        # Load waypoints
        self.waypoint_db = load_waypoints_from_sct(path)
        if not self.waypoint_db:
            print("ERROR: No waypoints loaded from file")
            return False
        
        # Load airports
        self.airport_db = load_airports_from_sct(path)
        if not self.airport_db:
            print("WARNING: No airports loaded - you'll need to enter coordinates manually")
        else:
            print(f"Loaded {len(self.airport_db)} airports")
        
        # Load runways
        self.runway_db = load_runways_from_sct(path)
        if not self.runway_db:
            print("WARNING: No runways loaded - runway validation will be limited")
        else:
            total_runways = sum(len(rwys) for rwys in self.runway_db.values())
            print(f"Loaded {total_runways} runways from {len(self.runway_db)} airports")
        
        # Convert to decimal for calculations
        self.waypoint_coords = {}
        for name, (lat_str, lon_str) in self.waypoint_db.items():
            try:
                lat = dms_to_decimal(lat_str)
                lon = dms_to_decimal(lon_str)
                if validate_coordinate_range(lat, lon):
                    self.waypoint_coords[name] = (lat, lon)
                else:
                    print(f"WARNING: Invalid coordinates for {name}: {lat}, {lon}")
            except:
                print(f"WARNING: Could not parse coordinates for {name}")
        
        self.airport_coords = {}
        for icao, (lat_str, lon_str) in self.airport_db.items():
            try:
                lat = dms_to_decimal(lat_str)
                lon = dms_to_decimal(lon_str)
                if validate_coordinate_range(lat, lon):
                    self.airport_coords[icao] = (lat, lon)
            except:
                print(f"WARNING: Could not parse coordinates for airport {icao}")
        
        self.sct_path = path
        print(f"Loaded {len(self.waypoint_db)} waypoints")
        return True
    
    def get_airport_coordinates(self, airport_icao: str) -> Optional[Tuple[float, float]]:
        """Get airport coordinates from loaded database."""
        if airport_icao in self.airport_coords:
            return self.airport_coords[airport_icao]
        return None
    
    def get_airport_runways(self, airport_icao: str) -> Optional[List[str]]:
        """Get list of runways for an airport."""
        if airport_icao in self.runway_db:
            return sorted(self.runway_db[airport_icao])
        return None
    
    def validate_runway(self, airport_icao: str, runway: str) -> Tuple[bool, str]:
        """
        Validate runway exists at airport.
        Returns: (is_valid, error_message)
        """
        # Check format first
        if not validate_runway_format(runway):
            return False, f"Invalid runway format '{runway}' (must be 01-36 with optional L/R/C)"
        
        # Check if runway exists at this airport
        airport_runways = self.get_airport_runways(airport_icao)
        if airport_runways is None:
            # No runway data - accept if format is valid
            return True, ""
        
        if runway not in airport_runways:
            available = ', '.join(airport_runways)
            return False, f"Runway {runway} not found at {airport_icao}. Available: {available}"
        
        return True, ""
    
    def verify_waypoints(self, waypoint_list: List[str]) -> bool:
        """Verify all waypoints exist in database with validation."""
        missing = []
        invalid_format = []
        invalid_coords = []
        
        for wpt in waypoint_list:
            # Check format
            if not validate_waypoint_format(wpt):
                invalid_format.append(wpt)
                continue
            
            # Check exists
            if wpt not in self.waypoint_db:
                missing.append(wpt)
                continue
            
            # Check coordinates are valid
            if wpt not in self.waypoint_coords:
                invalid_coords.append(wpt)
        
        has_errors = False
        
        if invalid_format:
            print(f"ERROR: Invalid waypoint format (must be 5 alphanumeric): {', '.join(invalid_format)}")
            has_errors = True
        
        if missing:
            print(f"ERROR: Waypoints not found in .sct file: {', '.join(missing)}")
            print(f"       Check spelling or verify waypoints exist in [FIXES] section")
            has_errors = True
        
        if invalid_coords:
            print(f"ERROR: Invalid coordinates for waypoints: {', '.join(invalid_coords)}")
            has_errors = True
        
        return not has_errors
    
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
            
            # Get airport code with validation
            while True:
                airport = input("\nAirport code (e.g., CYFC): ").strip().upper()
                if airport.lower() == 'quit':
                    return
                
                if len(airport) != 4:
                    print(f"ERROR: Airport code must be 4 characters (you entered {len(airport)})")
                    continue
                
                if not airport.isalpha():
                    print(f"ERROR: Airport code must be letters only")
                    continue
                
                # Check if airport exists in database
                airport_coords_auto = self.get_airport_coordinates(airport)
                if airport_coords_auto:
                    print(f"✓ Found {airport} in .sct file")
                    airport_lat, airport_lon = airport_coords_auto
                    lat_str = decimal_to_dms(airport_lat, True)
                    lon_str = decimal_to_dms(airport_lon, False)
                    print(f"  Coordinates: {lat_str} {lon_str}")
                    break
                else:
                    print(f"WARNING: Airport {airport} not found in .sct [AIRPORT] section")
                    use_anyway = input(f"Use {airport} anyway and enter coordinates manually? (y/n): ").strip().lower()
                    if use_anyway == 'y':
                        break
                    # Otherwise loop back to enter airport again
            
            # Get runway with validation
            airport_runways = self.get_airport_runways(airport)
            
            if airport_runways:
                print(f"\nAvailable runways at {airport}: {', '.join(airport_runways)}")
            
            while True:
                if airport_runways:
                    runway = input(f"Runway (e.g., {airport_runways[0]}): ").strip().upper()
                else:
                    runway = input("Runway (e.g., 09, 24L): ").strip().upper()
                
                if runway.lower() == 'quit':
                    return
                
                # Validate runway
                is_valid, error_msg = self.validate_runway(airport, runway)
                if is_valid:
                    break
                else:
                    print(f"ERROR: {error_msg}")
                    continue
            
            # Get airport coordinates (auto-detected or manual entry)
            if airport_coords_auto:
                airport_lat, airport_lon = airport_coords_auto
                print(f"\nUsing airport coordinates from .sct file:")
                print(f"  Latitude: {decimal_to_dms(airport_lat, True)}")
                print(f"  Longitude: {decimal_to_dms(airport_lon, False)}")
            else:
                print("\nAirport coordinates (needed for turn direction detection)")
                print("Format: N45.52.00.000 or N045.52.00.000")
                
                while True:
                    airport_lat_str = input("Airport latitude: ").strip()
                    if airport_lat_str.lower() == 'quit':
                        return
                    
                    try:
                        airport_lat = dms_to_decimal(airport_lat_str)
                        if not validate_coordinate_range(airport_lat, 0):
                            print(f"ERROR: Latitude out of range (-90 to +90): {airport_lat}")
                            continue
                        break
                    except:
                        print("ERROR: Invalid format. Use format like N45.52.00.000 or N045.52.00.000")
                
                while True:
                    airport_lon_str = input("Airport longitude: ").strip()
                    if airport_lon_str.lower() == 'quit':
                        return
                    
                    try:
                        airport_lon = dms_to_decimal(airport_lon_str)
                        if not validate_coordinate_range(0, airport_lon):
                            print(f"ERROR: Longitude out of range (-180 to +180): {airport_lon}")
                            continue
                        break
                    except:
                        print("ERROR: Invalid format. Use format like W66.32.00.000 or W066.32.00.000")
            
            # Get transitions with improved validation
            transitions = {}
            print("\nEnter transitions (one per line)")
            print("Format: IF_POINT waypoint1 waypoint2 ... FAP")
            print("Example: VESBI UKNUM URTIT VYSTA")
            print("Note: Waypoints must be 5 alphanumeric characters, separated by spaces")
            print("Enter blank line when done")
            
            while True:
                line = input(f"Transition {len(transitions)+1}: ").strip()
                if not line:
                    break
                if line.lower() == 'quit':
                    return
                
                # Parse and validate waypoint sequence
                waypoints, errors = parse_waypoint_sequence(line, set(self.waypoint_db.keys()))
                
                if errors:
                    print("\n⚠️  ERRORS DETECTED:")
                    for error in errors:
                        print(f"    {error}")
                    
                    if waypoints:
                        print(f"\n  Interpreted as: {' '.join(waypoints)}")
                        use_anyway = input("  Use this sequence? (y/n): ").strip().lower()
                        if use_anyway != 'y':
                            print("  Skipping this transition. Please re-enter.")
                            continue
                    else:
                        print("  No valid waypoints found. Please re-enter.")
                        continue
                
                if len(waypoints) < 2:
                    print("ERROR: Need at least 2 waypoints")
                    continue
                
                if_point = waypoints[0]
                transitions[if_point] = waypoints
                print(f"✓ Added transition: {' '.join(waypoints)}")
            
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
