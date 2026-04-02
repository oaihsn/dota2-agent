# -*- coding: utf-8 -*-
"""
Скрипт для скачивания реплеев Dota 2 через OpenDota API.
Автоматически ищет All Pick / Ranked матчи, пока не найдёт нужное количество.
"""
import sys
import io
import os
import requests
import time
from pathlib import Path
from datetime import datetime

# Настраиваем кодировку для вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# Конфигурация
API_URL = "https://api.opendota.com/api/publicMatches"
OUTPUT_DIR = Path("data/raw")
LINKS_FILE = Path("data/raw_links.txt")
MIN_MATCH_AGE_HOURS = 24  # Минимум 1 день назад
TARGET_MATCHES = 50  # Ищем минимум 50 матчей
MAX_API_CALLS = 50  # Максимум запросов к API (каждый = 100 матчей)
REQUEST_DELAY = 1  # Задержка между запросами (сек)


def is_valid_match(match):
    """Проверяет, подходит ли матч по критериям."""
    
    # 1. Проверяем lobby_type (должен быть Public/Ranked)
    lobby_type = match.get("lobby_type", -1)
    is_ranked = lobby_type in [0, 2]  # 0=Public, 2=Ranked
    
    # 2. Проверяем game_mode (должен быть All Pick)
    game_mode = match.get("game_mode", -1)
    is_all_pick = game_mode == 1
    
    # 3. Проверяем возраст матча (минимум 24 часа)
    start_time = match.get("start_time", 0)
    age_hours = 0
    if start_time > 0:
        match_datetime = datetime.fromtimestamp(start_time / 1000)
        now = datetime.now()
        age_hours = (now - match_datetime).total_seconds() / 3600
    
    is_old_enough = age_hours >= MIN_MATCH_AGE_HOURS
    
    return is_ranked, is_all_pick, age_hours


def fetch_matches_loop():
    """Ищет матчи через OpenDota API, пока не найдёт нужное количество."""
    
    print("=" * 60)
    print("ПОИСК ALL PICK / RANKED МАТЧЕЙ")
    print("=" * 60)
    
    print(f"Фильтры:")
    print(f"  - lobby_type: Public (0) или Ranked (2)")
    print(f"  - game_mode: All Pick (1)")
    print(f"  - возраст: > {MIN_MATCH_AGE_HOURS} часов")
    print(f"  - цель: найти {TARGET_MATCHES} матчей")
    
    all_valid_matches = []
    total_fetched = 0
    api_calls = 0
    
    # Статистика
    stats = {
        "ranked_allpick": 0,
        "turbo": 0,
        "other_modes": 0,
        "too_fresh": 0,
        "no_api_data": 0
    }
    
    while len(all_valid_matches) < TARGET_MATCHES and api_calls < MAX_API_CALLS:
        api_calls += 1
        offset = (api_calls - 1) * 100
        
        params = {
            "mmr_descending": True,
            "limit": 100,
            "offset": offset
        }
        
        print(f"\n[{api_calls}/{MAX_API_CALLS}] Запрос к API (offset={offset})...")
        
        try:
            response = requests.get(API_URL, params=params, timeout=30)
            response.raise_for_status()
            matches = response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ОШИБКА] Не удалось получить данные: {e}")
            break
        
        if not matches:
            print("[INFO] API вернул пустой список, прекращаем поиск")
            break
        
        total_fetched += len(matches)
        print(f"    Получено матчей: {len(matches)}, всего: {total_fetched}, валидных: {len(all_valid_matches)}")
        
        for match in matches:
            is_ranked, is_all_pick, age_hours = is_valid_match(match)
            
            # Пропускаем слишком свежие матчи
            if age_hours < MIN_MATCH_AGE_HOURS and age_hours > 0:
                stats["too_fresh"] += 1
                continue
            
            # Проверяем режим
            lobby_type = match.get("lobby_type", -1)
            game_mode = match.get("game_mode", -1)
            
            if is_ranked and is_all_pick:
                stats["ranked_allpick"] += 1
                all_valid_matches.append(match)
            elif game_mode == 23:  # Turbo
                stats["turbo"] += 1
            else:
                stats["other_modes"] += 1
        
        # Показываем прогресс
        print(f"    [Прогресс: {len(all_valid_matches)}/{TARGET_MATCHES} нужных матчей]")
        
        # Задержка между запросами
        time.sleep(REQUEST_DELAY)
    
    # Итоги поиска
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ПОИСКА")
    print("=" * 60)
    print(f"Всего запросов к API: {api_calls}")
    print(f"Всего матчей получено: {total_fetched}")
    print(f"Найдено All Pick/Ranked: {len(all_valid_matches)}")
    print(f"\n--- Статистика ---")
    print(f"  All Pick/Ranked (нужные): {stats['ranked_allpick']}")
    print(f"  Turbo: {stats['turbo']}")
    print(f"  Другие режимы: {stats['other_modes']}")
    print(f"  Слишком свежие: {stats['too_fresh']}")
    
    return all_valid_matches


def save_links(matches, filepath):
    """Сохраняет ссылки на реплеи в текстовый файл."""
    
    print(f"\nСохранение ссылок в {filepath}...")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Ссылки на реплеи Dota 2\n")
        f.write(f"# Дата: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Фильтры: All Pick, Ranked, >{MIN_MATCH_AGE_HOURS}ч назад\n")
        f.write(f"# Всего матчей: {len(matches)}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, match in enumerate(matches, 1):
            match_id = match.get("match_id", "N/A")
            lobby_type = match.get("lobby_type", -1)
            game_mode = match.get("game_mode", -1)
            start_time = match.get("start_time", 0)
            
            age_str = "N/A"
            if start_time > 0:
                dt = datetime.fromtimestamp(start_time / 1000)
                age_hours = (datetime.now() - dt).total_seconds() / 3600
                age_str = f"{age_hours:.1f}ч ({dt.strftime('%Y-%m-%d %H:%M')})"
            
            lobby_name = "Public" if lobby_type == 0 else ("Ranked" if lobby_type == 2 else str(lobby_type))
            
            f.write(f"{i}. Match ID: {match_id}\n")
            f.write(f"   Режим: {lobby_name}, All Pick\n")
            f.write(f"   возраст: {age_str}\n")
            f.write(f"   radiant_team: {match.get('radiant_team', [])}\n")
            f.write(f"   dire_team: {match.get('dire_team', [])}\n")
            f.write(f"   Ссылка: https://www.opendota.com/matches/{match_id}\n")
            f.write("\n")
    
    print(f"[OK] Сохранено {len(matches)} ссылок")


def main():
    """Основная функция."""
    
    print("\n" + "=" * 60)
    print("ПОИСК РЕПЛЕЕВ DOTA 2")
    print("=" * 60)
    
    # Создаём папки
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Ищем матчи
    matches = fetch_matches_loop()
    
    if not matches:
        print("\n[ОШИБКА] Не найдено подходящих матчей")
        return
    
    # Сохраняем все ссылки
    save_links(matches, LINKS_FILE)
    
    print(f"\nГотово! Найдено {len(matches)} матчей.")
    print(f"Сохранено в: {LINKS_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
