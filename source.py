import os
import simplejson
import datetime
import time
import urllib2
from elementtree import ElementTree
from strings import *
import api

STREAM_DR1 = 'rtmp://rtmplive.dr.dk/live/livedr01astream3'
STREAM_DR2 = 'rtmp://rtmplive.dr.dk/live/livedr02astream3'
STREAM_DRUPDATE = 'rtmp://rtmplive.dr.dk/live/livedr03astream3'
STREAM_DRK = 'rtmp://rtmplive.dr.dk/live/livedr04astream3'
STREAM_DRRAMASJANG = 'rtmp://rtmplive.dr.dk/live/livedr05astream3'
STREAM_24NORDJYSKE = 'mms://stream.nordjyske.dk/24nordjyske - Full Broadcast Quality'
STREAM_FOLKETINGET = 'rtmp://chip.arkena.com/webtvftfl/hi1'

class Channel(object):
    def __init__(self, id, title, logo = None, webTvChannel = None):
        self.id = id
        self.title = title
        self.logo = logo
        self.webTvChannel = webTvChannel

        self.previousChannel = None
        self.nextChannel = None

    def __str__(self):
        return 'Channel(id=%s, title=%s, logo=%s, nextChannel=%s, previousChannel=%s)' \
               % (self.id, self.title, self.logo, self.nextChannel.id, self.previousChannel.id)

class Program(object):
    def __init__(self, channel, title, startDate, endDate, description):
        self.channel = channel
        self.title = title
        self.startDate = startDate
        self.endDate = endDate
        self.description = description

    def __str__(self):
        return 'Program(channel=%s, title=%s, startDate=%s, endDate=%s, description=%s)' % \
            (self.channel, self.title, self.startDate, self.endDate, self.description)


class Source(object):
    CACHE_MINUTES = 10

    def __init__(self, cachePath, hasChannelIcons, provider = None):
        self.channelIcons = hasChannelIcons
        self.cachePath = cachePath
        self.provider = provider

        self.webTvAvailableChannels = None
        if self.provider is not None:
            self.webTvAvailableChannels = self.provider.getAvailableChannels()
        print self.webTvAvailableChannels

        self.cachedChannelList = None
        self.cachedProgramList = dict()

    def hasChannelIcons(self):
        return self.channelIcons

    def getCurrentProgram(self, channel):
        programs = self.cachedProgramList.get(channel)
        now = datetime.datetime.today()
        for program in programs:
            if program.startDate < now and program.endDate > now:
                return program

        return None

    def getChannelList(self):
        if self.cachedChannelList is None:
            self.cachedChannelList = self._getChannelList()

            for idx, channel in enumerate(self.cachedChannelList):
                if idx >= len(self.cachedChannelList) - 1:
                    channel.nextChannel = self.cachedChannelList[0]
                else:
                    channel.nextChannel = self.cachedChannelList[idx + 1]
                    
                if idx == 0:
                    channel.previousChannel = self.cachedChannelList[len(self.cachedChannelList) - 1]
                else:
                    channel.previousChannel = self.cachedChannelList[idx - 1]

        return self.cachedChannelList

    def _getChannelList(self):
        return None

    def getProgramList(self, channel):
        if not self.cachedProgramList.has_key(channel):
            programList = self._getProgramList(channel)
            self.cachedProgramList[channel] = programList

            for idx, program in enumerate(programList):
                if idx >= len(programList) - 1:
                    program.nextProgram = programList[0]
                else:
                    program.nextProgram = programList[idx + 1]

                if idx == 0:
                    program.previousProgram = programList[len(programList) - 1]
                else:
                    program.previousProgram = programList[idx - 1]

        return self.cachedProgramList[channel]
    
    def _getProgramList(self, channel):
        return None

    def _downloadAndCacheUrl(self, url, cacheName):
        cacheFile = os.path.join(self.cachePath, cacheName)
        try:
            cachedOn = os.path.getmtime(cacheFile)
        except OSError:
            cachedOn = 0

        if time.time() - self.CACHE_MINUTES * 60 >= cachedOn:
            # Cache expired or miss
            u = urllib2.urlopen(url)
            content = u.read()
            u.close()
            
            if not os.path.exists(self.cachePath):
                os.mkdir(self.cachePath)

            f = open(cacheFile, 'w')
            f.write(content)
            f.close()

        else:
            f = open(cacheFile)
            content = f.read()
            f.close()

        return content

    def _cacheLogo(self, url, cacheName):
        cacheFile = os.path.join(self.cachePath, cacheName)
        if not os.path.exists(cacheFile):
            try:
                u = urllib2.urlopen(url)
                content = u.read()
                u.close()
            except urllib2.HTTPError:
                return None

            if not os.path.exists(self.cachePath):
                os.mkdir(self.cachePath)

            f = open(cacheFile, 'w')
            f.write(content)
            f.close()

        return cacheFile


class DrDkSource(Source):
    KEY = 'drdk'

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

    def _getChannelList(self):
        jsonChannels = simplejson.loads(self._downloadAndCacheUrl(self.CHANNELS_URL, self.KEY + '-channels.json'))
        channelList = list()

        for channel in jsonChannels['result']:
            c = Channel(id = channel['source_url'], title = channel['name'])
            if self.STREAMS.has_key(c.id):
                c.streamUrl = self.STREAMS[c.id]

            channelList.append(c)

        return channelList


    def _getProgramList(self, channel):
        url = self.PROGRAMS_URL % (channel.id.replace('+', '%2b'), self.date.strftime('%Y-%m-%dT%H:%M:%S'))
        jsonPrograms = simplejson.loads(self._downloadAndCacheUrl(url, self.KEY + '-' + channel.id.replace('/', '')))
        programs = list()

        for program in jsonPrograms['result']:
            if program.has_key('ppu_description'):
                description = program['ppu_description']
            else:
                description = strings(NO_DESCRIPTION)

            programs.append(Program(channel, program['pro_title'], self._parseDate(program['pg_start']), self._parseDate(program['pg_stop']), description))

        return programs
    
    def _parseDate(self, dateString):
        t = time.strptime(dateString[:19], '%Y-%m-%dT%H:%M:%S')
        return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)

class YouSeeTvSource(Source):
    KEY = 'youseetv'

    CHANNELS_URL = 'http://yousee.tv'
    PROGRAMS_URL = 'http://yousee.tv/feeds/tvguide/getprogrammes/?channel=%s'

    CHANNELS = api.WebTvLookup({
        'dr1' : api.CHANNEL_DK_DR1,
        'tv 2' : api.CHANNEL_DK_TV2,
        'dr2' : api.CHANNEL_DK_DR2,
        'zulu' : api.CHANNEL_DK_TV2ZULU,
        'charli' : api.CHANNEL_DK_TV2CHARLIE,
        'tv3' : api.CHANNEL_DK_TV3,
        'dr hd' : api.CHANNEL_DK_DRHD,
        'dr k' : api.CHANNEL_DK_DRK,
        'dr ram' :api.CHANNEL_DK_DR_RAMASJANG,
        'tv3plus' : api.CHANNEL_DK_TV3PLUS,
        '3puls' : api.CHANNEL_DK_TV3PULS,
        'kanal4': api.CHANNEL_DK_KANAL4,
        'kanal5': api.CHANNEL_DK_KANAL5,
        'k5 hd': api.CHANNEL_DK_KANAL5HD,
        '6eren': api.CHANNEL_DK_6EREN,
        'canal9' : api.CHANNEL_DK_CANAL9,
        '2news' : api.CHANNEL_DK_TV2NEWS,
        'dk4': api.CHANNEL_DK_DK4,
        'update' :api.CHANNEL_DK_DR_UPDATE,
        'svt1': api.CHANNEL_SV_SVT1,
        'svt2': api.CHANNEL_SV_SVT2,
        'tv4': api.CHANNEL_SV_TV4,
        'nrk1': api.CHANNEL_NO_NRK1,
        'ard': api.CHANNEL_DE_ARD,
        'zdf': api.CHANNEL_DE_ZDF,
        'rtl': api.CHANNEL_DE_RTL,
        'ndr': api.CHANNEL_DE_NDR,
        'tinget': api.CHANNEL_DK_FOLKETINGET
    })


    def __init__(self, cachePath, webTvProvider = None):
        Source.__init__(self, cachePath, False, webTvProvider)
        self.date = datetime.datetime.today()

    def _getChannelList(self):
        channelList = list()
#        for m in re.finditer('href="/livetv/([^"]+)".*?src="(http://cloud.yousee.tv/static/img/logos/large_[^"]+)" alt="(.*?)"', html):
        for id in self.CHANNELS.keys():
            title = id
#            logoFile = self._cacheLogo(m.group(2), self.KEY + '-' + m.group(1) + '.jpg')
            c = Channel(id = id, title = title)
            #c = Channel(id = id, title = m.group(3), logo = logoFile)

            print id
            if self.webTvAvailableChannels is None:
                channelList.append(c)
            elif self.CHANNELS.has_value(id) and self.CHANNELS.get_value(id) in self.webTvAvailableChannels:
                c.webTvChannel = self.CHANNELS.get_value(id)
                channelList.append(c)

        return channelList

    def _getProgramList(self, channel):
        url = self.PROGRAMS_URL % channel.id.replace(' ', '%20')
        xml = self._downloadAndCacheUrl(url, 'youseetv-' + channel.id.replace(' ', '_'))
        programs = list()

        doc = ElementTree.fromstring(xml)

        for program in doc.findall('programme'):
            description = program.find('description').text
            if description is None:
                description = strings(NO_DESCRIPTION)

            programs.append(Program(channel, program.find('title').text, self._parseDate(program.find('start').text), self._parseDate(program.find('end').text), description))

        return programs

    def _parseDate(self, dateString):
        t = time.strptime(dateString, '%Y,%m,%d,%H,%M,%S')
        return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)




class TvTidSource(Source):
    # http://tvtid.tv2.dk/js/fetch.js.php/from-1291057200.js
    KEY = 'tvtiddk'

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

    def _getChannelList(self):
        response = self._downloadAndCacheUrl(self.FETCH_URL % self.time, self.KEY + '-data.json')
        json = simplejson.loads(response)

        channelList = list()
        for channel in json['channels']:
            logoFile = self._cacheLogo(self.BASE_URL % channel['logo'], self.KEY + '-' + str(channel['id']) + '.jpg')

            c = Channel(id = channel['id'], title = channel['name'], logo = logoFile)
            if self.STREAMS.has_key(c.id):
                c.streamUrl = self.STREAMS[c.id]
            channelList.append(c)

        return channelList

    def _getProgramList(self, channel):
        response = self._downloadAndCacheUrl(self.FETCH_URL % self.time, 'tvtiddk-data.json')
        json = simplejson.loads(response)

        c = None
        for c in json['channels']:
            if c['id'] == channel.id:
                break

        # assume we always find a channel
        programs = list()

        for program in c['program']:
            description = program['short_description']
            if description is None:
                description = strings(NO_DESCRIPTION)

            programs.append(Program(channel, program['title'], datetime.datetime.fromtimestamp(program['start_timestamp']), datetime.datetime.fromtimestamp(program['end_timestamp']), description))

        return programs

class XMLTVSource(Source):
    KEY = 'xmltv'

    def __init__(self, xmlTvFile):
        Source.__init__(self, None, True)
        self.xmlTvFile = xmlTvFile
        self.time = time.time()

        # calculate nearest hour
        self.time -= self.time % 3600

    def _getChannelList(self):
        doc = self._loadXml()
        channelList = list()
        for channel in doc.findall('channel'):
            c = Channel(id = channel.get('id'), title = channel.findtext('display-name'), logo = channel.find('icon').get('src'))
            channelList.append(c)

        return channelList

    def _getProgramList(self, channel):
        doc = self._loadXml()
        programs = list()
        for program in doc.findall('programme'):
            if program.get('channel') != channel.id:
                continue

            description = program.findtext('desc')
            if description is None:
                description = strings(NO_DESCRIPTION)

            programs.append(Program(channel, program.findtext('title'), self._parseDate(program.get('start')), self._parseDate(program.get('stop')), description))

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

