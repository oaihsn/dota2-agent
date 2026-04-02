# -*- coding: utf-8 -*-
"""
Скрипт для скачивания реплеев Dota 2 через OpenDota API.
Фильтрует матчи: All Pick, не менее 1 дня назад, высокий MMR.
"""
import sys
import io
import os
import requests
import time
from pathlib import Path
from tqdm import tqdm
from datetime import datetime, timedelta

# Настраиваем кодировку для вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# Конфигурация
API_URL = "https://api.opendota.com/api/publicMatches"
OUTPUT_DIR = Path("data/raw")
LINKS_FILE = Path("data/raw_links.txt")
MIN_AVG_MMR = 5000  # Immortal/Divine
MIN_MATCH_AGE_HOURS = 24  # Минимум 1 день назад
MAX_MATCHES_TO_FETCH = 200  # Получаем больше для фильтрации
MAX_DOWNLOADS = 10  # Скачиваем только 10 реплеев
REQUEST_DELAY = 1  # Задержка между запросами (сек)

# ID режимов игры (lobby_type и game_mode)
# game_mode: 1=All Pick, 2=CAPTAINS MODE, 3=Draft
# lobby_type: 0=Public matchmaking, 2=Ranked
LOBBY_TYPE_RANKED = 2  # Ranked matchmaking
GAME_MODE_ALL_PICK = 1  # All Pick


def is_valid_match(match):
    """Проверяет, подходит ли матч по критериям."""
    
    # 1. Проверяем lobby_type (должен быть Public/Ranked matchmaking)
    lobby_type = match.get("lobby_type", -1)
    if lobby_type not in [0, 2]:  # 0=Public, 2=Ranked
        return False, "Не Public/Ranked lobby"
    
    # 2. Проверяем game_mode (должен быть All Pick)
    game_mode = match.get("game_mode", -1)
    if game_mode != GAME_MODE_ALL_PICK:
        return False, f"Не All Pick (mode={game_mode})"
    
    # 3. Проверяем возраст матча (минимум 24 часа)
    start_time = match.get("start_time", 0)
    if start_time > 0:
        match_datetime = datetime.fromtimestamp(start_time / 1000)
        now = datetime.now()
        age_hours = (now - match_datetime).total_seconds() / 3600
        
        if age_hours < MIN_MATCH_AGE_HOURS:
            return False, f"Матч свежий ({age_hours:.1f}ч назад)"
    
    return True, "OK"


def fetch_matches():
    """Получает матчи через OpenDota API с фильтрами."""
    
    print("=" * 60)
    print("ПОИСК МАТЧЕЙ")
    print("=" * 60)
    
    params = {
        "mmr_descending": True,
        "limit": MAX_MATCHES_TO_FETCH
    }
    
    print(f"Запрос к OpenDota API...")
    print(f"Фильтры:")
    print(f"  - lobby_type: Public/Ranked (0, 2)")
    print(f"  - game_mode: All Pick (1)")
    print(f"  - возраст: > {MIN_MATCH_AGE_HOURS} часов")
    
    try:
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        matches = response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ОШИБКА] Не удалось получить данные: {e}")
        return []
    
    print(f"\nПолучено матчей: {len(matches)}")
    
    # Фильтруем матчи
    valid_matches = []
    skip_reasons = {}
    
    for match in matches:
        is_valid, reason = is_valid_match(match)
        
        if is_valid:
            avg_mmr = match.get("avg_mmr", 0)
            if avg_mmr >= MIN_AVG_MMR or avg_mmr == 0:  # 0 = данные недоступны
                valid_matches.append(match)
        else:
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
    
    print(f"\n--- Статистика фильтрации ---")
    for reason, count in skip_reasons.items():
        print(f"  Пропущено ({reason}): {count}")
    
    print(f"\nПодходящих матчей: {len(valid_matches)}")
    
    # Показываем пример
    if valid_matches:
        sample = valid_matches[0]
        print(f"\nПример первого матча:")
        print(f"  match_id: {sample.get('match_id')}")
        print(f"  game_mode: {sample.get('game_mode')} (1=All Pick)")
        print(f"  lobby_type: {sample.get('lobby_type')} (0=Public, 2=Ranked)")
        start_time = sample.get("start_time", 0)
        if start_time > 0:
            dt = datetime.fromtimestamp(start_time / 1000)
            age = (datetime.now() - dt).total_seconds() / 3600
            print(f"  возраст: {age:.1f} часов ({dt.strftime('%Y-%m-%d %H:%M')})")
    
    return valid_matches


def get_replay_url(match_id):
    """Получает ссылку на реплей матча."""
    
    try:
        replay_info_url = f"https://api.opendota.com/api/replays?match_id={match_id}"
        response = requests.get(replay_info_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                cluster = data[0].get("cluster")
                replay_hash = data[0].get("replay_hash")
                
                if cluster and replay_hash:
                    download_url = (
                        f"https://replay{cluster}.valve.net/"
                        f"{match_id}_{replay_hash}.dem.bz2"
                    )
                    return download_url
        
        return None
        
    except requests.exceptions.RequestException:
        return None


def save_links(matches, filepath):
    """Сохраняет ссылки на реплеи в текстовый файл."""
    
    print(f"\nСохранение ссылок в {filepath}...")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Ссылки на реплеи Dota 2\n")
        f.write(f"# Дата: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Фильтры: All Pick, >{MIN_MATCH_AGE_HOURS}ч назад\n")
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
            
            f.write(f"{i}. Match ID: {match_id}\n")
            f.write(f"   lobby_type: {lobby_type} (0=Public, 2=Ranked)\n")
            f.write(f"   game_mode: {game_mode} (1=All Pick)\n")
            f.write(f"   возраст: {age_str}\n")
            f.write(f"   radiant_team: {match.get('radiant_team', [])}\n")
            f.write(f"   dire_team: {match.get('dire_team', [])}\n")
            f.write(f"   Ссылка: https://www.opendota.com/matches/{match_id}\n")
            f.write("\n")
    
    print(f"[OK] Сохранено {len(matches)} ссылок")


def main():
    """Основная функция."""
    
    print("\n" + "=" * 60)
    print("СКАЧИВАНИЕ РЕПЛЕЕВ DOTA 2")
    print("=" * 60)
    
    # Создаём папки
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Получаем матчи
    matches = fetch_matches()
    
    if not matches:
        print("[ОШИБКА] Не найдено подходящих матчей")
        print("\nВозможные причины:")
        print("  1. OpenDota API не возвращает данные для этого региона")
        print("  2. Мало публичных матчей с фильтрами")
        print("  3. Попробуйте позже")
        return
    
    # Сохраняем все ссылки
    save_links(matches, LINKS_FILE)
    
    # Скачиваем первые N реплеев
    matches_to_check = matches[:MAX_DOWNLOADS]
    
    print(f"\n" + "=" * 60)
    print(f"ПРОВЕРКА ДОСТУПНОСТИ {len(matches_to_check)} РЕПЛЕЕВ")
    print("=" * 60)
    
    available_replays = []
    
    for i, match in enumerate(matches_to_check, 1):
        match_id = match.get("match_id")
        
        print(f"\n[{i}/{len(matches_to_check)}] Match ID: {match_id}")
        
        replay_url = get_replay_url(match_id)
        
        if replay_url:
            print(f"   [OK] Реплей доступен")
            available_replays.append({
                "match_id": match_id,
                "url": replay_url
            })
        else:
            print(f"   [ПРОПУСК] Реплей недоступен")
        
        time.sleep(REQUEST_DELAY)
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ")
    print("=" * 60)
    print(f"Всего матчей найдено: {len(matches)}")
    print(f"Доступных реплеев: {len(available_replays)}")
    print(f"Все ссылки сохранены в: {LINKS_FILE}")
    
    if available_replays:
        print("\nДоступные реплеи:")
        for r in available_replays[:5]:
            print(f"  - Match {r['match_id']}")
    
    print("\n[СОВЕТ] Для скачивания реплеев:")
    print("  1. Используйте OpenDota Parse API")
    print("  2. Или соберите реплеи через Dota 2")
    print("=" * 60)


if __name__ == "__main__":
    main()
