from ultralytics import YOLO
import torch

if __name__ == '__main__':
    # 1. Проверка видеокарты
    print(f"Используем карту: {torch.cuda.get_device_name(0)}")

    # 2. Загрузка модели
    model = YOLO('yolov8n.pt') 

    # 3. Старт обучения
    model.train(
        data='dota_data/data.yaml', 
        epochs=30,      # Сделаем 30 эпох для начала
        imgsz=640, 
        device=0,       # Твоя RTX 5060 Ti
        batch=16        # Размер пачки данных
    )