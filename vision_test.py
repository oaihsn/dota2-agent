import cv2
import numpy as np
import pyautogui
import pygame
import win32gui
import win32con
import time
import requests # Не забудь: pip install requests

# --- НАСТРОЙКИ ---
MONITOR_W, MONITOR_H = 2560, 1440 
MAP_SIZE = 325 

TOWER_LOCATIONS = [
    (173, 153), (209, 124), (278, 206), (280, 156), (279, 105), (243, 89), 
    (231, 59), (160, 53), (68, 56), (256, 73), (301, 50), (252, 279), 
    (136, 186), (104, 216), (155, 277), (42, 177), (45, 127), (42, 227), 
    (73, 242), (87, 274), (55, 257)
]

def start_vision():
    pygame.init()
    screen = pygame.display.set_mode((MAP_SIZE, MAP_SIZE))
    pygame.display.set_caption("AI VISION -> DATA COLLECTOR")
    
    hwnd = pygame.display.get_wm_info()["window"]
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 50, 50, 0, 0, win32con.SWP_NOSIZE)

    clock = pygame.time.Clock()
    TOWER_RADIUS = 15 
    STATIC_THRESHOLD = 15 
    object_memory = {} 

    print("Vision запущен. Отправка данных на http://localhost:5000/update_enemies")

    try:
        while True:
            screenshot = pyautogui.screenshot(region=(0, MONITOR_H - MAP_SIZE, MAP_SIZE, MAP_SIZE))
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, np.array([0, 150, 80]), np.array([10, 255, 255])) + \
                   cv2.inRange(hsv, np.array([170, 150, 80]), np.array([180, 255, 255]))
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            new_memory = {}
            current_time = time.time()
            detected_enemies = [] 

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 12: continue
                
                x, y, w, h = cv2.boundingRect(cnt)
                center = (x + w//2, y + h//2)
                
                in_tower_zone = any(np.sqrt((center[0]-tx)**2 + (center[1]-ty)**2) < TOWER_RADIUS for tx, ty in TOWER_LOCATIONS)

                duration = 0
                for old_pos, start_time in object_memory.items():
                    if np.sqrt((center[0]-old_pos[0])**2 + (center[1]-old_pos[1])**2) < 5:
                        duration = current_time - start_time
                        new_memory[old_pos] = start_time
                        break
                if duration == 0: new_memory[center] = current_time

                if not (duration > STATIC_THRESHOLD and in_tower_zone):
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    # Добавляем врага в список (нормализуем координаты 0-1 для нейронки)
                    detected_enemies.append([round(center[0]/MAP_SIZE, 3), round(center[1]/MAP_SIZE, 3)])

            # ОТПРАВКА ДАННЫХ В COLLECTOR
            if detected_enemies:
                try:
                    requests.post("http://localhost:5000/update_enemies", json={"enemies": detected_enemies}, timeout=0.01)
                except:
                    pass # Если коллектор еще не запущен

            object_memory = new_memory
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            surf = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            screen.blit(surf, (0, 0))
            pygame.display.update()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); return
            clock.tick(30)
    finally:
        pygame.quit()

if __name__ == "__main__":
    start_vision()