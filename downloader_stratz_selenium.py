# -*- coding: utf-8 -*-
"""
Скрипт для скачивания реплеев Dota 2 через Stratz API.
Собирает матчи без привязки к конкретному Steam ID.
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
MIN_IMP = 40  # averageImp >= 40 ~= 4000+ MMR

BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiNTUxNjZkNTAtOTY0MS00MmU1LWEyMjQtMjZlMDcyNWE1YTAwIiwiU3RlYW1JZCI6IjEwNzg4MDI5ODEiLCJBUElVc2VyIjoidHJ1ZSIsIm5iZiI6MTc3MTE2MDYwMiwiZXhwIjoxODAyNjk2NjAyLCJpYXQiOjE3NzExNjA2MDIsImlzcyI6Imh0dHBzOi8vYXBpLnN0cmF0ei5jb20ifQ.VPrAkCuJ4KlttFGGtae09_LoQk91GkR4vEaybt6X3iM"

# Запрос для конкретного игрока
QUERY = """
query {
  player(steamAccountId: 1078802981) {
    matches(request: {take: 100}) {
      id
      gameMode
      startDateTime
      durationSeconds
      averageImp
    }
  }
}
"""

MODE_NAMES = {
    "ALL_PICK_RANKED": "All Pick Ranked",
    "ALL_PICK": "All Pick",
    "CAPTAINS_MODE": "Captains Mode",
    "TURBO": "Turbo",
}

def get_mode_name(mode):
    if isinstance(mode, str):
        return MODE_NAMES.get(mode, mode)
    return str(mode)

def get_mmr_from_imp(imp):
    return 1000 + (imp * 75)

def fetch_with_selenium():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    import chromedriver_autoinstaller

    print("=" * 60)
    print("ПОИСК ПУБЛИЧНЫХ МАТЧЕЙ (MMR > 4000)")
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
        
        # Фильтруем по averageImp
        for match in matches:
            avg_imp = match.get("averageImp")
            if avg_imp is not None and avg_imp >= MIN_IMP:
                all_valid_matches.append({
                    "id": match.get("id"),
                    "gameMode": match.get("gameMode"),
                    "startDateTime": match.get("startDateTime"),
                    "durationSeconds": match.get("durationSeconds"),
                    "averageImp": avg_imp
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
        print("Режимы:")
        modes = {}
        for m in all_valid_matches:
            mode = m.get("gameMode", "Unknown")
            modes[mode] = modes.get(mode, 0) + 1
        for mode, count in modes.items():
            print(f"  {get_mode_name(mode)}: {count}")
    
    return all_valid_matches


def save_links(matches, filepath):
    print(f"\n[3/3] Сохранение в {filepath}...")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Dota 2 Matches - High MMR (Imp >= {MIN_IMP})\n")
        f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total: {len(matches)}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, match in enumerate(matches, 1):
            match_id = match.get("id", "N/A")
            start_time = match.get("startDateTime", 0)
            duration = match.get("durationSeconds", 0)
            game_mode = match.get("gameMode", "")
            avg_imp = match.get("averageImp", 0)
            est_mmr = get_mmr_from_imp(avg_imp)
            
            dt_str = "N/A"
            if start_time > 0:
                dt = datetime.fromtimestamp(start_time)
                dt_str = dt.strftime('%Y-%m-%d %H:%M')
            
            mode_name = get_mode_name(game_mode)
            
            f.write(f"{i}. Match ID: {match_id}\n")
            f.write(f"   Date: {dt_str}\n")
            f.write(f"   Duration: {duration}s ({duration//60}m)\n")
            f.write(f"   Mode: {mode_name}\n")
            f.write(f"   Avg Imp: {avg_imp} (~{est_mmr} MMR)\n")
            f.write(f"   URL: https://stratz.com/matches/{match_id}\n\n")
    
    print(f"[OK] Saved {len(matches)} matches")


def main():
    print("\n" + "=" * 60)
    print("DOTA 2 MATCH SEARCH - PUBLIC MATCHES")
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
