from roboflow import Roboflow
from ultralytics import YOLO
import torch

# 1. СКАЧИВАЕМ ГОТОВЫЙ ДАТАСЕТ
# Вставь сюда свой API ключ
rf = Roboflow(api_key="2jhN7BGc5MWQTgCWdwcj")
project = rf.workspace("dota-2-detection").project("dota2-objects") # Популярный датасет
dataset = project.version(1).download("yolov8")

# 2. ПРОВЕРЯЕМ GPU
device = 0 if torch.cuda.is_available() else 'cpu'
print(f"Обучение пойдет на: {torch.cuda.get_device_name(0)}")

# 3. ЗАПУСКАЕМ ОБУЧЕНИЕ НА 5060 Ti
model = YOLO('yolov8n.pt') # Берем быструю базовую модель

model.train(
    data=f"{dataset.location}/data.yaml", 
    epochs=50, 
    imgsz=640, 
    device=device,
    project='dota2_ai_project',
    name='dota_vision_v1'
)

print("Обучение завершено! Модель лежит в папке dota2_ai_project/dota_vision_v1/weights/best.pt")