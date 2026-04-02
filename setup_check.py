# -*- coding: utf-8 -*-
"""
Скрипт проверки окружения для проекта Dota 2 Agent.
Проверяет доступность GPU и выводит информацию о системе.
"""
import sys
import io

# Настраиваем кодировку для вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("[ОШИБКА] PyTorch не установлен!")

try:
    import pandas
    import numpy
    import requests
    import tqdm
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False


def check_gpu():
    """Проверяет доступность GPU через PyTorch."""
    
    print("=" * 60)
    print("Проверка GPU (PyTorch)")
    print("=" * 60)
    
    if not TORCH_AVAILABLE:
        print("[НЕТ] PyTorch не установлен!")
        print("Установите: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
        return False
    
    cuda_available = torch.cuda.is_available()
    
    if not cuda_available:
        print("[НЕТ] CUDA недоступна!")
        return False
    
    print(f"[ДА] CUDA доступна!")
    print(f"   Версия CUDA: {torch.version.cuda}")
    print(f"   Количество GPU: {torch.cuda.device_count()}")
    
    for i in range(torch.cuda.device_count()):
        print(f"\n--- GPU #{i} ---")
        gpu_name = torch.cuda.get_device_name(i)
        print(f"   Название: {gpu_name}")
        
        props = torch.cuda.get_device_properties(i)
        total_memory = props.total_memory
        total_memory_gb = total_memory / (1024 ** 3)
        print(f"   Общая память: {total_memory_gb:.2f} GB")
        
        allocated = torch.cuda.memory_allocated(i)
        reserved = torch.cuda.memory_reserved(i)
        free_gb = total_memory_gb - (reserved / (1024 ** 3))
        
        print(f"   Свободная память: {free_gb:.2f} GB")
        print(f"   Занятая память: {allocated / (1024 ** 3):.2f} GB")
    
    print("\n" + "=" * 60)
    return True


def check_dependencies():
    """Проверяет установленные зависимости."""
    
    print("\n" + "=" * 60)
    print("Проверка зависимостей")
    print("=" * 60)
    
    deps = {
        "torch": "PyTorch",
        "torchvision": "TorchVision",
        "pandas": "Pandas",
        "numpy": "NumPy",
        "requests": "Requests",
        "tqdm": "tqdm"
    }
    
    all_ok = True
    for module, name in deps.items():
        try:
            __import__(module)
            print(f"[OK] {name}")
        except ImportError:
            print(f"[НЕТ] {name}")
            all_ok = False
    
    if not all_ok:
        print("\nУстановите зависимости:")
        print("pip install -r requirements.txt")
    
    return all_ok


def main():
    """Основная функция проверки."""
    
    print("\n" + "=" * 60)
    print("ПРОВЕРКА ОКРУЖЕНИЯ DOTA 2 AGENT")
    print("=" * 60)
    
    gpu_ok = check_gpu()
    deps_ok = check_dependencies()
    
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТ")
    print("=" * 60)
    
    if gpu_ok and deps_ok:
        print("✓ Все проверки пройдены! Можно начинать обучение.")
    else:
        print("✗ Есть проблемы. Исправьте их перед началом работы.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
