# -*- coding: utf-8 -*-
"""
Dota 2 Demo (.dem) Parser
Прямой парсинг демо-файлов
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
class DemoEvent:
    """Событие из демо."""
    tick: int
    event_type: str
    data: dict


class DemoParser:
    """Парсер демо-файлов Dota 2."""
    
    # Demo commands
    DEM_SIGNON = 1
    DEM_PACKET = 2
    DEM_SYNCWEBSOCKET = 4
    DEM_USERCMD = 7
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.match_id = int(filepath.stem) if filepath.stem.isdigit() else 0
        self.events = []
        
    def parse(self) -> dict:
        """Парсит демо и возвращает данные."""
        print(f"Parsing: {self.filepath}")
        
        with open(self.filepath, 'rb') as f:
            # Читаем заголовок
            header = self._read_header(f)
            if not header:
                print("Invalid demo header")
                return {}
            
            print(f"  Header: {header}")
            
            # Парсим сообщения
            self._parse_messages(f)
        
        print(f"  Total events: {len(self.events)}")
        
        return {
            'match_id': self.match_id,
            'header': header,
            'events': self.events
        }
    
    def _read_header(self, f) -> dict:
        """Читает заголовок демо."""
        # HL2DEMO signature
        magic = f.read(8)
        
        if magic == b'HL2DEMO\x00':
            return self._read_hl2_header(f)
        elif magic == b'PBDEMS2\x00':
            return self._read_pb_header(f)
        else:
            print(f"Unknown magic: {magic}")
            return {}
    
    def _read_hl2_header(self, f) -> dict:
        """Читает HL2DEMO заголовок."""
        header = {}
        
        try:
            header['demo_protocol'] = struct.unpack('<I', f.read(4))[0]
            header['network_protocol'] = struct.unpack('<I', f.read(4))[0]
            header['server_name'] = f.read(260).split(b'\x00')[0].decode('utf-8', errors='ignore')
            header['client_name'] = f.read(260).split(b'\x00')[0].decode('utf-8', errors='ignore')
            header['map_name'] = f.read(260).split(b'\x00')[0].decode('utf-8', errors='ignore')
            header['game_dir'] = f.read(260).split(b'\x00')[0].decode('utf-8', errors='ignore')
            header['playback_time'] = struct.unpack('<f', f.read(4))[0]
            header['ticks'] = struct.unpack('<I', f.read(4))[0]
            header['frames'] = struct.unpack('<I', f.read(4))[0]
            header['singletons'] = struct.unpack('<I', f.read(4))[0]
            header['string_table_size'] = struct.unpack('<I', f.read(4))[0]
            
            print(f"  Map: {header.get('map_name')}")
            print(f"  Ticks: {header.get('ticks')}")
            print(f"  Playback time: {header.get('playback_time'):.1f}s")
            
            return header
        except Exception as e:
            print(f"Error reading header: {e}")
            return {}
    
    def _read_pb_header(self, f) -> dict:
        """Читает PBDEMS2 заголовок (новый формат)."""
        header = {}
        
        try:
            # Читаем остаток заголовка
            data = f.read(1024)
            
            # Новый формат использует protobuf
            # Пока просто возвращаем базовую информацию
            header['format'] = 'PBDEMS2'
            header['ticks'] = 0
            
            return header
        except Exception as e:
            print(f"Error reading PB header: {e}")
            return {}
    
    def _parse_messages(self, f):
        """Парсит сообщения демо."""
        tick = 0
        message_count = 0
        max_messages = 100000  # Limit for safety
        
        while message_count < max_messages:
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
            
            # Пропускаем данные сообщения
            msg_data = f.read(size)
            if len(msg_data) < size:
                break
            
            # Определяем тип сообщения
            event_type = self._get_event_type(cmd)
            
            # Сохраняем событие каждые 1000 тиков
            if tick % 1000 == 0:
                self.events.append(DemoEvent(
                    tick=tick,
                    event_type=event_type,
                    data={'size': size, 'cmd': cmd}
                ))
            
            message_count += 1
        
        print(f"  Parsed {message_count} messages")
    
    def _get_event_type(self, cmd: int) -> str:
        """Возвращает название типа сообщения."""
        types = {
            0: 'DEM_SIGNON',
            1: 'DEM_PACKET',
            2: 'DEM_SYNCMWEBSOCKET',
            3: 'DEM_USERCMD',
            4: 'DEM_DATATABLES',
            5: 'DEM_STOP',
            6: 'DEM_STRINGTABLES',
            7: 'DEM_USERCMD'
        }
        return types.get(cmd, f'UNKNOWN_{cmd}')


def parse_demo(dem_path: str) -> dict:
    """Парсит демо-файл."""
    parser = DemoParser(Path(dem_path))
    return parser.parse()


def save_demo_data(dem_path: str, output_path: str = None):
    """Парсит демо и сохраняет события."""
    data = parse_demo(dem_path)
    
    if not data:
        return None
    
    match_id = data['match_id']
    
    if output_path is None:
        output_path = DATA_PROCESSED_DIR / f"demo_events_{match_id}.json"
    else:
        output_path = Path(output_path)
    
    # Сохраняем события
    events_data = [
        {
            'tick': e.tick,
            'event_type': e.event_type,
            'data': e.data
        }
        for e in data['events']
    ]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'match_id': match_id,
            'header': data['header'],
            'events': events_data
        }, f, indent=2)
    
    print(f"Saved: {output_path}")
    return output_path


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        dem_path = sys.argv[1]
    else:
        # Тест на первом файле
        dem_files = list(DATA_RAW_DIR.glob("*.dem"))
        if dem_files:
            dem_path = str(dem_files[0])
        else:
            print("No .dem files found")
            sys.exit(1)
    
    print(f"Parsing: {dem_path}")
    save_demo_data(dem_path)
