import dxcam
from ultralytics import YOLO
import torch
import win32api, win32con
import keyboard
import time

# 1. Загрузка модели
model = YOLO('best.pt') 

# 2. Настройки
camera = dxcam.create(output_color="BGR")
camera.start(target_fps=60)

# ID классов из твоего YAML (проверь порядок!)
# 0: creep_ally, 1: creep_enemy, 2: hero_ally, 3: hero_enemy...
CREEP_ENEMY_ID = 1
HERO_ENEMY_ID = 3

def click_at(x, y):
    # Наводим и кликаем правой кнопкой (атака в Доте)
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    time.sleep(0.01)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

def bot_logic():
    print("Бот в боевом режиме!")
    print("Зажми 'ALT' — аим в ГЕРОЯ | Зажми 'SPACE' — фарм КРИПОВ")

    while True:
        frame = camera.get_latest_frame()
        if frame is None: continue

        # Детекция
        results = model.predict(frame, conf=0.5, device=0, verbose=False)
        
        target = None
        
        # РЕЖИМ 1: Охота на героев (зажат ALT)
        if keyboard.is_pressed('alt'):
            targets = [box for box in results[0].boxes if int(box.cls[0]) == HERO_ENEMY_ID]
            if targets:
                # Берем самого близкого к курсору
                curr_x, curr_y = win32api.GetCursorPos()
                targets.sort(key=lambda b: ((b.xywh[0][0]-curr_x)**2 + (b.xywh[0][1]-curr_y)**2))
                target = targets[0].xywh[0].tolist()
                win32api.SetCursorPos((int(target[0]), int(target[1])))

        # РЕЖИМ 2: Авто-фарм (зажат Пробел)
        elif keyboard.is_pressed('space'):
            creeps = [box for box in results[0].boxes if int(box.cls[0]) == CREEP_ENEMY_ID]
            if creeps:
                # Берем случайного или ближайшего крипа и кликаем по нему
                target = creeps[0].xywh[0].tolist()
                click_at(int(target[0]), int(target[1]))
                time.sleep(0.2) # Небольшая пауза, чтобы не спамить кликами

        if keyboard.is_pressed('end'):
            break

if __name__ == "__main__":
    bot_logic()