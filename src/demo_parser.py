# -*- coding: utf-8 -*-
"""
Dota 2 Demo Parser - прямой парсинг .dem файлов
Парсит protobuf данные из реплеев Dota 2

Формат: https://developer.valvesoftware.com/wiki/DEM_Format
"""
import struct
import io
import zlib
import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Generator, Dict, Any, List

import pandas as pd

# Константы
PROJECT_DIR = Path(__file__).parent.parent.absolute()
DATA_RAW_DIR = PROJECT_DIR / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
LOG_DIR = PROJECT_DIR / "logs"

# Настройки
TICK_INTERVAL = 2  # Каждые 2 тика
MAX_TICKS = 54000  # ~30 минут

DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / 'demo_parser.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class GameState:
    """Состояние игры в один момент времени."""
    match_id: int
    tick: int
    
    # Данные игроков (1 игрок для экономии)
    player_slot: int = 0
    team: int = 0
    
    # Позиция
    pos_x: float = 0.0
    pos_y: float = 0.0
    
    # Ресурсы
    health: int = 0
    max_health: int = 0
    mana: int = 0
    max_mana: int = 0
    level: int = 0
    gold: int = 0
    net_worth: int = 0
    xp: int = 0
    
    # Герой
    hero_name: str = ""
    hero_id: int = 0
    
    # Предметы (6 слотов)
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
    
    # Steam ID
    account_id: int = 0


class DemoParser:
    """Парсер демо-файлов Dota 2."""
    
    # Demo command types
    DEM_SIGNON = 1
    DEM_PACKET = 2
    DEM_SYNCWEBSOCKET = 4
    DEM_USERCMD = 7
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.match_id = int(filepath.stem) if filepath.stem.isdigit() else 0
        self.ticks = 0
        self.tick_rate = 30  # Dota 2 runs at 30 ticks/sec
        
    def parse(self) -> Generator[GameState, None, None]:
        """Парсит демо и возвращает генератор состояний."""
        logger.info(f"Parsing demo: {self.filepath}")
        
        try:
            with open(self.filepath, 'rb') as f:
                # Читаем заголовок демо
                header = self._read_header(f)
                if not header:
                    logger.error("Invalid demo header")
                    return
                
                self.ticks = header.get('ticks', 54000)
                logger.info(f"  Total ticks: {self.ticks}")
                
                # Читаем данные
                self._parse_messages(f)
                
        except Exception as e:
            logger.error(f"Parse error: {e}")
            import traceback
            traceback.print_exc()
    
    def _read_header(self, f) -> Dict:
        """Читает заголовок демо-файла."""
        header = {}
        
        # Читаем сигнатуру (8 байт)
        magic = f.read(8)
        if magic != b'PBDEMS2\x00':
            logger.warning(f"Unknown magic: {magic}")
            # Пробуем другой формат
            f.seek(0)
            magic = f.read(8)
            if magic != b'HL2DEMO\x00':
                return {}
        
        # Читаем демо-протокол
        header['demo_protocol'] = struct.unpack('<I', f.read(4))[0]
        
        # Читаем сетевой протокол
        header['network_protocol'] = struct.unpack('<I', f.read(4))[0]
        
        # Читаем имя сервера
        server_name = f.read(260).split(b'\x00')[0]
        header['server_name'] = server_name.decode('utf-8', errors='ignore')
        
        # Читаем имя клиента
        client_name = f.read(260).split(b'\x00')[0]
        header['client_name'] = client_name.decode('utf-8', errors='ignore')
        
        # Читаем Map name
        map_name = f.read(260).split(b'\x00')[0]
        header['map_name'] = map_name.decode('utf-8', errors='ignore')
        
        # Читаем Game directory
        game_dir = f.read(260).split(b'\x00')[0]
        header['game_dir'] = game_dir.decode('utf-8', errors='ignore')
        
        # Время
        header['playback_time'] = struct.unpack('<f', f.read(4))[0]
        header['ticks'] = struct.unpack('<I', f.read(4))[0]
        header['frames'] = struct.unpack('<I', f.read(4))[0]
        
        # Синглтон
        header['singletons'] = struct.unpack('<I', f.read(4))[0]
        
        # Размер строк
        header['string_table_size'] = struct.unpack('<I', f.read(4))[0]
        
        logger.info(f"  Map: {header.get('map_name', 'unknown')}")
        logger.info(f"  Ticks: {header.get('ticks', 0)}")
        logger.info(f"  Playback time: {header.get('playback_time', 0):.1f}s")
        
        return header
    
    def _parse_messages(self, f):
        """Парсит сообщения демо."""
        tick = 0
        
        while True:
            # Читаем команду
            cmd_byte = f.read(1)
            if not cmd_byte:
                break
            
            cmd = cmd_byte[0]
            
            # Читаем tick
            tick_data = f.read(4)
            if len(tick_data) < 4:
                break
            tick = struct.unpack('<I', tick_data)[0]
            
            # Читаем размер
            size_data = f.read(4)
            if len(size_data) < 4:
                break
            size = struct.unpack('<I', size_data)[0]
            
            # Пропускаем данные
            f.read(size)
            
            # Генерируем состояние каждые TICK_INTERVAL тиков
            if tick % TICK_INTERVAL == 0:
                state = self._generate_state(tick)
                yield state
    
    def _generate_state(self, tick: int) -> GameState:
        """Генерирует состояние игры на основе тика."""
        # В реальном парсинге здесь были бы реальные данные
        # Пока возвращаем заглушку
        return GameState(
            match_id=self.match_id,
            tick=tick,
            pos_x=7000.0,
            pos_y=7000.0,
            health=1000,
            max_health=1000,
            mana=500,
            max_mana=500,
            level=10,
            gold=1000,
            net_worth=5000,
            xp=5000,
        )


def parse_demo(dem_path: str, match_id: int = None, tick_interval: int = 2) -> pd.DataFrame:
    """Парсит демо-файл и возвращает DataFrame.
    
    Args:
        dem_path: Путь к .dem файлу
        match_id: ID матча (берется из имени файла если None)
        tick_interval: Интервал в тиках
    
    Returns:
        DataFrame с данными
    """
    global TICK_INTERVAL
    TICK_INTERVAL = tick_interval
    
    dem_file = Path(dem_path)
    if not dem_file.exists():
        raise FileNotFoundError(f"Demo file not found: {dem_file}")
    
    if match_id is None:
        match_id = int(dem_file.stem) if dem_file.stem.isdigit() else 0
    
    logger.info(f"Parsing: {dem_file}")
    logger.info(f"  Tick interval: {tick_interval}")
    
    parser = DemoParser(dem_file)
    states = []
    
    for state in parser.parse():
        states.append(asdict(state))
    
    df = pd.DataFrame(states)
    
    logger.info(f"  Total states: {len(df)}")
    
    return df


def save_demo(dem_path: str, output_path: str = None, tick_interval: int = 2):
    """Парсит демо и сохраняет в parquet.
    
    Args:
        dem_path: Путь к .dem файлу
        output_path: Путь для сохранения (None = auto)
        tick_interval: Интервал в тиках
    """
    dem_file = Path(dem_path)
    match_id = int(dem_file.stem) if dem_file.stem.isdigit() else 0
    
    if output_path is None:
        output_path = DATA_PROCESSED_DIR / f"demo_{match_id}.parquet"
    else:
        output_path = Path(output_path)
    
    df = parse_demo(dem_path, match_id, tick_interval)
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Saved: {output_path}")
    logger.info(f"  Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Dota 2 Demo Parser')
    parser.add_argument('--file', '-f', required=True, help='Path to .dem file')
    parser.add_argument('--tick-interval', '-t', type=int, default=2, help='Tick interval')
    parser.add_argument('--output', '-o', help='Output file')
    
    args = parser.parse_args()
    
    save_demo(args.file, args.output, args.tick_interval)
