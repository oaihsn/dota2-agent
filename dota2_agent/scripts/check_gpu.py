# -*- coding: utf-8 -*-
"""
Скрипт для проверки GPU с помощью PyTorch.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("[ОШИБКА] PyTorch не установлен!")

def check_gpu():
    print("=" * 50)
    print("Проверка GPU с помощью PyTorch")
    print("=" * 50)
    
    if not TORCH_AVAILABLE:
        print("[НЕТ] PyTorch не установлен!")
        print("Установите: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
        return
    
    cuda_available = torch.cuda.is_available()
    
    if not cuda_available:
        print("[НЕТ] CUDA недоступна!")
        print("Установите PyTorch с поддержкой CUDA")
        return
    
    print(f"\n[ДА] CUDA доступна!")
    print(f"   Версия CUDA: {torch.version.cuda}")
    print(f"   Количество GPU: {torch.cuda.device_count()}")
    
    for i in range(torch.cuda.device_count()):
        print(f"\n--- GPU #{i} ---")
        gpu_name = torch.cuda.get_device_name(i)
        print(f"   Название: {gpu_name}")
        
        props = torch.cuda.get_device_properties(i)
        total_memory_gb = props.total_memory / (1024 ** 3)
        print(f"   Общая память: {total_memory_gb:.2f} GB")
        
        allocated = torch.cuda.memory_allocated(i)
        reserved = torch.cuda.memory_reserved(i)
        free_gb = total_memory_gb - (reserved / (1024 ** 3))
        
        print(f"   Свободная память: {free_gb:.2f} GB")
        print(f"   Занятая память: {allocated / (1024 ** 3):.2f} GB")
    
    print("\n" + "=" * 50)
    print("Проверка завершена!")
    print("=" * 50)

if __name__ == "__main__":
    check_gpu()
