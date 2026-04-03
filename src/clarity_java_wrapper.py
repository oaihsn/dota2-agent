# -*- coding: utf-8 -*-
"""
Python обёртка для запуска Java Clarity парсера.
Запускает DemoParser через Jython или компилирует и запускает через Java.
"""
import subprocess
import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import tempfile


PROJECT_DIR = Path(__file__).parent.parent.absolute()
CLARITY_DIR = PROJECT_DIR / "clarity_parser"
DATA_DIR = PROJECT_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"


def ensure_clarity_jar() -> Optional[Path]:
    """Проверяет и возвращает путь к JAR файлу Clarity."""
    # Проверяем различные JAR файлы
    jar_options = [
        PROJECT_DIR / "lib" / "clarity-protobuf-4.8.jar",
        PROJECT_DIR / "lib" / "clarity-2.7.0.jar",
        PROJECT_DIR / "lib" / "clarity-3.0.0.jar",
        PROJECT_DIR / "lib" / "clarity.jar",
    ]
    
    for jar_path in jar_options:
        if jar_path.exists() and jar_path.stat().st_size > 10000:
            print(f"Using JAR: {jar_path}")
            return jar_path
    
    return None


def ensure_java_compiled() -> Optional[Path]:
    """Проверяет, скомпилирован ли DemoParser."""
    classes_dir = CLARITY_DIR / "target" / "classes"
    
    # Проверяем, существует ли DemoParser.class
    demo_parser_class = classes_dir / "DemoParser.class"
    if demo_parser_class.exists():
        return classes_dir
    
    return None


def compile_java() -> bool:
    """Компилирует DemoParser.java через javac."""
    jar_path = ensure_clarity_jar()
    if not jar_path:
        print("Clarity JAR not found!")
        return False
    
    # Создаём директорию для классов
    classes_dir = CLARITY_DIR / "target" / "classes"
    classes_dir.mkdir(parents=True, exist_ok=True)
    
    # Компилируем
    source_file = CLARITY_DIR / "src" / "main" / "java" / "DemoParser.java"
    if not source_file.exists():
        print(f"Source file not found: {source_file}")
        return False
    
    # Формируем команду
    # Добавляем все JAR из lib в classpath
    lib_dir = CLARITY_DIR / "lib"
    classpath = [str(jar_path)]
    
    if lib_dir.exists():
        for lib_jar in lib_dir.glob("*.jar"):
            classpath.append(str(lib_jar))
    
    # Также ищем JAR в gradle lib
    gradle_lib = CLARITY_DIR / "gradle-8.5" / "lib"
    if gradle_lib.exists():
        for lib_jar in gradle_lib.glob("*.jar"):
            classpath.append(str(lib_jar))
    
    classpath_str = ";".join(classpath)
    
    cmd = [
        "javac",
        "-encoding", "UTF-8",
        "-cp", classpath_str,
        "-d", str(classes_dir),
        "-source", "17",
        "-target", "17",
        str(source_file)
    ]
    
    print(f"Compiling: {' '.join(cmd[:3])} ...")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"Compilation failed: {result.stderr}")
            return False
        
        print("Compilation successful!")
        return True
    except subprocess.TimeoutExpired:
        print("Compilation timeout!")
        return False
    except FileNotFoundError:
        print("javac not found!")
        return False


def run_java_parser(demo_file: Path, output_file: Optional[Path] = None) -> Optional[Path]:
    """Запускает Java парсер."""
    # Сначала компилируем
    if not ensure_java_compiled():
        if not compile_java():
            return None
    
    if output_file is None:
        output_file = DATA_PROCESSED_DIR / f"clarity_{demo_file.stem}.json"
    
    classes_dir = CLARITY_DIR / "target" / "classes"
    
    # Собираем classpath
    jar_path = ensure_clarity_jar()
    classpath = [str(classes_dir)]
    
    if jar_path:
        classpath.append(str(jar_path))
    
    lib_dir = CLARITY_DIR / "lib"
    if lib_dir.exists():
        for lib_jar in lib_dir.glob("*.jar"):
            classpath.append(str(lib_jar))
    
    gradle_lib = CLARITY_DIR / "gradle-8.5" / "lib"
    if gradle_lib.exists():
        for lib_jar in gradle_lib.glob("*.jar"):
            classpath.append(str(lib_jar))
    
    classpath_str = ";".join(classpath)
    
    cmd = [
        "java",
        "-cp", classpath_str,
        "DemoParser",
        str(demo_file.absolute()),
        str(output_file.absolute())
    ]
    
    print(f"Running: java DemoParser {demo_file.name} ...")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode != 0:
            print(f"Parser error: {result.stderr}")
            return None
        
        print(result.stdout)
        
        if output_file.exists():
            print(f"Output saved to: {output_file}")
            return output_file
        
        return None
        
    except subprocess.TimeoutExpired:
        print("Parser timeout!")
        return None


def load_json_output(output_file: Path) -> Optional[Dict]:
    """Загружает результаты парсинга."""
    if not output_file.exists():
        return None
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading output: {e}")
        return None


def process_replay_with_clarity(match_id: int) -> Optional[Path]:
    """Обрабатывает реплей через Clarity."""
    # Ищем файл реплея
    demo_file = DATA_RAW_DIR / f"{match_id}.dem"
    
    if not demo_file.exists():
        # Пробуем другие форматы
        for ext in ['.dem.bz2', '.dem.gz', '.zip']:
            alt_file = DATA_RAW_DIR / f"{match_id}{ext}"
            if alt_file.exists():
                demo_file = alt_file
                break
    
    if not demo_file.exists():
        print(f"Demo file not found: {demo_file}")
        return None
    
    print(f"Processing: {demo_file}")
    
    output_file = DATA_PROCESSED_DIR / f"clarity_{match_id}.json"
    
    return run_java_parser(demo_file, output_file)


def process_all_demos() -> List[Path]:
    """Обрабатывает все демо файлы из raw директории."""
    if not DATA_RAW_DIR.exists():
        print(f"Raw directory not found: {DATA_RAW_DIR}")
        return []
    
    demo_files = list(DATA_RAW_DIR.glob("*.dem"))
    
    if not demo_files:
        print(f"No demo files found in: {DATA_RAW_DIR}")
        return []
    
    print(f"Found {len(demo_files)} demo files")
    
    results = []
    for demo_file in demo_files:
        match_id = demo_file.stem
        try:
            match_id_int = int(match_id)
            output = process_replay_with_clarity(match_id_int)
            if output:
                results.append(output)
        except ValueError:
            print(f"Skipping non-numeric filename: {demo_file}")
    
    return results


def main():
    """Главная функция."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clarity Parser Wrapper')
    parser.add_argument('--match-id', '-m', type=int, help='Match ID to process')
    parser.add_argument('--list', '-l', action='store_true', help='List all demo files')
    parser.add_argument('--compile', '-c', action='store_true', help='Just compile Java code')
    
    args = parser.parse_args()
    
    if args.compile:
        compile_java()
        return
    
    if args.list:
        if DATA_RAW_DIR.exists():
            demos = list(DATA_RAW_DIR.glob("*.dem"))
            print(f"Demo files in {DATA_RAW_DIR}:")
            for d in demos:
                print(f"  {d.name}")
        return
    
    if args.match_id:
        process_replay_with_clarity(args.match_id)
    else:
        # Обрабатываем все
        process_all_demos()


if __name__ == "__main__":
    main()
