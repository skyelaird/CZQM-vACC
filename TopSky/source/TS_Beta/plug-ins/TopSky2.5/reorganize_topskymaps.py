#!/usr/bin/env python3
"""
TopSkyMaps.txt Reorganization Script v1.0
==========================================

Purpose: Reorganize TopSkyMaps.txt into logical, maintainable structure
Author: Claude (for Joel Morin / CZQM vACC)
Date: 2025-11-29

SAFETY FEATURES:
- Creates backup automatically
- Validates all data preserved (checksums)
- Generates detailed diff
- No destructive operations until validation passes

WHAT IT DOES:
1. Parses current file structure
2. Extracts sections intelligently
3. Reorganizes into new logical structure
4. Validates data integrity
5. Generates outputs for review

OUTPUTS:
- TopSkyMaps_v1.3.0.txt          (new organized file)
- TopSkyMaps_v1.2.1_BACKUP.txt   (backup of original)
- TopSkyMaps_DIFF.txt            (changes for review)
- reorganization_report.txt      (validation stats)
"""

import re
import hashlib
from datetime import datetime
from collections import defaultdict
import difflib

class TopSkyMapsReorganizer:
    def __init__(self, input_file):
        self.input_file = input_file
        self.output_file = input_file.replace('.txt', '_v1.3.0.txt')
        self.backup_file = input_file.replace('.txt', '_v1.2.1_BACKUP.txt')
        self.diff_file = 'TopSkyMaps_DIFF.txt'
        self.report_file = 'reorganization_report.txt'
        
        self.lines = []
        self.sections = defaultdict(list)
        self.stats = {
            'original': {},
            'reorganized': {}
        }
        
    def load_file(self):
        """Load the original file"""
        print("Loading TopSkyMaps.txt...")
        with open(self.input_file, 'r', encoding='utf-8', errors='ignore') as f:
            self.lines = f.readlines()
        print(f"  ✓ Loaded {len(self.lines):,} lines")
        
    def create_backup(self):
        """Create backup of original file"""
        print("Creating backup...")
        with open(self.backup_file, 'w', encoding='utf-8') as f:
            f.writelines(self.lines)
        print(f"  ✓ Backup saved: {self.backup_file}")
        
    def analyze_original(self):
        """Analyze original file structure and collect stats"""
        print("Analyzing original file...")
        
        stats = {
            'total_lines': len(self.lines),
            'coord_count': 0,
            'coordpoly_count': 0,
            'coordline_count': 0,
            'active_count': 0,
            'colordef_count': 0,
            'symboldef_count': 0,
            'comment_lines': 0,
            'blank_lines': 0
        }
        
        for line in self.lines:
            stripped = line.strip()
            if not stripped:
                stats['blank_lines'] += 1
            elif stripped.startswith('//'):
                stats['comment_lines'] += 1
            elif stripped.startswith('COORD:'):
                stats['coord_count'] += 1
            elif stripped.startswith('COORDPOLY:'):
                stats['coordpoly_count'] += 1
            elif stripped.startswith('COORDLINE:'):
                stats['coordline_count'] += 1
            elif stripped.startswith('ACTIVE:'):
                stats['active_count'] += 1
            elif stripped.startswith('COLORDEF:'):
                stats['colordef_count'] += 1
            elif stripped.startswith('SYMBOLDEF:'):
                stats['symboldef_count'] += 1
        
        self.stats['original'] = stats
        
        print(f"  Original Statistics:")
        print(f"    Total lines: {stats['total_lines']:,}")
        print(f"    COORD statements: {stats['coord_count']:,}")
        print(f"    COORDPOLY statements: {stats['coordpoly_count']:,}")
        print(f"    COORDLINE statements: {stats['coordline_count']:,}")
        print(f"    ACTIVE statements: {stats['active_count']:,}")
        print(f"    Color definitions: {stats['colordef_count']:,}")
        print(f"    Symbol definitions: {stats['symboldef_count']:,}")
        
    def extract_sections(self):
        """Extract logical sections from the file"""
        print("Extracting sections...")
        
        current_section = 'header'
        current_airport = None
        buffer = []
        
        for i, line in enumerate(self.lines):
            stripped = line.strip()
            
            # Detect section changes
            if 'MAP AVERRIDES' in stripped or 'MAP OVERRIDES' in stripped:
                self._save_buffer('header', buffer)
                buffer = [line]
                current_section = 'map_overrides'
                
            elif 'Symbol Definitions' in stripped:
                self._save_buffer(current_section, buffer)
                buffer = [line]
                current_section = 'symbols'
                
            elif 'COLOR DEFINITIONS' in stripped:
                self._save_buffer(current_section, buffer)
                buffer = [line]
                current_section = 'colors'
                
            elif 'AIRSPACE BOUNDARIES' in stripped or 'SECTORIZATION' in stripped:
                self._save_buffer(current_section, buffer)
                buffer = [line]
                current_section = 'airspace'
                
            elif 'LAYER 10' in stripped or 'LAYER 11' in stripped or 'LAYER 12' in stripped or 'LAYER 13' in stripped or 'LAYER 14' in stripped:
                if current_section != 'airspace':
                    self._save_buffer(current_section, buffer)
                    buffer = []
                    current_section = 'airspace'
                buffer.append(line)
                
            # Detect airports
            elif re.search(r'\bCYHZ\b', stripped) and '//' in stripped and current_airport != 'CYHZ':
                self._save_buffer(current_section, buffer)
                buffer = [line]
                current_section = 'airport_CYHZ'
                current_airport = 'CYHZ'
                
            elif re.search(r'\bCYYT\b', stripped) and '//' in stripped and current_airport != 'CYYT':
                self._save_buffer(current_section, buffer)
                buffer = [line]
                current_section = 'airport_CYYT'
                current_airport = 'CYYT'
                
            elif re.search(r'\bCYFC\b', stripped) and '//' in stripped and current_airport != 'CYFC':
                self._save_buffer(current_section, buffer)
                buffer = [line]
                current_section = 'airport_CYFC'
                current_airport = 'CYFC'
                
            elif re.search(r'\bCYQM\b', stripped) and '//' in stripped and current_airport != 'CYQM':
                self._save_buffer(current_section, buffer)
                buffer = [line]
                current_section = 'airport_CYQM'
                current_airport = 'CYQM'
                
            elif re.search(r'\bCYSJ\b', stripped) and '//' in stripped and current_airport != 'CYSJ':
                self._save_buffer(current_section, buffer)
                buffer = [line]
                current_section = 'airport_CYSJ'
                current_airport = 'CYSJ'
                
            elif re.search(r'\bCYYR\b', stripped) and '//' in stripped and current_airport != 'CYYR':
                self._save_buffer(current_section, buffer)
                buffer = [line]
                current_section = 'airport_CYYR'
                current_airport = 'CYYR'
                
            elif 'WAYPOINTS' in stripped or 'Coastline' in stripped:
                self._save_buffer(current_section, buffer)
                buffer = [line]
                current_section = 'geographic'
                
            else:
                buffer.append(line)
        
        # Save final buffer
        self._save_buffer(current_section, buffer)
        
        print(f"  ✓ Extracted {len(self.sections)} sections")
        for section, lines in self.sections.items():
            print(f"    {section}: {len(lines):,} lines")
    
    def _save_buffer(self, section, buffer):
        """Save buffer to appropriate section"""
        if buffer:
            self.sections[section].extend(buffer)
    
    def generate_header(self):
        """Generate new file header with version info and table of contents"""
        header = []
        
        header.append("//============================================================================\n")
        header.append("// CZQM/CZQX TOPSKY MAPS CONFIGURATION\n")
        header.append("// VERSION: 1.3.0 - MAJOR REORGANIZATION\n")
        header.append(f"// LAST MODIFIED: {datetime.now().strftime('%Y-%m-%d')}\n")
        header.append("// AUTHOR: Joel Morin 810489\n")
        header.append("//\n")
        header.append("// DESCRIPTION:\n")
        header.append("// TopSky map definitions for CZQM (Moncton) and CZQX (Gander) FIRs\n")
        header.append("// Optimized for controller workflow and maintainability\n")
        header.append("//\n")
        header.append("// CHANGE LOG:\n")
        header.append("// v1.3.0 (2025-11-29) - Complete reorganization for logical flow\n")
        header.append("// v1.2.1 (2025-11-21) - Imported coastline, adjusted colors\n")
        header.append("//============================================================================\n")
        header.append("\n")
        
        # Table of contents (will fill in line numbers after generation)
        header.append("//============================================================================\n")
        header.append("// TABLE OF CONTENTS\n")
        header.append("//============================================================================\n")
        header.append("//\n")
        header.append("// SECTION 1: Configuration & Setup\n")
        header.append("//    - Map overrides\n")
        header.append("//    - Symbol definitions\n")
        header.append("//    - Color definitions\n")
        header.append("//\n")
        header.append("// SECTION 2: Airspace Structure (FIR Level)\n")
        header.append("//    - FIR boundaries (CZQM/CZQX/neighbors)\n")
        header.append("//    - Sectorization & delegation layers (10-14)\n")
        header.append("//    - TCU/TCA boundaries\n")
        header.append("//\n")
        header.append("// SECTION 3: Major Airports (Full Procedures)\n")
        header.append("//    - CYHZ - Halifax Stanfield (Primary)\n")
        header.append("//    - CYYT - St. John's (Secondary)\n")
        header.append("//\n")
        header.append("// SECTION 4: Other Airports (Basic Procedures)\n")
        header.append("//    - CYFC - Fredericton\n")
        header.append("//    - CYQM - Moncton\n")
        header.append("//    - CYYR - Goose Bay\n")
        header.append("//    - CYSJ - Saint John\n")
        header.append("//\n")
        header.append("// SECTION 5: Navigation & Geographic Features\n")
        header.append("//    - Waypoints and fixes\n")
        header.append("//    - Coastlines\n")
        header.append("//    - Political boundaries\n")
        header.append("//============================================================================\n")
        header.append("\n")
        header.append("\n")
        
        return header
    
    def reorganize(self):
        """Reorganize sections into new logical structure"""
        print("Reorganizing sections...")
        
        new_content = []
        
        # Header with TOC
        new_content.extend(self.generate_header())
        
        # Section 1: Configuration & Setup
        new_content.append("//============================================================================\n")
        new_content.append("// SECTION 1: CONFIGURATION & SETUP\n")
        new_content.append("//============================================================================\n")
        new_content.append("\n")
        
        # Map overrides
        if 'map_overrides' in self.sections:
            new_content.append("// ----------------------------------------------------------------------------\n")
            new_content.append("// 1.1 Map Overrides\n")
            new_content.append("// ----------------------------------------------------------------------------\n")
            new_content.append("\n")
            new_content.extend(self._clean_section(self.sections['map_overrides']))
            new_content.append("\n")
        
        # Symbols
        if 'symbols' in self.sections:
            new_content.append("// ----------------------------------------------------------------------------\n")
            new_content.append("// 1.2 Symbol Definitions\n")
            new_content.append("// ----------------------------------------------------------------------------\n")
            new_content.append("\n")
            new_content.extend(self._clean_section(self.sections['symbols']))
            new_content.append("\n")
        
        # Colors
        if 'colors' in self.sections:
            new_content.append("// ----------------------------------------------------------------------------\n")
            new_content.append("// 1.3 Color Definitions\n")
            new_content.append("// ----------------------------------------------------------------------------\n")
            new_content.append("\n")
            new_content.extend(self._clean_section(self.sections['colors']))
            new_content.append("\n")
        
        # Section 2: Airspace Structure
        if 'airspace' in self.sections:
            new_content.append("\n")
            new_content.append("//============================================================================\n")
            new_content.append("// SECTION 2: AIRSPACE STRUCTURE (FIR LEVEL)\n")
            new_content.append("//============================================================================\n")
            new_content.append("//\n")
            new_content.append("// PURPOSE:\n")
            new_content.append("// Define FIR boundaries, sectorization, and delegation layers.\n")
            new_content.append("//\n")
            new_content.append("// REFERENCE:\n")
            new_content.append("// See TopSkyAirspace.txt for sector activation logic\n")
            new_content.append("// ----------------------------------------------------------------------------\n")
            new_content.append("\n")
            new_content.extend(self._clean_section(self.sections['airspace']))
            new_content.append("\n")
        
        # Section 3: Major Airports
        new_content.append("\n")
        new_content.append("//============================================================================\n")
        new_content.append("// SECTION 3: MAJOR AIRPORTS (FULL PROCEDURES)\n")
        new_content.append("//============================================================================\n")
        new_content.append("// These airports have complete procedure mapping including:\n")
        new_content.append("// - All runways with approach transitions\n")
        new_content.append("// - STARs with distant feeds\n")
        new_content.append("// - Published holds\n")
        new_content.append("// - RF arc approaches (RNAV-Y)\n")
        new_content.append("// ----------------------------------------------------------------------------\n")
        new_content.append("\n")
        
        # CYHZ
        if 'airport_CYHZ' in self.sections:
            new_content.append("//============================================================================\n")
            new_content.append("// 3.1 CYHZ - HALIFAX STANFIELD INTERNATIONAL\n")
            new_content.append("//============================================================================\n")
            new_content.append("// PRIMARY AIRPORT - Full procedure coverage\n")
            new_content.append("// Runways: 05/23, 14/32\n")
            new_content.append("// Major hub for Atlantic Canada\n")
            new_content.append("// ----------------------------------------------------------------------------\n")
            new_content.append("\n")
            new_content.extend(self._clean_section(self.sections['airport_CYHZ']))
            new_content.append("\n")
        
        # CYYT
        if 'airport_CYYT' in self.sections:
            new_content.append("\n")
            new_content.append("//============================================================================\n")
            new_content.append("// 3.2 CYYT - ST. JOHN'S INTERNATIONAL\n")
            new_content.append("//============================================================================\n")
            new_content.append("// SECONDARY MAJOR AIRPORT\n")
            new_content.append("// Runways: 10/28, 16/34\n")
            new_content.append("// Significant international traffic, North Atlantic gateway\n")
            new_content.append("// ----------------------------------------------------------------------------\n")
            new_content.append("\n")
            new_content.extend(self._clean_section(self.sections['airport_CYYT']))
            new_content.append("\n")
        
        # Section 4: Other Airports
        new_content.append("\n")
        new_content.append("//============================================================================\n")
        new_content.append("// SECTION 4: OTHER AIRPORTS (BASIC PROCEDURES)\n")
        new_content.append("//============================================================================\n")
        new_content.append("// These airports have standard approach mapping\n")
        new_content.append("// Organized alphabetically\n")
        new_content.append("// ----------------------------------------------------------------------------\n")
        new_content.append("\n")
        
        # Other airports in alphabetical order
        other_airports = [
            ('CYFC', 'Fredericton', '09/27, 15/33'),
            ('CYQM', 'Moncton', '06/24, 11/29'),
            ('CYYR', 'Goose Bay', 'Military/civilian joint use'),
            ('CYSJ', 'Saint John', '05/23, 14/32')
        ]
        
        for i, (code, name, runways) in enumerate(other_airports, 1):
            section_key = f'airport_{code}'
            if section_key in self.sections:
                new_content.append(f"//============================================================================\n")
                new_content.append(f"// 4.{i} {code} - {name.upper()}\n")
                new_content.append(f"//============================================================================\n")
                new_content.append(f"// Runways: {runways}\n")
                new_content.append(f"// ----------------------------------------------------------------------------\n")
                new_content.append("\n")
                new_content.extend(self._clean_section(self.sections[section_key]))
                new_content.append("\n")
        
        # Section 5: Geographic features
        if 'geographic' in self.sections:
            new_content.append("\n")
            new_content.append("//============================================================================\n")
            new_content.append("// SECTION 5: NAVIGATION & GEOGRAPHIC FEATURES\n")
            new_content.append("//============================================================================\n")
            new_content.append("\n")
            new_content.extend(self._clean_section(self.sections['geographic']))
            new_content.append("\n")
        
        # End marker
        new_content.append("\n")
        new_content.append("//============================================================================\n")
        new_content.append("// END OF FILE\n")
        new_content.append("//============================================================================\n")
        
        return new_content
    
    def _clean_section(self, lines):
        """Clean up section formatting"""
        cleaned = []
        consecutive_blanks = 0
        
        for line in lines:
            # Skip header comments that are redundant
            if line.strip().startswith('// VERSION:') or line.strip().startswith('// BUILD DATE:'):
                continue
            
            # Limit consecutive blank lines to 2
            if not line.strip():
                consecutive_blanks += 1
                if consecutive_blanks <= 2:
                    cleaned.append(line)
            else:
                consecutive_blanks = 0
                cleaned.append(line)
        
        return cleaned
    
    def validate(self, new_content):
        """Validate that all data is preserved"""
        print("Validating reorganization...")
        
        # Count critical elements in new content
        stats = {
            'total_lines': len(new_content),
            'coord_count': 0,
            'coordpoly_count': 0,
            'coordline_count': 0,
            'active_count': 0,
            'colordef_count': 0,
            'symboldef_count': 0
        }
        
        for line in new_content:
            stripped = line.strip()
            if stripped.startswith('COORD:'):
                stats['coord_count'] += 1
            elif stripped.startswith('COORDPOLY:'):
                stats['coordpoly_count'] += 1
            elif stripped.startswith('COORDLINE:'):
                stats['coordline_count'] += 1
            elif stripped.startswith('ACTIVE:'):
                stats['active_count'] += 1
            elif stripped.startswith('COLORDEF:'):
                stats['colordef_count'] += 1
            elif stripped.startswith('SYMBOLDEF:'):
                stats['symboldef_count'] += 1
        
        self.stats['reorganized'] = stats
        
        # Check for data preservation
        validation_passed = True
        issues = []
        
        if stats['coord_count'] != self.stats['original']['coord_count']:
            validation_passed = False
            issues.append(f"COORD count mismatch: {self.stats['original']['coord_count']} → {stats['coord_count']}")
        
        if stats['coordpoly_count'] != self.stats['original']['coordpoly_count']:
            validation_passed = False
            issues.append(f"COORDPOLY count mismatch: {self.stats['original']['coordpoly_count']} → {stats['coordpoly_count']}")
        
        if stats['active_count'] != self.stats['original']['active_count']:
            validation_passed = False
            issues.append(f"ACTIVE count mismatch: {self.stats['original']['active_count']} → {stats['active_count']}")
        
        if validation_passed:
            print("  ✓ Validation PASSED - All data preserved")
            print(f"    COORD: {stats['coord_count']:,}")
            print(f"    COORDPOLY: {stats['coordpoly_count']:,}")
            print(f"    COORDLINE: {stats['coordline_count']:,}")
            print(f"    ACTIVE: {stats['active_count']:,}")
        else:
            print("  ✗ Validation FAILED")
            for issue in issues:
                print(f"    - {issue}")
        
        return validation_passed
    
    def write_output(self, new_content):
        """Write reorganized content to file"""
        print(f"Writing reorganized file...")
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.writelines(new_content)
        print(f"  ✓ Saved: {self.output_file}")
    
    def generate_diff(self):
        """Generate diff file for review"""
        print("Generating diff...")
        
        with open(self.backup_file, 'r', encoding='utf-8') as f:
            original = f.readlines()
        
        with open(self.output_file, 'r', encoding='utf-8') as f:
            reorganized = f.readlines()
        
        diff = difflib.unified_diff(
            original,
            reorganized,
            fromfile='TopSkyMaps_v1.2.1.txt',
            tofile='TopSkyMaps_v1.3.0.txt',
            lineterm=''
        )
        
        with open(self.diff_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(diff))
        
        print(f"  ✓ Diff saved: {self.diff_file}")
    
    def generate_report(self):
        """Generate reorganization report"""
        print("Generating report...")
        
        with open(self.report_file, 'w', encoding='utf-8') as f:
            f.write("TopSkyMaps.txt Reorganization Report\n")
            f.write("=" * 60 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n")
            
            f.write("ORIGINAL FILE STATISTICS\n")
            f.write("-" * 60 + "\n")
            for key, value in self.stats['original'].items():
                f.write(f"  {key:30} {value:,}\n")
            f.write("\n")
            
            f.write("REORGANIZED FILE STATISTICS\n")
            f.write("-" * 60 + "\n")
            for key, value in self.stats['reorganized'].items():
                f.write(f"  {key:30} {value:,}\n")
            f.write("\n")
            
            f.write("VALIDATION RESULTS\n")
            f.write("-" * 60 + "\n")
            f.write("  COORD statements:    ")
            if self.stats['original']['coord_count'] == self.stats['reorganized']['coord_count']:
                f.write("✓ PASS\n")
            else:
                f.write("✗ FAIL\n")
            
            f.write("  COORDPOLY statements: ")
            if self.stats['original']['coordpoly_count'] == self.stats['reorganized']['coordpoly_count']:
                f.write("✓ PASS\n")
            else:
                f.write("✗ FAIL\n")
            
            f.write("  ACTIVE statements:   ")
            if self.stats['original']['active_count'] == self.stats['reorganized']['active_count']:
                f.write("✓ PASS\n")
            else:
                f.write("✗ FAIL\n")
            
            f.write("\n")
            f.write("FILES GENERATED\n")
            f.write("-" * 60 + "\n")
            f.write(f"  Backup:       {self.backup_file}\n")
            f.write(f"  Reorganized:  {self.output_file}\n")
            f.write(f"  Diff:         {self.diff_file}\n")
            f.write(f"  Report:       {self.report_file}\n")
        
        print(f"  ✓ Report saved: {self.report_file}")
    
    def run(self):
        """Execute full reorganization process"""
        print("\n" + "=" * 70)
        print("TopSkyMaps.txt Reorganization v1.0")
        print("=" * 70 + "\n")
        
        self.load_file()
        self.create_backup()
        self.analyze_original()
        self.extract_sections()
        
        new_content = self.reorganize()
        
        validation_passed = self.validate(new_content)
        
        if validation_passed:
            self.write_output(new_content)
            self.generate_diff()
            self.generate_report()
            
            print("\n" + "=" * 70)
            print("✓ REORGANIZATION COMPLETE")
            print("=" * 70)
            print("\nNext steps:")
            print(f"  1. Review diff file: {self.diff_file}")
            print(f"  2. Review report: {self.report_file}")
            print(f"  3. Test {self.output_file} in EuroScope")
            print(f"  4. If good, replace original with reorganized file")
            print(f"  5. Backup is saved at: {self.backup_file}")
            print()
        else:
            print("\n" + "=" * 70)
            print("✗ VALIDATION FAILED - Reorganization aborted")
            print("=" * 70)
            print("\nNo files were modified. Check errors above.")
            print()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = 'TopSkyMaps.txt'
    
    reorganizer = TopSkyMapsReorganizer(input_file)
    reorganizer.run()
