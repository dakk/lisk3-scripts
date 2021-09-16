#!/usr/bin/python
import requests
import time
import json
import sys
from datetime import datetime, timedelta
import dateutil.parser

f = open('config.json', 'r')
conf = json.loads(f.read())

apiToken=conf['telegramApi']
chat_id=conf['chatId']
trackedDelegates = conf['delegates']


API = "https://service.lisk.io/api/v2/"
EP = "accounts?isDelegate=true&offset=%d&limit=%d"

currentRank = {}
trackedChanges = ['isBanned', 'rank', 'consecutiveMissedBlocks', 'voteWeight']
# trackedDelegates = None


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
		st = ""

		if key == 'voteWeight':
			vold = int(int(vold) / 100000000.)
			vnew = int(int(vnew) / 100000000.)

			if int(vnew) > int(vold):
				st = "⬆️ "
			else:
				st = "⬇️ "
		elif key == 'rank':
			if int(vnew) > int(vold):
				st = "🔴 "
			else:
				st = "🟢 "

		st += ('%s => Changed %s to %d (was %d, diff %+d)' % (user, key, vnew, vold, vnew-vold))
		return st

	return None



notifies = []

def notify(st):
	return 
	print (st.encode('utf-8'))
	d = requests.get ('https://api.telegram.org/bot%s/sendMessage?text=%s&chat_id=%s' % (apiToken, st, chat_id)).json()
	#print (d.encode('utf-8'))

def appendNotify(s):
	global notifies 
	notifies.append(s)

def flushNotify():
	global notifies 
	if len(notifies) > 0:
		st = '\n'.join(notifies)		
		notify(st)
		notifies = []

def summary():
	st = "Rank, Delegate, Weight\n"
	nrank, nborder = getRank()
	for x in nrank:
		if x in trackedDelegates:
			st += ("%d %s %d\n" % (nrank[x]['rank'], x, int(int(nrank[x]['voteWeight']) / 100000000)))
	appendNotify(st)

class BorderHistory:
	borderHistory = []
	lastborderHistoryDate = None

	def update(self):

		if self.lastborderHistoryDate == None or (datetime.now() > (self.lastborderHistoryDate + timedelta(hours=24))):
			nrank, nborder = getRank()
			self.lastborderHistoryDate = datetime.now()

			self.borderHistory.append({
				'd': self.lastborderHistoryDate.isoformat(),
				'v': nborder
			})

			with open('border.json', 'w') as f:
				f.write(json.dumps(self.borderHistory))

			sc = 'Border history:\n'
			for x in self.borderHistory:
				sc += ("%s => %s\n" % (x['d'], x['v']))
			appendNotify (sc)

	def __init__(self):
		try:
			with open('border.json', 'r') as f:
				self.borderHistory = json.loads(f.read())
				if len(self.borderHistory) > 0:
					self.lastborderHistoryDate = dateutil.parser.isoparse(self.borderHistory[0]['d'])
		except Exception as e:
			self.update()
		


# notify('Starting rank monitor')
currentRank, border = getRank()

borderHistory = BorderHistory()

i = 1
print ("Started")

	
while True:
	try:
		nrank, nborder = getRank()
	except:
		print ("Failed to update")
		continue

	if i % 120 == 0:
		summary()

	borderHistory.update()
	print('.')

	if nborder != None and border != None and nborder > border:
		appendNotify(('The 101 border has increased to %d LSK (+%d)' % (nborder, nborder - border)))
		border = nborder
	elif nborder != None and border != None and nborder < border:
		appendNotify(('The 101 border has decreased to %d LSK (%d)' % (nborder, nborder - border)))
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
	time.sleep(120)
	
	
