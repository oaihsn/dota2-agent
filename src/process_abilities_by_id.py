# -*- coding: utf-8 -*-
import json

# Load abilities from OpenDota
with open('data/abilities_by_id.json', 'r', encoding='utf-8') as f:
    abilities_data = json.load(f)

# Find abilities that have 'id' field
abilities_by_id = {}
for key, value in abilities_data.items():
    if isinstance(value, dict):
        aid = value.get('id')
        dname = value.get('dname', '')
        if aid and dname:
            abilities_by_id[int(aid)] = dname

# Save
with open('data/abilities_by_id.json', 'w', encoding='utf-8') as f:
    json.dump(abilities_by_id, f, indent=2, ensure_ascii=False)

print(f'Saved {len(abilities_by_id)} abilities with ID to abilities_by_id.json')

# Show sample
print()
print('Sample abilities:')
for i, (aid, aname) in enumerate(list(abilities_by_id.items())[:10]):
    print(f'  {aid}: {aname}')

# Test mapping for a specific ability
print()
print('Test mapping:')
for test_id in [5016, 5175, 5518, 5339, 5458]:
    print(f'  {test_id}: {abilities_by_id.get(test_id, "Unknown")}')
