# -*- coding: utf-8 -*-
"""
Скрипт для генерации справочных таблиц героев и предметов Dota 2
Запустить: python src/generate_ref.py
"""
import urllib.request
import json
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")

def get_data():
    """Получает данные из OpenDota API"""
    # Heroes
    req = urllib.request.Request('https://api.opendota.com/api/constants/heroes')
    req.add_header('User-Agent', 'Mozilla/5.0')
    heroes = json.loads(urllib.request.urlopen(req, timeout=15).read())
    heroes_dict = {v['id']: v['localized_name'] for v in heroes.values()}
    
    # Items - some items may not have localized_name
    req = urllib.request.Request('https://api.opendota.com/api/constants/items')
    req.add_header('User-Agent', 'Mozilla/5.0')
    items = json.loads(urllib.request.urlopen(req, timeout=15).read())
    items_dict = {}
    for v in items.values():
        name = v.get('localized_name') or v.get('dname') or v.get('name', f"item_{v['id']}")
        items_dict[v['id']] = name
    
    return heroes_dict, items_dict

def save_files(heroes, items):
    """Сохраняет файлы"""
    # heroes.json
    with open(os.path.join(DATA_DIR, 'heroes.json'), 'w', encoding='utf-8') as f:
        json.dump(heroes, f, ensure_ascii=False, indent=2)
    
    # items.json
    with open(os.path.join(DATA_DIR, 'items.json'), 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    
    # heroes.txt
    with open(os.path.join(DATA_DIR, 'heroes.txt'), 'w', encoding='utf-8') as f:
        f.write('=== DOTA 2 HEROES ===\n')
        f.write('ID | Name\n')
        f.write('-' * 40 + '\n')
        for id in sorted(heroes.keys()):
            f.write(f'{id:3} | {heroes[id]}\n')
    
    # items.txt
    with open(os.path.join(DATA_DIR, 'items.txt'), 'w', encoding='utf-8') as f:
        f.write('=== DOTA 2 ITEMS ===\n')
        f.write('ID | Name\n')
        f.write('-' * 40 + '\n')
        for id in sorted(items.keys()):
            f.write(f'{id:3} | {items[id]}\n')
    
    print(f'Saved: heroes.json ({len(heroes)}), items.json ({len(items)})')
    print(f'Saved: heroes.txt, items.txt')

def main():
    print('Fetching data from OpenDota API...')
    heroes, items = get_data()
    print(f'Found: {len(heroes)} heroes, {len(items)} items')
    save_files(heroes, items)
    print('Done!')

if __name__ == "__main__":
    main()
