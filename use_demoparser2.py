# -*- coding: utf-8 -*-
"""
Dota 2 demo parser using demoparser2 - pure Python solution.
"""
import demoparser2
import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.absolute()
DATA_RAW_DIR = PROJECT_DIR / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

# Demo file
demo_file = DATA_RAW_DIR / "8749329335.dem"

print("=" * 60)
print("DEMOPARSER2 - Pure Python Dota 2 Replay Parser")
print("=" * 60)

print(f"\nParsing: {demo_file}")

try:
    # Parse the demo
    parser = demoparser2.DemoParser(str(demo_file))
    
    print(f"Parser created successfully!")
    
    # Get players
    players = parser.players()
    print(f"\nPlayers: {len(players)}")
    for p in players:
        print(f"  - {p}")
    
    # Get entity snapshots - this is the key method
    print("\nGetting entity snapshots...")
    
    # Use entity_ticks method - filter by tick interval
    # demoparser2 parses all ticks by default, we can use tick_filter
    
    # Get entities at specific intervals
    # Using None gets all entities
    entity_data = parser.entity_ticks(tick_filter=None)
    
    print(f"Entity data type: {type(entity_data)}")
    
    # Convert to pandas if it's a list of dicts
    if isinstance(entity_data, list) and len(entity_data) > 0:
        df = pd.DataFrame(entity_data)
        print(f"\nDataFrame shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()[:20]}")  # First 20 columns
        
        # Check for hero data
        # Usually in 'key' or 'classname' column
        print(f"\nFirst few rows:")
        print(df.head(3))
        
        # Look for position data
        # Common column names for positions
        pos_cols = [c for c in df.columns if 'x' in c.lower() or 'y' in c.lower() or 'pos' in c.lower()]
        print(f"\nPosition-related columns: {pos_cols}")
        
    elif hasattr(entity_data, 'to_pandas'):
        # Might be a Polars DataFrame
        print(f"Converting to pandas...")
        df = entity_data.to_pandas()
        print(f"DataFrame shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()[:20]}")
    
    # Let's try another approach - get snapshot for specific ticks
    print("\n--- Trying fixed tick intervals ---")
    
    # Fixed tick parser - get entities at specific ticks
    # demoparser2 has tick based filtering
    try:
        # Get tick info
        tick_info = parser.tick()
        print(f"Tick info: {tick_info}")
        
        # Try getting entities in chunks
        # Using entity_ticks returns list
        all_entities = parser.entity_ticks(tick_filter=list(range(0, 1000, 30)))
        print(f"Filtered entities: {len(all_entities)}")
        
        if len(all_entities) > 0:
            df = pd.DataFrame(all_entities)
            print(f"Columns: {df.columns.tolist()}")
            print(df.head())
            
    except Exception as e2:
        print(f"Tick filter approach error: {e2}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nDone!")