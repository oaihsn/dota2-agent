# -*- coding: utf-8 -*-
"""
Скрипт для скачивания реплеев Dota 2 через Stratz API.
Фильтрует матчи по MMR (minimum 4000).
"""
import sys
import io
import time
import json
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

STRATZ_API = "https://api.stratz.com/graphql"
OUTPUT_DIR = Path("data/raw")
LINKS_FILE = Path("data/raw_links.txt")
TARGET_MATCHES = 50
MIN_MMR = 4000  # Минимальный MMR

# Токен - получите на https://stratz.com/api
BEARER_TOKEN = "YOUR_TOKEN_HERE"

# GraphQL запрос с фильтром по averageBracket
QUERY = """
query {
  player(steamAccountId: 1078802981) {
    matches(request: {take: 200, averageBracket: [8, 9, 10, 11, 12, 13, 14, 15]}) {
      id
      gameMode
      startDateTime
      durationSeconds
      averageBracket
    }
  }
}
"""

MODE_NAMES = {
    "ALL_PICK_RANKED": "All Pick Ranked",
    "ALL_PICK": "All Pick",
    "CAPTAINS_MODE": "Captains Mode",
    "TURBO": "Turbo",
    "ALL_RANDOM": "All Random",
    "SINGLE_DRAFT": "Single Draft",
    "CAPTAINS_DRAFT": "Captains Draft",
    "ABILITY_DRAFT": "Ability Draft",
    "ALL_RANDOM_DRAFT": "All Random Draft",
    "MUTATION": "Mutation"
}

BRACKET_NAMES = {
    1: "Herald",
    2: "Guardian",
    3: "Crusader",
    4: "Archon",
    5: "Legend",
    6: "Ancient",
    7: "Divine",
    8: "Immortal 1-100",
    9: "Immortal 101-500",
    10: "Immortal 501-1000",
    11: "Immortal 1001-2500",
    12: "Immortal 2501-5000",
    13: "Immortal 5001-7500",
    14: "Immortal 7501-10000",
    15: "Immortal 10000+"
}

def get_bracket_name(bracket):
    if bracket is None:
        return "Unknown"
    return BRACKET_NAMES.get(bracket, f"Bracket {bracket}")

def get_mode_name(mode):
    if isinstance(mode, str):
        return MODE_NAMES.get(mode, mode)
    return str(mode)

def fetch_with_selenium():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    import chromedriver_autoinstaller

    print("=" * 60)
    print("ПОИСК РЕЙТИНГОВЫХ МАТЧЕЙ (MMR > 4000)")
    print("=" * 60)

    try:
        chromedriver_autoinstaller.install()
    except:
        pass

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    driver = None
    all_valid_matches = []

    try:
        print("\n[1/3] Запуск браузера Chrome...")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("[2/3] Выполнение запроса к API...")
        
        script = f"""
        return fetch('{STRATZ_API}', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {BEARER_TOKEN}'
            }},
            body: JSON.stringify({{ query: `{QUERY}` }})
        }})
        .then(response => response.json())
        .then(data => JSON.stringify(data))
        .catch(error => JSON.stringify({{ error: error.message }}));
        """

        driver.get("about:blank")
        time.sleep(2)

        result = driver.execute_script(script)
        
        if not result:
            print("[ERROR] Пустой ответ")
            return []
        
        data = json.loads(result)
        
        if "errors" in data:
            print(f"[ERROR] {data['errors']}")
            return []
        
        if "data" not in data:
            print("[ERROR] Нет данных")
            return []
        
        matches = []
        if data["data"] and data["data"].get("player"):
            matches = data["data"]["player"].get("matches") or []
        
        print(f"[OK] Получено матчей: {len(matches)}")
        
        if not matches:
            print("[INFO] Матчей не найдено")
            return []
        
        # Фильтруем по bracket (MMR)
        for match in matches:
            bracket = match.get("averageBracket")
            
            # averageBracket 8+ = Immortal (примерно 4000+ MMR)
            if bracket is not None and bracket >= 8:
                all_valid_matches.append({
                    "id": match.get("id"),
                    "gameMode": match.get("gameMode"),
                    "startDateTime": match.get("startDateTime"),
                    "durationSeconds": match.get("durationSeconds"),
                    "averageBracket": bracket
                })

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return []
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 60)
    print(f"Найдено высоких MMR матчей: {len(all_valid_matches)}")
    
    if all_valid_matches:
        brackets = {}
        for m in all_valid_matches:
            b = m.get("averageBracket", 0)
            brackets[b] = brackets.get(b, 0) + 1
        print("Bracket распределение:")
        for b in sorted(brackets.keys()):
            print(f"  {get_bracket_name(b)}: {brackets[b]}")
    
    return all_valid_matches


def save_links(matches, filepath):
    print(f"\n[3/3] Сохранение в {filepath}...")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Dota 2 Matches - High MMR (4000+)\n")
        f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total: {len(matches)}\n")
        f.write(f"# Min MMR: ~4000 (Bracket 8+)\n")
        f.write("=" * 60 + "\n\n")
        
        for i, match in enumerate(matches, 1):
            match_id = match.get("id", "N/A")
            start_time = match.get("startDateTime", 0)
            duration = match.get("durationSeconds", 0)
            game_mode = match.get("gameMode", "")
            bracket = match.get("averageBracket", 0)
            
            dt_str = "N/A"
            if start_time > 0:
                dt = datetime.fromtimestamp(start_time)
                dt_str = dt.strftime('%Y-%m-%d %H:%M')
            
            mode_name = get_mode_name(game_mode)
            bracket_name = get_bracket_name(bracket)
            
            f.write(f"{i}. Match ID: {match_id}\n")
            f.write(f"   Date: {dt_str}\n")
            f.write(f"   Duration: {duration}s ({duration//60}m)\n")
            f.write(f"   Mode: {mode_name}\n")
            f.write(f"   Bracket: {bracket_name} (~{bracket * 500}+ MMR)\n")
            f.write(f"   URL: https://stratz.com/matches/{match_id}\n")
            f.write("\n")
    
    print(f"[OK] Saved {len(matches)} matches")


def main():
    print("\n" + "=" * 60)
    print("DOTA 2 MATCH SEARCH - HIGH MMR (4000+)")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    matches = fetch_with_selenium()
    
    if matches:
        save_links(matches, LINKS_FILE)
        print(f"\n[SUCCESS] Saved {len(matches)} matches!")
    else:
        print("\n[INFO] No matches found.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
