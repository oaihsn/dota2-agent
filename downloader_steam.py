# -*- coding: utf-8 -*-
"""
Скрипт для поиска матчей Dota 2 через Steam Web API.
Использует GetMatchHistory для поиска рейтинговых матчей.
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
# Получите ключ на https://steamcommunity.com/dev/apikey
STEAM_API_KEY = "YOUR_STEAM_API_KEY"  # <-- ВСТАВЬТЕ СВОЙ КЛЮЧ!
STEAM_API = "https://api.steampowered.com"
OUTPUT_DIR = Path("data/raw")
LINKS_FILE = Path("data/raw_links.txt")
MIN_MATCH_AGE_HOURS = 24
TARGET_MATCHES = 50


def get_match_history(start_match_id=None):
    """Получает историю матчей через Steam API."""
    
    params = {
        "key": STEAM_API_KEY,
        "min_players": 10
    }
    
    if start_match_id:
        params["start_at_match_id"] = start_match_id
    
    url = f"{STEAM_API}/IDOTA2Match_570/GetMatchHistory/v001/"
    
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json()
    except:
        return None


def get_match_details(match_id):
    """Получает детали матча."""
    
    url = f"{STEAM_API}/IDOTA2Match_570/GetMatchDetails/v001/"
    params = {"key": STEAM_API_KEY, "match_id": match_id}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        return response.json()
    except:
        return None


def fetch_matches():
    """Ищет рейтинговые матчи."""
    
    print("=" * 60)
    print("ПОИСК МАТЧЕЙ ЧЕРЕЗ STEAM API")
    print("=" * 60)
    
    if STEAM_API_KEY == "YOUR_STEAM_API_KEY":
        print("[ОШИБКА] Укажите Steam API ключ!")
        print("Получите ключ на: https://steamcommunity.com/dev/apikey")
        return []
    
    print(f"Фильтры:")
    print(f"  - возраст: > {MIN_MATCH_AGE_HOURS} часов")
    print(f"  - цель: найти {TARGET_MATCHES} матчей")
    
    all_matches = []
    start_id = None
    total = 0
    
    stats = {"valid": 0, "too_fresh": 0, "no_details": 0}
    
    while len(all_matches) < TARGET_MATCHES and total < 500:
        print(f"\nЗапрос... найдено={len(all_matches)}/{TARGET_MATCHES}")
        
        result = get_match_history(start_id)
        
        if not result or "result" not in result:
            print("[INFO] Нет данных")
            break
        
        matches = result["result"].get("matches", [])
        
        if not matches:
            print("[INFO] Матчей больше нет")
            break
        
        for match in matches:
            total += 1
            
            match_id = match.get("match_id")
            start_time = match.get("start_time", 0)
            
            # Проверяем возраст
            age_hours = 0
            if start_time > 0:
                match_dt = datetime.fromtimestamp(start_time)
                age_hours = (datetime.now() - match_dt).total_seconds() / 3600
            
            if age_hours < MIN_MATCH_AGE_HOURS:
                stats["too_fresh"] += 1
                continue
            
            # Получаем детали для проверки lobby_type
            details = get_match_details(match_id)
            
            if details and "result" in details:
                lobby = details["result"].get("lobby_type", -1)
                mode = details["result"].get("game_mode", 0)
                
                # lobby_type: 0=Public, 2=Ranked
                # game_mode: 1=All Pick, 2=CAPTAINS, 3=DRAFT
                if lobby in [0, 2] and mode == 1:
                    stats["valid"] += 1
                    all_matches.append({
                        "match_id": match_id,
                        "start_time": start_time,
                        "lobby_type": lobby,
                        "game_mode": mode,
                        "duration": details["result"].get("duration", 0)
                    })
        
        # Следующая страница
        start_id = matches[-1].get("match_id") - 1
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 60)
    print(f"Всего проверено: {total}")
    print(f"Найдено All Pick/Ranked: {len(all_matches)}")
    print(f"  - Валидных: {stats['valid']}")
    print(f"  - Свежих: {stats['too_fresh']}")
    
    return all_matches


def save_links(matches, filepath):
    """Сохраняет ссылки."""
    
    print(f"\nСохранение в {filepath}...")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Dota 2 Matches - Steam API\n")
        f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total: {len(matches)}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, m in enumerate(matches, 1):
            dt = datetime.fromtimestamp(m["start_time"])
            duration = m.get("duration", 0)
            
            f.write(f"{i}. Match ID: {m['match_id']}\n")
            f.write(f"   Date: {dt.strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"   Duration: {duration}s ({duration//60}m)\n")
            f.write(f"   URL: https://www.dotabuff.com/matches/{m['match_id']}\n")
            f.write("\n")
    
    print(f"[OK] Saved {len(matches)} matches")


def main():
    """Основная функция."""
    
    print("\n" + "=" * 60)
    print("DOTA 2 MATCH SEARCH - STEAM API")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    matches = fetch_matches()
    
    if matches:
        save_links(matches, LINKS_FILE)
        print(f"\nFound {len(matches)} matches!")
    else:
        print("\nNo matches found.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
