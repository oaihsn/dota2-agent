# -*- coding: utf-8 -*-
"""
Применяет маппинги героев, предметов и способностей к данным реплея.
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


def apply_hero_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """Применяет маппинг героев - заменяет hero_id на названия."""
    heroes = load_heroes()
    
    if 'hero_id' in df.columns:
        # Создаём колонку с названиями
        df['hero_name_mapped'] = df['hero_id'].map(heroes)
        # Заполняем отсутствующие значения
        df['hero_name_mapped'] = df['hero_name_mapped'].fillna(df['hero_id'].apply(lambda x: f"hero_{x}"))
    
    return df


def apply_item_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """Применяет маппинг предметов - декодирует JSON инвентарь."""
    items = load_items()
    
    if 'inventory' in df.columns:
        # Парсим JSON инвентарь
        def decode_inventory(inv_json):
            if pd.isna(inv_json) or inv_json == '':
                return []
            try:
                inv_dict = json.loads(inv_json) if isinstance(inv_json, str) else inv_json
                # Получаем названия предметов (могут быть именами или ID)
                item_names = []
                for key, item_val in inv_dict.items():
                    if item_val:
                        # Пробуем как ID (число)
                        if isinstance(item_val, int):
                            item_name = items.get(item_val, f"item_{item_val}")
                        else:
                            # Уже имя - убираем префикс item_
                            item_name = str(item_val).replace('item_', '')
                        item_names.append(item_name)
                return item_names
            except:
                return []
        
        df['inventory_mapped'] = df['inventory'].apply(decode_inventory)
    
    return df


def apply_ability_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """Применяет маппинг способностей - декодирует JSON способностей."""
    abilities = load_abilities()
    
    if 'abilities' in df.columns:
        def decode_abilities(abil_json):
            if pd.isna(abil_json) or abil_json == '':
                return []
            try:
                abil_dict = json.loads(abil_json) if isinstance(abil_json, str) else abil_json
                # Получаем названия способностей
                ability_names = []
                for key, level in abil_dict.items():
                    if key:
                        ability_name = abilities.get(key, key)
                        ability_names.append(f"{ability_name} (Lv{level})")
                return ability_names
            except:
                return []
        
        df['abilities_mapped'] = df['abilities'].apply(decode_abilities)
    
    return df


def process_replay_file(match_id: int):
    """Обрабатывает файл реплея, применяя все маппинги."""
    input_file = DATA_PROCESSED_DIR / f"replay_{match_id}.parquet"
    
    if not input_file.exists():
        print(f"File not found: {input_file}")
        return
    
    print(f"Processing: {input_file}")
    
    # Читаем данные
    df = pd.read_parquet(input_file)
    print(f"  Loaded {len(df)} rows")
    
    # Применяем маппинги
    df = apply_hero_mapping(df)
    df = apply_item_mapping(df)
    df = apply_ability_mapping(df)
    
    # Показываем результат
    print(f"\n  Sample with mappings:")
    print(df[['tick', 'player_slot', 'hero_id', 'hero_name_mapped', 'inventory_mapped', 'abilities_mapped']].head(5).to_string())
    
    # Сохраняем
    output_file = DATA_PROCESSED_DIR / f"replay_{match_id}_mapped.parquet"
    df.to_parquet(output_file, index=False)
    print(f"\n  Saved to: {output_file}")
    
    return df


def main():
    import sys
    
    if len(sys.argv) > 1:
        match_id = int(sys.argv[1])
    else:
        match_id = 8749329335  # По умолчанию
    
    process_replay_file(match_id)


if __name__ == "__main__":
    main()
