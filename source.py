STREAM_DR1 = 'rtmp://rtmplive.dr.dk/live/livedr01astream3'
STREAM_DR2 = 'rtmp://rtmplive.dr.dk/live/livedr02astream3'
STREAM_DRUPDATE = 'rtmp://rtmplive.dr.dk/live/livedr03astream3'
STREAM_DRK = 'rtmp://rtmplive.dr.dk/live/livedr04astream3'
STREAM_DRRAMASJANG = 'rtmp://rtmplive.dr.dk/live/livedr05astream3'
STREAM_24NORDJYSKE = 'mms://stream.nordjyske.dk/24nordjyske - Full Broadcast Quality'
STREAM_FOLKETINGET = 'rtmp://chip.arkena.com/webtvftfl/hi1'

class Source(object):

	def __init__(self, hasChannelIcons):
		self.channelIcons = hasChannelIcons

	def hasChannelIcons(self):
		return self.channelIcons

	def getStreamURL(self, channelId):
		return None


class DrDkSource(Source):
	CHANNELS_URL = 'http://www.dr.dk/tjenester/programoversigt/dbservice.ashx/getChannels?type=tv'
	PROGRAMS_URL = 'http://www.dr.dk/tjenester/programoversigt/dbservice.ashx/getSchedule?channel_source_url=%s&broadcastDate=%s'

	STREAMS = {
		'dr.dk/mas/whatson/channel/DR1' : source.STREAM_DR1,
		'dr.dk/mas/whatson/channel/DR2' : source.STREAM_DR2,
		'dr.dk/mas/whatson/channel/TVR' : source.STREAM_DRRAMASJANG,
		'dr.dk/mas/whatson/channel/TVK' : source.STREAM_DRK,
		'dr.dk/external/ritzau/channel/dru' : source.STREAM_DRUPDATE
	}

	def __init__(self):
		super(Source, self).__init__(False)
		self.date = datetime.datetime.today()

	def getChannelList(self):
		jsonChannels = simplejson.loads(danishaddons.web.downloadAndCacheUrl(CHANNELS_URL, os.path.join(danishaddons.ADDON_DATA_PATH, 'drdk-channels.json'), 60))
		channels = []

		for channel in jsonChannels['result']:
			channels.append({
				'id' : channel['source_url'],
				'title' : channel['name']
			})
	
		return channels
	
	def getProgramList(self, channelId):
		url = PROGRAMS_URL % (channelId.replace('+', '%2b'), self.date.strftime('%Y-%m-%dT%H:%M:%S'))
		cachePath = os.path.join(danishaddons.ADDON_DATA_PATH, 'drdk-' + channelId.replace('/', ''))
		jsonPrograms = simplejson.loads(danishaddons.web.downloadAndCacheUrl(url, cachePath, 60))
		programs = []

		for program in jsonPrograms['result']:
			if program.has_key('ppu_description'):
				description = program['ppu_description']
			else:
				description = 'Ingen beskrivelse'

			programs.append({
				'channel_id' : channelId,
				'title' : program['pro_title'],
				'start_date' : self._parseDate(program['pg_start']),
				'end_date' : self._parseDate(program['pg_stop']),
				'description' : description
			})

		return programs

	def getStreamURL(self, channelId):
		if STREAMS.has_key(channelId):
			return STREAMS[channelId]
		else:
			return None

	def _parseDate(self, dateString):
		t = time.strptime(dateString[:19], '%Y-%m-%dT%H:%M:%S')
		return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)

class YouSeeTvSource(Source):
	CHANNELS_URL = 'http://yousee.tv'
	PROGRAMS_URL = 'http://yousee.tv/feeds/tvguide/getprogrammes/?channel=%s'

	STREAMS = {
		'dr1' : source.STREAM_DR1,
		'dr2' : source.STREAM_DR2,
		'update' : source.STREAM_DRUPDATE,
		'dr k' : source.STREAM_DRK,
		'dr ram' : source.STREAM_DRRAMASJANG
	}

	def __init__(self):
		super(Source, self).__init__(True)
		self.date = datetime.datetime.today()

	def getChannelList(self):
		html = danishaddons.web.downloadAndCacheUrl(CHANNELS_URL, os.path.join(danishaddons.ADDON_DATA_PATH, 'youseetv-channels.json'), 60)
		channels = []

		for m in re.finditer('href="/livetv/([^"]+)".*?src="(http://cloud.yousee.tv/static/img/logos/large_[^"]+)" alt="(.*?)"', html):
			channels.append({
				'id' : m.group(1),
				'title' : m.group(3),
				'logo' : m.group(2)
			})
	
		return channels
	
	def getProgramList(self, channelId):
		url = PROGRAMS_URL % channelId.replace(' ', '%20')
		cachePath = os.path.join(danishaddons.ADDON_DATA_PATH, 'youseetv-' + channelId.replace(' ', '_'))
		xml = danishaddons.web.downloadAndCacheUrl(url, cachePath, 60)
		programs = []

		doc = ElementTree.fromstring(xml)

		for program in doc.findall('programme'):
			description = program.find('description').text
			if description is None:
				description = 'Ingen beskrivelse'

			programs.append({
				'channel_id' : channelId,
				'title' : program.find('title').text,
				'start_date' : self._parseDate(program.find('start').text),
				'end_date' : self._parseDate(program.find('end').text),
				'description' : description
			})

		return programs

	def getStreamURL(self, channelId):
		if STREAMS.has_key(channelId):
			return STREAMS[channelId]
		else:
			return None


	def _parseDate(self, dateString):
		t = time.strptime(dateString, '%Y,%m,%d,%H,%M,%S')
		return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)

			


class TvTidSource(Source):
	# http://tvtid.tv2.dk/js/fetch.js.php/from-1291057200.js
	BASE_URL = 'http://tvtid.tv2.dk%s'
	FETCH_URL = BASE_URL % '/js/fetch.js.php/from-%d.js'

	STREAMS = {
		'dr1' : source.STREAM_DR1,
		'dr2' : source.STREAM_DR2,
		'update' : source.STREAM_DRUPDATE,
		'dr k' : source.STREAM_DRK,
		'dr ram' : source.STREAM_DRRAMASJANG
	}

	def __init__(self):
		super(Source, self).__init__(True)
		self.time = time.time()

		# calculate nearest hour
		self.time -= self.time % 3600

	def getChannelList(self):
		response = danishaddons.web.downloadAndCacheUrl(FETCH_URL % self.time, os.path.join(danishaddons.ADDON_DATA_PATH, 'tvtiddk-data.json'), 60)
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
		response = danishaddons.web.downloadAndCacheUrl(FETCH_URL % self.time, os.path.join(danishaddons.ADDON_DATA_PATH, 'tvtiddk-data.json'), 60)
		json = simplejson.loads(response)

		for channel in json['channels']:
			if channel['id'] == channelId:
				break

		# assume we always find a channel
		programs = []


		for program in channel['program']:
			description = program['short_description']
			if description is None:
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
		if STREAMS.has_key(channelId):
			return STREAMS[channelId]
		else:
			return None


	def _parseDate(self, dateString):
		t = time.strptime(dateString, '%Y,%m,%d,%H,%M,%S')
		return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)

			
	

