# -*- coding: utf-8 -*-
"""
Скрипт для скачивания публичных матчей Dota 2 через OpenDota API.
Без привязки к конкретному Steam ID.
"""
import sys
import io
import time
import json
import requests
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

OPENDOTA_API = "https://api.opendota.com/api"
OUTPUT_DIR = Path("data/raw")
LINKS_FILE = Path("data/raw_links.txt")
MIN_MMR = 4000
BATCH_SIZE = 100

MODE_NAMES = {
    1: "All Pick",
    2: "Captains Mode", 
    3: "All Pick",
    4: "Single Draft",
    5: "All Random",
    6: "Captains Draft",
    8: "All Pick",
    9: "Captains Mode",
    10: "All Pick",
    12: "All Pick",
    13: "All Pick",
    14: "Ranked All Pick",
    15: "Diretide",
    16: "Captains Mode",
    18: "Arch All Pick",
    19: "Arch Captains",
    20: "All Pick",
    21: "Turbo",
    22: "Mutation",
}

def get_mode_name(mode):
    return MODE_NAMES.get(mode, f"Mode {mode}")

def get_rank_tier(avg_rank):
    """Конвертирует avg_rank_tier в примерный MMR"""
    if avg_rank is None:
        return "Unknown"
    tier = avg_rank // 10
    rank = avg_rank % 10
    if tier == 0:
        return "Herald"
    elif tier == 1:
        return "Guardian"
    elif tier == 2:
        return "Crusader"
    elif tier == 3:
        return "Archon"
    elif tier == 4:
        return "Legend"
    elif tier == 5:
        return "Ancient"
    elif tier == 6:
        return "Divine"
    elif tier == 7:
        return "Immortal"
    return f"Tier {tier}"

def fetch_public_matches():
    print("=" * 60)
    print("ПОИСК ПУБЛИЧНЫХ МАТЧЕЙ (MMR > 4000)")
    print("=" * 60)
    
    all_matches = []
    offset = 0
    
    try:
        while len(all_matches) < BATCH_SIZE:
            print(f"\n[1/3] Загрузка матчей (смещение {offset})...")
            
            url = f"{OPENDOTA_API}/publicMatches"
            params = {"mmr_above": MIN_MMR, "limit": 100, "offset": offset}
            
            print(f"[DEBUG] URL: {url}")
            print(f"[DEBUG] Params: {params}")
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"[ERROR] HTTP {response.status_code}")
                break
            
            matches = response.json()
            
            if not matches:
                print("[INFO] Больше матчей нет")
                break
            
            print(f"[OK] Получено: {len(matches)}")
            
            for match in matches:
                all_matches.append({
                    "match_id": match.get("match_id"),
                    "start_time": match.get("start_time"),
                    "duration": match.get("duration"),
                    "game_mode": match.get("game_mode"),
                    "avg_rank_tier": match.get("avg_rank_tier"),
                    "radiant_win": match.get("radiant_win"),
                })
            
            offset += 100
            
            if len(matches) < 100:
                break
            
            time.sleep(1)
        
        print(f"\n[OK] Всего собрано: {len(all_matches)}")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return []
    
    return all_matches


def save_links(matches, filepath):
    print(f"\n[2/3] Сохранение в {filepath}...")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Dota 2 Public Matches (MMR > {MIN_MMR})\n")
        f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total: {len(matches)}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, match in enumerate(matches, 1):
            match_id = match.get("match_id", "N/A")
            start_time = match.get("start_time", 0)
            duration = match.get("duration", 0)
            game_mode = match.get("game_mode", 0)
            avg_tier = match.get("avg_rank_tier", 0)
            
            dt_str = "N/A"
            if start_time > 0:
                dt = datetime.fromtimestamp(start_time)
                dt_str = dt.strftime('%Y-%m-%d %H:%M')
            
            mode_name = get_mode_name(game_mode)
            rank_name = get_rank_tier(avg_tier)
            
            f.write(f"{i}. Match ID: {match_id}\n")
            f.write(f"   Date: {dt_str}\n")
            f.write(f"   Duration: {duration}s ({duration//60}m)\n")
            f.write(f"   Mode: {mode_name}\n")
            f.write(f"   Avg Rank: {rank_name} (tier {avg_tier})\n")
            f.write(f"   URL: https://www.opendota.com/matches/{match_id}\n\n")
    
    print(f"[OK] Saved {len(matches)} matches")


def main():
    print("\n" + "=" * 60)
    print("DOTA 2 - PUBLIC MATCHES (OPENDOTA)")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    matches = fetch_public_matches()
    
    if matches:
        save_links(matches, LINKS_FILE)
        print(f"\n[SUCCESS] Saved {len(matches)} matches!")
    else:
        print("\n[INFO] No matches found.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
