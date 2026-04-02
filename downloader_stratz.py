# -*- coding: utf-8 -*-
"""
Скрипт для скачивания реплеев Dota 2 через Stratz API.
Требуется Bearer токен для авторизации.

Как получить токен:
1. Зайди на https://stratz.com в браузере
2. Нажми F12 -> Network (Сеть)
3. Обнови страницу
4. Найди любой запрос к api.stratz.com
5. Скопируй значение "Authorization: Bearer XXXXX"
6. Вставь токен ниже (без "Bearer ")
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
STRATZ_API = "https://api.stratz.com/graphql"
OUTPUT_DIR = Path("data/raw")
LINKS_FILE = Path("data/raw_links.txt")
MIN_MATCH_AGE_HOURS = 24
TARGET_MATCHES = 50

# ВСТАВЬ СВОЙ ТОКЕН НИЖЕ!
BEARER_TOKEN = "YOUR_BEARER_TOKEN_HERE"


# GraphQL запрос
QUERY = """
query publicMatches($options: PublicMatchesQueryOption) {
  publicMatches(options: $options) {
    matchId
    gameMode
    lobbyType
    startDateTime
    durationSeconds
    averageRank
    region
    players {
      heroId
      isRadiant
      accountId
    }
  }
}
"""


def fetch_matches():
    """Получает матчи через Stratz API."""
    
    print("=" * 60)
    print("ПОИСК МАТЧЕЙ ЧЕРЕЗ STRATZ API")
    print("=" * 60)
    
    if BEARER_TOKEN == "YOUR_BEARER_TOKEN_HERE":
        print("[ОШИБКА] Укажите Bearer токен!")
        print("\nКак получить токен:")
        print("1. Зайди на https://stratz.com в браузере")
        print("2. Нажми F12 -> Network (Сеть)")
        print("3. Обнови страницу")
        print("4. Найди запрос к api.stratz.com")
        print("5. Скопируй токен из Authorization header")
        print("6. Вставь в переменную BEARER_TOKEN")
        return []
    
    all_valid_matches = []
    skip = 0
    batch_size = 25
    total_fetched = 0
    
    stats = {"allpick": 0, "turbo": 0, "other": 0, "too_fresh": 0}
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }
    
    while len(all_valid_matches) < TARGET_MATCHES:
        print(f"\nЗапрос: skip={skip}, найдено={len(all_valid_matches)}/{TARGET_MATCHES}")
        
        variables = {
            "options": {
                "take": batch_size,
                "skip": skip,
                "gameMode": 1,
                "lobbyType": [0, 2],
                "isStats": True
            }
        }
        
        try:
            response = requests.post(
                STRATZ_API,
                json={"query": QUERY, "variables": variables},
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and data["data"]:
                    matches = data["data"].get("publicMatches", [])
                    
                    if not matches:
                        print("[INFO] Матчей больше нет")
                        break
                    
                    total_fetched += len(matches)
                    
                    for match in matches:
                        game_mode = match.get("gameMode", 0)
                        start_time = match.get("startDateTime", 0)
                        
                        age_hours = 0
                        if start_time > 0:
                            match_dt = datetime.fromtimestamp(start_time)
                            age_hours = (datetime.now() - match_dt).total_seconds() / 3600
                        
                        if age_hours < MIN_MATCH_AGE_HOURS:
                            stats["too_fresh"] += 1
                            continue
                        
                        if game_mode == 1:
                            stats["allpick"] += 1
                            all_valid_matches.append(match)
                        elif game_mode == 22:
                            stats["turbo"] += 1
                        else:
                            stats["other"] += 1
                    
                    print(f"    AllPick={stats['allpick']}, Turbo={stats['turbo']}")
                    
                    if len(matches) < batch_size:
                        break
                    
                    skip += batch_size
                    time.sleep(0.3)
                else:
                    print(f"[INFO] Нет данных: {data}")
                    break
            else:
                print(f"[ОШИБКА] HTTP {response.status_code}")
                break
                
        except Exception as e:
            print(f"[ОШИБКА] {e}")
            break
    
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 60)
    print(f"Получено: {total_fetched}")
    print(f"Найдено All Pick: {len(all_valid_matches)}")
    
    return all_valid_matches


def save_links(matches, filepath):
    """Сохраняет ссылки."""
    
    print(f"\nСохранение в {filepath}...")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Dota 2 Matches - Stratz API\n")
        f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total: {len(matches)}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, match in enumerate(matches, 1):
            match_id = match.get("matchId", "N/A")
            start_time = match.get("startDateTime", 0)
            duration = match.get("durationSeconds", 0)
            avg_rank = match.get("averageRank", 0)
            
            dt_str = "N/A"
            if start_time > 0:
                dt = datetime.fromtimestamp(start_time)
                dt_str = dt.strftime('%Y-%m-%d %H:%M')
            
            f.write(f"{i}. Match ID: {match_id}\n")
            f.write(f"   Date: {dt_str}\n")
            f.write(f"   Duration: {duration}s ({duration//60}m)\n")
            f.write(f"   Avg Rank: {avg_rank}\n")
            f.write(f"   URL: https://stratz.com/matches/{match_id}\n")
            f.write("\n")
    
    print(f"[OK] Saved {len(matches)} matches")


def main():
    """Основная функция."""
    
    print("\n" + "=" * 60)
    print("DOTA 2 MATCH SEARCH - STRATZ API")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    matches = fetch_matches()
    
    if matches:
        save_links(matches, LINKS_FILE)
        print(f"\nFound {len(matches)} matches!")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
