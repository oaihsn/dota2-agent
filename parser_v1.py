# -*- coding: utf-8 -*-
"""
parser_v1.py - Python wrapper for Clarity hero_track example
Extracts hero data with tick filter (every 30 ticks) including health!

Updated: Now includes hero names and health from hero_track!
"""
import subprocess
import csv
import re
from pathlib import Path

# Configuration - clarity-examples is sibling to dota2-agent
BASE_DIR = Path(__file__).parent.resolve()
PARENT_DIR = BASE_DIR.parent
CLARITY_DIR = PARENT_DIR / "clarity-examples"
DEMO_FILE = BASE_DIR / "data" / "raw" / "8749329335.dem"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "training_data_clarity.csv"
TICK_INTERVAL = 30

# Java classpath
GRADLEW = CLARITY_DIR / "gradlew.bat"


def run_clarity_hero_track():
    """Run Clarity hero_track example and capture output."""
    cmd = [
        str(GRADLEW),
        "hero_trackRun",
        "--args", str(DEMO_FILE)
    ]
    
    print(f"Running Clarity hero_track...")
    print(f"  Demo: {DEMO_FILE.name}")
    print(f"  Command: {' '.join(cmd)}")
    print()
    
    # Run and capture output
    result = subprocess.run(
        cmd,
        cwd=str(CLARITY_DIR),
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    return result.stdout + result.stderr


def parse_hero_track_output(output):
    """
    Parse Clarity hero_track output.
    Format: "tick,player,hero_name,[x,y,z],health"
    Example: "4031,5,Magnataur,[23271.594, 23017.875, 16768.0],720"
    
    Returns list of records with tick, player_id, hero_name, pos_x, pos_y, pos_z, health
    """
    records = []
    
    # Skip header line and any warning lines
    lines = output.split('\n')
    for line in lines:
        # Skip header and warnings
        if line.startswith('tick,player') or 'unknown' in line:
            continue
        
        # Parse data line: "tick,player,hero,[x, y, z],health"
        # Example: "4031,5,Magnataur,[23271.594, 23017.875, 16768.0],720"
        match = re.match(r'^(\d+),(\d+),(\w+),\[([\d.]+),\s*([\d.]+),\s*([\d.]+)\],(\d+)$', line.strip())
        if match:
            tick = int(match.group(1))
            player_id = int(match.group(2))
            hero_name = match.group(3)
            x = float(match.group(4))
            y = float(match.group(5))
            z = float(match.group(6))
            health = int(match.group(7))
            
            records.append({
                'tick': tick,
                'player_id': player_id,
                'hero_name': hero_name,
                'pos_x': x,
                'pos_y': y,
                'pos_z': z,
                'health': health,
            })
    
    return records


def filter_by_interval(records, interval=30):
    """Filter records to only include every Nth state per player."""
    filtered = []
    
    # Group by player
    player_records = {}
    for r in records:
        pid = r['player_id']
        if pid not in player_records:
            player_records[pid] = []
        player_records[pid].append(r)
    
    # Take every Nth record per player
    for pid, recs in player_records.items():
        for i in range(0, len(recs), interval):
            filtered.append(recs[i])
    
    return sorted(filtered, key=lambda x: (x['tick'], x['player_id']))


def main():
    print("=" * 60)
    print("CLARITY PARSER v1 - Dota 2 Replay Data Extraction")
    print("=" * 60)
    print()
    
    # Debug paths
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"CLARITY_DIR: {CLARITY_DIR}")
    print(f"DEMO_FILE: {DEMO_FILE}")
    print(f"GRADLEW: {GRADLEW}")
    print()
    
    # Check files exist
    if not DEMO_FILE.exists():
        print(f"ERROR: Demo file not found: {DEMO_FILE}")
        return
    
    if not GRADLEW.exists():
        print(f"ERROR: Gradle not found: {GRADLEW}")
        return
    
    # Step 1: Run hero_track
    output = run_clarity_hero_track()
    
    # Step 2: Parse output
    print("Parsing hero track data...")
    records = parse_hero_track_output(output)
    print(f"Total position+health records: {len(records)}")
    
    # Step 3: Filter by tick interval
    print(f"Filtering to every {TICK_INTERVAL} ticks...")
    filtered = filter_by_interval(records, TICK_INTERVAL)
    print(f"Filtered records: {len(filtered)}")
    
    # Show sample output
    print("\n=== SAMPLE OUTPUT (verification) ===")
    sample_lines = [l for l in output.split('\n') if re.match(r'^\d+,\d+,\w+,\[', l)][:5]
    for line in sample_lines:
        print(line)
    print("...")
    print()
    
    # Step 4: Save to CSV with columns: tick, hero_name, x, y, hp
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['tick', 'hero_name', 'x', 'y', 'hp'])
        writer.writeheader()
        for rec in filtered:
            writer.writerow({
                'tick': rec['tick'],
                'hero_name': rec['hero_name'],
                'x': round(rec['pos_x'], 2),
                'y': round(rec['pos_y'], 2),
                'hp': rec['health']  # Now includes real health values!
            })
    
    print(f"=== SAVED ===")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Total records: {len(filtered)}")
    
    # Show first few rows with hero names and health
    print("\nSample data with hero names and health:")
    for r in filtered[:10]:
        print(f"  tick={r['tick']}, hero={r['hero_name']}, pos=({r['pos_x']:.1f}, {r['pos_y']:.1f}), hp={r['health']}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()