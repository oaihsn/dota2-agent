import pandas as pd
import time
from flask import Flask, request
import threading
import os

# --- НАСТРОЙКИ ---
FILE_NAME = "dota_training_dataa.csv"

app = Flask(__name__)

# Состояние мира
current_state = {
    "my_x": 0, "my_y": 0,
    "enemies": [] 
}

# Прием данных от Vision (на порт 5000)
@app.route('/update_enemies', methods=['POST'])
def update_enemies():
    data = request.json
    current_state["enemies"] = data.get("enemies", [])
    return "OK"

# Прием данных от GSI (на порт 3000)
gsi_app = Flask(__name__)
@gsi_app.route('/', methods=['POST'])
def update_gsi():
    data = request.json
    if 'hero' in data and 'position' in data['hero']:
        pos = data['hero']['position']
        current_state["my_x"], current_state["my_y"] = pos[0], pos[1]
    return "OK"

def run_gsi():
    gsi_app.run(port=3000)

def start_collecting():
    print(f"Запись в {FILE_NAME} запущена. Ожидание данных...")
    
    while True:
        # Берем 3-х ближайших врагов (больше данных — умнее LSTM)
        enemies = current_state["enemies"][:3]
        while len(enemies) < 3:
            enemies.append([0, 0])
            
        row = {
            'timestamp': time.time(),
            'my_x': current_state["my_x"],
            'my_y': current_state["my_y"],
            'e1_x': enemies[0][0], 'e1_y': enemies[0][1],
            'e2_x': enemies[1][0], 'e2_y': enemies[1][1],
            'e3_x': enemies[2][0], 'e3_y': enemies[2][1]
        }
        
        df = pd.DataFrame([row])
        df.to_csv(FILE_NAME, mode='a', header=not os.path.exists(FILE_NAME), index=False)
        time.sleep(0.5)

if __name__ == "__main__":
    # Запуск GSI
    threading.Thread(target=run_gsi, daemon=True).start()
    # Запуск Collector
    threading.Thread(target=lambda: app.run(port=5000), daemon=True).start()
    # Запуск цикла записи
    start_collecting()