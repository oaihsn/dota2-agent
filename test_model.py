# -*- coding: utf-8 -*-
"""
test_model.py - Test the trained Dota 2 AI model
"""
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

# Configuration
SEQ_LENGTH = 20
MODEL_PATH = "models/dota_ai_v1.pth"

device = torch.device('cpu')


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


def denormalize_coords(x, y):
    """Convert [0,1] back to Dota 2 coordinates"""
    real_x = x * 17000 - 8500
    real_y = y * 17000 - 8500
    return real_x, real_y


def main():
    print("=" * 70)
    print("DOTA 2 AI - MODEL PREDICTION TEST")
    print("=" * 70)
    
    # Load data
    csv_path = "data/processed/master_dataset_v2.csv"
    print(f"\nLoading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Total records: {len(df)}")
    
    feature_cols = ['x', 'y', 'vx', 'vy', 'hp_pct', 'mana_pct', 'enemy_near', 'under_tower']
    
    # Prepare all sequences
    all_data = []
    for player_id in df['player_id'].unique():
        player_df = df[df['player_id'] == player_id].sort_values(['match_id', 'tick'])
        features = player_df[feature_cols].values.astype(np.float32)
        features = np.nan_to_num(features, 0.0)
        
        # Normalize
        features[:, 0] = (features[:, 0] + 8500) / 17000
        features[:, 1] = (features[:, 1] + 8500) / 17000
        features[:, 2] = (features[:, 2] + 100) / 200
        features[:, 3] = (features[:, 3] + 100) / 200
        
        hero_names = player_df['hero_name'].values
        player_ids = player_df['player_id'].values
        
        for i in range(len(features) - SEQ_LENGTH):
            all_data.append({
                'seq': features[i:i + SEQ_LENGTH],
                'target': features[i + SEQ_LENGTH, :2],
                'hero': hero_names[i + SEQ_LENGTH],
                'player_id': player_ids[i + SEQ_LENGTH]
            })
    
    print(f"Total sequences: {len(all_data)}")
    
    # Load model
    print(f"\nLoading model from {MODEL_PATH}...")
    model = DotaLSTM(input_size=8, hidden_size=128, num_layers=2, output_size=2, dropout=0.2)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.eval()
    print("Model loaded successfully!")
    
    # Select 5 random sequences from the end (more recent game state)
    np.random.seed(42)
    end_idx = len(all_data) - 5000  # Last 5000 sequences
    start_idx = max(0, end_idx)
    sample_indices = np.random.choice(range(start_idx, len(all_data)), 5, replace=False)
    
    print("\n" + "=" * 70)
    print("PREDICTION RESULTS")
    print("=" * 70)
    print(f"{'Hero':<15} {'Actual (X, Y)':<25} {'Predicted (X, Y)':<25} {'Error':<10}")
    print("-" * 70)
    
    total_error = 0
    
    for idx in sample_indices:
        data = all_data[idx]
        seq = torch.FloatTensor(data['seq']).unsqueeze(0).to(device)
        
        # Predict
        with torch.no_grad():
            pred = model(seq).cpu().numpy()[0]
        
        # Actual
        actual = data['target']
        
        # Denormalize
        actual_x, actual_y = denormalize_coords(actual[0], actual[1])
        pred_x, pred_y = denormalize_coords(pred[0], pred[1])
        
        # Calculate error distance
        error = np.sqrt((actual_x - pred_x)**2 + (actual_y - pred_y)**2)
        total_error += error
        
        print(f"{data['hero']:<15} ({actual_x:>8.1f}, {actual_y:>8.1f})    ({pred_x:>8.1f}, {pred_y:>8.1f})    {error:>6.1f}")
    
    avg_error = total_error / 5
    
    print("-" * 70)
    print(f"\nAverage Error Distance: {avg_error:.1f} units")
    print(f"Model Accuracy: {'EXCELLENT' if avg_error < 100 else 'GOOD' if avg_error < 200 else 'NEEDS MORE TRAINING'}")
    
    if avg_error < 100:
        print("\n🎉 AI is ready for Real-Time Overlay!")
    elif avg_error < 200:
        print("\n👍 AI is working, but needs more training data.")
    else:
        print("\n⚠️ AI needs more training or better features.")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()