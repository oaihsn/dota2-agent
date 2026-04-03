# -*- coding: utf-8 -*-
"""
Dota 2 Demo Parser - Python версия
Парсит .dem файлы без внешних зависимостей
"""
import struct
import json
from pathlib import Path
from dataclasses import dataclass
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"

DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class GameEvent:
    """Событие в игре."""
    tick: int
    event_type: str
    player_slot: int
    data: dict


class DemoParser:
    """Парсер демо-файлов Dota 2."""
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.match_id = int(filepath.stem) if filepath.stem.isdigit() else 0
        self.events = []
        
    def parse(self) -> dict:
        """Парсит демо."""
        print(f"Parsing: {self.filepath}")
        
        with open(self.filepath, 'rb') as f:
            # Читаем заголовок
            magic = f.read(8)
            
            if magic == b'HL2DEMO\x00':
                return self._parse_hl2(f)
            elif magic == b'PBDEMS2\x00':
                return self._parse_pb(f)
            else:
                print(f"Unknown format: {magic}")
                return {}
    
    def _parse_hl2(self, f) -> dict:
        """Парсит HL2DEMO формат."""
        header = {
            'format': 'HL2DEMO',
            'demo_protocol': struct.unpack('<I', f.read(4))[0],
            'network_protocol': struct.unpack('<I', f.read(4))[0],
            'server_name': f.read(260).split(b'\x00')[0].decode('utf-8', errors='ignore'),
            'client_name': f.read(260).split(b'\x00')[0].decode('utf-8', errors='ignore'),
            'map_name': f.read(260).split(b'\x00')[0].decode('utf-8', errors='ignore'),
            'game_dir': f.read(260).split(b'\x00')[0].decode('utf-8', errors='ignore'),
            'playback_time': struct.unpack('<f', f.read(4))[0],
            'ticks': struct.unpack('<I', f.read(4))[0],
            'frames': struct.unpack('<I', f.read(4))[0],
        }
        
        print(f"  Format: HL2DEMO")
        print(f"  Map: {header['map_name']}")
        print(f"  Ticks: {header['ticks']}")
        
        # Парсим сообщения
        self._parse_messages(f)
        
        return {'match_id': self.match_id, 'header': header, 'events': self.events}
    
    def _parse_pb(self, f) -> dict:
        """Парсит PBDEMS2 формат (protobuf)."""
        # Новый формат - пропускаем заголовок и читаем как protobuf
        header_size_data = f.read(4)
        if len(header_size_data) == 4:
            header_size = struct.unpack('<I', header_size_data)[0]
            f.read(header_size)  # Пропускаем protobuf header
        
        print(f"  Format: PBDEMS2 (protobuf)")
        
        # Парсим сообщения
        self._parse_messages(f)
        
        return {
            'match_id': self.match_id, 
            'header': {'format': 'PBDEMS2'}, 
            'events': self.events
        }
    
    def _parse_messages(self, f):
        """Парсит сообщения демо."""
        tick = 0
        msg_count = 0
        
        while msg_count < 100000:  # Limit
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
            
            # Читаем данные
            msg_data = f.read(size)
            if len(msg_data) < size:
                break
            
            # Типы сообщений
            msg_types = {
                0: 'DEM_SIGNON',
                1: 'DEM_PACKET', 
                2: 'DEM_SYNCMWEBSOCKET',
                3: 'DEM_USERCMD',
                4: 'DEM_DATATABLES',
                5: 'DEM_STOP',
                6: 'DEM_STRINGTABLES',
                7: 'DEM_USERCMD'
            }
            
            event_type = msg_types.get(cmd, f'UNKNOWN_{cmd}')
            
            # Сохраняем каждый 100-й тик для примера
            if tick % 100 == 0:
                self.events.append(GameEvent(
                    tick=tick,
                    event_type=event_type,
                    player_slot=0,
                    data={'size': size, 'cmd': cmd}
                ))
            
            msg_count += 1
        
        print(f"  Parsed {msg_count} messages")
    
    def get_events_df(self) -> pd.DataFrame:
        """Возвращает DataFrame событий."""
        if not self.events:
            return pd.DataFrame()
        
        return pd.DataFrame([{
            'tick': e.tick,
            'event_type': e.event_type,
            'player_slot': e.player_slot,
            **e.data
        } for e in self.events])


def parse_demo(dem_path: str, output_path: str = None) -> pd.DataFrame:
    """Парсит демо и возвращает DataFrame."""
    parser = DemoParser(Path(dem_path))
    result = parser.parse()
    
    if not result:
        return pd.DataFrame()
    
    df = parser.get_events_df()
    
    if output_path and not df.empty:
        df.to_parquet(output_path, index=False)
        print(f"Saved: {output_path}")
    
    return df


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        dem_path = sys.argv[1]
    else:
        dem_files = list(DATA_RAW_DIR.glob("*.dem"))
        if dem_files:
            dem_path = str(dem_files[0])
        else:
            print("No .dem files found")
            sys.exit(1)
    
    print(f"Parsing: {dem_path}")
    df = parse_demo(dem_path)
    
    if not df.empty:
        print(f"\nEvents: {len(df)}")
        print(df.head())
