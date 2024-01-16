#!/usr/bin/python
import requests
import time
import sys
import json

API = "https://service.lisk.io/api/v3/"
EP = "pos/validators?address="


cfile = 'config.json'
if len(sys.argv) == 2:
	cfile = sys.argv[1]

f = open(cfile, 'r')
conf = json.loads(f.read())


prevConsec = 0

def alert(cons):
    if cons > 0:
        text = f"Consecutive missed block increased to {cons}"
    else:
        text = f"Missed blocks come back to zero"
    d = requests.get('https://api.telegram.org/bot%s/sendMessage?text=%s&chat_id=%s' %
						 (conf['telegramApi'], text, conf['chatId'])).json()

while True:
    print ('monitor running')
    r = requests.get(API + EP + conf['address']).json()['data'][0]
    if r['consecutiveMissedBlocks'] > prevConsec:
        alert(r['consecutiveMissedBlocks'])
    if r['consecutiveMissedBlocks'] == 0 and prevConsec > 0:
        alert(0)
    
    prevConsec = r['consecutiveMissedBlocks']
        
    time.sleep(60)