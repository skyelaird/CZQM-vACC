#!/usr/bin/env python3
"""
Analyze TopSkyMaps.txt to find current status of Layer 10-14 boundaries
Run this to see what's already completed.
"""

import sys

def analyze_topskymaps(filepath):
    """Find all MAP definitions and determine what's completed"""
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    print("=" * 80)
    print("TOPSKYMAPS.TXT ANALYSIS")
    print("=" * 80)
    print(f"\nTotal lines: {len(lines)}")
    print(f"File: {filepath}")
    
    # Find version
    for line in lines[:10]:
        if 'VERSION' in line.upper():
            print(f"Version: {line.strip()}")
            break
    
    # Find all MAP definitions
    maps = {}
    
    for i, line in enumerate(lines):
        if line.startswith('MAP:'):
            parts = line.strip().split(':')
            if len(parts) >= 2:
                layer_or_name = parts[1]
                if len(parts) >= 3:
                    name = parts[2]
                else:
                    name = layer_or_name
                
                if layer_or_name not in maps:
                    maps[layer_or_name] = []
                maps[layer_or_name].append({
                    'line': i + 1,
                    'name': name,
                    'full': line.strip()
                })
    
    # Report MAP definitions
    print("\n" + "=" * 80)
    print("ALL MAP DEFINITIONS:")
    print("=" * 80)
    
    for layer in sorted(maps.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        if layer.isdigit():
            layer_name = f"Layer {layer}"
        else:
            layer_name = layer
        
        print(f"\n{layer_name}: {len(maps[layer])} definition(s)")
        for m in maps[layer]:
            print(f"  Line {m['line']:5d}: {m['full']}")
    
    # Check for Class G areas specifically
    print("\n" + "=" * 80)
    print("CLASS G AREAS (Layer 10):")
    print("=" * 80)
    
    keywords = ['CHARLO', 'LABRADOR', 'ST_ANTHONY', 'ST ANTHONY']
    
    for keyword in keywords:
        found = []
        for i, line in enumerate(lines):
            if keyword.replace('_', ' ') in line.upper() or keyword.replace(' ', '_') in line.upper():
                found.append((i+1, line.strip()))
        
        if found:
            print(f"\n✓ {keyword}: FOUND ({len(found)} occurrences)")
            for line_num, text in found[:3]:
                print(f"    Line {line_num}: {text[:70]}")
        else:
            print(f"\n✗ {keyword}: NOT FOUND")
    
    # Layer 10-14 summary
    print("\n" + "=" * 80)
    print("LAYER STATUS SUMMARY:")
    print("=" * 80)
    
    layer_descriptions = {
        '10': 'Static uncontrolled (Class G)',
        '11': 'Cold neighbors (always visible)',
        '12': 'Internal delegations (APP/TWR)',
        '13': 'Hot neighbors (when online)',
        '14': 'CZQM/CZQX split'
    }
    
    for layer_num in range(10, 15):
        layer_str = str(layer_num)
        desc = layer_descriptions.get(layer_str, '')
        if layer_str in maps:
            print(f"✓ Layer {layer_num} ({desc}): {len(maps[layer_str])} boundaries defined")
        else:
            print(f"✗ Layer {layer_num} ({desc}): NOT STARTED")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    filepath = r"D:\GitHub\CZQM-vACC\TopSky\TopSkyMaps.txt"
    try:
        analyze_topskymaps(filepath)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
