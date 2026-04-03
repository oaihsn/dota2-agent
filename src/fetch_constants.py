# -*- coding: utf-8 -*-
"""
Скрипт для загрузки данных Dota 2 из OpenDota API
Запустить: python src/fetch_constants.py
"""
import urllib.request
import json
import csv
import os
import time

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")

def fetch_with_retry(url, retries=3):
    """Загрузка с повторными попытками"""
    for i in range(retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            response = urllib.request.urlopen(req, timeout=30)
            return json.loads(response.read().decode())
        except Exception as e:
            print(f"  Попытка {i+1} неудачна: {e}")
            time.sleep(2)
    return None

def main():
    print("=" * 50)
    print("Загрузка данных из OpenDota API")
    print("=" * 50)
    
    # 1. Heroes
    print("\n[1/3] Загрузка героев...")
    heroes_url = "https://api.opendota.com/api/constants/heroes"
    heroes = fetch_with_retry(heroes_url)
    if heroes:
        heroes_list = list(heroes.values())
        print(f"  Найдено героев: {len(heroes_list)}")
        # Save JSON
        heroes_dict = {h['id']: h['localized_name'] for h in heroes_list}
        with open(os.path.join(DATA_DIR, 'heroes.json'), 'w', encoding='utf-8') as f:
            json.dump(heroes_dict, f, ensure_ascii=False, indent=2)
        # Save CSV
        with open(os.path.join(DATA_DIR, 'heroes.csv'), 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name'])
            for h in heroes_list:
                writer.writerow([h['id'], h['localized_name']])
        print("  Сохранено: heroes.json, heroes.csv")
    else:
        print("  Ошибка загрузки героев")
    
    # 2. Items
    print("\n[2/3] Загрузка предметов...")
    items_url = "https://api.opendota.com/api/constants/items"
    items = fetch_with_retry(items_url)
    if items:
        items_list = list(items.values())
        print(f"  Найдено предметов: {len(items_list)}")
        # Save JSON
        items_dict = {i['id']: i.get('localized_name', i.get('dname', '')) for i in items_list}
        with open(os.path.join(DATA_DIR, 'items.json'), 'w', encoding='utf-8') as f:
            json.dump(items_dict, f, ensure_ascii=False, indent=2)
        # Save CSV
        with open(os.path.join(DATA_DIR, 'items.csv'), 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name'])
            for i in items_list:
                name = i.get('localized_name', i.get('dname', ''))
                writer.writerow([i['id'], name])
        print("  Сохранено: items.json, items.csv")
    else:
        print("  Ошибка загрузки предметов")
    
    # 3. Abilities
    print("\n[3/3] Загрузка способностей...")
    abilities_url = "https://api.opendota.com/api/constants/abilities"
    abilities = fetch_with_retry(abilities_url)
    if abilities:
        # Abilities может быть словарём с разными ключами
        if isinstance(abilities, dict):
            abilities_list = list(abilities.values())
        else:
            abilities_list = abilities
        print(f"  Найдено способностей: {len(abilities_list)}")
        # Сохраняем всё что есть
        abilities_data = []
        for a in abilities_list:
            if isinstance(a, dict):
                abilities_data.append({
                    'id': a.get('id', a.get('ability_id', '')),
                    'name': a.get('name', a.get('full_name', ''))
                })
        # Save JSON
        abilities_dict = {a['id']: a['name'] for a in abilities_data if a['id']}
        with open(os.path.join(DATA_DIR, 'abilities.json'), 'w', encoding='utf-8') as f:
            json.dump(abilities_dict, f, ensure_ascii=False, indent=2)
        # Save CSV
        with open(os.path.join(DATA_DIR, 'abilities.csv'), 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name'])
            for a in abilities_data:
                if a['id']:
                    writer.writerow([a['id'], a['name']])
        print("  Сохранено: abilities.json, abilities.csv")
    else:
        print("  Ошибка загрузки способностей")
    
    print("\n" + "=" * 50)
    print("Готово!")
    print("=" * 50)

if __name__ == "__main__":
    main()
