# -*- coding: utf-8 -*-
"""
Сопоставление ID героев, предметов и способностей с их названиями.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = PROJECT_DIR / "data"


def load_heroes() -> Dict[int, str]:
    """Загружает ID -> название героя."""
    heroes_path = DATA_DIR / "heroes.json"
    if heroes_path.exists():
        with open(heroes_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Преобразуем ключи в int
            return {int(k): v for k, v in data.items()}
    return {}


def load_items() -> Dict[int, str]:
    """Загружает ID -> название предмета."""
    items_path = DATA_DIR / "items.json"
    if items_path.exists():
        with open(items_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    return {}


def load_abilities() -> Dict[int, str]:
    """Загружает ID -> название способности."""
    abilities_path = DATA_DIR / "abilities.json"
    if abilities_path.exists():
        with open(abilities_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    return {}


def get_hero_name(hero_id: int) -> str:
    """Получает название героя по ID."""
    heroes = load_heroes()
    return heroes.get(hero_id, f"hero_{hero_id}")


def get_item_name(item_id: int) -> str:
    """Получает название предмета по ID."""
    items = load_items()
    return items.get(item_id, f"item_{item_id}")


def get_ability_name(ability_id: int) -> str:
    """Получает название способности по ID."""
    abilities = load_abilities()
    return abilities.get(ability_id, f"ability_{ability_id}")


def map_hero_ids_to_names(hero_ids: List[int]) -> List[str]:
    """Преобразует список ID героев в названия."""
    return [get_hero_name(hid) for hid in hero_ids]


def map_item_ids_to_names(item_ids: List[int]) -> List[str]:
    """Преобразует список ID предметов в названия."""
    return [get_item_name(iid) for iid in item_ids]


def map_ability_ids_to_names(ability_ids: List[int]) -> List[str]:
    """Преобразует список ID способностей в названия."""
    return [get_ability_name(aid) for aid in ability_ids]


def create_hero_lookup() -> Dict[int, str]:
    """Создаёт справочник героев из dota2_metadata.json если heroes.json не существует."""
    meta_path = DATA_DIR / "dota2_metadata.json"
    if meta_path.exists():
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
            heroes = meta.get('heroes', {}).get('by_id', {})
            return {int(k): v for k, v in heroes.items()}
    return {}


def create_item_lookup() -> Dict[int, str]:
    """Создаёт справочник предметов из dota2_metadata.json если items.json не существует."""
    meta_path = DATA_DIR / "dota2_metadata.json"
    if meta_path.exists():
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
            items = meta.get('items', {}).get('by_id', {})
            return {int(k): v for k, v in items.items()}
    return {}


def create_ability_lookup() -> Dict[int, str]:
    """Создаёт справочник способностей - пока пустой, нужно получить из API."""
    # Способности нужно получить из OpenDota API
    return {}


def build_all_mappings():
    """Создаёт все справочники и сохраняет в JSON."""
    # Герои
    heroes = create_hero_lookup()
    if heroes:
        with open(DATA_DIR / "heroes.json", 'w', encoding='utf-8') as f:
            json.dump(heroes, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(heroes)} heroes to heroes.json")
    
    # Предметы
    items = create_item_lookup()
    if items:
        with open(DATA_DIR / "items.json", 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(items)} items to items.json")
    
    # Способности - пока пустой
    abilities = {}
    with open(DATA_DIR / "abilities.json", 'w', encoding='utf-8') as f:
        json.dump(abilities, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(abilities)} abilities to abilities.json (empty)")
    
    return heroes, items, abilities


def test_mappings():
    """Тестирует сопоставления."""
    print("=" * 50)
    print("Testing mappings")
    print("=" * 50)
    
    # Тест героев
    heroes = load_heroes()
    if not heroes:
        heroes = create_hero_lookup()
    
    print(f"\nHeroes ({len(heroes)}):")
    for hid in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        print(f"  {hid}: {heroes.get(hid, 'Unknown')}")
    
    # Тест предметов
    items = load_items()
    if not items:
        items = create_item_lookup()
    
    print(f"\nItems ({len(items)}):")
    for iid in [1, 2, 6, 10, 29, 30, 43, 44, 46, 48]:
        print(f"  {iid}: {items.get(iid, 'Unknown')}")
    
    # Тест способностей
    abilities = load_abilities()
    print(f"\nAbilities ({len(abilities)}):")
    print("  (Need to fetch from OpenDota API)")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        build_all_mappings()
    else:
        test_mappings()
