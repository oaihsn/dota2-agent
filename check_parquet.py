# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

processed_dir = Path("data/processed")

print("Checking parquet files...")
print()

for f in processed_dir.glob("*.parquet"):
    print(f"=== {f.name} ===")
    try:
        df = pd.read_parquet(f)
        print(f"Shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()[:15]}")
        print(df.head(2))
    except Exception as e:
        print(f"Error: {e}")
    print()