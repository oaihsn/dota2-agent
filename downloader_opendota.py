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
MIN_MATCH_AGE_HOURS = 24
TARGET_MATCHES = 50
REQUEST_DELAY = 1


def fetch_matches():
    """Получает матчи через OpenDota API."""
    
    print("=" * 60)
    print("ПОИСК МАТЧЕЙ ЧЕРЕЗ OPENDOTA API")
    print("=" * 60)
    
    all_valid_matches = []
    offset = 0
    batch_size = 100
    total_fetched = 0
    max_requests = 100  # Максимум запросов
    
    stats = {
        "allpick_rank": 0,
        "turbo": 0,
        "allpick_public": 0,
        "other": 0,
        "too_fresh": 0
    }
    
    requests_made = 0
    
    while len(all_valid_matches) < TARGET_MATCHES and requests_made < max_requests:
        requests_made += 1
        
        params = {
            "mmr_descending": True,
            "limit": batch_size,
            "offset": offset
        }
        
        print(f"\n[{requests_made}] Запрос: offset={offset}, найдено={len(all_valid_matches)}/{TARGET_MATCHES}")
        
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
            
            total_fetched += len(matches)
            
            for match in matches:
                lobby_type = match.get("lobby_type", -1)
                game_mode = match.get("game_mode", 0)
                start_time = match.get("start_time", 0)
                
                # Проверяем возраст
                age_hours = 0
                if start_time > 0:
                    match_dt = datetime.fromtimestamp(start_time / 1000)
                    age_hours = (datetime.now() - match_dt).total_seconds() / 3600
                
                if age_hours < MIN_MATCH_AGE_HOURS:
                    stats["too_fresh"] += 1
                    continue
                
                # Фильтруем по режиму
                # game_mode: 1=All Pick, 22=Turbo
                # lobby_type: 0=Public, 2=Ranked
                if game_mode == 1 and lobby_type in [0, 2]:
                    stats["allpick_rank"] += 1
                    all_valid_matches.append(match)
                elif game_mode == 22:
                    stats["turbo"] += 1
                else:
                    stats["other"] += 1
            
            print(f"    AllPick/Ranked={stats['allpick_rank']}, Turbo={stats['turbo']}, Other={stats['other']}, Fresh={stats['too_fresh']}")
            
            # Если нашли достаточно - выходим
            if len(all_valid_matches) >= TARGET_MATCHES:
                break
            
            offset += batch_size
            time.sleep(REQUEST_DELAY)
            
        except Exception as e:
            print(f"[ОШИБКА] {e}")
            break
    
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 60)
    print(f"Всего запросов: {requests_made}")
    print(f"Всего получено: {total_fetched}")
    print(f"Найдено All Pick/Ranked: {len(all_valid_matches)}")
    print(f"  - All Pick + Public/Ranked: {stats['allpick_rank']}")
    print(f"  - Turbo: {stats['turbo']}")
    print(f"  - Другие режимы: {stats['other']}")
    print(f"  - Свежие (<24ч): {stats['too_fresh']}")
    
    return all_valid_matches


def save_links(matches, filepath):
    """Сохраняет ссылки."""
    
    print(f"\nСохранение в {filepath}...")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Dota 2 Matches - OpenDota API\n")
        f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total: {len(matches)}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, match in enumerate(matches, 1):
            match_id = match.get("match_id", "N/A")
            lobby_type = match.get("lobby_type", -1)
            game_mode = match.get("game_mode", 0)
            start_time = match.get("start_time", 0)
            avg_mmr = match.get("avg_mmr", 0)
            
            dt_str = "N/A"
            if start_time > 0:
                dt = datetime.fromtimestamp(start_time / 1000)
                dt_str = dt.strftime('%Y-%m-%d %H:%M')
            
            lobby_name = {0: "Public", 2: "Ranked"}.get(lobby_type, str(lobby_type))
            
            f.write(f"{i}. Match ID: {match_id}\n")
            f.write(f"   Lobby: {lobby_name}, Mode: All Pick\n")
            f.write(f"   Date: {dt_str}\n")
            f.write(f"   Avg MMR: {avg_mmr}\n")
            f.write(f"   URL: https://www.opendota.com/matches/{match_id}\n")
            f.write("\n")
    
    print(f"[OK] Saved {len(matches)} matches")


def main():
    """Основная функция."""
    
    print("\n" + "=" * 60)
    print("DOTA 2 MATCH SEARCH - OPENDOTA API")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    matches = fetch_matches()
    
    if matches:
        save_links(matches, LINKS_FILE)
        print(f"\nFound {len(matches)} matches!")
    else:
        print("\nNo matches found.")
        print("\n[СОВЕТ] Все найденные матчи могут быть:")
        print("  - Turbo режим (не All Pick)")
        print("  - Менее 24 часов назад")
        print("  - Другие режимы (All Random, Captains Mode)")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
