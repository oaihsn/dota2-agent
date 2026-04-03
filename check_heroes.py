import json

with open('data/processed/match_8749329335_full.json') as f:
    data = json.load(f)

print("Hero IDs in match:")
for p in data['players']:
    print(f"  ID {p['hero_id']} -> slot {p['player_slot']}")