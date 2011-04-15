import os
import simplejson
import datetime
import time
import re
import urllib2
from elementtree import ElementTree

STREAM_DR1 = 'rtmp://rtmplive.dr.dk/live/livedr01astream3'
STREAM_DR2 = 'rtmp://rtmplive.dr.dk/live/livedr02astream3'
STREAM_DRUPDATE = 'rtmp://rtmplive.dr.dk/live/livedr03astream3'
STREAM_DRK = 'rtmp://rtmplive.dr.dk/live/livedr04astream3'
STREAM_DRRAMASJANG = 'rtmp://rtmplive.dr.dk/live/livedr05astream3'
STREAM_24NORDJYSKE = 'mms://stream.nordjyske.dk/24nordjyske - Full Broadcast Quality'
STREAM_FOLKETINGET = 'rtmp://chip.arkena.com/webtvftfl/hi1'

class Channel(object):
    def __init__(self, id, title, logoUrl = None):
        self.id = id
        self.title = title
        self.logoUrl = logoUrl

    def __str__(self):
        return 'Channel(id=%s, title=%s, logoUrl=%s)' % (self.id, self.title, self.logoUrl)

class Program(object):
    def __init__(self, channel, title, startTime, endTime, description, streamUrl = None):
        self.channel = channel
        self.title = title
        self.startTime = startTime
        self.endTime = endTime
        self.description = description
        self.streamUrl = streamUrl

    def __str__(self):
        return 'Program(channel=%s, title=%s, startTime=%s, endTime=%s, description=%s, streamUrl=%s)' % \
            (self.channel, self.title, self.startTime, self.endTime, self.description, self.streamUrl)


class Source(object):
    CACHE_MINUTES = 10

    def __init__(self, cachePath, hasChannelIcons):
        self.channelIcons = hasChannelIcons
        self.cachePath = cachePath

    def hasChannelIcons(self):
        return self.channelIcons

    def _downloadAndCacheUrl(self, url, cacheName):
        cacheFile = os.path.join(self.cachePath, cacheName)
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

    def __init__(self, cachePath):
        Source.__init__(self, cachePath, False)
        self.date = datetime.datetime.today()

    def getChannelList(self):
        jsonChannels = simplejson.loads(self._downloadAndCacheUrl(self.CHANNELS_URL, 'drdk-channels.json'))
        channels = list()

        for channel in jsonChannels['result']:
            channels.append(Channel(id = channel['source_url'], title = channel['name']))

        return channels

    def getProgramList(self, channel):
        url = self.PROGRAMS_URL % (channel.id.replace('+', '%2b'), self.date.strftime('%Y-%m-%dT%H:%M:%S'))
        jsonPrograms = simplejson.loads(self._downloadAndCacheUrl(url, 'drdk-' + channel.id.replace('/', '')))
        programs = list()

        for program in jsonPrograms['result']:
            if program.has_key('ppu_description'):
                description = program['ppu_description']
            else:
                description = 'Ingen beskrivelse'

            p = Program(channel, program['pro_title'], self._parseDate(program['pg_start']), self._parseDate(program['pg_stop']), description)
            if self.STREAMS.has_key(channelId):
                p.streamUrl = self.STREAMS[channelId]

            programs.append(p)

        return programs

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

    def __init__(self, cachePath):
        Source.__init__(self, cachePath, True)
        self.date = datetime.datetime.today()

    def getChannelList(self):
        html = self._downloadAndCacheUrl(self.CHANNELS_URL, 'youseetv-channels.json')
        channels = list()

        for m in re.finditer('href="/livetv/([^"]+)".*?src="(http://cloud.yousee.tv/static/img/logos/large_[^"]+)" alt="(.*?)"', html):
            channels.append(Channel(id = m.group(1), title = m.group(3), logoUrl = m.group(2)))

        return channels

    def getProgramList(self, channel):
        url = self.PROGRAMS_URL % channel.id.replace(' ', '%20')
        xml = self._downloadAndCacheUrl(url, 'youseetv-' + channel.id.replace(' ', '_'))
        programs = list()

        doc = ElementTree.fromstring(xml)

        for program in doc.findall('programme'):
            description = program.find('description').text
            if description is None:
                description = 'Ingen beskrivelse'

            p = Program(channel, program.find('title').text, self._parseDate(program.find('start').text), self._parseDate(program.find('end').text), description)
            if self.STREAMS.has_key(channel.id):
                p.streamUrl = self.STREAMS[channel.id]

            programs.append(p)


        return programs


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

    def __init__(self, cachePath):
        Source.__init__(self, cachePath, True)
        self.time = time.time()

        # calculate nearest hour
        self.time -= self.time % 3600

    def getChannelList(self):
        response = self._downloadAndCacheUrl(self.FETCH_URL % self.time, 'tvtiddk-data.json')
        json = simplejson.loads(response)

        channels = list()
        for channel in json['channels']:
            channels.append(Channel(id = channel['id'], title = channel['name'], logoUrl = self.BASE_URL % channel['logo']))

        return channels

    def getProgramList(self, channel):
        response = self._downloadAndCacheUrl(self.FETCH_URL % self.time, 'tvtiddk-data.json')
        json = simplejson.loads(response)

        channel = None
        for channel in json['channels']:
            if channel['id'] == channel.id:
                break

        # assume we always find a channel
        programs = list()

        for program in channel['program']:
            description = program['short_description']
            if description is None:
                description = 'Ingen beskrivelse'

            p = Program(channel, program['title'], datetime.datetime.fromtimestamp(program['start_timestamp']), datetime.datetime.fromtimestamp(program['end_timestamp']), description)
            if self.STREAMS.has_key(channel.id):
                p.streamUrl = self.STREAMS[channel.id]
            programs.append(p)

        return programs



class XMLTVSource(Source):
    def __init__(self, xmlTvFile):
        Source.__init__(self, None, True)
        self.xmlTvFile = xmlTvFile
        self.time = time.time()

        # calculate nearest hour
        self.time -= self.time % 3600

    def getChannelList(self):
        doc = self._loadXml()
        channels = list()
        for channel in doc.findall('channel'):
            channels.append(Channel(id = channel.get('id'), title = channel.findtext('display-name'), logoUrl = channel.find('icon').get('src')))

        return channels

    def getProgramList(self, channel):
        doc = self._loadXml()
        programs = list()
        for program in doc.findall('programme'):
            if program.get('channel') != channel.id:
                continue

            description = program.findtext('desc')
            if description is None:
                description = 'Ingen beskrivelse'

            p = Program(channel, program.findtext('title'), self._parseDate(program.get('start')), self._parseDate(program.get('stop')), description)
            programs.append(p)

        return programs

    def _loadXml(self):
        f = open(self.xmlTvFile)
        xml = f.read()
        f.close()

        return ElementTree.fromstring(xml)


    def _parseDate(self, dateString):
        dateStringWithoutTimeZone = dateString[:-6]
        t = time.strptime(dateStringWithoutTimeZone, '%Y%m%d%H%M%S')
        return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)

