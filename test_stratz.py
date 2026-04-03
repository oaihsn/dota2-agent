# -*- coding: utf-8 -*-
import cloudscraper, json

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiNTUxNjZkNTAtOTY0MS00MmU1LWEyMjQtMjZlMDcyNWE1YTAwIiwiU3RlYW1JZCI6IjEwNzg4MDI5ODEiLCJBUElVc2VyIjoidHJ1ZSIsIm5iZiI6MTc3MTE2MDYwMiwiZXhwIjoxODAyNjk2NjAyLCJpYXQiOjE3NzExNjA2MDIsImlzcyI6Imh0dHBzOi8vYXBpLnN0cmF0ei5jb20ifQ.VPrAkCuJ4KlttFGGtae09_LoQk91GkR4vEaybt6X3iM'

scraper = cloudscraper.create_scraper()

# Get match data
print('Fetching match...')
r = scraper.get('https://api.stratz.com/api/v1/match/8749329335', 
                 headers={'Authorization': 'Bearer ' + token}, 
                 timeout=60)
print('Status:', r.status_code)

if r.status_code == 200:
    data = r.json()
    print('Match ID:', data.get('id'))
    print('Duration:', data.get('durationSeconds'))
    print('Players:', len(data.get('players', [])))
    
    # Save
    with open(r'C:\Users\User\Desktop\dota2agent\dota2-agent\data\stratz_match.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print('Saved!')
else:
    print('Error:', r.text[:500])
