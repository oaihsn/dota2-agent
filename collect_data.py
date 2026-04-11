import cv2
import numpy as np
import dxcam
import time
import os

# --- НАСТРОЙКИ ---
SAVE_PATH = "dota_dataset/images"
# Как часто делать скриншот (в секундах)
# 2.0 - 2.5 секунды идеально, чтобы кадры были разными
INTERVAL = 2.0 

if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH, exist_ok=True)

def start_collection():
    # Инициализируем быстрый захват экрана
    camera = dxcam.create(output_color="BGR")
    
    print("--- СБОР ДАННЫХ ДЛЯ YOLO ---")
    print(f"Папка сохранения: {SAVE_PATH}")
    print("Инструкция: Запусти реплей или игру, затем вернись сюда.")
    print("Начинаю через 5 секунд...")
    time.sleep(5)
    
    count = 0
    camera.start(target_fps=60) # Запускаем поток захвата
    
    try:
        while True:
            # Получаем самый свежий кадр
            frame = camera.get_latest_frame()
            
            if frame is not None:
                # Генерируем уникальное имя файла
                timestamp = int(time.time() * 1000)
                filename = os.path.join(SAVE_PATH, f"dota_frame_{timestamp}.jpg")
                
                # Сохраняем (качество 95, чтобы YOLO видела детали)
                cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                
                count += 1
                print(f"[{time.strftime('%H:%M:%S')}] Сохранено кадров: {count}", end="\r")
            
            # Ждем интервал
            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print(f"\nСбор остановлен кнопками.")
    finally:
        camera.stop()
        print(f"Итого собрано: {count} изображений.")
        print(f"Теперь проверь папку: {os.path.abspath(SAVE_PATH)}")

if __name__ == "__main__":
    start_collection()