# -*- coding: utf-8 -*-
"""
Dota 2 Replay Parser с использованием JPype2 + Clarity (новый API).
Извлекает данные из .dem файлов с интервалом в 30 тиков.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import jpype
import jpype.imports

# Константы
PROJECT_DIR = Path(__file__).parent.parent.absolute()
DATA_RAW_DIR = PROJECT_DIR / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
LIB_DIR = PROJECT_DIR / "lib"

# Настройки парсинга
TICK_INTERVAL = 30  # Каждые 30 тиков (~1 сек)
MAX_TICKS = 54000   # Максимум тиков

DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


class Dota2ReplayParser:
    """Парсер Dota 2 реплеев через JPype2 + Clarity (новый API)."""
    
    def __init__(self):
        self.jpype = None
        self.jvm_started = False
        self.runner = None
    
    def start_jvm(self):
        """Запускает JVM и загружает все JAR файлы."""
        if self.jvm_started:
            return True
            
        try:
            import jpype
            self.jpype = jpype
            
            # Находим все необходимые JAR файлы
            jars = []
            
            # Список JAR файлов в правильном порядке
            jar_files = [
                "clarity-proto-5.4.jar",   # protobuf
                "fastutil.jar",            # зависимость
                "slf4j-api.jar",          # логирование
                "classindex.jar",         # annotation processor
                "snappy-java.jar",        # compression
                "clarity-with-processor.jar",  # JAR с нашим процессором
            ]
            
            for jar_name in jar_files:
                jar_path = LIB_DIR / jar_name
                if jar_path.exists() and jar_path.stat().st_size > 1000:
                    jars.append(str(jar_path))
                    logger.info(f"Found: {jar_name}")
                else:
                    logger.warning(f"Not found or too small: {jar_name}")
            
            if not jars:
                logger.error("No JAR files found!")
                return False
            
            # Путь к JDK
            jvm_path = None
            possible_jdk_paths = [
                "C:\\Program Files\\Java\\jdk-17\\bin\\server\\jvm.dll",
                "C:\\Program Files\\Java\\jdk-21\\bin\\server\\jvm.dll",
                "C:\\Program Files\\Java\\jdk-11\\bin\\server\\jvm.dll",
            ]
            
            for path in possible_jdk_paths:
                if os.path.exists(path):
                    jvm_path = path
                    break
            
            # Запускаем JVM
            logger.info(f"Starting JVM with {len(jars)} JAR files...")
            
            if jvm_path and os.path.exists(jvm_path):
                jpype.startJVM(jvm_path, "-ea", convertStrings=True, classpath=jars)
            else:
                jpype.startJVM("-ea", convertStrings=True, classpath=jars)
            
            self.jvm_started = True
            logger.info("JVM started successfully!")
            return True
            
        except ImportError:
            logger.error("JPype2 not installed! Run: pip install jpype1")
            return False
        except Exception as e:
            logger.error(f"Failed to start JVM: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def parse_demo(self, demo_path: Path, match_id: int) -> Optional[Dict]:
        """Парсит .dem файл и возвращает данные."""
        if not self.start_jvm():
            return None
        
        try:
            # Импортируем Java классы
            from java.io import IOException
            from skadistats.clarity.source import MappedFileSource
            from skadistats.clarity.processor.runner import SimpleRunner
            from skadistats.clarity.processor.entities import Entities
            from skadistats.clarity.model import Entity
            
            logger.info(f"Parsing: {demo_path.name}")
            
            # Создаём source и runner
            source = MappedFileSource(str(demo_path))
            runner = SimpleRunner(source)
            
            # Данные для сбора
            tick_data = []
            entities_cache = {}
            
            # Получаем процессор Entities через Context
            # runner.runWith() принимает процессоры, но мы используем альтернативный подход
            
            # Запускаем парсинг вручную
            # SimpleRunner.runWith() принимает массив процессоров
            # Мы можем создать простой processor
            
            # Создаём простой класс-процессор для обработки тиков
            class TickProcessor:
                def __init__(self, tick_interval=30):
                    self.tick_interval = tick_interval
                    self.last_tick = -1
                    self.tick_data = []
                    self.entities = None
                
                def setEntities(self, entities):
                    self.entities = entities
                
                def onTickEnd(self, synthetic):
                    """Вызывается в конце каждого тика"""
                    # Получаем текущий тик из runner через reflection
                    # Это сложно без доступа к runner
                    return True
                
                def onEntityCreated(self, entity):
                    """Вызывается при создании entity"""
                    return True
                
                def onEntityUpdated(self, entity):
                    """Вызывается при обновлении entity"""
                    return True
            
            # Создаём processor
            tick_processor = TickProcessor(TICK_INTERVAL)
            
            # Запускаем с processor
            # runner.runWith() требует процессоры как varargs
            # Но мы не можем передать Python объект напрямую
            
            # Альтернативный подход: запустить без процессоров и получить runner
            # Затем вручную итерировать
            logger.info("Runner created, checking for entities...")
            
            # Создаём Java процессор
            from skadistats.clarity.processor import Dota2TickProcessor
            processor = Dota2TickProcessor()
            
            # Запускаем парсинг с процессором
            try:
                runner.runWith(processor)
                logger.info("Runner runWith(processor) completed")
                
                # Получаем данные героев
                heroes_list = processor.getHeroes()
                logger.info(f"Found {len(heroes_list)} heroes via Java processor")
                
                for h in heroes_list:
                    logger.info(f"  - {h}")
                
                # Получаем собранные данные по тикам
                tick_data = processor.getTickData()
                logger.info(f"Tick data collected: {len(tick_data)} ticks")
                
                # Выводим пример данных
                for tick, heroes in list(tick_data.items())[:3]:
                    logger.info(f"Tick {tick}: {len(heroes)} heroes")
                    for h in heroes[:2]:
                        logger.info(f"  - {h}")
                    
            except Exception as e:
                logger.warning(f"runWith(processor) error: {e}")
                # Пробуем запустить без процессора
                try:
                    runner.runWith()
                    logger.info("Runner runWith() completed (fallback)")
                except Exception as e2:
                    logger.warning(f"runWith() fallback error: {e2}")
            
            # Теперь runner инициализирован, можем получить Context
            context = runner.getContext()
            logger.info(f"Runner initialized, tick: {runner.getTick()}")
            
            # Пробуем получить Entities через Python
            entities = None
            try:
                # После runWith можно получить контекст и процессоры
                entities = context.getProcessor(Entities)
                logger.info(f"Entities processor from context: {entities}")
                
                if entities:
                    # Получаем всех героев через Python
                    hero_iter = entities.getAllByDtName("CDOTA_BaseHero")
                    heroes = []
                    while hero_iter.hasNext():
                        entity = hero_iter.next()
                        heroes.append({
                            "index": entity.getIndex(),
                            "handle": entity.getHandle(),
                            "class": str(entity.getDtClass().getDtName()) if entity.getDtClass() else "unknown"
                        })
                    logger.info(f"Found {len(heroes)} heroes via Python+Context")
                    for h in heroes[:5]:
                        logger.info(f"  - {h}")
            except Exception as e:
                logger.warning(f"Error getting entities via Python: {e}")
            
            if entities:
                # Получаем все entities
                try:
                    all_entities = list(entities.getAll())
                    logger.info(f"Total entities: {len(all_entities)}")
                    
                    # Ищем героев
                    heroes = []
                    for entity in all_entities:
                        try:
                            dt_class = entity.getDtClass()
                            if dt_class:
                                classname = dt_class.getName()
                                if classname and "CDOTA_BaseHero" in classname:
                                    heroes.append({
                                        "classname": classname,
                                        "index": entity.getIndex()
                                    })
                        except:
                            continue
                    
                    logger.info(f"Found {len(heroes)} hero entities")
                    for h in heroes[:5]:
                        logger.info(f"  - {h}")
                except Exception as e:
                    logger.warning(f"Error getting all entities: {e}")
            
            # Создаём тики
            last_tick = runner.getTick()
            last_source_tick = source.getLastTick()
            logger.info(f"Last tick from runner: {last_tick}")
            logger.info(f"Last tick from source: {last_source_tick}")
            
            # Собираем данные по тикам
            # Проблема: в JPype сложно использовать event-driven подход
            # Поэтому мы сделаем простой обход
            
            return {
                "match_id": match_id,
                "total_ticks": last_source_tick if last_source_tick > 0 else last_tick,
                "tick_interval": TICK_INTERVAL,
                "entities_found": len(heroes) if 'heroes' in dir() else 0,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Parse error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def stop_jvm(self):
        """Останавливает JVM."""
        if self.jvm_started:
            try:
                jpype.shutdownJVM()
            except:
                pass
            self.jvm_started = False


def parse_replay(
    demo_path: str,
    match_id: int = None,
    output_format: str = "json",
    tick_interval: int = 30
) -> Optional[Path]:
    """Парсит .dem файл и сохраняет результат."""
    global TICK_INTERVAL
    TICK_INTERVAL = tick_interval
    
    demo_file = Path(demo_path)
    if not demo_file.exists():
        logger.error(f"File not found: {demo_file}")
        return None
    
    # ID матча из имени файла
    if match_id is None:
        try:
            match_id = int(demo_file.stem)
        except ValueError:
            match_id = hash(demo_file.name) % 10000000000
    
    logger.info("=" * 60)
    logger.info("DOTA 2 REPLAY PARSER")
    logger.info(f"Match ID: {match_id}")
    logger.info(f"File: {demo_file.name}")
    logger.info(f"Tick interval: {tick_interval}")
    logger.info("=" * 60)
    
    # Парсим
    parser = Dota2ReplayParser()
    result = parser.parse_demo(demo_file, match_id)
    parser.stop_jvm()
    
    if result is None:
        logger.error("Parsing failed!")
        return None
    
    # Сохраняем
    if output_format == "json":
        output_file = DATA_PROCESSED_DIR / f"match_{match_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    else:
        output_file = DATA_PROCESSED_DIR / f"match_{match_id}.csv"
    
    logger.info(f"\nSaved to: {output_file}")
    return output_file


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(description='Dota 2 Replay Parser')
    parser.add_argument('--file', '-f', help='Path to .dem file')
    parser.add_argument('--match-id', '-m', type=int, help='Match ID')
    parser.add_argument('--all', '-a', action='store_true', help='Process all files in raw/')
    parser.add_argument('--tick-interval', '-t', type=int, default=30, help='Tick interval')
    parser.add_argument('--output', '-o', choices=['json', 'csv'], default='json')
    
    args = parser.parse_args()
    
    if args.all:
        if not DATA_RAW_DIR.exists():
            logger.error(f"Raw directory not found: {DATA_RAW_DIR}")
            return
        
        demo_files = list(DATA_RAW_DIR.glob("*.dem"))
        logger.info(f"Found {len(demo_files)} .dem files")
        
        for demo_file in demo_files:
            try:
                parse_replay(str(demo_file), tick_interval=args.tick_interval, output_format=args.output)
            except Exception as e:
                logger.error(f"Error: {e}")
    elif args.file:
        parse_replay(args.file, match_id=args.match_id, tick_interval=args.tick_interval, output_format=args.output)
    else:
        parser.print_help()
    
    logger.info("\nDone!")


if __name__ == "__main__":
    main()