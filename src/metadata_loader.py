# -*- coding: utf-8 -*-
"""
Metadata Loader для Dota 2
========================
Скачивает актуальные ID героев, предметов и способностей из OpenDota API
и сохраняет их в JSON для кодирования в нейросети.

Использование:
    python src/metadata_loader.py

Выходной файл:
    data/dota2_metadata.json
"""
import urllib.request
import json
import os
from typing import Dict, Any

# Настройки
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "dota2_metadata.json")

# URL OpenDota API
URLS = {
    "heroes": "https://api.opendota.com/api/constants/heroes",
    "items": "https://api.opendota.com/api/constants/items",
    "abilities": "https://api.opendota.com/api/constants/abilities",
}

# Fallback URLs (dotaconstants)
FALLBACK_URLS = {
    "abilities": "https://raw.githubusercontent.com/odota/dotaconstants/master/json/abilities.json",
}


def fetch_json(url: str, timeout: int = 30) -> Any:
    """Загрузка JSON по URL"""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    req.add_header("Accept", "application/json")
    response = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(response.read().decode())


def fetch_with_fallback(url: str) -> Dict:
    """Загрузка с fallback на dotaconstants"""
    try:
        data = fetch_json(url)
        return data
    except Exception as e:
        print(f"  Ошибка: {e}")
        return {}


def load_heroes() -> Dict[int, str]:
    """Загрузка героев"""
    print("  Загрузка героев...")
    data = fetch_with_fallback(URLS["heroes"])
    if isinstance(data, dict):
        heroes = {}
        for h in data.values():
            if isinstance(h, dict) and "id" in h and "localized_name" in h:
                heroes[int(h["id"])] = h["localized_name"]
        return heroes
    elif isinstance(data, list):
        return {int(h["id"]): h["localized_name"] for h in data}
    return {}


def load_items() -> Dict[int, str]:
    """Загрузка предметов"""
    print("  Загрузка предметов...")
    data = fetch_with_fallback(URLS["items"])
    if isinstance(data, dict):
        items = {}
        for item in data.values():
            if isinstance(item, dict) and "id" in item:
                # Ищем название в разных полях
                name = item.get("localized_name") or item.get("dname") or ""
                if name:
                    items[int(item["id"])] = name
        return items
    elif isinstance(data, list):
        result = {}
        for item in data:
            name = item.get("localized_name") or item.get("dname") or ""
            if name:
                result[int(item["id"])] = name
        return result
    return {}


def load_abilities() -> Dict[int, str]:
    """Загрузка способностей"""
    print("  Загрузка способностей...")
    
    # Пробуем сначала OpenDota
    data = fetch_with_fallback(URLS["abilities"])
    
    # Если не работает - используем fallback
    if not data or len(data) == 0:
        print("  Использую fallback (dotaconstants)...")
        data = fetch_with_fallback(FALLBACK_URLS["abilities"])
        # Fallback - это JSONL формат
        if data:
            abilities = {}
            for line in str(data).strip().split('\n'):
                if line.strip():
                    try:
                        a = json.loads(line)
                        if 'id' in a and 'name' in a:
                            abilities[int(a['id'])] = a['name']
                    except:
                        pass
            return abilities
    
    if isinstance(data, dict):
        abilities = {}
        for a in data.values():
            if isinstance(a, dict):
                # Ищем ID и имя
                aid = a.get("id") or a.get("ability_id")
                name = a.get("name") or a.get("full_name") or ""
                if aid and name:
                    abilities[int(aid)] = name
        return abilities
    elif isinstance(data, list):
        result = {}
        for a in data:
            aid = a.get("id") or a.get("ability_id")
            name = a.get("name") or a.get("full_name") or ""
            if aid and name:
                result[int(aid)] = name
        return result
    return {}


def create_mappings(heroes: Dict, items: Dict, abilities: Dict) -> Dict:
    """Создание маппинга для нейросети"""
    
    # Сортируем по ID для консистентности
    sorted_heroes = sorted(heroes.items(), key=lambda x: x[0])
    sorted_items = sorted(items.items(), key=lambda x: x[0])
    sorted_abilities = sorted(abilities.items(), key=lambda x: x[0])
    
    # Создаём маппинги: name -> index (0-based для нейросети)
    hero_to_idx = {name: idx for idx, (_, name) in enumerate(sorted_heroes)}
    item_to_idx = {name: idx for idx, (_, name) in enumerate(sorted_items)}
    ability_to_idx = {name: idx for idx, (_, name) in enumerate(sorted_abilities)}
    
    # Маппинг ID -> index
    hero_id_to_idx = {id: idx for idx, (id, _) in enumerate(sorted_heroes)}
    item_id_to_idx = {id: idx for idx, (id, _) in enumerate(sorted_items)}
    ability_id_to_idx = {id: idx for idx, (id, _) in enumerate(sorted_abilities)}
    
    return {
        "heroes": {
            "count": len(heroes),
            "by_id": {str(k): v for k, v in heroes.items()},
            "by_name": hero_to_idx,
            "id_to_idx": hero_id_to_idx,
            "idx_to_id": {v: k for k, v in hero_id_to_idx.items()},
        },
        "items": {
            "count": len(items),
            "by_id": {str(k): v for k, v in items.items()},
            "by_name": item_to_idx,
            "id_to_idx": item_id_to_idx,
            "idx_to_id": {v: k for k, v in item_id_to_idx.items()},
        },
        "abilities": {
            "count": len(abilities),
            "by_id": {str(k): v for k, v in abilities.items()},
            "by_name": ability_to_idx,
            "id_to_idx": ability_id_to_idx,
            "idx_to_id": {v: k for k, v in ability_id_to_idx.items()},
        },
    }


def main():
    print("=" * 60)
    print("Dota 2 Metadata Loader")
    print("Загрузка ID героев, предметов и способностей")
    print("=" * 60)
    
    # Загрузка данных
    heroes = load_heroes()
    items = load_items()
    abilities = load_abilities()
    
    print(f"\nЗагружено:")
    print(f"  Героев: {len(heroes)}")
    print(f"  Предметов: {len(items)}")
    print(f"  Способностей: {len(abilities)}")
    
    # Создание маппинга
    metadata = create_mappings(heroes, items, abilities)
    metadata["info"] = {
        "source": "OpenDota API",
        "description": "Mapping файлы для кодирования Dota 2 данных в нейросеть",
    }
    
    # Сохранение
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"\nСохранено в: {OUTPUT_FILE}")
    print("=" * 60)
    
    # Пример использования
    print("\nПример использования в нейросети:")
    print("-" * 40)
    print("  # Получить index героя по имени:")
    print("  hero_idx = metadata['heroes']['by_name']['Anti-Mage']  # = 0")
    print("")
    print("  # Получить index предмета по ID:")
    print("  item_idx = metadata['items']['id_to_idx'][1]  # blink dagger")
    print("")
    print("  # Получить one-hot encoding для героя:")
    print("  hero_vector = torch.zeros(metadata['heroes']['count'])")
    print("  hero_vector[hero_idx] = 1")
    print("=" * 60)


if __name__ == "__main__":
    main()
