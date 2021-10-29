#!/usr/bin/python
import requests
import time
import json
import os
import sys
from datetime import datetime, timedelta
import dateutil.parser
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

DEBUG = False

cfile = 'config.json'
if len(sys.argv) == 2:
	cfile = sys.argv[1]

f = open(cfile, 'r')
conf = json.loads(f.read())

apiToken = conf['telegramApi']
chat_id = conf['chatId']
trackedDelegates = conf['delegates']


# API = "https://mainnet-service.lisktools.eu/api/v2/"
API = "https://service.lisk.io/api/v2/"
EP = "accounts?isDelegate=true&offset=%d&limit=%d&sort=rank:asc"

currentRank = {}
trackedChanges = ['isBanned', 'rank', 'consecutiveMissedBlocks', 'voteWeight']
# trackedDelegates = None


def getCurrentBlock():
	return requests.get(API + 'blocks').json()['data'][0]['height']

def getRank():
	border = None
	borderStep = None
	data = requests.get(
		API + (EP % (0, 100))).json()['data'] + requests.get(API + (EP % (100, 100))).json()['data']
	nrank = {}

	data = list(map(lambda x: x['dpos']['delegate'], data))
	data = list(filter(lambda x: x['status'] != 'punished', data))
	data.sort(key=lambda x: int(x['voteWeight']), reverse=True)

	border = int(data[100]['voteWeight']) / 100000000.
	w102 = int(data[101]['voteWeight']) / 100000000.
	borderStep = border - w102

	i = 1
	for dd in data:
		dd['rank'] = i
		nrank[dd['username']] = dd
		i += 1

	return nrank, border, borderStep


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

		st += ('%s => Changed %s to %d (was %d, diff %+d)' %
			   (user, key, vnew, vold, vnew-vold))
		return st

	return None


class Notification:
	notifies = []

	def send(self, st):
		print(st.encode('utf-8'))

		if DEBUG:
			return

		d = requests.get('https://api.telegram.org/bot%s/sendMessage?text=%s&chat_id=%s' %
						 (apiToken, st, chat_id)).json()
		#print (d.encode('utf-8'))

	def sendPhoto(self, file):
		os.system('curl -F photo=@"./%s" https://api.telegram.org/bot%s/sendPhoto?chat_id=%s' %
				  (file, apiToken, chat_id))

	def append(self, s):
		self.notifies.append(s)

	def flush(self):
		if len(self.notifies) > 0:
			self.notifies.append('\n' + datetime.now().isoformat())
			st = '\n'.join(self.notifies)
			if DEBUG:
				print(st)
			else:
				self.send(st)
			self.notifies = []


class BorderHistory:
	borderHistory = []
	lastborderHistoryDate = None
	notification = None

	def __init__(self, notification):
		self.notification = notification

		try:
			with open('border.json', 'r') as f:
				self.borderHistory = json.loads(f.read())
				if len(self.borderHistory) > 0:
					self.lastborderHistoryDate = dateutil.parser.isoparse(
						self.borderHistory[-1]['d'])

		except Exception as e:
			self.update()
		
		self.savePlot()

	def update(self):
		if self.lastborderHistoryDate == None or (datetime.now() > (self.lastborderHistoryDate + timedelta(hours=24))):
			nrank, nborder, borderStep = getRank()
			self.lastborderHistoryDate = datetime.now()

			self.borderHistory.append({
				'd': self.lastborderHistoryDate.isoformat(),
				'v': nborder,
				's': borderStep
			})

			with open('border.json', 'w') as f:
				f.write(json.dumps(self.borderHistory))

			# sc = 'Border history:\n'
			# for x in self.borderHistory:
			# 	sc += ("%s => %s\n" % (x['d'], x['v']))
			# self.notification.append(sc)

			self.savePlot()
			self.notification.sendPhoto('border_history.png')
			


	def savePlot(self):
		plt.clf()
		fig, ax1 = plt.subplots()

		ax2 = ax1.twinx()
		ax1.title.set_text('Border History')
		ax1.plot(list(map(lambda l: dateutil.parser.isoparse(l['d']), self.borderHistory)), list(map(lambda l: l['v'], self.borderHistory)), 'g-')
		ax2.plot(list(map(lambda l: dateutil.parser.isoparse(l['d']), self.borderHistory)), list(map(lambda l: l['s'] if 's' in l else 0, self.borderHistory)), 'b-')
		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
		plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
		ax1.set_xlabel('Date')
		ax1.set_ylabel('Border (LSK)', color='g')
		ax2.set_ylabel('102/101 diff (LSK)', color='b')

		plt.savefig('border_history.png', bbox_inches="tight")



notification = Notification()

if conf['borderHistory']:
	borderHistory = BorderHistory(notification)



def summary(notification):
	nrank, nborder, borderStep = getRank()

	st = "Rank, Delegate, Weight\n"
	for x in nrank:
		if x in trackedDelegates:
			st += ("%d %s %d\n" % (nrank[x]['rank'], x,
				   int(int(nrank[x]['voteWeight']) / 100000000)))

	if nborder != None and borderStep != None:
		st += '\nBorder is: %d LSK\n' % nborder
		st += 'Diff between 102 and 101 is: %d LSK' % borderStep

	notification.append(st)


# notify('Starting rank monitor')
currentRank, border, borderStep = getRank()

i = 1
print("Started")

while True:
	try:
		nrank, nborder, nborderStep = getRank()
	except Exception as e:
		print("Failed to update")
		time.sleep(1)
		continue

	if i % 120 == 0:
		summary(notification)

	if conf['borderHistory']:
		borderHistory.update()
	print('.')

	if nborder != None and border != None and nborder > border:
		notification.append(
			('The 101 border has increased to %d LSK (+%d)' % (nborder, nborder - border)))
		border = nborder
	elif nborder != None and border != None and nborder < border:
		notification.append(
			('The 101 border has decreased to %d LSK (%d)' % (nborder, nborder - border)))
		border = nborder

	if nborderStep != None and borderStep != None and nborderStep > borderStep:
		notification.append(
			('The 101/102 diff has increased to %d LSK (+%d)' % (nborderStep, nborderStep - borderStep)))
		borderStep = nborderStep
	elif nborderStep != None and borderStep != None and nborderStep < borderStep:
		notification.append(
			('The 101/102 diff has decreased to %d LSK (%d)' % (nborderStep, nborderStep - borderStep)))
		borderStep = nborderStep

	if border:
		print('Updated %d' % (border))

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
				notification.append(st)

	cblock = getCurrentBlock()
	for x in conf['nextHardFork']:
		if cblock < x and (i % 10 == 0 or (x - cblock) < 100):
			notification.append(
				('The next hard fork will occur in %d blocks' % (x - cblock)))

	currentRank = nrank
	i += 1
	sys.stdout.flush()
	notification.flush()
	time.sleep(120)
