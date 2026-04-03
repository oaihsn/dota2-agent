# -*- coding: utf-8 -*-
"""
Парсер данных о матче из Stratz API
Создаёт структурированные данные об игроках для нейросети
"""
import json
from pathlib import Path
from dataclasses import dataclass
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"

@dataclass
class PlayerInfo:
    """Информация об игроке в матче."""
    match_id: int
    player_slot: int
    team: int  # 0 = Radiant, 1 = Dire
    
    # Steam
    account_id: int
    steam_id: int
    
    # Герой
    hero_id: int
    hero_name: str
    
    # Статистика
    kills: int
    deaths: int
    assists: int
    last_hits: int
    denies: int
    
    # Экономика
    gold: int
    net_worth: int
    xp: int
    level: int
    
    # Инвентарь (ID предметов)
    items: list
    
    # Способности (ID)
    abilities: list


def load_metadata():
    """Загружает метаданные (hero names, item names)."""
    with open(DATA_DIR / "dota2_metadata.json", encoding='utf-8') as f:
        meta = json.load(f)
    
    heroes = {int(k): v for k, v in meta['heroes']['by_id'].items()}
    return heroes


def parse_match_data(match_file: str, output_file: str = None) -> pd.DataFrame:
    """Парсит данные матча и создаёт DataFrame игроков.
    
    Args:
        match_file: Путь к JSON файлу с данными матча
        output_file: Путь для сохранения CSV
    
    Returns:
        DataFrame с информацией об игроках
    """
    # Загружаем метаданные
    heroes = load_metadata()
    
    # Загружаем матч
    with open(match_file, encoding='utf-8') as f:
        match = json.load(f)
    
    players = []
    
    for p in match.get('players', []):
        player_slot = p.get('playerSlot', 0)
        team = 0 if player_slot < 128 else 1
        
        hero_id = p.get('heroId', 0)
        hero_name = heroes.get(hero_id, f'hero_{hero_id}')
        
        # Собираем предметы
        items = []
        for i in range(6):
            item_id = p.get(f'hero{hero_id}item{i}', 0) if False else p.get('inventory', [{}])[i] if isinstance(p.get('inventory'), list) else 0
            # Упрощаем - предметы могут быть в разных местах
            items.append(0)  # Placeholder
        
        player = PlayerInfo(
            match_id=match.get('id', 0),
            player_slot=player_slot,
            team=team,
            account_id=p.get('accountId', 0),
            steam_id=p.get('steamId', 0),
            hero_id=hero_id,
            hero_name=hero_name,
            kills=p.get('numKills', 0),
            deaths=p.get('numDeaths', 0),
            assists=p.get('numAssists', 0),
            last_hits=p.get('numLastHits', 0),
            denies=p.get('numDenies', 0),
            gold=p.get('gold', 0),
            net_worth=p.get('netWorth', 0),
            xp=p.get('experience', 0),
            level=p.get('level', 0),
            items=items,
            abilities=[]
        )
        
        players.append(player)
    
    # Создаём DataFrame в формате как opendota_parser
    df = pd.DataFrame([{
        'match_id': p.match_id,
        'tick': 0,  # Финальное состояние
        'player_slot': p.player_slot,
        'team': p.team,
        'hero_id': p.hero_id,
        'hero_name': p.hero_name,
        'level': p.level,
        'gold': p.gold,
        'net_worth': p.net_worth,
        'gold_per_min': 0,  # Недоступно
        'xp_per_min': 0,    # Недоступно
        'item_0': '',
        'item_1': '',
        'item_2': '',
        'item_3': '',
        'item_4': '',
        'item_5': '',
        'ability_0': '',
        'ability_1': '',
        'ability_2': '',
        'ability_3': '',
        'ability_4': '',
        'ability_5': '',
        'ability_6': '',
        'ability_7': '',
        'kills': p.kills,
        'deaths': p.deaths,
        'assists': p.assists,
        'last_hits': p.last_hits,
        'denies': p.denies,
        'account_id': p.account_id,
        'personaname': '',
    } for p in players])
    
    if output_file:
        df.to_csv(output_file, index=False)
        print(f"Saved to: {output_file}")
    
    return df


if __name__ == "__main__":
    # Тест
    df = parse_match_data(
        DATA_DIR / "stratz_match.json",
        DATA_DIR / "players.csv"
    )
    
    print("\n=== MATCH PLAYERS ===")
    print(df.to_string())
