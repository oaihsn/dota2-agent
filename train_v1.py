# -*- coding: utf-8 -*-
"""
train_v1.py - LSTM Model for Dota 2 Hero Movement Prediction

This script trains an LSTM model to predict the next position of a hero
based on the last 20 ticks of game state.

Features: x, y, vx, vy, hp_pct, mana_pct, enemy_near, tower_near
Output: Predicted X, Y for the next tick
"""
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import os

# Configuration
SEQ_LENGTH = 20  # Last 20 ticks
BATCH_SIZE = 64
EPOCHS = 50
LEARNING_RATE = 0.001
MODEL_PATH = "models/dota_ai_v1.pth"
PLOT_PATH = "models/training_loss.png"

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")


class DotaDataset(Dataset):
    """Dataset for Dota 2 hero movement sequences."""
    
    def __init__(self, sequences, targets):
        self.sequences = torch.FloatTensor(sequences)
        self.targets = torch.FloatTensor(targets)
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.targets[idx]


class DotaLSTM(nn.Module):
    """LSTM model for hero movement prediction."""
    
    def __init__(self, input_size=8, hidden_size=128, num_layers=2, output_size=2, dropout=0.2):
        super(DotaLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm1 = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
        self.lstm2 = nn.LSTM(hidden_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        out, _ = self.lstm1(x)
        out = self.dropout(out)
        out, _ = self.lstm2(out)
        out = self.dropout(out)
        
        # Take the output from the last time step
        out = self.fc(out[:, -1, :])
        return out


def load_and_preprocess_data(csv_path):
    """Load and preprocess the data."""
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"Total records: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # Features to use
    feature_cols = ['x', 'y', 'vx', 'vy', 'hp_pct', 'mana_pct', 'enemy_near', 'under_tower']
    
    # Normalize coordinates: range [-8500, 8500] -> [0, 1]
    # We'll scale them after loading
    
    # Group by player to keep movement paths continuous
    sequences = []
    targets = []
    
    for player_id in df['player_id'].unique():
        player_df = df[df['player_id'] == player_id].sort_values(['match_id', 'tick'])
        
        # Scale data for this player
        scaler_x = MinMaxScaler(feature_range=(0, 1))
        scaler_y = MinMaxScaler(feature_range=(0, 1))
        
        # Prepare features
        features = player_df[feature_cols].values.astype(np.float32)
        
        # Handle missing values
        features = np.nan_to_num(features, 0.0)
        
        # Normalize x, y separately (they have different ranges)
        # Scale coordinates to [0, 1] assuming range [-8500, 8500]
        features[:, 0] = (features[:, 0] + 8500) / 17000  # x
        features[:, 1] = (features[:, 1] + 8500) / 17000  # y
        
        # vx, vy range is similar, scale by same factor
        features[:, 2] = (features[:, 2] + 100) / 200  # vx
        features[:, 3] = (features[:, 3] + 100) / 200  # vy
        
        # hp, mana are already [0, 1]
        
        # Create sequences
        for i in range(len(features) - SEQ_LENGTH):
            seq = features[i:i + SEQ_LENGTH]
            # Target: next x, y (already scaled)
            target = features[i + SEQ_LENGTH, :2]  # x, y
            
            sequences.append(seq)
            targets.append(target)
    
    sequences = np.array(sequences, dtype=np.float32)
    targets = np.array(targets, dtype=np.float32)
    
    print(f"Created {len(sequences)} sequences")
    print(f"Features shape: {sequences.shape}")
    print(f"Targets shape: {targets.shape}")
    
    return sequences, targets


def train_model(model, train_loader, criterion, optimizer, scheduler, num_epochs):
    """Train the model."""
    losses = []
    
    for epoch in range(num_epochs):
        model.train()
        epoch_loss = 0
        num_batches = 0
        
        for batch_idx, (sequences, targets) in enumerate(train_loader):
            sequences = sequences.to(device)
            targets = targets.to(device)
            
            # Forward pass
            outputs = model(sequences)
            loss = criterion(outputs, targets)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            
            epoch_loss += loss.item()
            num_batches += 1
            
            # Print batch progress
            if (batch_idx + 1) % 50 == 0:
                print(f"  Epoch [{epoch+1}/{num_epochs}], Batch [{batch_idx+1}/{len(train_loader)}], Loss: {loss.item():.6f}")
        
        # Average loss for epoch
        avg_loss = epoch_loss / num_batches
        losses.append(avg_loss)
        
        # Learning rate scheduler
        scheduler.step()
        
        print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {avg_loss:.6f}, LR: {optimizer.param_groups[0]['lr']:.6f}")
    
    return losses


def plot_training_loss(losses, save_path):
    """Plot and save the training loss."""
    plt.figure(figsize=(10, 6))
    plt.plot(losses, label='Training Loss', linewidth=2)
    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('Loss (MSE)', fontsize=12)
    plt.title('Dota 2 AI Training Loss', fontsize=14)
    plt.legend()
    plt.grid(True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"Training loss plot saved to {save_path}")
    plt.close()


def main():
    print("=" * 70)
    print("DOTA 2 HERO MOVEMENT PREDICTION - LSTM MODEL")
    print("=" * 70)
    print()
    
    # Load data
    csv_path = "data/processed/master_dataset_v2.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found!")
        return
    
    sequences, targets = load_and_preprocess_data(csv_path)
    
    # Split data
    train_size = int(0.8 * len(sequences))
    train_sequences = sequences[:train_size]
    train_targets = targets[:train_size]
    
    print(f"Training samples: {len(train_sequences)}")
    
    # Create dataset and dataloader
    train_dataset = DotaDataset(train_sequences, train_targets)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    
    # Create model
    model = DotaLSTM(input_size=8, hidden_size=128, num_layers=2, output_size=2, dropout=0.2)
    model = model.to(device)
    
    print(f"\nModel Architecture:")
    print(model)
    
    # Loss and optimizer
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)
    
    # Train
    print("\n" + "=" * 70)
    print("STARTING TRAINING")
    print("=" * 70)
    print(f"Epochs: {EPOCHS}")
    print(f"Batch Size: {BATCH_SIZE}")
    print(f"Learning Rate: {LEARNING_RATE}")
    print(f"Sequence Length: {SEQ_LENGTH}")
    print()
    
    losses = train_model(model, train_loader, criterion, optimizer, scheduler, EPOCHS)
    
    # Save model
    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")
    
    # Plot training loss
    plot_training_loss(losses, PLOT_PATH)
    
    # Final loss
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)
    print(f"Final Loss: {losses[-1]:.6f}")
    print(f"Initial Loss: {losses[0]:.6f}")
    print(f"Improvement: {(losses[0] - losses[-1]) / losses[0] * 100:.2f}%")
    print(f"\nModel saved to: {MODEL_PATH}")
    print(f"Plot saved to: {PLOT_PATH}")
    print("\nDone!")


if __name__ == "__main__":
    main()