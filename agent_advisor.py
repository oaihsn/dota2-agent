import torch
import torch.nn as nn
import numpy as np
import joblib
import pygame
import requests
import time

# --- НАСТРОЙКИ ---
MAP_SIZE = 325
SERVER_URL = "http://127.0.0.1:5555/get_latest" # Нам нужно будет добавить этот эндпоинт в сервер

# Загружаем "Мозг" и "Скалер"
class DotaBrain(nn.Module):
    def __init__(self):
        super(DotaBrain, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(8, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 8)
        )
    def forward(self, x):
        return self.net(x)

model = DotaBrain()
model.load_state_dict(torch.load('dota_model.pth'))
model.eval()
scaler = joblib.load('scaler.pkg')

def start_advisor():
    pygame.init()
    # Создаем прозрачное или отдельное окно для советов
    screen = pygame.display.set_mode((MAP_SIZE, 100)) 
    pygame.display.set_caption("AI_ADVISOR")
    font = pygame.font.SysFont("Arial", 18, bold=True)
    clock = pygame.time.Clock()

    print("Агент запущен. Анализирую ситуацию...")

    while True:
        try:
            # Запрашиваем последние данные у сервера
            # (Для этого нужно в data_collector.py добавить выдачу данных)
            resp = requests.get("http://127.0.0.1:5555/get_data", timeout=0.1)
            if resp.status_code == 200:
                data = resp.json()
                enemies = np.array(data['enemies']).reshape(1, -1)
                
                # Нейросеть делает предсказание
                with torch.no_grad():
                    inputs = torch.FloatTensor(scaler.transform(enemies))
                    prediction = model(inputs).numpy()

                # ЛОГИКА АНАЛИЗА:
                # Если сумма координат врагов стала 0, значит они ушли в инвиз или туман
                enemy_count = data['count']
                
                screen.fill((0, 0, 0))
                if enemy_count == 0:
                    msg = "ВРАГИ ПРОПАЛИ! ОПАСНОСТЬ!"
                    color = (255, 0, 0)
                elif enemy_count < 3:
                    msg = f"Вижу {enemy_count} врага. Будь осторожен."
                    color = (255, 255, 0)
                else:
                    msg = "Вижу всю команду. Можно пушить."
                    color = (0, 255, 0)
                
                txt = font.render(msg, True, color)
                screen.blit(txt, (10, 40))
        except:
            pass

        pygame.display.update()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: return
        clock.tick(10)

if __name__ == "__main__":
    start_advisor()