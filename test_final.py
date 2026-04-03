# -*- coding: utf-8 -*-
"""
Тест - используем JProxy без @JImplements
"""
import jpype
import jpype.imports
from jpype import JProxy
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

print("Classes imported")

# Создаём Python класс с нужным методом
class TickProcessor:
    """Процессор для обработки тиков"""
    
    def __init__(self):
        self.tick_data = []
        self.entities = None
        self.hero_data = []
        self.tick_count = 0
    
    def setEntities(self, entities):
        """Вызывается Clarity при инициализации"""
        print(f"setEntities called!")
        self.entities = entities
        
        # Попробуем получить entities
        if entities:
            try:
                # Получаем всех героев
                heroes = []
                all_entities = entities.getAll()
                print(f"Total entities: {len(all_entities)}")
                
                for entity in all_entities:
                    try:
                        dt_class = entity.getDtClass()
                        if dt_class:
                            classname = dt_class.getDtName()
                            if classname and "CDOTA_BaseHero" in classname:
                                heroes.append({
                                    "classname": classname,
                                    "index": entity.getIndex(),
                                })
                    except Exception as e:
                        continue
                
                print(f"Found {len(heroes)} heroes")
                self.hero_data = heroes
                
            except Exception as e:
                print(f"Error getting entities: {e}")

# Создаём JProxy через словарь - это позволяет не указывать интерфейс
processor = TickProcessor()

# Создаём словарь с методами
methods_dict = {
    'setEntities': processor.setEntities,
    'equals': lambda other: processor is other,
    'hashCode': lambda: id(processor),
    'toString': lambda: 'TickProcessor',
}

proxy = JProxy(intf=None, dict=methods_dict)
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
        print(f"Found heroes: {len(processor.hero_data)}")
        
        # Выводим героев
        for h in processor.hero_data[:5]:
            print(f"  - {h}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"File not found: {demo_file}")

print("\nDone!")