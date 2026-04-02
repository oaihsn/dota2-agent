# -*- coding: utf-8 -*-
"""
Скрипт для проверки доступности GPU с помощью PyTorch.
Выводит название видеокарты и объём свободной памяти.
"""
import sys
import io

# Настраиваем кодировку для вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import torch


def check_gpu():
    """Проверяет доступность GPU и выводит информацию о нём."""
    
    print("=" * 50)
    print("Проверка GPU с помощью PyTorch")
    print("=" * 50)
    
    # Проверяем доступность CUDA
    cuda_available = torch.cuda.is_available()
    
    if not cuda_available:
        print("\n[НЕТ] CUDA недоступна!")
        print("PyTorch собран без поддержки CUDA.")
        print("Для работы с GPU установите PyTorch с поддержкой CUDA:")
        print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
        return
    
    print(f"\n[ДА] CUDA доступна!")
    print(f"   Версия CUDA: {torch.version.cuda}")
    print(f"   Количество GPU: {torch.cuda.device_count()}")
    
    # Получаем информацию о каждом GPU
    for i in range(torch.cuda.device_count()):
        print(f"\n--- GPU #{i} ---")
        
        # Название видеокарты
        gpu_name = torch.cuda.get_device_name(i)
        print(f"   Название: {gpu_name}")
        
        # Общая память GPU
        props = torch.cuda.get_device_properties(i)
        total_memory = props.total_memory
        total_memory_gb = total_memory / (1024 ** 3)
        print(f"   Общая память: {total_memory_gb:.2f} GB")
        
        # Свободная и занятая память
        allocated = torch.cuda.memory_allocated(i)
        reserved = torch.cuda.memory_reserved(i)
        allocated_gb = allocated / (1024 ** 3)
        reserved_gb = reserved / (1024 ** 3)
        free_gb = total_memory_gb - reserved_gb
        
        print(f"   Свободная память: {free_gb:.2f} GB")
        print(f"   Занятая память: {allocated_gb:.2f} GB")
        print(f"   Зарезервированная память: {reserved_gb:.2f} GB")
    
    print("\n" + "=" * 50)
    print("Проверка завершена!")
    print("=" * 50)
    
    # Предупреждение о совместимости
    print("\n*** ВНИМАНИЕ ***")
    print("RTX 5060 Ti использует архитектуру Blackwell (sm_120).")
    print("Для полной поддержки может потребоваться PyTorch 2.6+")
    print("или используйте nightly сборку.")


if __name__ == "__main__":
    check_gpu()
