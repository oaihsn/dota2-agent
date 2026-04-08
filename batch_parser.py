# -*- coding: utf-8 -*-
"""
batch_parser.py - Batch processing of multiple Dota 2 replay files

Features:
- File Scanning: Looks into /raw folder for all .dem files
- Looping: Parses each file using Clarity + Python processing
- Error Handling: Uses try-except, logs errors and continues
- Progress Bar: Uses tqdm to show progress
- Data Merging: Appends all data into master_dataset.csv with match_id
- Concurrency: Uses multiprocessing (2-4 workers)
"""
import subprocess
import csv
import re
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
PARENT_DIR = BASE_DIR.parent
CLARITY_DIR = PARENT_DIR / "clarity-examples"
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "master_dataset.csv"
HEROES_FILE = BASE_DIR / "data" / "heroes.json"
GRADLEW = CLARITY_DIR / "gradlew.bat"
TICK_INTERVAL = 30  # Sample every N ticks
MAX_WORKERS = 4  # Number of parallel processes

# Map boundaries
MAP_MIN = -12800
MAP_MAX = 12800
MAX_HP = 2000


def load_heroes(filepath):
    """Load heroes.json and create name -> ID mapping."""
    with open(filepath, 'r', encoding='utf-8') as f:
        heroes_dict = json.load(f)
    
    hero_name_to_id = {}
    for hero_id, hero_name in heroes_dict.items():
        hero_name_to_id[hero_name] = int(hero_id)
    
    # Add known name fixes
    name_fixes = {
        'Magnataur': 97, 'DoomBringer': 69, 'QueenOfPain': 39, 'WitchDoctor': 30,
    }
    hero_name_to_id.update(name_fixes)
    return hero_name_to_id


def run_clarity_hero_track(dem_file):
    """Run Clarity hero_track for a single .dem file."""
    cmd = [str(GRADLEW), "hero_trackRun", "--args", str(dem_file)]
    
    result = subprocess.run(
        cmd,
        cwd=str(CLARITY_DIR),
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=300  # 5 minute timeout per file
    )
    
    return result.stdout + result.stderr


def parse_hero_track_output(output):
    """Parse Clarity output into records."""
    records = []
    lines = output.split('\n')
    
    for line in lines:
        if line.startswith('tick,player') or 'unknown' in line:
            continue
        
        match = re.match(r'^(\d+),(\d+),(\w+),\[([\d.]+),\s*([\d.]+),\s*([\d.]+)\],(\d+)$', line.strip())
        if match:
            records.append({
                'tick': int(match.group(1)),
                'player_id': int(match.group(2)),
                'hero_name': match.group(3),
                'x': float(match.group(4)),
                'y': float(match.group(5)),
                'z': float(match.group(6)),
                'hp': int(match.group(7)),
            })
    
    return records


def filter_by_interval(records, interval=30):
    """Filter records to every Nth state per player."""
    filtered = []
    player_records = {}
    
    for r in records:
        pid = r['player_id']
        if pid not in player_records:
            player_records[pid] = []
        player_records[pid].append(r)
    
    for pid, recs in player_records.items():
        for i in range(0, len(recs), interval):
            filtered.append(recs[i])
    
    return sorted(filtered, key=lambda x: (x['tick'], x['player_id']))


def process_single_replay(args):
    """Process a single replay file. Designed for multiprocessing."""
    dem_file, match_id, heroes_map = args
    
    try:
        # Run Clarity parser
        output = run_clarity_hero_track(dem_file)
        
        # Parse output
        records = parse_hero_track_output(output)
        
        if not records:
            return {'match_id': match_id, 'status': 'empty', 'count': 0, 'records': []}
        
        # Filter by interval
        filtered = filter_by_interval(records, TICK_INTERVAL)
        
        # Process and normalize each record
        processed = []
        for rec in filtered:
            hero_id = heroes_map.get(rec['hero_name'], 0)
            x_norm = (rec['x'] - MAP_MIN) / (MAP_MAX - MAP_MIN)
            y_norm = (rec['y'] - MAP_MIN) / (MAP_MAX - MAP_MIN)
            hp_percent = (rec['hp'] / MAX_HP * 100)
            
            processed.append({
                'match_id': match_id,
                'tick': rec['tick'],
                'player_id': rec['player_id'],
                'hero_id': hero_id,
                'hero_name': rec['hero_name'],
                'x': round(x_norm, 6),
                'y': round(y_norm, 6),
                'hp_raw': rec['hp'],
                'hp_percent': round(min(hp_percent, 100), 2),
            })
        
        return {'match_id': match_id, 'status': 'success', 'count': len(processed), 'records': processed}
        
    except Exception as e:
        return {
            'match_id': match_id,
            'status': 'error',
            'error': str(e),
            'count': 0,
            'records': []
        }


def scan_dem_files(raw_dir):
    """Scan directory for all .dem files."""
    dem_files = list(raw_dir.glob("*.dem"))
    print(f"Found {len(dem_files)} .dem files in {raw_dir}")
    return dem_files


def main():
    print("=" * 60)
    print("BATCH PARSER - Multiple Dota 2 Replay Processing")
    print("=" * 60)
    print()
    
    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load heroes mapping
    heroes_map = load_heroes(HEROES_FILE)
    
    # Scan for .dem files
    dem_files = scan_dem_files(RAW_DIR)
    
    if not dem_files:
        print("No .dem files found! Place replay files in data/raw/")
        return
    
    # Prepare arguments for parallel processing
    tasks = []
    for i, dem_file in enumerate(dem_files):
        match_id = dem_file.stem  # Use filename as match_id
        tasks.append((dem_file, match_id, heroes_map))
    
    print(f"Processing {len(tasks)} replays with {MAX_WORKERS} workers...")
    print()
    
    all_records = []
    errors = []
    
    # Process with multiprocessing and tqdm
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_single_replay, task): task for task in tasks}
        
        with tqdm(total=len(tasks), desc="Parsing replays", unit="replay") as pbar:
            for future in as_completed(futures):
                result = future.result()
                
                if result['status'] == 'success':
                    all_records.extend(result['records'])
                    pbar.set_postfix_str(f"{result['count']} records")
                elif result['status'] == 'error':
                    errors.append(result)
                    print(f"\nERROR in {result['match_id']}: {result.get('error', 'Unknown')}")
                elif result['status'] == 'empty':
                    print(f"\nWARNING: {result['match_id']} returned no data")
                
                pbar.update(1)
    
    # Save master dataset
    print(f"\nTotal records collected: {len(all_records)}")
    
    if all_records:
        # Sort by match_id and tick
        all_records.sort(key=lambda x: (x['match_id'], x['tick'], x['player_id']))
        
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = ['match_id', 'tick', 'player_id', 'hero_id', 'hero_name', 'x', 'y', 'hp_raw', 'hp_percent']
        
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_records)
        
        print(f"Saved to: {OUTPUT_FILE}")
    else:
        print("No data to save!")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total replays processed: {len(tasks)}")
    print(f"Successful: {len(tasks) - len(errors)}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  - {err['match_id']}: {err.get('error', 'Unknown error')}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()