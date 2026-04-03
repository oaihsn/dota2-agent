# -*- coding: utf-8 -*-
"""
Python wrapper to run Java DemoParser directly via subprocess.
"""
import subprocess
import os
import json
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.absolute()
LIB_DIR = PROJECT_DIR / "lib"
OUT_DIR = PROJECT_DIR / "out"
DATA_RAW_DIR = PROJECT_DIR / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

# Find Java
JAVA_PATHS = [
    "C:\\Program Files\\Java\\jdk-17\\bin\\java.exe",
    "C:\\Program Files\\Java\\jdk-21\\bin\\java.exe",
    "C:\\Program Files\\Java\\jdk-11\\bin\\java.exe",
    "java",
]

def find_java():
    """Find Java executable."""
    for path in JAVA_PATHS:
        if os.path.exists(path):
            return path
    result = subprocess.run(["java", "-version"], capture_output=True, text=True)
    if result.returncode == 0:
        return "java"
    return None


def build_classpath():
    """Build classpath string."""
    paths = [str(OUT_DIR)]  # Start with out directory
    # Filter out bad JARs (size < 100 bytes)
    for jar in LIB_DIR.glob("*.jar"):
        if jar.stat().st_size > 100:
            paths.append(str(jar))
    return ";".join(paths)


def run_demo_parser():
    """Run Java DemoParser via subprocess."""
    java_cmd = find_java()
    if not java_cmd:
        print("Java not found!")
        return []
    
    classpath = build_classpath()
    
    # Demo file
    demo_files = list(DATA_RAW_DIR.glob("*.dem"))
    if not demo_files:
        print("No .dem files found!")
        return []
    
    demo_path = demo_files[0]
    
    print(f"Running Java DemoParser...")
    print(f"  Demo: {demo_path.name}")
    print(f"  Java: {java_cmd}")
    
    # Run Java
    cmd = [
        java_cmd,
        "-cp", classpath,
        "skadistats.clarity.DemoParser",
        str(demo_path)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(f"\n--- Java Output ---")
        print(result.stdout)
        if result.stderr:
            print(f"\n--- Java Errors ---")
            print(result.stderr)
        
        # Parse output
        return parse_java_output(result.stdout)
        
    except subprocess.TimeoutExpired:
        print("Java process timed out!")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def parse_java_output(output):
    """Parse hero data from Java output."""
    hero_data = []
    
    for line in output.split("\n"):
        if line.startswith("HERO:"):
            parts = line[5:].split(",")
            if len(parts) >= 6:
                try:
                    record = {
                        "tick": int(parts[0]),
                        "team": int(parts[1]),
                        "x": float(parts[2]),
                        "y": float(parts[3]),
                        "health": int(parts[4]),
                        "level": int(parts[5]),
                    }
                    hero_data.append(record)
                except:
                    pass
    
    return hero_data


def main():
    print("=" * 60)
    print("JAVA DEMO PARSER - Direct subprocess execution")
    print("=" * 60)
    
    # First compile Java
    print("\nCompiling Java...")
    java_src = PROJECT_DIR / "clarity_parser" / "src" / "main" / "java" / "skadistats" / "clarity" / "DemoParser.java"
    
    if java_src.exists():
        compile_cmd = [
            "javac",
            "-cp", build_classpath(),
            "-d", "out",
            str(java_src)
        ]
        result = subprocess.run(compile_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Compilation error: {result.stderr}")
            return
        print("Compiled OK")
    
    # Run parser
    hero_data = run_demo_parser()
    
    if hero_data:
        print(f"\nCollected {len(hero_data)} records")
        
        # Save to CSV
        df = pd.DataFrame(hero_data)
        output_file = DATA_PROCESSED_DIR / "training_data_real.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\nSaved to: {output_file}")
        print("\nSample:")
        print(df.head(20))
    else:
        print("\nNo data collected!")


if __name__ == "__main__":
    main()