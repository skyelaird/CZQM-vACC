#!/usr/bin/env python3
"""
TopSkyMaps.txt Cleanup Script - Pass 1 (Formatting Only)
=========================================================

Purpose: Clean up formatting and add clear section headers WITHOUT reorganizing
Author: Claude (for Joel Morin / CZQM vACC)
Date: 2025-11-29

WHAT THIS DOES:
- Adds clear section headers where they're missing
- Consolidates verbose multi-line comments to inline comments (where appropriate)
- Removes excessive blank lines (max 2 consecutive)
- Standardizes comment formatting
- DOES NOT move any sections around

WHAT THIS DOESN'T DO:
- Does NOT reorganize sections
- Does NOT change any functional code (COORD, ACTIVE, etc.)
- Does NOT remove any data

OUTPUTS:
- TopSkyMaps_v1.2.6_cleaned.txt   (cleaned file)
- TopSkyMaps_v1.2.1_BACKUP.txt    (backup of original)
- cleanup_report.txt               (validation stats)
"""

import re
from datetime import datetime
from collections import defaultdict

class TopSkyMapsCleanup:
    def __init__(self, input_file):
        self.input_file = input_file
        self.output_file = input_file.replace('.txt', '_v1.2.6_cleaned.txt')
        self.backup_file = input_file.replace('.txt', '_v1.2.1_BACKUP.txt')
        self.report_file = 'cleanup_report.txt'
        
        self.lines = []
        self.cleaned_lines = []
        self.stats = {
            'original': {},
            'cleaned': {}
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
        
    def analyze_file(self, lines, label):
        """Analyze file structure and collect stats"""
        stats = {
            'total_lines': len(lines),
            'coord_count': 0,
            'coordpoly_count': 0,
            'coordline_count': 0,
            'coordline_markers': 0,
            'active_count': 0,
            'colordef_count': 0,
            'symboldef_count': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'line_count': 0,
            'coord_hm_count': 0
        }
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                stats['blank_lines'] += 1
            elif stripped.startswith('//') or stripped.startswith(';'):
                stats['comment_lines'] += 1
            elif stripped == 'COORDLINE':
                stats['coordline_markers'] += 1
            elif stripped.startswith('COORD:'):
                stats['coord_count'] += 1
            elif stripped.startswith('COORD_HM:'):
                stats['coord_hm_count'] += 1
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
            elif stripped.startswith('LINE:'):
                stats['line_count'] += 1
        
        return stats
        
    def cleanup_formatting(self):
        """Clean up formatting without reorganizing"""
        print("Cleaning up formatting...")
        
        cleaned = []
        i = 0
        consecutive_blanks = 0
        
        while i < len(self.lines):
            line = self.lines[i]
            stripped = line.strip()
            
            # Limit consecutive blank lines to 2
            if not stripped:
                consecutive_blanks += 1
                if consecutive_blanks <= 2:
                    cleaned.append(line)
                i += 1
                continue
            else:
                consecutive_blanks = 0
            
            # Detect and enhance airport section headers
            if self.is_airport_header(stripped):
                airport_code = self.extract_airport_code(stripped)
                if airport_code:
                    # Add enhanced header
                    cleaned.append("\n")
                    cleaned.append(f"// {'=' * 76}\n")
                    cleaned.append(f"// {airport_code} PROCEDURES\n")
                    cleaned.append(f"// {'=' * 76}\n")
                    cleaned.append(line)  # Keep original comment too
                    i += 1
                    continue
            
            # Detect runway sections and add headers
            if stripped.startswith('MAP:') and ('_RWY' in stripped or 'RWY' in stripped or 'AR' in stripped):
                runway = self.extract_runway(stripped)
                if runway:
                    cleaned.append("\n")
                    cleaned.append(f"// {'-' * 76}\n")
                    cleaned.append(f"// Runway {runway} Approaches\n")
                    cleaned.append(f"// {'-' * 76}\n")
            
            # Consolidate COLORDEF multi-line comments to inline
            if stripped.startswith('COLORDEF:'):
                # Check if next lines are explanatory comments
                inline_comment = self.extract_inline_comment(i)
                if inline_comment:
                    # Add COLORDEF with inline comment
                    colordef_parts = stripped.split('//')
                    if len(colordef_parts) > 1:
                        # Already has inline comment
                        cleaned.append(line)
                    else:
                        # Add the inline comment
                        cleaned.append(f"{stripped:50} // {inline_comment}\n")
                    # Skip the verbose comment lines
                    i = self.skip_verbose_comments(i)
                    i += 1
                    continue
                else:
                    cleaned.append(line)
                    i += 1
                    continue
            
            # Detect RF arc sections and add clear headers
            if ('RF Arc' in line or 'RNAV Y' in line) and (stripped.startswith(';') or stripped.startswith('//')):
                # Replace verbose generated headers with concise ones
                if 'Generated by' in line:
                    cleaned.append("\n")
                    cleaned.append(f"// RNAV-Y Approach (RF Arc - Generated by RF Arc Generator)\n")
                    # Skip other generated comment lines
                    i = self.skip_generated_header(i)
                    i += 1
                    continue
            
            # Add section labels for holds
            if stripped.startswith('MAP:HOLDS'):
                cleaned.append("\n")
                cleaned.append(f"// {'-' * 76}\n")
                cleaned.append(f"// Published Holding Patterns\n")
                cleaned.append(f"// {'-' * 76}\n")
            
            # Keep everything else as-is
            cleaned.append(line)
            i += 1
        
        self.cleaned_lines = cleaned
        print(f"  ✓ Cleaned {len(cleaned):,} lines")
    
    def is_airport_header(self, line):
        """Detect if this is an airport section header"""
        # Look for patterns like "//CYHZ" or "//YHZ" or "//============ CYHZ"
        if not line.startswith('//'):
            return False
        
        # Common airport codes in Atlantic Canada
        airports = ['CYHZ', 'CYYT', 'CYFC', 'CYQM', 'CYSJ', 'CYYR', 'CYQX']
        
        for airport in airports:
            if airport in line and '=' not in line:  # Not already a formatted header
                return True
        return False
    
    def extract_airport_code(self, line):
        """Extract airport code from header"""
        airports = ['CYHZ', 'CYYT', 'CYFC', 'CYQM', 'CYSJ', 'CYYR', 'CYQX']
        for airport in airports:
            if airport in line:
                return airport
        return None
    
    def extract_runway(self, map_line):
        """Extract runway identifier from MAP statement"""
        # Patterns: MAP:CYFC AR09, MAP:CYHZ_RWY05, MAP:CYYT_RWY10
        match = re.search(r'(?:RWY|AR)(\d{2})', map_line)
        if match:
            return match.group(1)
        return None
    
    def extract_inline_comment(self, index):
        """Extract key information from verbose multi-line comments after COLORDEF"""
        # Look ahead up to 5 lines for explanatory comments
        comments = []
        for j in range(index + 1, min(index + 6, len(self.lines))):
            next_line = self.lines[j].strip()
            if not next_line.startswith('//'):
                break
            if next_line.startswith('//') and len(next_line) > 3:
                # Extract the key phrase
                comment_text = next_line.replace('//', '').strip()
                # Skip section dividers
                if '-' * 10 in comment_text or '=' * 10 in comment_text:
                    continue
                # Take the first substantive comment
                if comment_text and len(comment_text) < 80:
                    return comment_text
        return None
    
    def skip_verbose_comments(self, index):
        """Skip verbose comment lines after COLORDEF to avoid duplication"""
        j = index + 1
        while j < len(self.lines):
            next_line = self.lines[j].strip()
            if not next_line.startswith('//'):
                break
            # Stop if we hit another COLORDEF or functional statement
            if next_line.startswith('COLORDEF:') or next_line.startswith('COORD'):
                break
            j += 1
        return j - 1  # Return last comment line index
    
    def skip_generated_header(self, index):
        """Skip verbose generated RF arc header comments"""
        j = index + 1
        while j < len(self.lines) and j < index + 10:
            next_line = self.lines[j].strip()
            if not (next_line.startswith(';') or next_line.startswith('//')):
                break
            if 'Generated by' in next_line or 'Uses airport' in next_line or '=====' in next_line:
                j += 1
                continue
            break
        return j - 1
    
    def validate(self):
        """Validate that all data is preserved"""
        print("Validating cleanup...")
        
        self.stats['original'] = self.analyze_file(self.lines, "original")
        self.stats['cleaned'] = self.analyze_file(self.cleaned_lines, "cleaned")
        
        # Check for data preservation
        validation_passed = True
        issues = []
        
        critical_keys = [
            'coord_count', 'coordpoly_count', 'coordline_count', 
            'coordline_markers', 'active_count', 'colordef_count', 
            'symboldef_count', 'line_count', 'coord_hm_count'
        ]
        
        for key in critical_keys:
            if self.stats['original'][key] != self.stats['cleaned'][key]:
                validation_passed = False
                issues.append(f"{key}: {self.stats['original'][key]} → {self.stats['cleaned'][key]}")
        
        if validation_passed:
            print("  ✓ Validation PASSED - All data preserved")
            for key in critical_keys:
                print(f"    {key:25} {self.stats['cleaned'][key]:,}")
        else:
            print("  ✗ Validation FAILED")
            for issue in issues:
                print(f"    - {issue}")
        
        return validation_passed
    
    def write_output(self):
        """Write cleaned content to file"""
        print(f"Writing cleaned file...")
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.writelines(self.cleaned_lines)
        print(f"  ✓ Saved: {self.output_file}")
    
    def generate_report(self):
        """Generate cleanup report"""
        print("Generating report...")
        
        with open(self.report_file, 'w', encoding='utf-8') as f:
            f.write("TopSkyMaps.txt Cleanup Report - Pass 1\n")
            f.write("=" * 60 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n")
            
            f.write("CHANGES MADE:\n")
            f.write("-" * 60 + "\n")
            f.write("  - Added clear section headers for airports and runways\n")
            f.write("  - Consolidated verbose COLORDEF comments to inline\n")
            f.write("  - Limited consecutive blank lines to maximum 2\n")
            f.write("  - Standardized RF arc section headers\n")
            f.write("  - NO sections were moved or reorganized\n")
            f.write("\n")
            
            f.write("ORIGINAL FILE STATISTICS\n")
            f.write("-" * 60 + "\n")
            for key, value in self.stats['original'].items():
                f.write(f"  {key:30} {value:,}\n")
            f.write("\n")
            
            f.write("CLEANED FILE STATISTICS\n")
            f.write("-" * 60 + "\n")
            for key, value in self.stats['cleaned'].items():
                f.write(f"  {key:30} {value:,}\n")
            f.write("\n")
            
            f.write("VALIDATION RESULTS\n")
            f.write("-" * 60 + "\n")
            
            critical_keys = [
                ('COORD statements', 'coord_count'),
                ('COORDPOLY statements', 'coordpoly_count'),
                ('COORDLINE statements', 'coordline_count'),
                ('COORDLINE markers', 'coordline_markers'),
                ('ACTIVE statements', 'active_count'),
                ('COLORDEF statements', 'colordef_count'),
                ('LINE statements', 'line_count'),
                ('COORD_HM statements', 'coord_hm_count')
            ]
            
            for label, key in critical_keys:
                f.write(f"  {label:25} ")
                if self.stats['original'][key] == self.stats['cleaned'][key]:
                    f.write("✓ PASS\n")
                else:
                    f.write(f"✗ FAIL ({self.stats['original'][key]} → {self.stats['cleaned'][key]})\n")
            
            f.write("\n")
            f.write(f"Blank lines reduced: {self.stats['original']['blank_lines']:,} → {self.stats['cleaned']['blank_lines']:,}\n")
            f.write("\n")
            
            f.write("FILES GENERATED\n")
            f.write("-" * 60 + "\n")
            f.write(f"  Backup:       {self.backup_file}\n")
            f.write(f"  Cleaned:      {self.output_file}\n")
            f.write(f"  Report:       {self.report_file}\n")
        
        print(f"  ✓ Report saved: {self.report_file}")
    
    def run(self):
        """Execute cleanup process"""
        print("\n" + "=" * 70)
        print("TopSkyMaps.txt Cleanup - Pass 1 (Formatting Only)")
        print("=" * 70 + "\n")
        
        self.load_file()
        self.create_backup()
        
        print(f"\nOriginal file analysis:")
        original_stats = self.analyze_file(self.lines, "original")
        print(f"  Total lines: {original_stats['total_lines']:,}")
        print(f"  COORD: {original_stats['coord_count']:,}")
        print(f"  COORDLINE markers: {original_stats['coordline_markers']:,}")
        print(f"  ACTIVE: {original_stats['active_count']:,}")
        print(f"  COLORDEF: {original_stats['colordef_count']:,}")
        print(f"  LINE: {original_stats['line_count']:,}")
        print(f"  Blank lines: {original_stats['blank_lines']:,}")
        
        self.cleanup_formatting()
        
        validation_passed = self.validate()
        
        if validation_passed:
            self.write_output()
            self.generate_report()
            
            print("\n" + "=" * 70)
            print("✓ CLEANUP COMPLETE")
            print("=" * 70)
            print("\nNext steps:")
            print(f"  1. Review report: {self.report_file}")
            print(f"  2. Test {self.output_file} in EuroScope")
            print(f"  3. If good, replace original with cleaned file")
            print(f"  4. Then proceed to Pass 2 (reorganization)")
            print(f"  5. Backup is saved at: {self.backup_file}")
            print()
        else:
            print("\n" + "=" * 70)
            print("✗ VALIDATION FAILED - Cleanup aborted")
            print("=" * 70)
            print("\nNo files were modified. Check errors above.")
            print()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = 'TopSkyMaps.txt'
    
    cleaner = TopSkyMapsCleanup(input_file)
    cleaner.run()
