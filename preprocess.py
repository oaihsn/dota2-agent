# -*- coding: utf-8 -*-
"""
preprocess.py - предобработка данных Dota 2 для ML

Загружает данные реплея, нормализует координаты, добавляет hp_percent,
кодирует героев в числовые ID из heroes.json.
"""
import pandas as pd
import numpy as np
import json

# Конфигурация
INPUT_FILE = "data/processed/training_data_clarity.csv"
OUTPUT_FILE = "data/processed/cleaned_data.csv"
HEROES_FILE = "data/heroes.json"

# Границы карты Dota 2 (стандартные значения)
MAP_MIN = -12800
MAP_MAX = 12800


def load_heroes(filepath):
    """Загружает heroes.json и создает маппинг имя -> ID."""
    print(f"Загрузка heroes.json из {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        heroes_dict = json.load(f)
    
    # Инвертируем: name -> id
    hero_name_to_id = {}
    
    # Точные совпадения
    for hero_id, hero_name in heroes_dict.items():
        hero_name_to_id[hero_name] = int(hero_id)
    
    # Частичные совпадения для героев с разными именами в реплее
    name_fixes = {
        'Magnataur': 97,      # Magnus ID = 97
        'DoomBringer': 69,    # Doom ID = 69
        'QueenOfPain': 39,     # Queen of Pain ID = 39
        'WitchDoctor': 30,    # Witch Doctor ID = 30
    }
    hero_name_to_id.update(name_fixes)
    
    print(f"  Загружено {len(heroes_dict)} героев")
    return hero_name_to_id


def load_data(filepath):
    """Загружает CSV файл."""
    print(f"\nЗагрузка данных из {filepath}...")
    df = pd.read_csv(filepath)
    print(f"  Загружено {len(df)} записей")
    print(f"  Колонки: {list(df.columns)}")
    return df


def normalize_coordinates(df, x_col='x', y_col='y'):
    """Нормализует координаты X и Y в диапазон [0, 1]."""
    print("\nНормализация координат...")
    print(f"  X диапазон: [{df[x_col].min():.2f}, {df[x_col].max():.2f}]")
    print(f"  Y диапазон: [{df[y_col].min():.2f}, {df[y_col].max():.2f}]")
    
    df['x_norm'] = (df[x_col] - MAP_MIN) / (MAP_MAX - MAP_MIN)
    df['y_norm'] = (df[y_col] - MAP_MIN) / (MAP_MAX - MAP_MIN)
    
    print(f"  Нормализованный X: [{df['x_norm'].min():.4f}, {df['x_norm'].max():.4f}]")
    print(f"  Нормализованный Y: [{df['y_norm'].min():.4f}, {df['y_norm'].max():.4f}]")
    
    return df


def add_hp_percent(df, hp_col='hp'):
    """Добавляет колонку hp_percent."""
    print("\nДобавление hp_percent...")
    MAX_HP = 2000
    df['hp_percent'] = (df[hp_col] / MAX_HP * 100).clip(0, 100)
    print(f"  HP диапазон: [{df[hp_col].min()}, {df[hp_col].max()}]")
    print(f"  HP% диапазон: [{df['hp_percent'].min():.2f}%, {df['hp_percent'].max():.2f}%]")
    return df


def encode_heroes(df, hero_name_to_id, hero_col='hero_name'):
    """Превращает имена героев в ID из heroes.json."""
    print("\nКодирование героев...")
    
    df['hero_id'] = df[hero_col].map(hero_name_to_id)
    
    missing = df[df['hero_id'].isna()][hero_col].unique()
    if len(missing) > 0:
        print(f"  WARNING: Не найдены герои: {missing}")
    
    hero_ids = df[[hero_col, 'hero_id']].drop_duplicates().sort_values('hero_id')
    print(f"  Всего уникальных героев: {len(hero_ids)}")
    print("  Примеры:")
    for _, row in hero_ids.iterrows():
        print(f"    {int(row['hero_id']):3d} -> {row[hero_col]}")
    
    return df


def save_data(df, filepath):
    """Сохраняет результат в CSV."""
    print(f"\nСохранение в {filepath}...")
    df.to_csv(filepath, index=False)
    print(f"  Сохранено {len(df)} записей")


def main():
    print("=" * 60)
    print("ПРЕДОБРАБОТКА ДАННЫХ DOTA 2")
    print("=" * 60)
    print()
    
    hero_name_to_id = load_heroes(HEROES_FILE)
    df = load_data(INPUT_FILE)
    print(f"\nПервые 5 строк:")
    print(df.head())
    
    df = normalize_coordinates(df)
    df = add_hp_percent(df)
    df = encode_heroes(df, hero_name_to_id)
    
    result_df = df[['tick', 'hero_id', 'hero_name', 'x_norm', 'y_norm', 'hp', 'hp_percent']].copy()
    result_df = result_df.rename(columns={'x_norm': 'x', 'y_norm': 'y', 'hp': 'hp_raw'})
    
    save_data(result_df, OUTPUT_FILE)
    
    print("\n" + "=" * 60)
    print("ГОТОВО!")
    print("=" * 60)
    print(f"\nФинальные колонки: {list(result_df.columns)}")
    print(f"\nПример данных:")
    print(result_df.head(10))
    
    return result_df


if __name__ == "__main__":
    main()