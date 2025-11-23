#!/usr/bin/env python3
"""
Run this script on your Windows machine to extract CHARLO-NO-CONTROL from ESE.
Usage: python extract_charlo_windows.py
"""

import os
import re

# Paths (Windows format)
ESE_PATH = r"D:\GitHub\CZQM-vACC\TopSky\References\CZQQ-DO-NOT-USE_20251107023304-251101-0017.ese"
OUTPUT_PATH = r"D:\GitHub\CZQM-vACC\TopSky\CHARLO_EXTRACTED.txt"

def extract_charlo():
    """Extract CHARLO-NO-CONTROL sector and sectorlines from ESE"""
    
    print("Reading ESE file...")
    with open(ESE_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    output = []
    output.append("="*80)
    output.append("CHARLO-NO-CONTROL EXTRACTION")
    output.append("="*80)
    output.append("")
    
    # Find CHARLO in SECTORS section
    in_sectors = False
    charlo_found = False
    border_ids = []
    
    for i, line in enumerate(lines):
        if '[SECTORS]' in line:
            in_sectors = True
        elif in_sectors and line.startswith('['):
            in_sectors = False
        
        if in_sectors and 'CHARLO-NO-CONTROL' in line:
            output.append("SECTOR DEFINITION:")
            output.append("-" * 80)
            output.append(f"Line {i+1}: {line.rstrip()}")
            charlo_found = True
            
            # Get next few lines (OWNER, BORDER, etc.)
            for j in range(i+1, min(i+10, len(lines))):
                next_line = lines[j].rstrip()
                output.append(f"Line {j+1}: {next_line}")
                
                if next_line.startswith('BORDER:'):
                    # Extract IDs
                    border_part = next_line.replace('BORDER:', '')
                    border_ids = [b.strip() for b in border_part.split(':') if b.strip()]
                elif next_line.startswith('SECTOR:') or next_line.strip() == '':
                    break
            
            output.append("")
            break
    
    if not charlo_found:
        output.append("ERROR: CHARLO-NO-CONTROL not found in [SECTORS]!")
        return "\n".join(output)
    
    output.append(f"BORDER IDs found: {border_ids}")
    output.append("")
    
    # Find SECTORLINE definitions
    output.append("="*80)
    output.append("SECTORLINE DEFINITIONS:")
    output.append("="*80)
    output.append("")
    
    for border_id in border_ids:
        found_sectorline = False
        collecting = False
        
        for i, line in enumerate(lines):
            if line.startswith(f'SECTORLINE:{border_id}'):
                output.append(f"SECTORLINE:{border_id} (Line {i+1})")
                output.append("-" * 80)
                found_sectorline = True
                collecting = True
                continue
            
            if collecting:
                stripped = line.strip()
                # End of this sectorline?
                if stripped.startswith('SECTORLINE:') or stripped == '':
                    output.append("")
                    break
                # Coordinate line
                if ':' in stripped and not stripped.startswith(';'):
                    output.append(stripped)
        
        if not found_sectorline:
            output.append(f"WARNING: SECTORLINE:{border_id} not found!")
            output.append("")
    
    result = "\n".join(output)
    
    # Write to file
    print(f"Writing to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print("Done!")
    print(f"\nExtracted data saved to: {OUTPUT_PATH}")
    return result

if __name__ == '__main__':
    try:
        result = extract_charlo()
        print("\n" + "="*80)
        print("PREVIEW:")
        print("="*80)
        print(result[:1000])  # Show first 1000 chars
        print("...")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
