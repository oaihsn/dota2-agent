from flask import Flask, request, jsonify
import csv
import time
import os

app = Flask(__name__)
CSV_FILE = 'dota_training_dataa.csv'
PORT = 5555 

# Глобальная переменная для хранения последних данных (для Агента)
last_data = {"enemies": [0,0,0,0,0,0,0,0], "count": 0}

@app.route('/update_enemies', methods=['POST'])
def update_enemies():
    global last_data
    try:
        data = request.json
        enemies = data.get('enemies', [])
        
        # 1. Подготовка данных для CSV и Агента
        row = [time.time()]
        current_coords = []
        for i in range(4):
            if i < len(enemies):
                x, y = enemies[i][0], enemies[i][1]
                row.extend([x, y])
                current_coords.extend([x, y])
            else:
                row.extend([0, 0])
                current_coords.extend([0, 0])
        
        # Обновляем данные для Агента
        last_data = {"enemies": current_coords, "count": len(enemies)}
        
        # 2. Запись в CSV
        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
            f.flush()
            
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"Ошибка сервера: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/get_data', methods=['GET'])
def get_data():
    # Эндпоинт, из которого Агент будет забирать данные
    return jsonify(last_data)

if __name__ == '__main__':
    # Создаем заголовки, если файл пустой
    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['ts', 'e1x', 'e1y', 'e2x', 'e2y', 'e3x', 'e3y', 'e4x', 'e4y'])
    
    print(f"--- СЕРВЕР ЗАПУЩЕН НА ПОРТУ {PORT} ---")
    app.run(port=PORT, debug=False, threaded=True)