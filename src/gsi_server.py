# -*- coding: utf-8 -*-
"""
Dota 2 Game State Integration (GSI) Server
Локальный сервер для получения данных в реальном времени

Инструкция:
1. Запустить этот сервер
2. В Dota 2: Settings → Game → Enable Developer Console = Yes
3. Открыть консоль (~) и ввести: dota_dev connect localhost
4. Смотреть матч - данные будут приходить автоматически
"""
from flask import Flask, request, jsonify
import json
from datetime import datetime
from pathlib import Path
import logging

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Директории
PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_RAW_DIR = DATA_DIR / "raw"

DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Файл для сохранения
OUTPUT_FILE = DATA_RAW_DIR / "gsi_live.json"

# Собираем все данные
gsi_data = {
    'timestamp': None,
    'provider': {},
    'map': {},
    'player': {},
    'hero': {},
    'items': {},
    'abilities': {},
    'events': []
}


@app.route('/')
def index():
    """Главная страница."""
    return """
    <html>
    <head><title>Dota 2 GSI Server</title></head>
    <body>
        <h1>🎮 Dota 2 GSI Server</h1>
        <p>Server running. Waiting for Dota 2 connection...</p>
        <p>Commands:</p>
        <ul>
            <li>Open Dota 2 console (~)</li>
            <li>Type: <code>hostip localhost</code></li>
            <li>Type: <code>dota_dev disconnect</code> to stop</li>
        </ul>
        <h2>Last Data:</h2>
        <pre id="data">Waiting...</pre>
        <script>
            setInterval(() => {
                fetch('/data')
                    .then(r => r.json())
                    .then(d => document.getElementById('data').textContent = JSON.stringify(d, null, 2));
            }, 1000);
        </script>
    </body>
    </html>
    """


@app.route('/data')
def get_data():
    """Возвращает последние данные GSI."""
    return jsonify(gsi_data)


@app.route('/gsi', methods=['POST'])
def gsi_endpoint():
    """GSI endpoint - Dota 2 отправляет данные сюда."""
    global gsi_data
    
    try:
        # Получаем данные
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data'}), 400
        
        # Обновляем глобальные данные
        gsi_data['timestamp'] = datetime.now().isoformat()
        
        # Provider - информация о подключении
        if 'provider' in data:
            gsi_data['provider'] = data['provider']
            logger.info(f"Provider: {data['provider'].get('name', 'Unknown')}")
        
        # Map - информация о карте
        if 'map' in data:
            gsi_data['map'] = data['map']
        
        # Player - информация об игроке
        if 'player' in data:
            gsi_data['player'] = data['player']
        
        # Hero - информация о герое
        if 'hero' in data:
            gsi_data['hero'] = data['hero']
            
            # Сохраняем в файл при каждом обновлении героя
            save_gsi_data(gsi_data)
        
        # Предметы
        if 'items' in data:
            gsi_data['items'] = data['items']
        
        # abilities
        if 'abilities' in data:
            gsi_data['abilities'] = data['abilities']
        
        # Дополнительные данные
        for key in ['buildings', 'drops', '自定义数据']:
            if key in data:
                gsi_data[key] = data[key]
        
        # Логируем важные события
        if 'player' in data and data['player']:
            p = data['player']
            logger.debug(f"Player update: {p.get('name', 'Unknown')}")
        
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


def save_gsi_data(data: dict):
    """Сохраняет GSI данные в файл."""
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Save error: {e}")


def load_gsi_data():
    """Загружает последние GSI данные."""
    global gsi_data
    
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                gsi_data = json.load(f)
            logger.info(f"Loaded existing data from {OUTPUT_FILE}")
        except Exception as e:
            logger.error(f"Load error: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("🎮 Dota 2 GSI Server")
    print("=" * 60)
    print()
    print("1. Запусти Dota 2")
    print("2. Settings → Game → Enable Developer Console = Yes")
    print("3. Открой консоль (~) и введи:")
    print("   dota_dev connect localhost")
    print()
    print(f"Server starting on http://localhost:3000")
    print(f"Data will be saved to: {OUTPUT_FILE}")
    print()
    
    # Загружаем существующие данные
    load_gsi_data()
    
    # Запускаем сервер (Dota 2 использует порт 1337 по умолчанию)
    app.run(host='0.0.0.0', port=1337, debug=False)
