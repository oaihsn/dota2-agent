# -*- coding: utf-8 -*-
"""
Clarity 2 Parser для Dota 2 реплеев (.dem файлы).

Использует Java Clarity library через subprocess.
"""
import os
import sys
import io
import json
import subprocess
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime

import pandas as pd

# Константы
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
LOGS_DIR = Path("logs")
INTERVAL_TICKS = 30

# Создаём директории
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Настройка логирования
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
    """Состояние игрока в определённый момент времени."""
    match_id: int
    tick: int
    player_slot: int
    steam_id: int
    hero_name: str
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
    last_action_target_x: float = 0.0
    last_action_target_y: float = 0.0


def ensure_java_project():
    """Проверяет/создаёт Java проект для Clarity."""
    clarity_dir = Path("clarity_parser")
    clarity_dir.mkdir(exist_ok=True)
    
    # build.gradle
    build_gradle = clarity_dir / "build.gradle"
    if not build_gradle.exists():
        build_gradle.write_text('''plugins {
    id 'application'
    id 'java'
}

repositories {
    mavenCentral()
}

dependencies {
    implementation 'com.skadistats:clarity:2.2.1'
}

application {
    mainClass = 'DemoParser'
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

run {
    workingDir = rootProject.projectDir
}
''', encoding='utf-8')
    
    # Java файл
    src_dir = clarity_dir / "src" / "main" / "java"
    src_dir.mkdir(parents=True, exist_ok=True)
    
    java_file = src_dir / "DemoParser.java"
    if not java_file.exists():
        java_file.write_text('''package clarity;

import com.skadistats.aspectj.runtime.reflect.FieldSignatureRef;
import com.skadistats.clarity.Clarity;
import com.skadistats.clarity.model.*;
import com.skadistats.clarity.processor.*;
import com.skadistats.clarity.processor.entities.*;
import com.skadistats.clarity.processor.stringtables.*;
import com.skadistats.clarity.source.*;
import com.skadistats.clarity.walker.*;
import com.skadistats.clarity.model.engine.*;
import org.slf4j.*;
import java.io.*;
import java.util.*;

public class DemoParser {
    private static final Logger log = LoggerFactory.getLogger(DemoParser.class);
    private static final int INTERVAL_TICKS = 30;
    
    private static List<String> outputLines = new ArrayList<>();
    private static int tickCount = 0;
    
    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("Usage: java DemoParser <demo_file>");
            System.exit(1);
        }
        
        String demoFile = args[0];
        log.info("Parsing: {}", demoFile);
        
        try {
            Clarity clarity = new Clarity(demoFile);
            clarity.run(new Processor[]{
                new Runner() {
                    public void run() {
                        processTick(getTick());
                    }
                }
            });
        } catch (Exception e) {
            log.error("Error parsing demo", e);
            System.err.println("ERROR:" + e.getMessage());
        }
    }
    
    private static void processTick(int tick) {
        if (tick % INTERVAL_TICKS != 0) return;
        tickCount++;
        
        for (int i = 0; i < 10; i++) {
            Entity e = getWorld().getEntityByIndex(0xFFFF - i);
            if (e == null) continue;
            
            // Проверяем, это ли игрок
            String name = e.getProperty("m_iName");
            if (name != null && name.contains("m_SrcPlayerInfo")) {
                printPlayerData(e, tick);
            }
        }
    }
    
    private static void printPlayerData(Entity e, int tick) {
        try {
            Integer playerSlot = e.getProperty("m_iPlayerSlot");
            Long steamId = e.getProperty("m_steamID");
            String name = e.getProperty("m_iszPlayerName");
            
            String line = String.format("PLAYER|%d|%d|%d|%s",
                tick, 
                playerSlot != null ? playerSlot : 0,
                steamId != null ? steamId : 0,
                name != null ? name.replace("|", "-") : "unknown"
            );
            outputLines.add(line);
            
        } catch (Exception ex) {
            // Игнорируем ошибки
        }
    }
    
    public static List<String> getOutputLines() {
        return outputLines;
    }
}
''', encoding='utf-8')
        
        logger.info("Java проект создан в папке clarity_parser")
        logger.info("Соберите проект: cd clarity_parser && gradle build")
    
    return clarity_dir


def build_clarity():
    """Собирает Java проект через Gradle."""
    clarity_dir = Path("clarity_parser")
    
    # Скачиваем Gradle wrapper если нужно
    gradlew = clarity_dir / "gradlew.bat"
    if not gradlew.exists():
        logger.info("Скачивание Gradle...")
        try:
            result = subprocess.run(
                ["gradle", "wrapper"],
                cwd=str(clarity_dir),
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                logger.error("Ошибка создания Gradle wrapper: {}", result.stderr)
                return False
        except FileNotFoundError:
            logger.warning("Gradle не найден. Установите Gradle или используйте Java 17+")
            return False
    
    # Собираем
    logger.info("Сборка Java проекта...")
    try:
        result = subprocess.run(
            ["./gradlew.bat", "build", "--no-daemon"],
            cwd=str(clarity_dir),
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            logger.info("Сборка успешна")
            return True
        else:
            logger.error("Ошибка сборки: {}", result.stderr)
            return False
    except Exception as e:
        logger.error("Ошибка: {}", e)
        return False


def parse_demo_java(dem_path: Path, match_id: int) -> List[PlayerState]:
    """Парсит .dem файл через Java."""
    clarity_dir = Path("clarity_parser")
    jar_file = clarity_dir / "build" / "libs" / "clarity_parser-1.0.jar"
    
    if not jar_file.exists():
        logger.error("JAR не найден. Сначала соберите проект.")
        return []
    
    states = []
    
    try:
        logger.info(f"Парсинг через Java: {dem_path}")
        
        result = subprocess.run(
            ["java", "-jar", str(jar_file), str(dem_path)],
            cwd=str(clarity_dir),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        output = result.stdout + result.stderr
        
        for line in output.split('\n'):
            if (line.startswith("PLAYER|")):
                parts = line.split('\\|')
                if len(parts) >= 5:
                    state = PlayerState(
                        match_id=match_id,
                        tick=int(parts[1]),
                        player_slot=int(parts[2]),
                        steam_id=int(parts[3]),
                        hero_name=parts[4]
                    )
                    states.append(state)
        
        logger.info(f"  Извлечено {len(states)} записей")
        
    except subprocess.TimeoutExpired:
        logger.error(f"Таймаут парсинга: {dem_path}")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    return states


def process_raw_folder():
    """Обрабатывает все .dem файлы."""
    logger.info("=" * 60)
    logger.info("CLARITY PARSER - Обработка реплеев")
    logger.info("=" * 60)
    
    # Проверяем Java проект
    clarity_dir = ensure_java_project()
    
    dem_files = list(DATA_RAW_DIR.glob("*.dem"))
    
    if not dem_files:
        logger.warning(f"Файлы .dem не найдены в {DATA_RAW_DIR}")
        logger.info("Сначала запустите downloader для получения реплеев")
        return
    
    logger.info(f"Найдено {len(dem_files)} .dem файлов")
    
    # Проверяем JAR
    jar_file = clarity_dir / "build" / "libs" / "clarity_parser-1.0.jar"
    if not jar_file.exists():
        logger.info("JAR не собран. Собираем...")
        if not build_clarity():
            logger.error("Не удалось собрать Java проект")
            return
    
    all_states = []
    errors = []
    
    for dem_file in dem_files:
        try:
            match_id = int(dem_file.stem.replace("match_", ""))
        except ValueError:
            match_id = hash(dem_file.name) % 10000000000
        
        states = parse_demo_java(dem_file, match_id)
        
        if states:
            all_states.extend(states)
        else:
            errors.append(dem_file.name)
    
    if not all_states:
        logger.warning("Данные не извлечены. Возможно, .dem файлы не найдены.")
        return
    
    # Создаём DataFrame
    logger.info(f"Создание DataFrame из {len(all_states)} записей...")
    
    df = pd.DataFrame([asdict(s) for s in all_states])
    
    # Сохраняем в parquet
    output_file = DATA_PROCESSED_DIR / f"replays_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    df.to_parquet(output_file, index=False)
    
    logger.info(f"Сохранено: {output_file}")
    logger.info(f"Размер: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    if errors:
        logger.warning(f"Пропущено: {len(errors)}")
        for err in errors:
            logger.warning(f"  - {err}")
    
    logger.info("\nСтатистика:")
    logger.info(f"  Матчей: {df['match_id'].nunique()}")
    logger.info(f"  Игроков: {df['steam_id'].nunique()}")


def main():
    """Главная функция."""
    logger.info("Clarity Parser для Dota 2 реплеев")
    logger.info(f"Реплеи: {DATA_RAW_DIR}")
    logger.info(f"Результат: {DATA_PROCESSED_DIR}")
    
    process_raw_folder()
    
    logger.info("Готово!")


if __name__ == "__main__":
    main()
