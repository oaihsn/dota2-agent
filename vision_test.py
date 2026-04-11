import cv2
import numpy as np
import pyautogui
import pygame
import time
import requests
import win32gui
import win32con

# --- НАСТРОЙКИ ---
MONITOR_W, MONITOR_H = 2560, 1440 
MAP_SIZE = 325 
SERVER_URL = "http://127.0.0.1:5555/update_enemies"

MIN_HERO_AREA = 96      
SINGLE_HERO_MAX = 211   
AVERAGE_HERO_SIZE = 155 

T4_TOWERS = [(63, 258), (58, 252), (259, 81), (252, 74)]
permanent_black_list = list(T4_TOWERS)
static_memory = {}

def set_window_topmost(window_title):
    hwnd = win32gui.FindWindow(None, window_title)
    if hwnd:
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

def start_vision():
    pygame.init()
    screen = pygame.display.set_mode((MAP_SIZE, MAP_SIZE))
    window_title = "AI_VISION_PRO"
    pygame.display.set_caption(window_title)
    font = pygame.font.SysFont("Arial", 12, bold=True)
    
    clock = pygame.time.Clock()
    print("Vision запущен. Собираем данные...")

    try:
        while True:
            now = time.time()
            img = pyautogui.screenshot(region=(0, MONITOR_H - MAP_SIZE, MAP_SIZE, MAP_SIZE))
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Маски цветов
            m_red = cv2.inRange(hsv, np.array([0, 150, 80]), np.array([10, 255, 255])) + \
                    cv2.inRange(hsv, np.array([170, 150, 80]), np.array([180, 255, 255]))
            m_green = cv2.inRange(hsv, np.array([35, 80, 70]), np.array([90, 255, 255]))
            combined = cv2.bitwise_or(m_red, m_green)

            for bx, by in permanent_black_list:
                cv2.circle(combined, (bx, by), 12, (0, 0, 0), -1)

            contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            detected_enemies = []
            screen.blit(pygame.surfarray.make_surface(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).swapaxes(0, 1)), (0, 0))

            for c in contours:
                area = cv2.contourArea(c)
                if area < 30 or area > 700: continue
                
                x, y, w, h = cv2.boundingRect(c)
                cx, cy = x + w//2, y + h//2

                # 1. ФИЛЬТР ФОРМЫ (Здания - вытянутые, Герои - квадратные)
                aspect_ratio = float(w) / h
                if not (0.7 < aspect_ratio < 1.4): continue

                # 2. ФИЛЬТР СТАТИКИ
                pos_key = (cx // 3, cy // 3)
                if pos_key in static_memory:
                    if now - static_memory[pos_key] > 2.0:
                        if pos_key not in permanent_black_list:
                            permanent_black_list.append(pos_key)
                        continue
                else: static_memory[pos_key] = now

                # 3. КРАСНЫЙ ИЛИ ЗЕЛЕНЫЙ
                is_red = (hsv[cy, cx][0] < 20 or hsv[cy, cx][0] > 160)
                
                if area >= MIN_HERO_AREA:
                    pygame.draw.rect(screen, (255,0,0) if is_red else (0,255,0), (x, y, w, h), 2)
                    if is_red:
                        detected_enemies.append([round(cx/MAP_SIZE, 3), round(cy/MAP_SIZE, 3)])

            # ОТПРАВКА БЕЗ ПРОКСИ
            if detected_enemies:
                try: 
                    requests.post(SERVER_URL, json={"enemies": detected_enemies}, timeout=0.3, 
                                  proxies={"http": None, "https": None})
                except: pass

            pygame.display.update()
            if int(now) % 3 == 0: set_window_topmost(window_title)
            for e in pygame.event.get():
                if e.type == pygame.QUIT: return
            clock.tick(25)
    finally: pygame.quit()

if __name__ == "__main__": start_vision()