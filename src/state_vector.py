# -*- coding: utf-8 -*-
"""
State Vector Generator для Dota 2 Agent.
Генерирует вектор состояния для нейросети PyTorch.

Вектор состояния включает:
1. Мой герой: позиция (x, y), HP, MP, уровень, gold, net_worth (7)
2. Способности: 4 слота с уровнями (4)
3. Инвентарь: 6 предметов как one-hot (6 * max_items)
4. 5 ближайших юнитов: тип, команда, HP, дистанция (5 * 4 = 20)

Итого: 7 + 4 + 6 + 20 = 37 признаков (без one-hot инвентаря)
Итого с one-hot инварём: ~337 признаков
"""
import json
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import pandas as pd

# Константы
MAX_ABILITIES = 4
MAX_INVENTORY = 6
MAX_NEARBY_UNITS = 5
MAX_ITEMS = 300  # Максимальное число предметов для one-hot

PROJECT_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = PROJECT_DIR / "data"


@dataclass
class HeroState:
    """Состояние героя."""
    hero_id: int
    pos_x: float
    pos_y: float
    health: float
    max_health: float
    mana: float
    max_mana: float
    level: int
    gold: int
    net_worth: int
    team: int  # 0 = Radiant, 1 = Dire


@dataclass
class UnitState:
    """Состояние юнита."""
    unit_type: str  # hero, creep, tower, etc.
    unit_id: int
    team: int
    pos_x: float
    pos_y: float
    health: float
    max_health: float
    is_hero: bool


@dataclass
class GameState:
    """Полное состояние игры."""
    tick: int
    my_hero: HeroState
    nearby_units: List[UnitState]
    inventory: List[int]  # ID предметов
    abilities: Dict[str, int]  # ability_name -> level


def load_item_names() -> Dict[int, str]:
    """Загружает имена предметов."""
    items_path = DATA_DIR / "items.json"
    if items_path.exists():
        with open(items_path, 'r', encoding='utf-8') as f:
            return {int(k): v for k, v in json.load(f).items()}
    return {}


def load_hero_names() -> Dict[int, str]:
    """Загружает имена героев."""
    heroes_path = DATA_DIR / "heroes.json"
    if heroes_path.exists():
        with open(heroes_path, 'r', encoding='utf-8') as f:
            return {int(k): v for k, v in json.load(f).items()}
    return {}


class StateVectorGenerator:
    """Генератор вектора состояния для PyTorch."""
    
    def __init__(self, include_one_hot_inventory: bool = False):
        """
        Args:
            include_one_hot_inventory: Если True, инвентарь кодируется как one-hot вектор
        """
        self.include_one_hot_inventory = include_one_hot_inventory
        self.item_names = load_item_names()
        self.hero_names = load_hero_names()
        self.max_items = MAX_ITEMS
        
        # Размер вектора
        self.vector_size = self._calculate_vector_size()
    
    def _calculate_vector_size(self) -> int:
        """Вычисляет размер вектора состояния."""
        size = 0
        
        # Мой герой (7 признаков)
        size += 7  # pos_x, pos_y, hp, max_hp, mp, max_mp, level, gold, net_worth -> 9
        size += 4   # abilities levels
        
        if self.include_one_hot_inventory:
            size += MAX_INVENTORY * MAX_ITEMS  # One-hot для каждого слота
        else:
            size += MAX_INVENTORY  # Просто ID предметов
        
        # 5 ближайших юнитов (20 признаков)
        size += MAX_NEARBY_UNITS * 4  # team, hp, distance, is_hero
        
        return size
    
    def euclidean_distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """Вычисляет евклидово расстояние."""
        return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def normalize_value(self, value: float, min_val: float, max_val: float) -> float:
        """Нормализует значение в диапазоне [0, 1]."""
        if max_val == min_val:
            return 0.0
        return (value - min_val) / (max_val - min_val)
    
    def encode_hero_state(self, hero: HeroState) -> np.ndarray:
        """Кодирует состояние героя в numpy массив."""
        features = []
        
        # Позиция (нормализуем к размеру карты ~16000)
        features.append(self.normalize_value(hero.pos_x, 0, 16000))
        features.append(self.normalize_value(hero.pos_y, 0, 16000))
        
        # HP/MP (нормализуем к 2000)
        features.append(self.normalize_value(hero.health, 0, 2000))
        features.append(self.normalize_value(hero.mana, 0, 1000))
        
        # Уровень (макс ~30)
        features.append(hero.level / 30.0)
        
        # Gold/Net Worth (нормализуем к 50000)
        features.append(self.normalize_value(hero.gold, 0, 50000))
        features.append(self.normalize_value(hero.net_worth, 0, 50000))
        
        return np.array(features, dtype=np.float32)
    
    def encode_abilities(self, abilities: Dict[str, int], max_abilities: int = 4) -> np.ndarray:
        """Кодирует уровни способностей."""
        levels = list(abilities.values())[:max_abilities]
        
        # Дополняем нулями
        while len(levels) < max_abilities:
            levels.append(0)
        
        return np.array(levels, dtype=np.float32) / 4.0  # Нормализуем к макс уровню 4
    
    def encode_inventory(self, inventory: List[int], use_one_hot: bool = False) -> np.ndarray:
        """Кодирует инвентарь."""
        if use_one_hot:
            # One-hot encoding для каждого слота
            features = []
            for _ in range(MAX_INVENTORY):
                slot_features = np.zeros(self.max_items, dtype=np.float32)
                features.append(slot_features)
            return np.concatenate(features)
        else:
            # Просто ID предметов (нормализованные)
            items = inventory[:MAX_INVENTORY]
            while len(items) < MAX_INVENTORY:
                items.append(0)
            return np.array(items, dtype=np.float32) / 1000.0  # Нормализуем
    
    def encode_nearby_units(
        self, 
        hero: HeroState, 
        units: List[UnitState],
        max_units: int = 5
    ) -> np.ndarray:
        """Кодирует ближайших юнитов."""
        # Сортируем по дистанции
        units_with_distance = []
        for unit in units:
            dist = self.euclidean_distance(
                hero.pos_x, hero.pos_y,
                unit.pos_x, unit.pos_y
            )
            units_with_distance.append((dist, unit))
        
        units_with_distance.sort(key=lambda x: x[0])
        
        features = []
        for i in range(max_units):
            if i < len(units_with_distance):
                dist, unit = units_with_distance[i]
                
                # Команда (0 = враг, 1 = союзник)
                team_feature = 0.0 if unit.team != hero.team else 1.0
                
                # HP нормализованный
                hp_feature = self.normalize_value(unit.health, 0, 2000)
                
                # Дистанция нормализованная
                dist_feature = self.normalize_value(dist, 0, 2000)
                
                # Это герой
                is_hero_feature = 1.0 if unit.is_hero else 0.0
                
                features.extend([team_feature, hp_feature, dist_feature, is_hero_feature])
            else:
                # Заполняем нулями
                features.extend([0.0, 0.0, 0.0, 0.0])
        
        return np.array(features, dtype=np.float32)
    
    def generate_state_vector(self, game_state: GameState) -> np.ndarray:
        """
        Генерирует полный вектор состояния.
        
        Returns:
            numpy массив формы (vector_size,)
        """
        features = []
        
        # 1. Состояние героя (9 признаков)
        hero_features = self.encode_hero_state(game_state.my_hero)
        features.extend(hero_features)
        
        # 2. Уровни способностей (4 признака)
        ability_features = self.encode_abilities(game_state.abilities)
        features.extend(ability_features)
        
        # 3. Инвентарь
        inventory_features = self.encode_inventory(
            game_state.inventory, 
            use_one_hot=self.include_one_hot_inventory
        )
        features.extend(inventory_features)
        
        # 4. Ближайшие юниты (20 признаков)
        nearby_features = self.encode_nearby_units(
            game_state.my_hero,
            game_state.nearby_units
        )
        features.extend(nearby_features)
        
        return np.array(features, dtype=np.float32)
    
    def generate_state_tensor(self, game_states: List[GameState]) -> np.ndarray:
        """
        Генерирует батч векторов состояния для PyTorch.
        
        Returns:
            numpy массив формы (batch_size, vector_size)
        """
        vectors = [self.generate_state_vector(gs) for gs in game_states]
        return np.stack(vectors, axis=0)
    
    def get_vector_info(self) -> Dict:
        """Возвращает информацию о структуре вектора."""
        return {
            'total_size': self.vector_size,
            'hero_features': 7,
            'ability_features': 4,
            'inventory_features': MAX_INVENTORY * MAX_ITEMS if self.include_one_hot_inventory else MAX_INVENTORY,
            'nearby_units_features': MAX_NEARBY_UNITS * 4,
            'include_one_hot': self.include_one_hot_inventory
        }


def demo():
    """Демонстрация использования."""
    print("=" * 60)
    print("State Vector Generator Demo")
    print("=" * 60)
    
    # Создаём генератор
    generator = StateVectorGenerator(include_one_hot_inventory=False)
    
    print(f"\nВектор состояния:")
    print(f"  Размер: {generator.vector_size}")
    print(f"  Структура: {generator.get_vector_info()}")
    
    # Создаём тестовое состояние игры
    test_hero = HeroState(
        hero_id=30,  # Witch doctor
        pos_x=7000.0,
        pos_y=5000.0,
        health=800.0,
        max_health=1000.0,
        mana=350.0,
        max_mana=500.0,
        level=15,
        gold=1500,
        net_worth=20000,
        team=0
    )
    
    test_units = [
        UnitState("hero", 39, 1, 7200.0, 5100.0, 600.0, 1000.0, True),  # Вражеский герой
        UnitState("creep", 100, 0, 6900.0, 4900.0, 300.0, 500.0, False),   # Союзный крип
        UnitState("creep", 101, 1, 7100.0, 5050.0, 250.0, 500.0, False), # Вражеский крип
        UnitState("tower", 200, 1, 7500.0, 5000.0, 3000.0, 3000.0, False), # Башня
        UnitState("hero", 87, 1, 7300.0, 5200.0, 500.0, 800.0, True),   # Вражеский герой
        UnitState("creep", 102, 0, 6800.0, 4800.0, 400.0, 500.0, False), # Союзный крип
    ]
    
    test_game_state = GameState(
        tick=45000,
        my_hero=test_hero,
        nearby_units=test_units,
        inventory=[1, 180, 116, 37, 123, 36],  # Item IDs
        abilities={
            'witch_doctor_paralyzing_cask': 4,
            'witch_doctor_voodoo_restoration': 3,
            'witch_doctor_maledict': 2,
            'witch_doctor_death_ward': 1
        }
    )
    
    # Генерируем вектор
    vector = generator.generate_state_vector(test_game_state)
    
    print(f"\nПример вектора состояния:")
    print(f"  Форма: {vector.shape}")
    print(f"  Первые 10 значений: {vector[:10]}")
    print(f"  Значения в диапазоне [0, 1]: {np.all((vector >= 0) & (vector <= 1))}")
    
    # Генерируем батч
    batch = generator.generate_state_tensor([test_game_state, test_game_state])
    print(f"\nБатч:")
    print(f"  Форма: {batch.shape}")
    
    # Для PyTorch
    print(f"\nДля PyTorch:")
    print(f"  import torch")
    print(f"  state_tensor = torch.from_numpy(state_vector).unsqueeze(0)  # Shape: (1, {generator.vector_size})")


if __name__ == "__main__":
    demo()
