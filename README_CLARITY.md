# Clarity Parser для Dota 2

## Установка

1. Скачай Clarity JAR с GitHub:
   - https://github.com/skadistats/clarity/releases

2. Или собери из исходников:
   ```bash
   git clone https://github.com/skadistats/clarity.git
   cd clarity
   mvn package
   ```

## Использование

```bash
java -jar clarity.jar <path_to_demo.dem>
```

## Пример парсинга

Clarity парсит .dem файлы и выводит:
- Все entity данные
- User commands (движения игроков)
- События игры

## Python интеграция

Можно вызывать Java из Python:

```python
import subprocess

result = subprocess.run([
    'java', '-jar', 'lib/clarity.jar',
    'data/raw/8749329335.dem'
], capture_output=True, text=True)

print(result.stdout)
```
