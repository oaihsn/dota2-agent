# -*- coding: utf-8 -*-
"""
Stratz API Parser для Dota 2
Получает timeline данные матча каждые 2 тика

https://stratz.com/api
"""
try:
    import cloudscraper
    SCRAPER = cloudscraper.create_scraper()
except ImportError:
    import requests
    SCRAPER = requests.Session()

import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

import pandas as pd

# Константы
PROJECT_DIR = Path(__file__).parent.parent.absolute()
DATA_PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
LOG_DIR = PROJECT_DIR / "logs"

# Stratz API Base URL
STRATZ_API = "https://api.stratz.com/api/v1"

# Настройки
TICK_INTERVAL = 2  # Каждые 2 тика
REQUEST_DELAY = 0.2  # Задержка между запросами (сек)
RATE_LIMIT = 30  # Макс запросов в минуту (без API ключа)

DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / 'stratz_parser.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class PlayerState:
    """Состояние игрока в один момент времени."""
    match_id: int
    game_time: float  # Время в секундах
    
    # Данные игрока
    player_slot: int
    team: int  # 0 = Radiant, 1 = Dire
    account_id: int
    hero_id: int
    
    # Ресурсы
    level: int = 0
    gold: int = 0
    net_worth: int = 0
    xp: int = 0
    
    # Координаты
    pos_x: float = 0.0
    pos_y: float = 0.0
    
    # Здоровье
    health: int = 0
    max_health: int = 0
    mana: int = 0
    max_mana: int = 0
    
    # Инвентарь (6 предметов)
    item_0: int = 0
    item_1: int = 0
    item_2: int = 0
    item_3: int = 0
    item_4: int = 0
    item_5: int = 0
    
    # Статистика
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    last_hits: int = 0
    denies: int = 0
    
    # buyback_log
    buyback_log: str = ""


class StratzParser:
    """Парсер данных через Stratz API."""
    
    def __init__(self, api_key: str = None, match_id: int = None):
        self.api_key = api_key
        self.match_id = match_id
        self.session = SCRAPER  # Используем cloudscraper
        
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        })
    
    def _request(self, url: str) -> Optional[Dict]:
        """Выполняет запрос с API ключом."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = self.session.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Request error {url}: {e}")
            return None
    
    def get_match(self, match_id: int) -> Optional[Dict]:
        """Получает базовые данные матча."""
        url = f"{STRATZ_API}/match/{match_id}"
        return self._request(url)
    
    def get_timeline(self, match_id: int) -> Optional[Dict]:
        """Получает timeline данные матча (посмертные события)."""
        url = f"{STRATZ_API}/match/{match_id}/timeline"
        return self._request(url)
    
    def parse_timeline(self, timeline: Dict) -> List[PlayerState]:
        """Парсит timeline в список состояний."""
        states = []
        
        if not timeline:
            return states
        
        # Получаем метаданные матча
        match_id = timeline.get("matchId", self.match_id)
        
        # Получаем временные метки
        times = timeline.get("times", [])
        
        # Получаем данные игроков
        players = timeline.get("players", [])
        
        if not times or not players:
            logger.warning("No timeline data found")
            return states
        
        logger.info(f"  Timeline: {len(times)} time points, {len(players)} players")
        
        # Создаём состояния для каждого временного среза
        for time_idx, game_time in enumerate(times):
            # Проверяем интервал (каждые 2 тика ≈ каждые 0.067 сек)
            if time_idx % TICK_INTERVAL != 0:
                continue
            
            # Для каждого игрока
            for player_data in players:
                player_slot = player_data.get("playerSlot", 0)
                team = 0 if player_slot < 128 else 1
                
                # Получаем данные на этом временном срезе
                gold_reasons = player_data.get("goldReasons", [])
                gold_t = gold_reasons[time_idx] if time_idx < len(gold_reasons) else {}
                xp_reasons = player_data.get("xpReasons", [])
                xp_t = xp_reasons[time_idx] if time_idx < len(xp_reasons) else {}
                
                # Базовые данные
                position = player_data.get("position", {})
                pos_t = position[time_idx] if time_idx < len(position) else {}
                
                # Инвентарь
                purchase = player_data.get("purchase", {})
                purchase_t = purchase[time_idx] if time_idx < len(purchase) else {}
                
                # Статистика
                stats = player_data.get("stats", [])
                stats_t = stats[time_idx] if time_idx < len(stats) else {}
                
                state = PlayerState(
                    match_id=match_id,
                    game_time=game_time,
                    player_slot=player_slot,
                    team=team,
                    account_id=player_data.get("accountId", 0),
                    hero_id=player_data.get("heroId", 0),
                    
                    level=stats_t.get("level", 0),
                    gold=gold_t.get("gold", 0),
                    net_worth=stats_t.get("networth", 0),
                    xp=xp_t.get("xp", 0),
                    
                    pos_x=pos_t.get("x", 0),
                    pos_y=pos_t.get("y", 0),
                    
                    health=stats_t.get("health", 0),
                    max_health=stats_t.get("maxHealth", 0),
                    mana=stats_t.get("mana", 0),
                    max_mana=stats_t.get("maxMana", 0),
                    
                    item_0=purchase_t.get("item_0", 0),
                    item_1=purchase_t.get("item_1", 0),
                    item_2=purchase_t.get("item_2", 0),
                    item_3=purchase_t.get("item_3", 0),
                    item_4=purchase_t.get("item_4", 0),
                    item_5=purchase_t.get("item_5", 0),
                    
                    kills=stats_t.get("kills", 0),
                    deaths=stats_t.get("deaths", 0),
                    assists=stats_t.get("assists", 0),
                    last_hits=stats_t.get("lastHits", 0),
                    denies=stats_t.get("denies", 0),
                )
                
                states.append(state)
        
        return states


def parse_match(match_id: int, api_key: str = None) -> pd.DataFrame:
    """Парсит матч через Stratz API.
    
    Args:
        match_id: ID матча
        api_key: Stratz API ключ (опционально)
    
    Returns:
        DataFrame с timeline данными
    """
    logger.info(f"Parsing match {match_id} via Stratz API")
    
    parser = StratzParser(api_key=api_key, match_id=match_id)
    
    # Получаем timeline
    logger.info("  Fetching timeline...")
    timeline = parser.get_timeline(match_id)
    
    if not timeline:
        logger.error("  No timeline data available")
        return pd.DataFrame()
    
    # Парсим timeline
    logger.info("  Parsing timeline...")
    states = parser.parse_timeline(timeline)
    
    if not states:
        logger.warning("  No states parsed from timeline")
        return pd.DataFrame()
    
    # Конвертируем в DataFrame
    df = pd.DataFrame([asdict(s) for s in states])
    
    logger.info(f"  Parsed {len(df)} records")
    
    return df


def save_match(match_id: int, api_key: str = None, output_path: str = None):
    """Парсит и сохраняет матч.
    
    Args:
        match_id: ID матча
        api_key: Stratz API ключ
        output_path: Путь для сохранения
    """
    df = parse_match(match_id, api_key)
    
    if df.empty:
        logger.error(f"  No data for match {match_id}")
        return None
    
    if output_path is None:
        output_path = DATA_PROCESSED_DIR / f"stratz_{match_id}.parquet"
    else:
        output_path = Path(output_path)
    
    df.to_parquet(output_path, index=False)
    
    size_mb = output_path.stat().st_size / 1024 / 1024
    logger.info(f"  Saved: {output_path} ({size_mb:.2f} MB)")
    
    return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Stratz API Parser")
    parser.add_argument("--match-id", "-m", type=int, required=True, help="Match ID")
    parser.add_argument("--api-key", "-k", help="Stratz API key")
    parser.add_argument("--output", "-o", help="Output file path")
    
    args = parser.parse_args()
    
    save_match(args.match_id, args.api_key, args.output)
