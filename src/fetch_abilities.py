# -*- coding: utf-8 -*-
import json

# Load abilities from OpenDota
with open('data/abilities_temp.json', 'r', encoding='utf-8') as f:
    abilities_data = json.load(f)

# Convert to {id: name} format
abilities = {}
for key, value in abilities_data.items():
    if isinstance(value, dict):
        # Use 'dname' for display name
        dname = value.get('dname', '')
        if dname:
            abilities[key] = dname

# Save
with open('data/abilities.json', 'w', encoding='utf-8') as f:
    json.dump(abilities, f, indent=2, ensure_ascii=False)

print(f'Saved {len(abilities)} abilities to abilities.json')

# Show sample
print()
print('Sample abilities:')
for i, (aid, aname) in enumerate(list(abilities.items())[:10]):
    print(f'  {aid}: {aname}')
