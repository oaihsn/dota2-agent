# -*- coding: utf-8 -*-
"""
Local Dota 2 Replay Parser using demoparser2
"""
import os
from pathlib import Path
from demoparser2 import DemoParser
import pandas as pd

# Constants
PROJECT_DIR = Path(__file__).parent.absolute()
DATA_RAW_DIR = PROJECT_DIR / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
TICK_INTERVAL = 30

# Hero ID to name mapping
HERO_IDS = {
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


def find_demo_file():
    """Find the .dem file in data/raw directory."""
    if not DATA_RAW_DIR.exists():
        print(f"Directory not found: {DATA_RAW_DIR}")
        return None
    
    demo_files = list(DATA_RAW_DIR.glob("*.dem"))
    if not demo_files:
        print("No .dem files found!")
        return None
    
    print(f"Found demo file: {demo_files[0].name}")
    return demo_files[0]


def parse_demo_efficient(demo_path: Path, tick_interval: int = 30):
    """
    Parse demo file efficiently, filtering to every Nth tick.
    Uses generator to avoid loading all data into memory at once.
    """
    print(f"Loading demo: {demo_path.name}")
    
    # Create parser
    parser = DemoParser(str(demo_path))
    
    # Get all ticks first - we need this to know which ticks to filter
    print("Getting tick list...")
    ticks = parser.parse_ticks()
    print(f"Total ticks in replay: {len(ticks)}")
    
    # Filter to every Nth tick
    filtered_ticks = ticks[::tick_interval]
    print(f"Filtered ticks (every {tick_interval}): {len(filtered_ticks)}")
    
    # Now we need to get entity data for these ticks
    # demoparser2 can filter by ticks when parsing entities
    
    # First, let's understand what entities we're looking for
    # For heroes, we need: CBodyComponentBaseBus.m_vecX, CBodyComponentBaseBus.m_vecY
    # For player stats: m_iHealth, m_iLevel, m_iNetWorth
    
    return filtered_ticks


def main():
    """Main function."""
    print("=" * 60)
    print("LOCAL DOTA 2 REPLAY PARSER (demoparser2)")
    print("=" * 60)
    
    # Find demo file
    demo_path = find_demo_file()
    if not demo_path:
        return
    
    # Parse efficiently
    ticks = parse_demo_efficient(demo_path, TICK_INTERVAL)
    
    print(f"\nFirst 10 filtered ticks: {ticks[:10]}")
    print("\nDone!")


if __name__ == "__main__":
    main()