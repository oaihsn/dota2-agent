# -*- coding: utf-8 -*-
"""
Парсер данных матчей Dota 2 через OpenDota API.
Извлекает: герои, уровни, золото, предметы, способности.
"""
import requests
import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List
from datetime import datetime
import pandas as pd

# Константы
PROJECT_DIR = Path(__file__).parent.parent.absolute()
DATA_PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
OPENDOTA_API = "https://api.opendota.com/api"

DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PlayerState:
    """Состояние игрока."""
    match_id: int
    tick: int  # секунды от начала
    player_slot: int
    team: int  # 0 = Radiant, 1 = Dire
    
    # Герой
    hero_id: int
    hero_name: str = ""
    
    # Ресурсы
    level: int = 0
    gold: int = 0
    net_worth: int = 0
    gold_per_min: int = 0
    xp_per_min: int = 0
    
    # Инвентарь (6 предметов)
    item_0: str = ""
    item_1: str = ""
    item_2: str = ""
    item_3: str = ""
    item_4: str = ""
    item_5: str = ""
    
    # Способности (обычно 4)
    ability_0: str = ""
    ability_1: str = ""
    ability_2: str = ""
    ability_3: str = ""
    ability_4: str = ""
    ability_5: str = ""
    ability_6: str = ""
    ability_7: str = ""
    
    # Статистика
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    last_hits: int = 0
    denies: int = 0
    
    # Steam
    account_id: int = 0
    personaname: str = ""


HERO_ID_TO_NAME = {
    1: "antimage", 2: "axe", 3: "bane", 4: "bloodseeker", 5: "crystal_maiden",
    6: "drow_ranger", 7: "earthshaker", 8: "earth_spirit", 9: "elder_titan",
    10: "enchantress", 11: "enigma", 12: "faceless_void", 13: "furion", 14: "juggernaut",
    15: "mirana", 16: "morphling", 17: "nevermore", 18: "phantom_lancer", 19: "puck",
    20: "pudge", 21: "rattletrap", 22: "razor", 23: "sand_king", 24: "shadow_shaman",
    25: "slardar", 26: "sniper", 27: "spectre", 28: "storm_spirit", 29: "sven",
    30: "tiny", 31: "vengefulspirit", 32: "viper", 33: "witch_doctor", 34: "lich",
    35: "lina", 36: "lion", 37: "shadow_fiend", 38: "slark", 39: "tidehunter",
    40: "rattletrap", 41: "witch_doctor", 42: "lich", 43: "rubick", 44: "disruptor",
    45: "necrophos", 46: "warlock", 47: "beastmaster", 48: "queenofpain", 49: "visage",
    50: "wraith_king", 51: "duff", 52: "leshrac", 53: "dark_seer", 54: "clinkz",
    55: "omniknight", 56: "chen", 57: "centaur", 58: "bristleback", 59: "tusk",
    60: "skywrath_mage", 61: "medusa", 62: "treant", 63: "ogre_magi", 64: "invoker",
    65: "silencer", 66: "natures_prophet", 67: "nyx_assassin", 68: " Keeper_of_the_Light",
    69: "wisp", 70: "sniper", 71: "storm_spirit", 72: "puppeteer", 73: "phoenix",
    74: "oracle", 75: "techies", 76: "templar_assassin", 77: "ember_spirit", 78: "legion_commander",
    79: "terrorblade", 80: "gyrocopter", 81: "chaos_knight", 82: "meepo", 83: "obsidian_destroyer",
    84: "shadow_demon", 85: "lycan", 86: "brewmaster", 87: "lone_druid", 88: "chaos_knight",
    89: "spectre", 90: "meepo", 91: "witch_doctor", 92: "skeleton_king", 93: "doom_bringer",
    94: "ancient_apparition", 95: "invoker", 96: "silencer", 97: "global_silencer",
    98: "techies", 99: "ta", 100: "shaker", 101: "meppo", 102: "king_c",
    103: "night_stalker", 104: "broodmother", 105: "spider", 106: "wolf",
    107: "bounty_hunter", 108: "weaver", 109: "spectre", 110: "necrolyte",
    # ... можно добавить больше
}


def get_match_data(match_id: int) -> dict:
    """Получает данные матча через OpenDota API."""
    url = f"{OPENDOTA_API}/matches/{match_id}"
    logger.info(f"Fetching: {url}")
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    return response.json()


def parse_match(match_id: int, tick_interval: int = 60) -> List[PlayerState]:
    """Парсит матч и создаёт состояния игроков."""
    logger.info(f"Parsing match {match_id}")
    
    match_data = get_match_data(match_id)
    duration = match_data.get('duration', 0)
    players = match_data.get('players', [])
    
    states = []
    
    # Создаём записи каждые tick_interval секунд
    for second in range(0, duration, tick_interval):
        for p in players:
            hero_id = p.get('hero_id', 0)
            player_slot = p.get('player_slot', 0)
            team = 0 if player_slot < 128 else 1
            
            state = PlayerState(
                match_id=match_id,
                tick=second,
                player_slot=player_slot,
                team=team,
                hero_id=hero_id,
                hero_name=HERO_ID_TO_NAME.get(hero_id, f"hero_{hero_id}"),
                level=p.get('level', 0),
                gold=p.get('gold', 0),
                net_worth=p.get('net_worth', 0),
                gold_per_min=p.get('gold_per_min', 0),
                xp_per_min=p.get('xp_per_min', 0),
                item_0=p.get('item_0', ''),
                item_1=p.get('item_1', ''),
                item_2=p.get('item_2', ''),
                item_3=p.get('item_3', ''),
                item_4=p.get('item_4', ''),
                item_5=p.get('item_5', ''),
                ability_0=p.get('ability_0', ''),
                ability_1=p.get('ability_1', ''),
                ability_2=p.get('ability_2', ''),
                ability_3=p.get('ability_3', ''),
                ability_4=p.get('ability_4', ''),
                ability_5=p.get('ability_5', ''),
                ability_6=p.get('ability_6', ''),
                ability_7=p.get('ability_7', ''),
                kills=p.get('kills', 0),
                deaths=p.get('deaths', 0),
                assists=p.get('assists', 0),
                last_hits=p.get('last_hits', 0),
                denies=p.get('denies', 0),
                account_id=p.get('account_id', 0),
                personaname=p.get('personaname', ''),
            )
            states.append(state)
    
    logger.info(f"  Generated {len(states)} records ({duration//tick_interval} ticks x 10 players)")
    
    return states


def save_match(match_id: int, tick_interval: int = 60):
    """Сохраняет матч в parquet."""
    states = parse_match(match_id, tick_interval)
    
    df = pd.DataFrame([asdict(s) for s in states])
    
    output_file = DATA_PROCESSED_DIR / f"opendota_{match_id}.parquet"
    df.to_parquet(output_file, index=False)
    
    logger.info(f"Saved: {output_file} ({len(df)} records)")
    
    return len(df)


def main():
    logger.info("OpenDota Match Parser")
    logger.info("=" * 40)
    
    # Пример: парсим матчи из data/raw
    raw_dir = PROJECT_DIR / "data" / "raw"
    dem_files = list(raw_dir.glob("*.dem"))
    
    if dem_files:
        # Extract match IDs from filenames
        for dem_file in dem_files[:3]:  # Первые 3
            try:
                match_id = int(dem_file.stem)
                save_match(match_id, tick_interval=60)
            except Exception as e:
                logger.error(f"Error: {dem_file}: {e}")
    else:
        # Тестовый матч
        save_match(8749329335, tick_interval=60)
    
    logger.info("\nDone!")


if __name__ == "__main__":
    main()
