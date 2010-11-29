# http://tvtid.tv2.dk/js/fetch.js.php/from-1291057200.js

import re
import datetime
import time
import simplejson

from danishaddons import *
import source

BASE_URL = 'http://tvtid.tv2.dk%s'
FETCH_URL = BASE_URL % '/js/fetch.js.php/from-%d.js'

STREAMS = {
	'dr1' : source.STREAM_DR1,
	'dr2' : source.STREAM_DR2,
	'update' : source.STREAM_DRUPDATE,
	'dr k' : source.STREAM_DRK,
	'dr ram' : source.STREAM_DRRAMASJANG
}

class Source(source.Source):

	def __init__(self):
		super(Source, self).__init__(True)
		self.time = time.time()

		# calculate nearest hour
		self.time -= self.time % 3600

	def getChannelList(self):
		response = web.downloadAndCacheUrl(FETCH_URL % self.time, os.path.join(ADDON_DATA_PATH, 'tvtiddk-data.json'), 60)
		json = simplejson.loads(response)

		channels = []
		for channel in json['channels']:
			channels.append({
				'id' : channel['id'],
				'title' : channel['name'],
				'logo' : BASE_URL % channel['logo']
			})

		return channels
	
	def getProgramList(self, channelId):
		response = web.downloadAndCacheUrl(FETCH_URL % self.time, os.path.join(ADDON_DATA_PATH, 'tvtiddk-data.json'), 60)
		json = simplejson.loads(response)

		for channel in json['channels']:
			if(channel['id'] == channelId):
				break

		# assume we always find a channel
		programs = []


		for program in channel['program']:
			description = program['short_description']
			if(description == None):
				description = 'Ingen beskrivelse'

			programs.append({
				'channel_id' : channelId,
				'title' : program['title'],
				'start_date' : datetime.datetime.fromtimestamp(program['start_timestamp']),
				'end_date' : datetime.datetime.fromtimestamp(program['end_timestamp']),
				'description' : description
			})

		return programs

	def getStreamURL(self, channelId):
		if(STREAMS.has_key(channelId)):
			return STREAMS[channelId]
		else:
			return None


	def _parseDate(self, dateString):
		t = time.strptime(dateString, '%Y,%m,%d,%H,%M,%S')
		return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)

			
	

