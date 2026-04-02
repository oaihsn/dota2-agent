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
├── clarity_parser/  # Парсер реплеев Clarity
├── downloader_opendota.py    # OpenDota API
├── downloader_stratz.py      # Stratz API (базовый)
├── downloader_stratz_selenium.py  # Stratz API через Selenium
└── README.md       # Этот файл
```

## Установка

```bash
pip install -r requirements.txt
```

## Быстрый старт

### 1. Проверка GPU

```bash
python scripts/check_gpu.py
```

### 2. Загрузка данных матчей

**Через Stratz API (рекомендуется):**
```bash
python downloader_stratz_selenium.py
```
Требуется токен с https://stratz.com/api

**Через OpenDota API:**
```bash
python downloader_opendota.py
```

## Требования

- Python 3.8+
- PyTorch с поддержкой CUDA
- NVIDIA GPU с достаточным объёмом памяти (рекомендуется 8GB+)

---

Удачи в разработке! 🎮
