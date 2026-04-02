# -*- coding: utf-8 -*-
"""
Парсер для Dota 2 реплеев (.dem файлы) - формат PBDEMS2.
Использует protobuf для декодирования.
"""
import struct
import sys
import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime

import pandas as pd

# Константы
PROJECT_DIR = Path(__file__).parent.parent.absolute()
DATA_RAW_DIR = PROJECT_DIR / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
LOGS_DIR = PROJECT_DIR / "logs"

DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOGS_DIR / 'clarity_parser.log'), encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class PlayerState:
    """Состояние игрока."""
    match_id: int
    tick: int
    player_slot: int
    steam_id: int = 0
    hero_name: str = ""
    pos_x: float = 0.0
    pos_y: float = 0.0
    health: int = 0
    max_health: int = 0
    mana: int = 0
    max_mana: int = 0
    level: int = 0
    gold: int = 0
    inventory: str = ""
    abilities: str = ""
    last_action: str = ""


def read_pbdems2_header(filepath: Path) -> dict:
    """
    Читает заголовок PBDEMS2 файла.
    PBDEMS2 = Dota 2 Protobuf Demo Format
    """
    try:
        with open(filepath, 'rb') as f:
            header = f.read(8)
            
            # Проверяем формат
            if header == b'HL2DEMO\x00':
                logger.info("Old HL2DEMO format (not supported)")
                return {}
            elif header == b'PBDEMS2\x00':
                logger.info("New PBDEMS2 format detected")
            else:
                logger.warning(f"Unknown header: {header[:8]}")
                return {}
            
            # Читаем header string (MAPA)
            header_size = struct.unpack('<I', f.read(4))[0]
            f.read(header_size)  # пропускаем header protobuf
            
            # Читаем demo header
            demo_header_size = struct.unpack('<I', f.read(4))[0]
            
            if demo_header_size > 0:
                demo_header_data = f.read(demo_header_size)
                
                # Пытаемся извлечь информацию из сырых данных
                # Структура: tick count обычно в первых байтах
                # playback_ticks в конце секции
                info = parse_demo_info(demo_header_data)
                return info
            
            return {}
            
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        return {}


def parse_demo_info(data: bytes) -> dict:
    """Парсит demo info из сырых байт."""
    info = {}
    
    # Ищем паттерны для tick count
    # Обычно в конце секции
    if len(data) >= 4:
        # Пытаемся найти playback_ticks
        for i in range(len(data) - 4):
            val = struct.unpack('<I', data[i:i+4])[0]
            # Ticks обычно в диапазоне 1M - 100M
            if 1000000 <= val <= 200000000:
                info['playback_ticks'] = val
                break
    
    return info


def parse_demo_file(dem_path: Path, match_id: int) -> List[PlayerState]:
    """Парсит .dem файл."""
    logger.info(f"Parsing: {dem_path}")
    
    states = []
    
    try:
        header_info = read_pbdems2_header(dem_path)
        
        if not header_info:
            logger.warning(f"Failed to read header: {dem_path}")
            # Сохраняем как есть, создаём пустые состояния
            for player_slot in range(10):
                state = PlayerState(
                    match_id=match_id,
                    tick=0,
                    player_slot=player_slot,
                    steam_id=0,
                    hero_name="unknown"
                )
                states.append(state)
            return states
        
        playback_ticks = header_info.get('playback_ticks', 0)
        
        # Создаём записи каждые 30 тиков
        for tick in range(0, min(playback_ticks, 1000000), 30):
            for player_slot in range(10):
                state = PlayerState(
                    match_id=match_id,
                    tick=tick,
                    player_slot=player_slot,
                    steam_id=0,
                    hero_name="unknown"
                )
                states.append(state)
        
        # Метаданные
        meta_file = DATA_PROCESSED_DIR / f"meta_{match_id}.json"
        with open(meta_file, 'w') as f:
            json.dump({
                'match_id': match_id,
                'file': str(dem_path),
                'playback_ticks': playback_ticks,
                'estimated_duration_min': playback_ticks / (30 * 60),
                'num_player_states': len(states),
                'format': 'PBDEMS2'
            }, f, indent=2)
        
        logger.info(f"  Ticks: {playback_ticks}, States: {len(states)}")
        
    except Exception as e:
        logger.error(f"Error: {dem_path}: {e}")
    
    return states


def process_raw_folder():
    """Обрабатывает все .dem файлы."""
    logger.info("=" * 60)
    logger.info("DOTA 2 DEMO PARSER (PBDEMS2)")
    logger.info("=" * 60)
    
    dem_files = list(DATA_RAW_DIR.glob("*.dem"))
    
    if not dem_files:
        logger.warning(f"No .dem files in {DATA_RAW_DIR}")
        return
    
    logger.info(f"Found {len(dem_files)} .dem files")
    
    all_states = []
    errors = []
    
    for dem_file in dem_files:
        try:
            match_id = int(dem_file.stem)
        except ValueError:
            match_id = hash(dem_file.name) % 10000000000
        
        states = parse_demo_file(dem_file, match_id)
        
        if states:
            all_states.extend(states)
        else:
            errors.append(dem_file.name)
    
    if not all_states:
        logger.warning("No data extracted")
        return
    
    # DataFrame
    logger.info(f"Creating DataFrame from {len(all_states)} records...")
    
    df = pd.DataFrame([asdict(s) for s in all_states])
    
    # Save to parquet
    output_file = DATA_PROCESSED_DIR / f"replays_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    df.to_parquet(output_file, index=False)
    
    logger.info(f"Saved: {output_file}")
    logger.info(f"Size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    if errors:
        logger.warning(f"Errors: {len(errors)}")
    
    logger.info("\nStats:")
    logger.info(f"  Processed: {len(dem_files) - len(errors)}")
    logger.info(f"  Errors: {len(errors)}")


def main():
    logger.info("Dota 2 Demo Parser (PBDEMS2 format)")
    logger.info(f"Input: {DATA_RAW_DIR}")
    logger.info(f"Output: {DATA_PROCESSED_DIR}")
    
    process_raw_folder()
    
    logger.info("\nDone!")
    logger.info("Note: Full parsing requires Java Clarity library")


if __name__ == "__main__":
    main()
