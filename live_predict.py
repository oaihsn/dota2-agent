import torch
import torch.nn as nn
import json
import collections
import numpy as np
from http.server import BaseHTTPRequestHandler, HTTPServer

# 1. Твоя архитектура из train_v2
class DotaLSTMDeep(nn.Module):
    def __init__(self, input_size=10, hidden_size=256, num_layers=3, output_size=2):
        super(DotaLSTMDeep, self).__init__()
        self.lstm1 = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc2 = nn.Linear(hidden_size // 2, output_size)
        self.relu = nn.ReLU()
    
    def forward(self, x):
        out, _ = self.lstm1(x)
        out = self.fc1(out[:, -1, :])
        out = self.relu(out)
        out = self.fc2(out)
        return out

# 2. Настройки
MODEL_PATH = "models/dota_ai_v2.pth"
SEQ_LENGTH = 20
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Загрузка модели
model = DotaLSTMDeep().to(device)
model.load_state_dict(torch.load(MODEL_PATH))
model.eval()

# Буфер для хранения истории (20 тиков)
# Формат тика: [x, y, vx, vy, ax, ay, hp, mana, enemy, tower]
history = collections.deque(maxlen=SEQ_LENGTH)
last_state = {"x": 0, "y": 0, "vx": 0, "vy": 0}

def normalize_input(features):
    """Твои формулы из train_v2"""
    f = np.array(features, dtype=np.float32)
    f[0] = (f[0] + 8500) / 17000  # x
    f[1] = (f[1] + 8500) / 17000  # y
    f[2] = (f[2] + 100) / 200     # vx
    f[3] = (f[3] + 100) / 200     # vy
    f[4] = (f[4] + 50) / 100      # ax
    f[5] = (f[5] + 50) / 100      # ay
    return f

def denormalize_output(pred):
    """Возвращаем координаты в игровые единицы"""
    x = pred[0] * 17000 - 8500
    y = pred[1] * 17000 - 8500
    return x, y

class GSIServer(BaseHTTPRequestHandler):
    def do_POST(self):
        global last_state
        content_length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(content_length).decode('utf-8'))

        if 'hero' in data:
            h = data['hero']
            x, y = h['xpos'], h['ypos']
            hp = h['health_percent'] / 100
            mana = h['mana_percent'] / 100
            
            # Вычисляем vx, vy, ax, ay на лету
            vx = x - last_state["x"]
            vy = y - last_state["y"]
            ax = vx - last_state["vx"]
            ay = vy - last_state["vy"]
            
            # Собираем вектор фич
            # enemy_near и under_tower пока ставим 0 (или добавь логику проверки)
            current_features = [x, y, vx, vy, ax, ay, hp, mana, 0, 0]
            norm_features = normalize_input(current_features)
            history.append(norm_features)
            
            # Обновляем состояние
            last_state = {"x": x, "y": y, "vx": vx, "vy": vy}

            if len(history) == SEQ_LENGTH:
                input_tensor = torch.FloatTensor(list(history)).unsqueeze(0).to(device)
                with torch.no_grad():
                    prediction = model(input_tensor).cpu().numpy()[0]
                    pred_x, pred_y = denormalize_output(prediction)
                    print(f"Current: ({x:.0f}, {y:.0f}) -> Prediction (next tick): ({pred_x:.0f}, {pred_y:.0f})")

        self.send_response(200)
        self.end_headers()

# Запуск
print("GSI Server started on port 3000. Waiting for Dota 2...")
HTTPServer(('localhost', 3000), GSIServer).serve_forever()