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
    d = requests.get('https://api.telegram.org/bot%s/sendMessage?text=%s&chat_id=%s' %
						 (conf['telegramApi'], f"Consecutive missed block increased to {cons}", conf['chatId'])).json()

while True:
    r = requests.get(API + EP + conf['address']).json()['data'][0]
    if r['consecutiveMissedBlocks'] > prevConsec:
        alert(r['consecutiveMissedBlocks'])
    
    prevConsec = r['consecutiveMissedBlocks']
        
    time.sleep(60)