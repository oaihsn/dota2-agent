# -*- coding: utf-8 -*-
"""
batch_parser_v2.py - Enhanced batch processing with movement vectors and threat detection

Features:
- Smart Filtering: Skip dead (hp=0), AFK (no movement), pre-game without movement
- Movement Vectors: vx, vy columns for velocity tracking
- Threat Detection: enemy_near (1200 units), under_tower (800 units)
"""
import subprocess
import csv
import re
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
PARENT_DIR = BASE_DIR.parent
CLARITY_DIR = PARENT_DIR / "clarity-examples"
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "master_dataset_v2.csv"
HEROES_FILE = BASE_DIR / "data" / "heroes.json"
GRADLEW = CLARITY_DIR / "gradlew.bat"
TICK_INTERVAL = 15
MAX_WORKERS = 4


def load_heroes(filepath):
    """Load heroes.json and create name -> ID mapping."""
    with open(filepath, 'r', encoding='utf-8') as f:
        heroes_dict = json.load(f)
    
    hero_name_to_id = {}
    for hero_id, hero_name in heroes_dict.items():
        hero_name_to_id[hero_name.lower()] = int(hero_id)
        hero_name_to_id["npc_dota_hero_" + hero_name.lower()] = int(hero_id)
    
    name_fixes = {
        'magnataur': 97, 'doombringer': 69, 'queen of pain': 39, 'witch doctor': 30,
    }
    hero_name_to_id.update(name_fixes)
    return hero_name_to_id


def run_clarity_enhanced(dem_file):
    """Run Clarity enhanced_hero_track for a single .dem file."""
    cmd = [str(GRADLEW), "enhanced_hero_trackRun", "--args", str(dem_file)]
    
    result = subprocess.run(
        cmd,
        cwd=str(CLARITY_DIR),
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=600,
        bufsize=10**6
    )
    
    return result.stdout + result.stderr


def parse_enhanced_output(output, match_id, heroes_map):
    """Parse enhanced Clarity output into records."""
    records = []
    lines = output.split('\n')
    
    header_skipped = False
    first_valid_record_printed = False
    line_count = 0
    unique_players = set()
    
    for line in lines:
        line_count += 1
        
        if line_count % 10000 == 0:
            print(f"Processing line {line_count}...")
        
        if not header_skipped:
            if line.startswith('match_id,tick'):
                header_skipped = True
            continue
        
        # Parse Key-Value format
        match = re.search(r"\[DOTA_DATA\](.+?)\[/DOTA_DATA\]", line)
        if not match:
            continue
        
        line = match.group(1).strip()
        if not line:
            continue
        
        try:
            # Parse key-value format
            data = {}
            for item in line.split('|'):
                if ':' in item:
                    key, val = item.split(':', 1)
                    data[key] = val
            
            # Extract values
            hero_name = data.get('hero', 'unknown')
            hero_id = heroes_map.get(hero_name.lower(), heroes_map.get("npc_dota_hero_" + hero_name.lower(), 0))
            
            x = float(data.get('x', '0').replace(',', '.') or '0')
            y = float(data.get('y', '0').replace(',', '.') or '0')
            vx = float(data.get('vx', '0').replace(',', '.') or '0')
            vy = float(data.get('vy', '0').replace(',', '.') or '0')
            hp = float(data.get('hp', '0').replace(',', '.') or '0')
            mana = float(data.get('mana', '0').replace(',', '.') or '0')
            level = int(data.get('lvl', '0') or '0')
            p_id = int(data.get('p_id', '0') or '0')
            tick = int(data.get('tick', '0') or '0')
            enemy_near = data.get('enemy_near', 'false').lower() == 'true'
            under_tower = data.get('under_tower', 'false').lower() == 'true'
            
            # Track unique players
            unique_players.add(p_id)
            
            # Debug output
            if not first_valid_record_printed and x != 0:
                print(f"Found Hero: {hero_name} at X: {x}, Y: {y}, Vx: {vx}, Vy: {vy}")
                first_valid_record_printed = True
            
            record = {
                'match_id': data.get('match', match_id),
                'tick': tick,
                'player_id': p_id,
                'hero_name': hero_name,
                'hero_id': hero_id,
                'x': x,
                'y': y,
                'vx': vx,
                'vy': vy,
                'hp_pct': hp,
                'mana_pct': mana,
                'level': level,
                'item0': 0, 'item1': 0, 'item2': 0, 'item3': 0, 'item4': 0, 'item5': 0,
                'dist_creep': 2000.0,
                'creep_hp': 0,
                'dist_tower': 2000.0,
                'gold_delta': 0,
                'xp_delta': 0,
                'enemy_near': 1 if enemy_near else 0,
                'under_tower': 1 if under_tower else 0,
            }
            
            records.append(record)
            
        except (ValueError, IndexError) as e:
            continue
    
    print(f"Total records: {len(records)}, Unique players: {sorted(unique_players)}")
    return records


def filter_by_interval(records, interval=15):
    """Filter records to every Nth tick per player."""
    filtered = []
    player_records = {}
    
    for r in records:
        key = r['player_id']
        if key not in player_records:
            player_records[key] = []
        player_records[key].append(r)
    
    for key, recs in player_records.items():
        for i in range(0, len(recs), interval):
            filtered.append(recs[i])
    
    return sorted(filtered, key=lambda x: (x['tick'], x['player_id']))


def process_single_replay(args):
    """Process a single replay file."""
    dem_file, match_id, heroes_map = args
    
    try:
        output = run_clarity_enhanced(dem_file)
        records = parse_enhanced_output(output, match_id, heroes_map)
        
        if not records:
            return {'match_id': match_id, 'status': 'empty', 'count': 0, 'records': []}
        
        filtered = filter_by_interval(records, TICK_INTERVAL)
        
        return {'match_id': match_id, 'status': 'success', 'count': len(filtered), 'records': filtered}
        
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
    print("=" * 70)
    print("BATCH PARSER v2 - Smart Filtering + Movement Vectors + Threat Detection")
    print("=" * 70)
    print()
    
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    heroes_map = load_heroes(HEROES_FILE)
    print(f"Loaded {len(heroes_map)} hero mappings")
    
    dem_files = scan_dem_files(RAW_DIR)
    
    if not dem_files:
        print("No .dem files found! Place replay files in data/raw/")
        return
    
    tasks = []
    for dem_file in dem_files:
        match_id = dem_file.stem
        tasks.append((dem_file, match_id, heroes_map))
    
    print(f"Processing {len(tasks)} replays with {MAX_WORKERS} workers...")
    print(f"Output: {OUTPUT_FILE}")
    print()
    
    all_records = []
    errors = []
    
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
    
    print(f"\nTotal records collected: {len(all_records)}")
    
    if all_records:
        all_records.sort(key=lambda x: (x['match_id'], x['tick'], x['player_id']))
        
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            'match_id', 'tick', 'player_id', 'hero_name', 'hero_id',
            'x', 'y', 'vx', 'vy',
            'hp_pct', 'mana_pct', 'level',
            'item0', 'item1', 'item2', 'item3', 'item4', 'item5',
            'dist_creep', 'creep_hp', 'dist_tower', 'gold_delta', 'xp_delta',
            'enemy_near', 'under_tower'
        ]
        
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_records)
        
        print(f"Saved to: {OUTPUT_FILE}")
        
        # Print stats
        unique_players = sorted(set(r['player_id'] for r in all_records))
        print(f"Unique player_ids: {unique_players}")
        
        # Count enemy_near and under_tower
        enemy_count = sum(1 for r in all_records if r['enemy_near'])
        tower_count = sum(1 for r in all_records if r['under_tower'])
        print(f"Records with enemy nearby: {enemy_count} ({100*enemy_count/len(all_records):.1f}%)")
        print(f"Records under tower: {tower_count} ({100*tower_count/len(all_records):.1f}%)")
    else:
        print("No data to save!")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total replays processed: {len(tasks)}")
    print(f"Successful: {len(tasks) - len(errors)}")
    print(f"Errors: {len(errors)}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()