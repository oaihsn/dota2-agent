# -*- coding: utf-8 -*-
import json
import cloudscraper

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiNTUxNjZkNTAtOTY0MS00MmU1LWEyMjQtMjZlMDcyNWE1YTAwIiwiU3RlYW1JZCI6IjEwNzg4MDI5ODEiLCJBUElVc2VyIjoidHJ1ZSIsIm5iZiI6MTc3MTE2MDYwMiwiZXhwIjoxODAyNjk2NjAyLCJpYXQiOjE3NzExNjA2MDIsImlzcyI6Imh0dHBzOi8vYXBpLnN0cmF0ei5jb20ifQ.VPrAkCuJ4KlttFGGtae09_LoQk91GkR4vEaybt6X3iM'

s = cloudscraper.create_scraper()
r = s.get('https://api.stratz.com/api/v1/match/8749329335', 
           headers={'Authorization': 'Bearer ' + token}, 
           timeout=60)

if r.status_code == 200:
    data = r.json()
    
    print('=== STRATZ MATCH DATA ===')
    print('Top keys:', list(data.keys()))
    
    # Check for gold_reasons, xp_reasons, times
    gold_keys = [k for k in data.keys() if 'gold' in k.lower()]
    xp_keys = [k for k in data.keys() if 'xp' in k.lower()]
    time_keys = [k for k in data.keys() if 'time' in k.lower()]
    
    print('\nGold-related:', gold_keys)
    print('XP-related:', xp_keys)
    print('Time-related:', time_keys)
    
    # Check players
    if data.get('players'):
        p = data['players'][0]
        print('\nPlayer keys:', list(p.keys()))
        
        # Check for gold_reasons, etc in player
        p_gold = [k for k in p.keys() if 'gold' in k.lower()]
        p_xp = [k for k in p.keys() if 'xp' in k.lower()]
        p_time = [k for k in p.keys() if 'time' in k.lower()]
        
        print('\nPlayer gold:', p_gold)
        print('Player xp:', p_xp)
        print('Player time:', p_time)
else:
    print('Error:', r.status_code, r.text[:200])
