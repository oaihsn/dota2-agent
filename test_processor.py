# -*- coding: utf-8 -*-
"""
Тест создания Java процессора через JPype JProxy
"""
import jpype
import jpype.imports
from jpype import JProxy, JOverride
from pathlib import Path

LIB_DIR = Path(__file__).parent / "lib"

# JAR файлы
jars = [
    str(LIB_DIR / "clarity-proto-5.4.jar"),
    str(LIB_DIR / "fastutil.jar"),
    str(LIB_DIR / "slf4j-api.jar"),
    str(LIB_DIR / "classindex.jar"),
    str(LIB_DIR / "snappy-java.jar"),
    str(LIB_DIR / "clarity-new.jar"),
]

# Запускаем JVM
jvm_path = "C:\\Program Files\\Java\\jdk-17\\bin\\server\\jvm.dll"
jpype.startJVM(jvm_path, "-ea", convertStrings=True, classpath=jars)

print("JVM started")

# Импортируем Java классы
from skadistats.clarity.source import MappedFileSource
from skadistats.clarity.processor.runner import SimpleRunner
from skadistats.clarity.processor.entities import UsesEntities
from skadistats.clarity.processor.reader import OnTickEnd

print("Classes imported")

# Создаём Python класс-процессор
class TickProcessor:
    """Процессор для обработки тиков"""
    
    def __init__(self):
        self.tick_data = []
        self.entities = None
    
    def setEntities(self, entities):
        """Вызывается Clarity при инициализации"""
        print(f"setEntities called: {entities}")
        self.entities = entities
    
    def onTickEnd(self, synthetic):
        """Вызывается в конце каждого тика"""
        # Это не будет работать - нужен proper interface implementation
        return True

# Создаём JProxy
# JProxy требует интерфейс и реализацию
print("Creating proxy...")

# Попробуем использовать JProxy с несколькими интерфейсами
processor = TickProcessor()

# JProxy для UsesEntities - используем inst параметр
proxy = JProxy(UsesEntities, inst=processor)
print(f"Created proxy: {proxy}")

# Попробуем запустить парсинг
demo_file = Path("data/raw/8749329335.dem")
if demo_file.exists():
    print(f"\nParsing: {demo_file.name}")
    source = MappedFileSource(str(demo_file))
    runner = SimpleRunner(source)
    
    # Запускаем с процессором
    try:
        runner.runWith(proxy)
        print("runWith completed")
        
        # Проверяем тики
        print(f"Final tick: {runner.getTick()}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

print("\nDone!")