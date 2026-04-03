# -*- coding: utf-8 -*-
"""
Пример использования StateVectorGenerator с PyTorch.
"""
import torch
import torch.nn as nn
import numpy as np
from state_vector import StateVectorGenerator, HeroState, UnitState, GameState


class SimpleDotaAgent(nn.Module):
    """Простая нейросеть для Dota 2 агента."""
    
    def __init__(self, state_size: int, action_size: int = 10):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(state_size, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, action_size)
        )
    
    def forward(self, x):
        return self.network(x)


def main():
    print("=" * 60)
    print("PyTorch Dota 2 Agent Example")
    print("=" * 60)
    
    # Создаём генератор вектора состояния
    generator = StateVectorGenerator(include_one_hot_inventory=False)
    state_size = generator.vector_size
    
    print(f"\nState Size: {state_size}")
    
    # Создаём модель
    model = SimpleDotaAgent(state_size=state_size, action_size=10)
    print(f"\nModel Architecture:")
    print(model)
    
    # Подсчёт параметров
    total_params = sum(p.numel() for p in model.parameters())
    print(f"\nTotal parameters: {total_params:,}")
    
    # Создаём тестовое состояние
    test_hero = HeroState(
        hero_id=30,
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
        UnitState("hero", 39, 1, 7200.0, 5100.0, 600.0, 1000.0, True),
        UnitState("creep", 100, 0, 6900.0, 4900.0, 300.0, 500.0, False),
        UnitState("creep", 101, 1, 7100.0, 5050.0, 250.0, 500.0, False),
        UnitState("tower", 200, 1, 7500.0, 5000.0, 3000.0, 3000.0, False),
        UnitState("hero", 87, 1, 7300.0, 5200.0, 500.0, 800.0, True),
    ]
    
    test_game_state = GameState(
        tick=45000,
        my_hero=test_hero,
        nearby_units=test_units,
        inventory=[1, 180, 116, 37, 123, 36],
        abilities={
            'witch_doctor_paralyzing_cask': 4,
            'witch_doctor_voodoo_restoration': 3,
            'witch_doctor_maledict': 2,
            'witch_doctor_death_ward': 1
        }
    )
    
    # Генерируем вектор
    state_vector = generator.generate_state_vector(test_game_state)
    print(f"\nState vector shape: {state_vector.shape}")
    
    # Конвертируем в PyTorch tensor
    state_tensor = torch.FloatTensor(state_vector).unsqueeze(0)  # Shape: (1, 37)
    print(f"State tensor shape: {state_tensor.shape}")
    
    # Forward pass
    model.eval()
    with torch.no_grad():
        action_logits = model(state_tensor)
        action_probs = torch.softmax(action_logits, dim=-1)
    
    print(f"\nAction logits: {action_logits}")
    print(f"Action probabilities: {action_probs}")
    
    # Выбираем действие
    action = torch.argmax(action_probs, dim=-1).item()
    actions = ['Move', 'Attack', 'Cast Q', 'Cast W', 'Cast E', 'Cast R', 'Use Item 1', 'Use Item 2', 'Use Item 3', 'Use Item 4']
    print(f"\nSelected action: {actions[action]}")
    
    # Пример батча для обучения
    print("\n" + "=" * 60)
    print("Batch Training Example")
    print("=" * 60)
    
    # Создаём батч из 32 состояний
    batch_size = 32
    batch_vectors = generator.generate_state_tensor([test_game_state] * batch_size)
    batch_tensor = torch.FloatTensor(batch_vectors)  # Shape: (32, 37)
    
    print(f"Batch tensor shape: {batch_tensor.shape}")
    
    # Forward pass для батча
    with torch.no_grad():
        batch_logits = model(batch_tensor)  # Shape: (32, 10)
        batch_probs = torch.softmax(batch_logits, dim=-1)
    
    print(f"Batch logits shape: {batch_logits.shape}")
    print(f"Batch probs shape: {batch_probs.shape}")


if __name__ == "__main__":
    main()
