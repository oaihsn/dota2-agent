# -*- coding: utf-8 -*-
"""
Тест создания Java процессора через JPype @JImplements
"""
import jpype
import jpype.imports
from jpype import JImplements, JOverride
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

print("Classes imported")

# Создаём Python класс-процессор с @JImplements
@JImplements(UsesEntities)
class TickProcessor:
    """Процессор для обработки тиков"""
    
    def __init__(self):
        self.tick_data = []
        self.entities = None
        self.hero_data = []
    
    # Методы Object, требуемые интерфейсом
    @JOverride
    def equals(self, other):
        return self is other
    
    @JOverride
    def hashCode(self):
        return id(self)
    
    @JOverride
    def toString(self):
        return "TickProcessor"
    
    @JOverride
    def setEntities(self, entities):
        """Вызывается Clarity при инициализации"""
        print(f"setEntities called: {type(entities)}")
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
                                # Пробуем получить имя героя
                                try:
                                    name = entity.getProperty("m_szName")
                                except:
                                    name = "Unknown"
                                heroes.append({
                                    "classname": classname,
                                    "index": entity.getIndex(),
                                    "name": str(name)
                                })
                    except Exception as e:
                        continue
                
                print(f"Found {len(heroes)} heroes")
                self.hero_data = heroes
                
            except Exception as e:
                print(f"Error getting entities: {e}")

print("Processor class created")

# Создаём экземпляр
processor = TickProcessor()

# Попробуем запустить парсинг
demo_file = Path("data/raw/8749329335.dem")
if demo_file.exists():
    print(f"\nParsing: {demo_file.name}")
    source = MappedFileSource(str(demo_file))
    runner = SimpleRunner(source)
    
    # Запускаем с процессором
    try:
        runner.runWith(processor)
        print("runWith completed")
        
        # Проверяем тики
        print(f"Final tick: {runner.getTick()}")
        print(f"Found heroes: {len(processor.hero_data)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"File not found: {demo_file}")

print("\nDone!")