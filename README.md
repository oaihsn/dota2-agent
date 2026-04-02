# Dota 2 Agent

Проект для создания AI-агента для игры Dota 2.

## Структура проекта

```
dota2_agent/
├── data/           # Данные (реплеи, датасеты)
├── models/         # Обученные модели
├── scripts/        # Скрипты (check_gpu.py и др.)
├── src/            # Исходный код проекта
├── logs/           # Логи
├── config/         # Конфигурационные файлы
└── README.md       # Этот файл
```

## Быстрый старт

### 1. Проверка GPU

Перед началом работы убедитесь, что PyTorch с поддержкой CUDA установлен:

```bash
# Для NVIDIA GPU с CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Для NVIDIA GPU с CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

Затем запустите скрипт проверки GPU:

```bash
python scripts/check_gpu.py
```

Скрипт выведет:
- Название вашей видеокарты (например, NVIDIA GeForce RTX 5060 Ti)
- Объём общей памяти GPU
- Объём свободной памяти

### 2. Требования

- Python 3.8+
- PyTorch с поддержкой CUDA
- NVIDIA GPU с достаточным объёмом памяти (рекомендуется 8GB+)

## Следующие шаги

1. Установите PyTorch с поддержкой CUDA
2. Запустите `python scripts/check_gpu.py` для проверки
3. Начните разработку агента в папке `src/`

---
Удачи в разработке! 🎮
