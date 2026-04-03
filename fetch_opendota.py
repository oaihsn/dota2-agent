# -*- coding: utf-8 -*-
"""
Скрипт для получения данных матча с OpenDota API
"""
import requests
import json

MATCH_ID = 8749329335

# Hero ID to name mapping (полный список)
HEROES = {
    1: 'Anti-Mage', 2: 'Axe', 3: 'Bane', 4: 'Bloodseeker', 5: 'Crystal Maiden',
    6: 'Drow Ranger', 7: 'Earthshaker', 8: 'Juggernaut', 9: 'Mirana', 10: 'Morphling',
    11: 'Phantom Lancer', 12: 'Puck', 13: 'Pugna', 14: 'Vengeful Spirit', 15: 'Weaver',
    16: 'Windrunner', 17: 'Storm Spirit', 18: 'Tinker', 19: 'Sven', 20: 'Tiny',
    21: 'Vengeful Spirit', 22: 'Windrunner', 23: 'Zeus', 24: 'Kunkka', 25: 'Slark',
    26: 'Tidehunter', 27: 'Razor', 28: 'Venomancer', 29: 'Faceless Void', 30: 'Skeleton King',
    31: 'Death Prophet', 32: 'Phantom Assassin', 33: 'Pugna', 34: 'Dazzle', 35: 'Shadow Shaman',
    36: 'Riki', 37: 'Enigma', 38: 'Tidehunter', 39: 'Wraith King', 40: 'Slark',
    41: 'Luna', 42: 'Sand King', 43: 'Night Stalker', 44: 'Broodmother', 45: 'Kunkka',
    46: 'Huskar', 47: 'Lina', 48: 'Lion', 49: 'Batrider', 50: 'Clinkz',
    51: 'Spectre', 52: 'Doom', 53: 'Ursa', 54: 'Faceless Void', 55: 'Sniper',
    56: 'Shadow Fiend', 57: 'Raven', 58: 'Storm Spirit', 59: 'Sand King', 60: 'Luna',
    61: 'Dragon Knight', 62: 'Dazzle', 63: 'Rattletrap', 64: 'Leshrac', 65: 'Nature\'s Prophet',
    66: 'Lich', 67: 'Viper', 68: 'Faceless Void', 69: 'Pudge', 70: 'Witch Doctor',
    71: 'Strygwyr', 72: 'Balanar', 73: 'Drow Ranger', 74: 'Morphling', 75: 'Nevermore',
    76: 'Necrolyte', 77: 'Warlock', 78: 'Beastmaster', 79: 'Jakiro', 80: 'Chen',
    81: 'Doom', 82: 'Ancient Apparition', 83: 'Ursa', 84: 'Spirit Breaker', 85: 'Gyrocopter',
    86: 'Alchemist', 87: 'Invoker', 88: 'Silencer', 89: 'Outworld Destroyer', 90: 'Shadow Demon',
    91: 'Lycan', 92: 'Brewmaster', 93: 'Shadow Shaman', 94: 'Slardar', 95: 'Medusa',
    96: 'Troll Warlord', 97: 'Centaur Warrunner', 98: 'Magnus', 99: 'Timbersaw',
    100: 'Bristleback', 101: 'Tusk', 102: 'Skywrath Mage', 103: 'Abaddon', 104: 'Elder Titan',
    105: 'Legion Commander', 106: 'Techies', 107: 'Ember Spirit', 108: 'Earth Spirit', 109: 'Underlord',
    110: 'Terrorblade', 111: 'Phoenix', 112: 'Oracle', 113: 'Winter Wyvern', 114: 'Arc Warden',
    115: 'Monkey King', 116: 'Dark Willow', 117: 'Pangolier', 118: 'Grimstroke', 119: 'Hoodwink',
    120: 'Void Spirit', 121: 'Snapfire', 122: 'Mars', 123: 'Dawnbreaker', 124: 'Marci', 125: 'Primal Beast',
    126: 'Trundle', 127: 'Undying', 128: 'Rubick', 129: 'Disruptor', 130: 'Nyx Assassin',
    131: 'Naga Siren', 132: 'Keeper of the Light', 133: 'Io', 134: 'Visage', 135: 'Enchantress',
    136: 'Nature\'s Prophet', 137: 'Nature\'s Prophet', 138: 'Templar Assassin', 139: 'Luna',
    140: 'Bounty Hunter', 141: 'Ursa', 142: 'Naga Siren', 143: 'Kunkka', 144: 'Tidehunter',
    145: 'Sand King', 146: 'Slark'
}

def get_match_data(match_id):
    """Получает данные матча с OpenDota API"""
    url = f"https://api.opendota.com/api/matches/{match_id}"
    response = requests.get(url)
    return response.json()

def format_table(data):
    """Форматирует данные матча в таблицу"""
    print("=" * 100)
    print(f"MATCH {MATCH_ID} - DOTA 2 MATCH DATA")
    print("=" * 100)
    print()
    print(f"Duration: {data['duration']} seconds ({data['duration']//60} min {data['duration']%60} sec)")
    print(f"Radiant Win: {data['radiant_win']}")
    print(f"Start Time: {data['start_time']}")
    print()
    
    print("PLAYERS:")
    print("-" * 100)
    print(f"{'Team':<10} {'Slot':<6} {'Hero':<25} {'K':<5} {'D':<5} {'A':<6} {'GPM':<6} {'XPM':<6} {'Level':<6} {'Net Worth':<10} {'Win':<6}")
    print("-" * 100)
    
    for p in data['players']:
        team = 'Radiant' if p['team_number'] == 0 else 'Dire'
        hero = HEROES.get(p['hero_id'], f"Hero {p['hero_id']}")
        win = 'WIN' if (p['isRadiant'] and data['radiant_win']) or (not p['isRadiant'] and not data['radiant_win']) else 'LOSE'
        
        print(f"{team:<10} {p['player_slot']:<6} {hero:<25} {p['kills']:<5} {p['deaths']:<5} {p['assists']:<6} {p['gold_per_min']:<6} {p['xp_per_min']:<6} {p['level']:<6} {p['net_worth']:<10} {win:<6}")
    
    print("-" * 100)

if __name__ == "__main__":
    print("Fetching match data from OpenDota API...")
    data = get_match_data(MATCH_ID)
    
    # Print table
    format_table(data)
    
    # Save to file
    with open('data/processed/match_8749329335_full.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print()
    print("Full data saved to: data/processed/match_8749329335_full.json")