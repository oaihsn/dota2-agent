import torch
import torch.nn as nn
import json
import collections
import numpy as np
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import pygame
import win32gui
import win32con
import os

# --- МОДЕЛЬ (Твоя обученная нейронка) ---
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

# Настройки 2K
RADAR_SIZE = 350 
MODEL_PATH = "models/dota_ai_v2.pth"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = DotaLSTMDeep().to(device)
if os.path.exists(MODEL_PATH):
    model.load_state_dict(torch.load(MODEL_PATH))
model.eval()

# Состояние
prediction_coords = [0, 0]
current_hero_coords = [0, 0]
all_units = [] 
history = collections.deque(maxlen=20)
last_state = {"x": 0, "y": 0}

def world_to_radar(world_x, world_y):
    rx = int((world_x + 8000) / 16000 * RADAR_SIZE)
    ry = int(RADAR_SIZE - ((world_y + 8000) / 16000 * RADAR_SIZE))
    return rx, ry

class GSIServer(BaseHTTPRequestHandler):
    def do_POST(self):
        global prediction_coords, current_hero_coords, last_state, all_units
        content_length = int(self.headers['Content-Length'])
        try:
            data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        except: return

        # 1. ОБРАБОТКА ТВОЕГО ГЕРОЯ (LSTM ПРОГНОЗ)
        if 'hero' in data:
            h = data['hero']
            x, y = h.get('xpos', 0), h.get('ypos', 0)
            current_hero_coords = [x, y]
            
            vx, vy = x - last_state["x"], y - last_state["y"]
            
            # Подготовка данных для GPU
            norm_f = np.zeros(10, dtype=np.float32)
            norm_f[0:2] = [x/8000, y/8000]
            norm_f[2:4] = [vx/25, vy/25]
            history.append(norm_f)

            if len(history) == 20:
                input_np = np.array(history, dtype=np.float32)
                input_t = torch.from_numpy(input_np).unsqueeze(0).to(device)
                with torch.no_grad():
                    pred = model(input_t).cpu().numpy()[0]
                    ai_dx, ai_dy = (pred[0]*8000 - x), (pred[1]*8000 - y)
                    
                    # Фильтр "анти-занос" (как в v2)
                    if (ai_dx * vx < 0): ai_dx = vx * 2.5
                    if (ai_dy * vy < 0): ai_dy = vy * 2.5
                    
                    # Масштабируем вектор предсказания
                    prediction_coords = [x + vx*12 + ai_dx*0.1, y + vy*12 + ai_dy*0.1]
            
            last_state = {"x": x, "y": y}

        # 2. ОБРАБОТКА ВРАГОВ
        temp_units = []
        if 'units' in data:
            for faction in data['units'].values():
                for u in faction.values():
                    ux, uy = u.get('xpos'), u.get('ypos')
                    if ux is not None and uy is not None:
                        # Если это не мы (дистанция > 150)
                        dist = ((ux - x)**2 + (uy - y)**2)**0.5
                        if dist > 150:
                            temp_units.append([ux, uy])
        all_units = temp_units

        self.send_response(200)
        self.end_headers()
    def log_message(self, format, *args): return 

def run_overlay():
    pygame.init()
    screen = pygame.display.set_mode((RADAR_SIZE, RADAR_SIZE), pygame.NOFRAME)
    hwnd = pygame.display.get_wm_info()["window"]
    # Позиция окна 50, 50
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 50, 50, 0, 0, win32con.SWP_NOSIZE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Consolas", 12, bold=True)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
        
        # Фон радара
        screen.fill((5, 5, 12)) 
        pygame.draw.rect(screen, (0, 200, 255), (0, 0, RADAR_SIZE, RADAR_SIZE), 1)

        # Рисуем ВРАГОВ (Красные точки с белой обводкой)
        for ux, uy in all_units:
            rx, ry = world_to_radar(ux, uy)
            pygame.draw.circle(screen, (255, 255, 255), (rx, ry), 6) # Обводка
            pygame.draw.circle(screen, (255, 0, 0), (rx, ry), 4)     # Враг

        # Твой герой (Зеленый)
        hx, hy = world_to_radar(current_hero_coords[0], current_hero_coords[1])
        pygame.draw.circle(screen, (0, 255, 100), (hx, hy), 6)

        # Твой ПРЕДИКТ (Красная точка вектора)
        if prediction_coords != [0, 0]:
            px, py = world_to_radar(prediction_coords[0], prediction_coords[1])
            pygame.draw.line(screen, (0, 150, 255), (hx, hy), (px, py), 2)
            pygame.draw.circle(screen, (255, 50, 50), (px, py), 4)
        
        # Инфо-панель
        txt = font.render(f"UNITS: {len(all_units)}", True, (0, 255, 255))
        screen.blit(txt, (10, 10))
        
        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    print("AI Radar Online!")
    threading.Thread(target=lambda: HTTPServer(('localhost', 3000), GSIServer).serve_forever(), daemon=True).start()
    run_overlay()