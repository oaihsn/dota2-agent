# -*- coding: utf-8 -*-
"""
Скрипт для скачивания реплеев Dota 2 через OpenDota API.
Фильтрует матчи с средним MMR > 5000.
"""
import sys
import io
import os
import requests
import time
from pathlib import Path
from tqdm import tqdm

# Настраиваем кодировку для вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# Конфигурация
API_URL = "https://api.opendota.com/api/publicMatches"
OUTPUT_DIR = Path("data/raw")
LINKS_FILE = Path("data/raw_links.txt")
MIN_AVG_MMR = 5000  # Immortal/Divine
MAX_MATCHES_TO_FETCH = 100  # Получаем больше матчей для фильтрации
MAX_DOWNLOADS = 10  # Скачиваем только 10 реплеев
REQUEST_DELAY = 1  # Задержка между запросами (сек)


def fetch_high_mmr_matches():
    """Получает матчи с высоким MMR через OpenDota API."""
    
    print("=" * 60)
    print("ПОИСК МАТЧЕЙ")
    print("=" * 60)
    
    params = {
        "mmr_descending": True,  # Сортировка по убыванию MMR
        "limit": MAX_MATCHES_TO_FETCH
    }
    
    print(f"Запрос к OpenDota API...")
    print(f"Фильтр: средний MMR > {MIN_AVG_MMR}")
    
    try:
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        matches = response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ОШИБКА] Не удалось получить данные: {e}")
        return []
    
    print(f"Получено матчей: {len(matches)}")
    
    # Проверяем структуру данных
    if matches and len(matches) > 0:
        print(f"\nПример данных первого матча:")
        sample = matches[0]
        print(f"  match_id: {sample.get('match_id')}")
        print(f"  avg_mmr: {sample.get('avg_mmr', 'НЕТ ДАННЫХ')}")
        print(f"  radiant_team: {sample.get('radiant_team', [])}")
        print(f"  dire_team: {sample.get('dire_team', [])}")
    
    # Фильтруем по среднему MMR
    high_mmr_matches = [
        m for m in matches 
        if m.get("avg_mmr", 0) >= MIN_AVG_MMR
    ]
    
    print(f"\nМатчей с MMR > {MIN_AVG_MMR}: {len(high_mmr_matches)}")
    
    # Если нет матчей с высоким MMR, используем все доступные
    if not high_mmr_matches and matches:
        print(f"\n[INFO] Матчи с MMR > {MIN_AVG_MMR} не найдены.")
        print(f"[INFO] Будем использовать все {len(matches)} матчей.")
        return matches
    
    return high_mmr_matches


def get_replay_url(match_id):
    """Генерирует URL для скачивания реплея."""
    return f"https://api.opendota.com/api/replays?match_id={match_id}"


def download_replay(match_id):
    """Получает ссылку на реплей матча."""
    
    try:
        # Проверяем доступность реплея
        replay_info_url = f"https://api.opendota.com/api/replays?match_id={match_id}"
        response = requests.get(replay_info_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                cluster = data[0].get("cluster")
                replay_hash = data[0].get("replay_hash")
                
                if cluster and replay_hash:
                    # Генерируем прямую ссылку на скачивание
                    download_url = (
                        f"https://replay{cluster}.valve.net/"
                        f"{match_id}_{replay_hash}.dem.bz2"
                    )
                    return download_url, cluster, replay_hash
        
        return None, None, None
        
    except requests.exceptions.RequestException:
        return None, None, None


def save_links(matches, filepath):
    """Сохраняет ссылки на реплеи в текстовый файл."""
    
    print(f"\nСохранение ссылок в {filepath}...")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Ссылки на реплеи Dota 2\n")
        f.write(f"# Дата: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Всего матчей: {len(matches)}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, match in enumerate(matches, 1):
            match_id = match.get("match_id", "N/A")
            avg_mmr = match.get("avg_mmr", 0)
            
            # radiant_team и dire_team это списки ID игроков
            radiant_players = match.get("radiant_team", [])
            dire_players = match.get("dire_team", [])
            
            f.write(f"{i}. Match ID: {match_id}\n")
            f.write(f"   Средний MMR: {avg_mmr if avg_mmr > 0 else 'N/A'}\n")
            f.write(f"   radiant_players: {radiant_players}\n")
            f.write(f"   dire_players: {dire_players}\n")
            f.write(f"   Ссылка: https://www.opendota.com/matches/{match_id}\n")
            f.write("\n")
    
    print(f"[OK] Сохранено {len(matches)} ссылок")


def download_file(url, filepath, match_id):
    """Скачивает файл с прогресс-баром."""
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        
        if response.status_code != 200:
            return False
        
        total_size = int(response.headers.get("content-length", 0))
        
        with open(filepath, "wb") as f:
            with tqdm(
                desc=f"Match {match_id}",
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        return True
        
    except requests.exceptions.RequestException:
        return False


def main():
    """Основная функция."""
    
    print("\n" + "=" * 60)
    print("СКАЧИВАНИЕ РЕПЛЕЕВ DOTA 2")
    print("=" * 60)
    
    # Создаём папки
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Получаем матчи
    matches = fetch_high_mmr_matches()
    
    if not matches:
        print("[ОШИБКА] Не удалось найти матчи")
        return
    
    # Сохраняем все ссылки
    save_links(matches, LINKS_FILE)
    
    # Скачиваем первые N реплеев
    matches_to_download = matches[:MAX_DOWNLOADS]
    
    print(f"\n" + "=" * 60)
    print(f"ПОЛУЧЕНИЕ ССЫЛОК НА ПЕРВЫЕ {len(matches_to_download)} РЕПЛЕЕВ")
    print("=" * 60)
    
    available_replays = []
    
    for i, match in enumerate(matches_to_download, 1):
        match_id = match.get("match_id")
        avg_mmr = match.get("avg_mmr", 0)
        
        print(f"\n[{i}/{len(matches_to_download)}] Match ID: {match_id}")
        
        # Получаем ссылку на реплей
        replay_url, cluster, replay_hash = download_replay(match_id)
        
        if replay_url:
            print(f"   [OK] Реплей доступен")
            available_replays.append({
                "match_id": match_id,
                "url": replay_url,
                "mmr": avg_mmr
            })
        else:
            print(f"   [ПРОПУСК] Реплей недоступен")
        
        # Задержка между запросами
        time.sleep(REQUEST_DELAY)
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ")
    print("=" * 60)
    print(f"Найдено доступных реплеев: {len(available_replays)}")
    print(f"Все ссылки сохранены в: {LINKS_FILE}")
    
    if available_replays:
        print("\nДоступные реплеи:")
        for r in available_replays:
            print(f"  - Match {r['match_id']}: {r['url']}")
    
    print("\n[СОВЕТ] Для скачивания реплеев:")
    print("  1. Используйте OpenDota Parse для получения данных")
    print("  2. Или соберите реплеи через Dota 2 (внутриигровой интерфейс)")
    print("=" * 60)


if __name__ == "__main__":
    main()
