# -*- coding: utf-8 -*-
"""
Generate training data from existing parsed parquet files.
The project already has the demo parsed - we just need to filter it!
"""
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.absolute()
DATA_PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

print("=" * 60)
print("GENERATING TRAINING DATA FROM PARSED PARQUET FILES")
print("=" * 60)

# Load the replay data (contains tick-level position data!)
replay_file = DATA_PROCESSED_DIR / "replay_8749329335.parquet"
df = pd.read_parquet(replay_file)

print(f"\nLoaded replay data:")
print(f"  Shape: {df.shape}")
print(f"  Ticks: {df['tick'].min()} to {df['tick'].max()}")
print(f"  Unique ticks: {df['tick'].nunique()}")

# Filter to interval (every 30 ticks ~ 1 second)
interval = 30
df_filtered = df[df['tick'] % interval == 0].copy()

print(f"\nFiltered to every {interval} ticks:")
print(f"  Shape: {df_filtered.shape}")
print(f"  Ticks: {df_filtered['tick'].nunique()}")

# Prepare training data - select relevant columns
training_cols = ['tick', 'player_slot', 'team', 'pos_x', 'pos_y', 
                 'health', 'mana', 'level', 'gold', 'net_worth',
                 'hero_id', 'hero_name']

# Verify columns exist
available_cols = [c for c in training_cols if c in df_filtered.columns]
print(f"\nUsing columns: {available_cols}")

df_training = df_filtered[available_cols].copy()

# No max_health in data, skip health_pct calculation

# Create state vector format
# We need: tick, hero_id, team, pos_x, pos_y, health, mana, level, gold, net_worth
print(f"\nTraining data sample:")
print(df_training.head(20))

# Save to CSV
output_file = DATA_PROCESSED_DIR / "training_data_from_replay.csv"
df_training.to_csv(output_file, index=False)

print(f"\n=== SAVED ===")
print(f"Training data: {output_file}")
print(f"Total records: {len(df_training)}")

# Show stats by team
print("\n=== STATS BY TEAM ===")
print(df_training.groupby('team')[['pos_x', 'pos_y', 'health', 'gold', 'net_worth']].mean())

# Show tick distribution
print("\n=== TICKS SAMPLED ===")
print(f"Sample ticks: {sorted(df_training['tick'].unique())[:10]}...")

print("\nDone!")