# -*- coding: utf-8 -*-
"""
train_v2.py - Deep Training for Dota 2 AI (GPU OPTIMIZED)
3 LSTM layers, 256 units, 30 epochs, full data, BATCH=1024
"""
import os
# Заставляем систему считать, что у нас архитектура Hopper (от 4090), 
# но добавляем +PTX, чтобы драйвер сам допилил код под Blackwell (5060 Ti)
os.environ['TORCH_CUDA_ARCH_LIST'] = "9.0+PTX"
os.environ['CUDA_LAUNCH_BLOCKING'] = "1"

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import os

# Configuration - GPU OPTIMIZED
SEQ_LENGTH = 20
EPOCHS = 30
BATCH_SIZE = 1024  # 16GB VRAM = big batch!
LEARNING_RATE = 0.001
MODEL_PATH = "models/dota_ai_v2.pth"
LOSS_PATH = "models/training_loss_v2.txt"

# Device - FORCE CUDA
device = torch.device("cuda")
print(f"Using device: {device}")
print(f"Current GPU: {torch.cuda.get_device_name(0)}")
print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")


class DotaDataset(Dataset):
    def __init__(self, sequences, targets):
        self.sequences = torch.FloatTensor(sequences)
        self.targets = torch.FloatTensor(targets)
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.targets[idx]


class DotaLSTMDeep(nn.Module):
    """Deep LSTM with 3 layers and 256 units"""
    def __init__(self, input_size=10, hidden_size=256, num_layers=3, output_size=2, dropout=0.3):
        super(DotaLSTMDeep, self).__init__()
        self.lstm1 = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
        self.dropout = nn.Dropout(dropout)
        self.fc1 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc2 = nn.Linear(hidden_size // 2, output_size)
        self.relu = nn.ReLU()
    
    def forward(self, x):
        out, _ = self.lstm1(x)
        out = self.dropout(out)
        out = self.fc1(out[:, -1, :])
        out = self.relu(out)
        out = self.fc2(out)
        return out


def load_and_preprocess_data(csv_path):
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Total records: {len(df)}")
    
    # Extended features with acceleration
    feature_cols = ['x', 'y', 'vx', 'vy', 'ax', 'ay', 'hp_pct', 'mana_pct', 'enemy_near', 'under_tower']
    
    # Check if ax/ay exist, if not calculate them
    if 'ax' not in df.columns or 'ay' not in df.columns:
        print("Calculating acceleration from velocity...")
        df = df.sort_values(['player_id', 'match_id', 'tick'])
        df['vx_prev'] = df.groupby(['player_id', 'match_id'])['vx'].shift(1).fillna(0)
        df['vy_prev'] = df.groupby(['player_id', 'match_id'])['vy'].shift(1).fillna(0)
        df['ax'] = df['vx'] - df['vx_prev']
        df['ay'] = df['vy'] - df['vy_prev']
        df['ax'] = df['ax'].fillna(0).clip(-50, 50)
        df['ay'] = df['ay'].fillna(0).clip(-50, 50)
    
    sequences = []
    targets = []
    
    for player_id in df['player_id'].unique():
        player_df = df[df['player_id'] == player_id].sort_values(['match_id', 'tick'])
        features = player_df[feature_cols].values.astype(np.float32)
        features = np.nan_to_num(features, 0.0)
        
        # Normalize
        features[:, 0] = (features[:, 0] + 8500) / 17000  # x
        features[:, 1] = (features[:, 1] + 8500) / 17000  # y
        features[:, 2] = (features[:, 2] + 100) / 200  # vx
        features[:, 3] = (features[:, 3] + 100) / 200  # vy
        features[:, 4] = (features[:, 4] + 50) / 100  # ax
        features[:, 5] = (features[:, 5] + 50) / 100  # ay
        
        for i in range(len(features) - SEQ_LENGTH):
            sequences.append(features[i:i + SEQ_LENGTH])
            targets.append(features[i + SEQ_LENGTH, :2])
    
    sequences = np.array(sequences, dtype=np.float32)
    targets = np.array(targets, dtype=np.float32)
    
    print(f"Created {len(sequences)} sequences (FULL DATASET)")
    return sequences, targets


def train_model(model, train_loader, criterion, optimizer, scheduler, num_epochs):
    losses = []
    for epoch in range(num_epochs):
        model.train()
        epoch_loss = 0
        num_batches = 0
        
        for sequences, targets in train_loader:
            sequences = sequences.to(device)
            targets = targets.to(device)
            
            outputs = model(sequences)
            loss = criterion(outputs, targets)
            
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            
            epoch_loss += loss.item()
            num_batches += 1
        
        avg_loss = epoch_loss / num_batches
        losses.append(avg_loss)
        scheduler.step(avg_loss)
        
        print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {avg_loss:.6f}, LR: {optimizer.param_groups[0]['lr']:.6f}")
    
    return losses


def main():
    print("=" * 70)
    print("DOTA 2 AI - DEEP TRAINING v2 (GPU)")
    print("3 LSTM layers, 256 units, 30 epochs, FULL data")
    print("=" * 70)
    
    sequences, targets = load_and_preprocess_data("data/processed/master_dataset_v2.csv")
    
    train_dataset = DotaDataset(sequences, targets)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0, pin_memory=True)
    
    model = DotaLSTMDeep(input_size=10, hidden_size=256, num_layers=3, output_size=2, dropout=0.3)
    model = model.to(device)
    
    print(f"\nModel created: 3 LSTM layers, 256 units")
    
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)
    
    print("\n" + "=" * 70)
    print("STARTING DEEP TRAINING ON GPU")
    print("=" * 70)
    print(f"Epochs: {EPOCHS}, Batch Size: {BATCH_SIZE}, Data: {len(train_dataset)} samples")
    print()
    
    losses = train_model(model, train_loader, criterion, optimizer, scheduler, EPOCHS)
    
    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")
    
    with open(LOSS_PATH, 'w') as f:
        for i, loss in enumerate(losses):
            f.write(f"Epoch {i+1}: {loss:.6f}\n")
    print(f"Loss saved to {LOSS_PATH}")
    
    print("\n" + "=" * 70)
    print("DEEP TRAINING COMPLETE!")
    print("=" * 70)
    print(f"Initial Loss: {losses[0]:.6f}")
    print(f"Final Loss: {losses[-1]:.6f}")
    print(f"Improvement: {(losses[0] - losses[-1]) / losses[0] * 100:.1f}%")


if __name__ == "__main__":
    main()