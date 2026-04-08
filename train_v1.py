# -*- coding: utf-8 -*-
"""
train_v1.py - LSTM Model for Dota 2 Hero Movement Prediction
OPTIMIZED VERSION: 10 epochs, 50% data, batch=256
"""
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import os

# Configuration - OPTIMIZED FOR SPEED
SEQ_LENGTH = 20
EPOCHS = 10
BATCH_SIZE = 256  # Increased from 64
LEARNING_RATE = 0.001
MODEL_PATH = "models/dota_ai_v1.pth"
PLOT_PATH = "models/training_loss.txt"
DATA_SAMPLE = 0.5  # Use only 50% of data

device = torch.device('cpu')
print(f"Using device: {device}")


class DotaDataset(Dataset):
    def __init__(self, sequences, targets):
        self.sequences = torch.FloatTensor(sequences)
        self.targets = torch.FloatTensor(targets)
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.targets[idx]


class DotaLSTM(nn.Module):
    def __init__(self, input_size=8, hidden_size=128, num_layers=2, output_size=2, dropout=0.2):
        super(DotaLSTM, self).__init__()
        self.lstm1 = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        out, _ = self.lstm1(x)
        out = self.dropout(out)
        out = self.fc(out[:, -1, :])
        return out


def load_and_preprocess_data(csv_path):
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Total records: {len(df)}")
    
    feature_cols = ['x', 'y', 'vx', 'vy', 'hp_pct', 'mana_pct', 'enemy_near', 'under_tower']
    sequences = []
    targets = []
    
    for player_id in df['player_id'].unique():
        player_df = df[df['player_id'] == player_id].sort_values(['match_id', 'tick'])
        features = player_df[feature_cols].values.astype(np.float32)
        features = np.nan_to_num(features, 0.0)
        
        # Normalize
        features[:, 0] = (features[:, 0] + 8500) / 17000
        features[:, 1] = (features[:, 1] + 8500) / 17000
        features[:, 2] = (features[:, 2] + 100) / 200
        features[:, 3] = (features[:, 3] + 100) / 200
        
        for i in range(len(features) - SEQ_LENGTH):
            sequences.append(features[i:i + SEQ_LENGTH])
            targets.append(features[i + SEQ_LENGTH, :2])
    
    sequences = np.array(sequences, dtype=np.float32)
    targets = np.array(targets, dtype=np.float32)
    
    # Sample 50% of data for speed
    if DATA_SAMPLE < 1.0:
        n_samples = int(len(sequences) * DATA_SAMPLE)
        indices = np.random.choice(len(sequences), n_samples, replace=False)
        sequences = sequences[indices]
        targets = targets[indices]
        print(f"Sampled {n_samples} sequences (50%)")
    
    print(f"Created {len(sequences)} sequences")
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
        scheduler.step()
        
        print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {avg_loss:.6f}")
    
    return losses


def main():
    print("=" * 70)
    print("DOTA 2 AI - OPTIMIZED TRAINING (10 epochs, 50% data, batch=256)")
    print("=" * 70)
    
    sequences, targets = load_and_preprocess_data("data/processed/master_dataset_v2.csv")
    
    train_dataset = DotaDataset(sequences, targets)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    
    model = DotaLSTM(input_size=8, hidden_size=128, num_layers=2, output_size=2, dropout=0.2)
    model = model.to(device)
    
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)
    
    print("\n" + "=" * 70)
    print("STARTING TRAINING")
    print("=" * 70)
    print(f"Epochs: {EPOCHS}, Batch Size: {BATCH_SIZE}, Data: {len(train_dataset)} samples")
    print()
    
    losses = train_model(model, train_loader, criterion, optimizer, scheduler, EPOCHS)
    
    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")
    
    # Save loss
    with open(PLOT_PATH, 'w') as f:
        for i, loss in enumerate(losses):
            f.write(f"Epoch {i+1}: {loss:.6f}\n")
    print(f"Loss saved to {PLOT_PATH}")
    
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE!")
    print("=" * 70)
    print(f"Initial Loss: {losses[0]:.6f}")
    print(f"Final Loss: {losses[-1]:.6f}")
    print(f"Improvement: {(losses[0] - losses[-1]) / losses[0] * 100:.1f}%")


if __name__ == "__main__":
    main()