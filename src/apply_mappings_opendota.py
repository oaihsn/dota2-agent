# -*- coding: utf-8 -*-
"""
Применяет маппинги к данным из OpenDota API.
"""
import json
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = PROJECT_DIR / "data"
DATA_PROCESSED_DIR = PROJECT_DIR / "data" / "processed"


def load_heroes() -> dict:
    heroes_path = DATA_DIR / "heroes.json"
    if heroes_path.exists():
        with open(heroes_path, 'r', encoding='utf-8') as f:
            return {int(k): v for k, v in json.load(f).items()}
    return {}


def load_items() -> dict:
    items_path = DATA_DIR / "items.json"
    if items_path.exists():
        with open(items_path, 'r', encoding='utf-8') as f:
            return {int(k): v for k, v in json.load(f).items()}
    return {}


def load_abilities() -> dict:
    abilities_path = DATA_DIR / "abilities.json"
    if abilities_path.exists():
        with open(abilities_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def apply_mappings_to_opendota(match_id: int):
    """Применяет маппинги к данным из OpenDota."""
    input_file = DATA_PROCESSED_DIR / f"opendota_match_{match_id}.json"
    
    if not input_file.exists():
        print(f"File not found: {input_file}")
        return
    
    print(f"Loading: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        match_data = json.load(f)
    
    players = match_data.get('players', [])
    if not players:
        print("No players data found")
        return
    
    # Загружаем маппинги
    heroes = load_heroes()
    items = load_items()
    abilities = load_abilities()
    
    print(f"\nMatch ID: {match_data.get('match_id')}")
    print(f"Duration: {match_data.get('duration')}s")
    print(f"Radiant win: {match_data.get('radiant_win')}")
    print(f"\nPlayers ({len(players)}):")
    
    # Обрабатываем каждого игрока
    for p in players:
        hero_id = p.get('hero_id', 0)
        hero_name = heroes.get(hero_id, f"hero_{hero_id}")
        
        # Маппим предметы
        item_ids = [p.get(f'item_{i}', 0) for i in range(6)]
        item_names = [items.get(iid, f"item_{iid}") for iid in item_ids if iid > 0]
        
        # Backpack
        backpack_ids = [p.get(f'backpack_{i}', 0) for i in range(3)]
        backpack_names = [items.get(iid, f"item_{iid}") for iid in backpack_ids if iid > 0]
        
        # Neutral item
        neutral_id = p.get('item_neutral', 0)
        neutral_name = items.get(neutral_id, f"item_{neutral_id}") if neutral_id else None
        
        # Маппим способности
        ability_ids = p.get('ability_upgrades_arr', [])
        ability_names = [abilities.get(str(aid), f"ability_{aid}") for aid in ability_ids]
        
        print(f"\n  Player: {p.get('personaname') or p.get('account_id')}")
        print(f"    Hero: {hero_id} -> {hero_name}")
        print(f"    Items: {item_names}")
        print(f"    Backpack: {backpack_names}")
        print(f"    Neutral: {neutral_name}")
        print(f"    Abilities: {ability_names[:5]}...")  # First 5
        print(f"    K/D/A: {p.get('kills')}/{p.get('deaths')}/{p.get('assists')}")
        print(f"    Net Worth: {p.get('net_worth')}")
        print(f"    Level: {p.get('level')}")


def main():
    import sys
    
    if len(sys.argv) > 1:
        match_id = int(sys.argv[1])
    else:
        match_id = 8749329335
    
    apply_mappings_to_opendota(match_id)


if __name__ == "__main__":
    main()
