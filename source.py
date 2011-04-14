import os
import simplejson
import datetime
import time
import re
import urllib2
from elementtree import ElementTree

import xbmcaddon

STREAM_DR1 = 'rtmp://rtmplive.dr.dk/live/livedr01astream3'
STREAM_DR2 = 'rtmp://rtmplive.dr.dk/live/livedr02astream3'
STREAM_DRUPDATE = 'rtmp://rtmplive.dr.dk/live/livedr03astream3'
STREAM_DRK = 'rtmp://rtmplive.dr.dk/live/livedr04astream3'
STREAM_DRRAMASJANG = 'rtmp://rtmplive.dr.dk/live/livedr05astream3'
STREAM_24NORDJYSKE = 'mms://stream.nordjyske.dk/24nordjyske - Full Broadcast Quality'
STREAM_FOLKETINGET = 'rtmp://chip.arkena.com/webtvftfl/hi1'

class Program(object):
    def __init__(self):
        self.channelId = None
        self.title = None
        self.startTime = None
        self.endTime = None
        self.description = None


class Source(object):
    ADDON = xbmcaddon.Addon(id = 'script.tvguide')
    CACHE_PATH = ADDON.getAddonInfo('profile')
    CACHE_MINUTES = 10

    def __init__(self, hasChannelIcons):
        self.channelIcons = hasChannelIcons

    def hasChannelIcons(self):
        return self.channelIcons

    def getStreamURL(self, channelId):
        return None
    
    def _downloadAndCacheUrl(self, url, cacheName):
        cacheFile = os.path.join(self.CACHE_PATH, cacheName)
        try:
            cachedOn = os.path.getmtime(cacheFile)
        except:
            cachedOn = 0

        if time.time() - self.CACHE_MINUTES * 60 >= cachedOn:
            # Cache expired or miss
            u = urllib2.urlopen(url)
            content = u.read()
            u.close()

            f = open(cacheFile, 'w')
            f.write(content)
            f.close()

        else:
            f = open(cacheFile)
            content = f.read()
            f.close()

        return content


class DrDkSource(Source):
    CHANNELS_URL = 'http://www.dr.dk/tjenester/programoversigt/dbservice.ashx/getChannels?type=tv'
    PROGRAMS_URL = 'http://www.dr.dk/tjenester/programoversigt/dbservice.ashx/getSchedule?channel_source_url=%s&broadcastDate=%s'

    STREAMS = {
        'dr.dk/mas/whatson/channel/DR1' : STREAM_DR1,
        'dr.dk/mas/whatson/channel/DR2' : STREAM_DR2,
        'dr.dk/mas/whatson/channel/TVR' : STREAM_DRRAMASJANG,
        'dr.dk/mas/whatson/channel/TVK' : STREAM_DRK,
        'dr.dk/external/ritzau/channel/dru' : STREAM_DRUPDATE
    }

    def __init__(self):
        Source.__init__(self, False)
        self.date = datetime.datetime.today()

    def getChannelList(self):
        jsonChannels = simplejson.loads(self._downloadAndCacheUrl(self.CHANNELS_URL, 'drdk-channels.json'))
        channels = []

        for channel in jsonChannels['result']:
            channels.append({
                'id' : channel['source_url'],
                'title' : channel['name']
            })

        return channels

    def getProgramList(self, channelId):
        url = self.PROGRAMS_URL % (channelId.replace('+', '%2b'), self.date.strftime('%Y-%m-%dT%H:%M:%S'))
        jsonPrograms = simplejson.loads(self._downloadAndCacheUrl(url, 'drdk-' + channelId.replace('/', '')))
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
        if self.STREAMS.has_key(channelId):
            return self.STREAMS[channelId]
        else:
            return None

    def _parseDate(self, dateString):
        t = time.strptime(dateString[:19], '%Y-%m-%dT%H:%M:%S')
        return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)

class YouSeeTvSource(Source):
    CHANNELS_URL = 'http://yousee.tv'
    PROGRAMS_URL = 'http://yousee.tv/feeds/tvguide/getprogrammes/?channel=%s'

    STREAMS = {
        'dr1' : STREAM_DR1,
        'dr2' : STREAM_DR2,
        'update' : STREAM_DRUPDATE,
        'dr k' : STREAM_DRK,
        'dr ram' : STREAM_DRRAMASJANG
    }

    def __init__(self):
        Source.__init__(self, True)
        self.date = datetime.datetime.today()

    def getChannelList(self):
        html = self._downloadAndCacheUrl(self.CHANNELS_URL, 'youseetv-channels.json')
        channels = []

        for m in re.finditer('href="/livetv/([^"]+)".*?src="(http://cloud.yousee.tv/static/img/logos/large_[^"]+)" alt="(.*?)"', html):
            channels.append({
                'id' : m.group(1),
                'title' : m.group(3),
                'logo' : m.group(2)
            })

        return channels

    def getProgramList(self, channelId):
        url = self.PROGRAMS_URL % channelId.replace(' ', '%20')
        xml = self._downloadAndCacheUrl(url, 'youseetv-' + channelId.replace(' ', '_'))
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
        if self.STREAMS.has_key(channelId):
            return self.STREAMS[channelId]
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
        'dr1' : STREAM_DR1,
        'dr2' : STREAM_DR2,
        'update' : STREAM_DRUPDATE,
        'dr k' : STREAM_DRK,
        'dr ram' : STREAM_DRRAMASJANG
    }

    def __init__(self):
        Source.__init__(self, True)
        self.time = time.time()

        # calculate nearest hour
        self.time -= self.time % 3600

    def getChannelList(self):
        response = self._downloadAndCacheUrl(self.FETCH_URL % self.time, 'tvtiddk-data.json')
        json = simplejson.loads(response)

        channels = []
        for channel in json['channels']:
            channels.append({
                'id' : channel['id'],
                'title' : channel['name'],
                'logo' : self.BASE_URL % channel['logo']
            })

        return channels

    def getProgramList(self, channelId):
        response = self._downloadAndCacheUrl(self.FETCH_URL % self.time, 'tvtiddk-data.json')
        json = simplejson.loads(response)

        channel = None
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
        if self.STREAMS.has_key(channelId):
            return self.STREAMS[channelId]
        else:
            return None


    def _parseDate(self, dateString):
        t = time.strptime(dateString, '%Y,%m,%d,%H,%M,%S')
        return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)




