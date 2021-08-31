#!/usr/bin/python
import requests
import time
import json
import sys
from datetime import datetime

f = open('config.json', 'r')
conf = json.loads(f.read())

apiToken=conf['telegramApi']
chat_id=conf['chatId']
trackedDelegates = conf['delegates']


API = "https://service.lisk.io/api/v2/"
EP = "accounts?isDelegate=true&offset=%d&limit=%d"
BLOCKTIME = 11

currentRank = {}
trackedChanges = ['isBanned', 'rank', 'consecutiveMissedBlocks', 'voteWeight']
# trackedDelegates = None

def getCountdown():
	data = requests.get(API + 'network/status').json()['data']
	togo = 16332092 - int (data['height'])
	togot = togo * BLOCKTIME / 60 / 60
	days = int(togot / 24)
	hours = int(togot % 24)

	t = time.time() + togo * BLOCKTIME	
	td = datetime.fromtimestamp(t)

	st = "%d blocks to new consensus: %d days and %d hours [%s]" % (togo, days, hours, td)
	return st

def getRank():
	border = None
	data = requests.get(API + (EP % (0, 100))).json()['data'] + requests.get(API + (EP % (100, 100))).json()['data']
	nrank = {}

	try:
		border = int(data[100]['dpos']['delegate']['voteWeight'])  / 100000000.
	except:
		pass
	
	for x in data:
		dd = x['dpos']['delegate']
		nrank[dd['username']] = dd
		
	return nrank, border
	
def checkChange(user, dataold, datanew, key):
	vold = dataold[key]
	vnew = datanew[key]

	if int(vold) != int(vnew):
		if key == 'voteWeight':
			vold = int(int(vold) / 100000000.)
			vnew = int(int(vnew) / 100000000.)

		st = ""
		if int(vnew) > int(vold):
			st = "⬆️ "
		else:
			st = "⬇️ "
		st = ('%s => Changed %s to %d (was %d)' % (user, key, vnew, vold))
		return st

	return None



notifies = []

def notify(st):
	print (st)
	d = requests.get ('https://api.telegram.org/bot%s/sendMessage?text=%s&chat_id=%s' % (apiToken, st, chat_id)).json()
	print (d)

def appendNotify(s):
	global notifies 
	notifies.append(s)

def flushNotify():
	global notifies 
	if len(notifies) > 0:
		st = '\n'.join(notifies)		
		notify(st)
		notifies = []


# notify('Starting rank monitor')
currentRank, border = getRank()

i = 1
print ("Started")
	
while True:
	if i % 1080 == 0:
		try:
			appendNotify(getCountdown())
		except:
			print ("Failed to update countdown")

	time.sleep(120)
	try:
		nrank, nborder = getRank()
	except:
		print ("Failed to update")
		continue
	
	print('.')

	if nborder != None and border != None and nborder > border:
		appendNotify(('The 101 border has increased to %d LSK (+%d)' % (nborder, nborder - border)))
		border = nborder

	if border:
		print ('Updated %d' % (border))

	for x in nrank:
		if not (x in nrank) or not (x in currentRank):
			continue

		d = nrank[x]
		od = currentRank[x]

		if trackedDelegates != None and (not (x in trackedDelegates)):
			continue

		for key in trackedChanges:
			st = checkChange(x, od, d, key)

			if st != None:
				appendNotify(st)

	currentRank = nrank
	i += 1
	sys.stdout.flush()
	flushNotify()
	
	
