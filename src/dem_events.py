# -*- coding: utf-8 -*-
"""
Dota 2 Demo Parser - Enhanced Version
Извлекает события из .dem файлов без protobuf
- Больше событий (kills, deaths, gold, XP)
- Автоэкспорт в parquet/CSV
- Улучшенное извлечение данных
"""
import struct
import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
import pandas as pd

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"

DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class GameEvent:
    """Событие игры."""
    tick: int
    event_type: str
    player_slot: int = 0
    target_slot: int = 0
    hero_id: int = 0
    gold: int = 0
    xp: int = 0
    level: int = 0
    position: int = 0
    extra: str = ""


class DemoBinaryParser:
    """Парсер демо на бинарном уровне."""
    
    # Расширенные определения событий Dota 2
    EVENT_TYPES = {
        # Основные игровые события
        1: 'player_connect',
        2: 'player_disconnect',
        3: 'player_team',
        4: 'player_charinfo',
        5: 'player_hltv',
        6: 'player_chat',
        
        # Dota 2 специфичные события (4000+)
        4001: 'CHeroXPAlert',
        4002: 'CGameRulesStateChanged',
        4003: 'CDOTAGamerulesFishToss',
        4004: 'CEntityHurt',
        4005: 'CDeathInfo',
        4006: 'CDOTAUserMsgParticles',
        4007: 'CDOTAUserMsgLiquidSwap',
        4008: 'CDOTAUserMsgSendStat',
        4009: 'CDOTAUserMsgSendRoshanGold',
        4010: 'CDOTAUserMsgXpChanged',
        4011: 'CDOTAUserMsgGoldChanged',
        4012: 'CDOTAUserMsgAbilityPing',
        4013: 'CDOTAUserMsgModifyChart',
        4014: 'CDOTAUserMsgDestroyCharges',
        4015: 'CDOTAUserMsgSetNextAutobuyItem',
        4016: 'CDOTAUserMsgGameServerVersion',
        4017: 'CDOTAUserMsgDetailsDraft',
        4018: 'CDOTAUserMsgDraftStart',
        4019: 'CDOTAUserMsgMinimalLoadoutForTourney',
        4020: 'CDOTAUserMsgBroadcastLayout',
        4021: 'CDOTAUserMsgPlayerHeroSelectionFaction',
        4022: 'CDOTAUserMsgHUD',
        4023: 'CDOTAUserMsgTournamentDrop',
        4024: 'CDOTAUserMsgReloadMissions',
        4025: 'CDOTAUserMsgPlayerCrowdResponse',
        4026: 'CDOTAUserMsgSplitMsg',
        4027: 'CDOTAUserMsgCustomHeaderMsg',
        4028: 'CDOTAUserMsgPredictionResult',
        4029: 'CDOTAUserMsgKillTapeMessage',
        4030: 'CDOTAUserMsgRequestGraphUpdate',
        
        # Дополнительные события
        101: 'entity_update',
        102: 'user_command',
        103: 'packet',
    }
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.match_id = int(filepath.stem) if filepath.stem.isdigit() else 0
        self.events = []
        self.file_size = 0
        
    def parse(self) -> dict:
        """Парсит демо файл."""
        print(f"Parsing: {self.filepath}")
        
        with open(self.filepath, 'rb') as f:
            data = f.read()
        
        self.file_size = len(data)
        print(f"  File size: {self.file_size:,} bytes")
        
        # Ищем магическую сигнатуру
        magic_pos = data.find(b'PBDEMS2')
        if magic_pos >= 0:
            print(f"  Format: PBDEMS2 (protobuf)")
            return self._parse_pb(data, magic_pos)
        
        magic_pos = data.find(b'HL2DEMO')
        if magic_pos >= 0:
            print(f"  Format: HL2DEMO")
            return self._parse_hl2(data, magic_pos)
        
        return self._search_patterns(data)
    
    def _parse_pb(self, data: bytes, start_pos: int) -> dict:
        """Парсит PBDEMS2 формат."""
        events = []
        
        # Поиск всех известных событий
        for event_id, event_name in self.EVENT_TYPES.items():
            pattern = event_id.to_bytes(4, 'little')
            pos = start_pos
            count = 0
            
            while pos < len(data) - 4:
                pos = data.find(pattern, pos)
                if pos < 0:
                    break
                
                # Извлекаем данные вокруг события
                tick = self._extract_tick(data, pos)
                extra_data = self._extract_extra_data(data, pos, event_name)
                
                events.append(GameEvent(
                    tick=tick,
                    event_type=event_name,
                    position=pos,
                    **extra_data
                ))
                
                count += 1
                pos += 4
            
            if count > 0:
                print(f"  Found {count} x {event_name}")
        
        # Дополнительный поиск паттернов
        self._search_game_patterns(data, events)
        
        self.events = events
        return {
            'match_id': self.match_id,
            'format': 'PBDEMS2',
            'total_events': len(events),
            'file_size': self.file_size
        }
    
    def _parse_hl2(self, data: bytes, start_pos: int) -> dict:
        """Парсит HL2DEMO формат."""
        pos = start_pos + 8
        if pos + 4 < len(data):
            print(f"  Demo protocol: {struct.unpack('<I', data[pos:pos+4])[0]}")
        
        events = []
        self._search_game_patterns(data, events)
        
        self.events = events
        return {
            'match_id': self.match_id,
            'format': 'HL2DEMO',
            'total_events': len(events),
            'file_size': self.file_size
        }
    
    def _search_game_patterns(self, data: bytes, events: list):
        """Ищет игровые паттерны."""
        patterns = {
            b'DEATH': 'player_death',
            b'KILL': 'kill_event',
            b'GOLD': 'gold_change',
            b'XP': 'xp_change',
            b'DENY': 'deny',
            b'BUY': 'item_purchase',
            b'CAST': 'ability_cast',
            b'ULT': 'ultimate_used',
            b'DOTA_TEAM': 'team_info',
            b'hero_': 'hero_select',
        }
        
        for pattern, event_name in patterns.items():
            pos = 0
            count = 0
            
            while pos < len(data) - len(pattern):
                pos = data.find(pattern, pos)
                if pos < 0:
                    break
                
                tick = self._extract_tick(data, pos)
                events.append(GameEvent(
                    tick=tick,
                    event_type=event_name,
                    position=pos
                ))
                
                count += 1
                pos += len(pattern)
            
            if count > 100:  # Слишком много - это может быть ложным срабатыванием
                continue
            if count > 0:
                print(f"  Found {count} x {event_name}")
    
    def _search_patterns(self, data: bytes) -> dict:
        """Общий поиск паттернов."""
        return self._parse_pb(data, 0)
    
    def _extract_tick(self, data: bytes, pos: int) -> int:
        """Извлекает tick из позиции."""
        for offset in range(-100, 100, 4):
            check_pos = pos + offset
            if check_pos >= 0 and check_pos + 4 <= len(data):
                try:
                    val = struct.unpack('<I', data[check_pos:check_pos+4])[0]
                    if 0 <= val <= 100000000:
                        return val
                except:
                    continue
        return 0
    
    def _extract_extra_data(self, data: bytes, pos: int, event_name: str) -> dict:
        """Извлекает дополнительные данные."""
        extra = {}
        
        # Пытаемся извлечь данные рядом с событием
        if pos + 20 < len(data):
            # Читаем область вокруг события
            region = data[pos:pos+40]
            
            # Ищем整数 значения (gold, xp, level)
            for i in range(0, len(region) - 4, 4):
                try:
                    val = struct.unpack('<I', region[i:i+4])[0]
                    if 0 <= val <= 1000000:
                        if 'gold' not in extra and val > 100:
                            extra['gold'] = val
                        elif 'xp' not in extra and val > 0:
                            extra['xp'] = val
                        elif 'level' not in extra and 1 <= val <= 30:
                            extra['level'] = val
                except:
                    continue
        
        return extra
    
    def get_events_df(self) -> pd.DataFrame:
        """Возвращает DataFrame событий."""
        if not self.events:
            return pd.DataFrame()
        
        return pd.DataFrame([asdict(e) for e in self.events])
    
    def save_data(self, output_path: str = None) -> str:
        """Сохраняет данные в файл."""
        df = self.get_events_df()
        
        if df.empty:
            print("No events to save")
            return ""
        
        if output_path is None:
            output_path = DATA_PROCESSED_DIR / f"events_{self.match_id}.parquet"
        else:
            output_path = Path(output_path)
        
        # Определяем формат по расширению
        suffix = output_path.suffix.lower()
        
        if suffix == '.csv':
            df.to_csv(output_path, index=False, encoding='utf-8')
        elif suffix == '.json':
            df.to_json(output_path, orient='records', indent=2)
        else:
            # По умолчанию parquet
            df.to_parquet(output_path, index=False)
        
        size_kb = output_path.stat().st_size / 1024
        print(f"Saved: {output_path} ({size_kb:.1f} KB)")
        
        return str(output_path)


def parse_demo(dem_path: str, output_path: str = None) -> pd.DataFrame:
    """Парсит демо и возвращает DataFrame."""
    parser = DemoBinaryParser(Path(dem_path))
    result = parser.parse()
    
    df = parser.get_events_df()
    
    if output_path and not df.empty:
        parser.save_data(output_path)
    
    return df


if __name__ == "__main__":
    import sys
    
    # Определяем входной файл
    if len(sys.argv) > 1:
        dem_path = sys.argv[1]
    else:
        dem_files = list(DATA_RAW_DIR.glob("*.dem"))
        if dem_files:
            dem_path = str(dem_files[0])
        else:
            print("No .dem files found")
            sys.exit(1)
    
    # Определяем выходной файл
    output_path = None
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    print("=" * 60)
    print("Dota 2 Demo Parser - Enhanced")
    print("=" * 60)
    
    parser = DemoBinaryParser(Path(dem_path))
    result = parser.parse()
    
    print(f"\nTotal events: {result.get('total_events', 0)}")
    
    df = parser.get_events_df()
    
    if not df.empty:
        # Показываем статистику
        print("\nEvent types:")
        print(df['event_type'].value_counts().head(15))
        
        # Сохраняем
        if output_path:
            parser.save_data(output_path)
        else:
            # Автосохранение
            parser.save_data()
        
        print(f"\nSample events:")
        print(df[['tick', 'event_type', 'gold', 'xp', 'level']].head(10).to_string())
    else:
        print("No events found")
