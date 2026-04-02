# -*- coding: utf-8 -*-
"""
Скрипт для поиска матчей Dota 2 через OpenDota API.
OpenDota имеет публичный доступ без ключа.
"""
import sys
import io
import requests
import time
from pathlib import Path
from datetime import datetime

# Настраиваем кодировку
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Конфигурация
OUTPUT_DIR = Path("data/raw")
LINKS_FILE = Path("data/raw_links.txt")
TARGET_MATCHES = 50
REQUEST_DELAY = 1


def get_mode_name(mode):
    modes = {
        1: "All Pick",
        2: "Captains Mode",
        3: "All Random",
        4: "Single Draft",
        22: "Turbo",
        23: "Mutation"
    }
    return modes.get(mode, f"Mode {mode}")


def fetch_matches():
    print("=" * 60)
    print("ПОИСК МАТЧЕЙ ЧЕРЕЗ OPENDOTA API")
    print("=" * 60)
    
    all_matches = []
    offset = 0
    batch_size = 100
    
    stats = {"all_pick": 0, "turbo": 0, "other": 0}
    
    while len(all_matches) < TARGET_MATCHES:
        params = {"mmr_descending": True, "limit": batch_size, "offset": offset}
        
        print(f"\nЗапрос: offset={offset}, найдено={len(all_matches)}/{TARGET_MATCHES}")
        
        try:
            response = requests.get(
                "https://api.opendota.com/api/publicMatches",
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"[ОШИБКА] HTTP {response.status_code}")
                break
            
            matches = response.json()
            
            if not matches:
                print("[INFO] Матчей больше нет")
                break
            
            for match in matches:
                game_mode = match.get("game_mode", 0)
                
                if game_mode == 1:
                    stats["all_pick"] += 1
                    all_matches.append(match)
                elif game_mode == 22:
                    stats["turbo"] += 1
                    all_matches.append(match)
                else:
                    stats["other"] += 1
                    all_matches.append(match)
            
            print(f"  AllPick={stats['all_pick']}, Turbo={stats['turbo']}, Other={stats['other']}")
            
            if len(all_matches) >= TARGET_MATCHES:
                break
            
            offset += batch_size
            time.sleep(REQUEST_DELAY)
            
        except Exception as e:
            print(f"[ОШИБКА] {e}")
            break
    
    print(f"\nНайдено: {len(all_matches)} матчей")
    return all_matches


def save_links(matches, filepath):
    print(f"\nСохранение в {filepath}...")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Dota 2 Matches - OpenDota API\n")
        f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total: {len(matches)}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, match in enumerate(matches, 1):
            match_id = match.get("match_id", "N/A")
            game_mode = match.get("game_mode", 0)
            start_time = match.get("start_time", 0)
            
            dt_str = "N/A"
            if start_time > 0:
                dt = datetime.fromtimestamp(start_time / 1000)
                dt_str = dt.strftime('%Y-%m-%d %H:%M')
            
            f.write(f"{i}. Match ID: {match_id}\n")
            f.write(f"   Mode: {get_mode_name(game_mode)}\n")
            f.write(f"   Date: {dt_str}\n")
            f.write(f"   URL: https://www.opendota.com/matches/{match_id}\n\n")
    
    print(f"[OK] Saved {len(matches)} matches")


def main():
    print("\n" + "=" * 60)
    print("DOTA 2 MATCH SEARCH - OPENDOTA API")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    matches = fetch_matches()
    
    if matches:
        save_links(matches, LINKS_FILE)
        print(f"\n[SUCCESS] Found {len(matches)} matches!")
    else:
        print("\n[INFO] No matches found.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
