from demoparser2 import DemoParser

print("Testing demoparser2 v0.41.1...")

p = DemoParser('data/raw/8749329335.dem')
print("Parser created")

# Try with very few ticks first
print("\nTrying parse_ticks with tick filter:")
try:
    ticks = p.parse_ticks(['m_nTick'], ticks=[0, 1, 2, 3, 4, 5])
    print(f"Ticks: {len(ticks)}")
    print(ticks.head())
except Exception as e:
    print(f"Error: {e}")

# Try player info 
print("\nTrying parse_player_info:")
try:
    info = p.parse_player_info()
    print(f"Players: {len(info)}")
    print(info.head())
except Exception as e:
    print(f"Error: {e}")