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

