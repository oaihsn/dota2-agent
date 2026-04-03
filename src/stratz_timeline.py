# -*- coding: utf-8 -*-
"""
Stratz Timeline Parser
Парсит данные матча по тикам (timeline)
"""
import cloudscraper
import json
from pathlib import Path
from dataclasses import dataclass
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"

TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiNTUxNjZkNTAtOTY0MS00MmU1LWEyMjQtMjZlMDcyNWE1YTAwIiwiU3RlYW1JZCI6IjEwNzg4MDI5ODEiLCJBUElVc2VyIjoidHJ1ZSIsIm5iZiI6MTc3MTE2MDYwMiwiZXhwIjoxODAyNjk2NjAyLCJpYXQiOjE3NzExNjA2MDIsImlzcyI6Imh0dHBzOi8vYXBpLnN0cmF0ei5jb20ifQ.VPrAkCuJ4KlttFGGtae09_LoQk91GkR4vEaybt6X3iM'


def load_metadata():
    """Загружает метаданные."""
    with open(DATA_DIR / "dota2_metadata.json", encoding='utf-8') as f:
        meta = json.load(f)
    heroes = {int(k): v for k, v in meta['heroes']['by_id'].items()}
    return heroes


def get_match_data(match_id: int) -> dict:
    """Получает данные матча через Stratz API."""
    scraper = cloudscraper.create_scraper()
    r = scraper.get(
        f'https://api.stratz.com/api/v1/match/{match_id}',
        headers={'Authorization': f'Bearer {TOKEN}'},
        timeout=60
    )
    if r.status_code == 200:
        return r.json()
    return None


def parse_timeline(match_id: int, target_player_slot: int = None, tick_interval: int = 2) -> pd.DataFrame:
    """Парсит timeline матча.
    
    Args:
        match_id: ID матча
        target_player_slot: Слот игрока для отслеживания (None = все игроки)
        tick_interval: Интервал в секундах (каждые N секунд)
    
    Returns:
        DataFrame с timeline данными
    """
    print(f"Fetching match {match_id}...")
    match = get_match_data(match_id)
    if not match:
        print("Error: Could not fetch match data")
        return pd.DataFrame()
    
    heroes = load_metadata()
    duration = match.get('durationSeconds', 0)
    
    print(f"Duration: {duration} seconds")
    print(f"Parsing timeline every {tick_interval} seconds...")
    
    # Собираем данные по времени
    all_states = []
    
    for player in match.get('players', []):
        player_slot = player.get('playerSlot', 0)
        
        # Фильтруем по игроку
        if target_player_slot is not None and player_slot != target_player_slot:
            continue
        
        hero_id = player.get('heroId', 0)
        hero_name = heroes.get(hero_id, f'hero_{hero_id}')
        team = 0 if player_slot < 128 else 1
        
        # Получаем playbackData
        playback = player.get('playbackData', {})
        
        if not playback:
            continue
        
        # Получаем events
        gold_events = playback.get('playerUpdateGoldEvents', [])
        level_events = playback.get('playerUpdateLevelEvents', [])
        
        print(f"  Player {player_slot} ({hero_name}): {len(gold_events)} gold events")
        
        # Парсим gold events
        gold_by_time = {}
        for event in gold_events:
            time = event.get('time', 0)
            gold = event.get('gold', 0)
            gold_by_time[time] = gold
        
        # Парсим level events
        level_by_time = {}
        for event in level_events:
            time = event.get('time', 0)
            level = event.get('level', 0)
            level_by_time[time] = level
        
        # Создаём состояния каждые tick_interval секунд
        for time in range(0, duration, tick_interval):
            state = {
                'match_id': match_id,
                'tick': time * 30,  # Конвертируем секунды в тики (30 тиков/сек)
                'time_seconds': time,
                'player_slot': player_slot,
                'team': team,
                'hero_id': hero_id,
                'hero_name': hero_name,
                'gold': gold_by_time.get(time, 0),
                'level': level_by_time.get(time, 0),
                'kills': player.get('numKills', 0),
                'deaths': player.get('numDeaths', 0),
                'assists': player.get('numAssists', 0),
                'net_worth': player.get('networth', 0),
                'last_hits': player.get('numLastHits', 0),
                'denies': player.get('numDenies', 0),
                'item_0': player.get('item0Id', 0),
                'item_1': player.get('item1Id', 0),
                'item_2': player.get('item2Id', 0),
                'item_3': player.get('item3Id', 0),
                'item_4': player.get('item4Id', 0),
                'item_5': player.get('item5Id', 0),
                'account_id': player.get('steamAccountId', 0),
            }
            all_states.append(state)
    
    df = pd.DataFrame(all_states)
    
    if not df.empty:
        # Сортируем по времени и игроку
        df = df.sort_values(['time_seconds', 'player_slot']).reset_index(drop=True)
    
    print(f"Total records: {len(df)}")
    
    return df


def save_timeline(match_id: int, output_file: str = None):
    """Сохраняет timeline в parquet."""
    df = parse_timeline(match_id)
    
    if df.empty:
        print("No data to save")
        return None
    
    if output_file is None:
        output_file = DATA_DIR / "processed" / f"timeline_{match_id}.parquet"
    else:
        output_file = Path(output_file)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_file, index=False)
    
    size_mb = output_file.stat().st_size / 1024 / 1024
    print(f"Saved: {output_file} ({size_mb:.2f} MB)")
    
    return output_file


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Stratz Timeline Parser')
    parser.add_argument('--match-id', '-m', type=int, required=True, help='Match ID')
    parser.add_argument('--player', '-p', type=int, help='Player slot (optional)')
    parser.add_argument('--interval', '-i', type=int, default=2, help='Interval in seconds')
    parser.add_argument('--output', '-o', help='Output file')
    
    args = parser.parse_args()
    
    save_timeline(args.match_id, args.output)
