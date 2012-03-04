#
#      Copyright (C) 2012 Tommy Winther
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import os
import simplejson
import datetime
import time
import urllib2
from xml.etree import ElementTree
from strings import *
import ysapi

import xbmc
import xbmcgui
import xbmcvfs
import pickle
import threading
from sqlite3 import dbapi2 as sqlite3

STREAM_DR1 = 'plugin://plugin.video.dr.dk.live/?playChannel=1'
STREAM_DR2 = 'plugin://plugin.video.dr.dk.live/?playChannel=2'
STREAM_DR_UPDATE = 'plugin://plugin.video.dr.dk.live/?playChannel=3'
STREAM_DR_K = 'plugin://plugin.video.dr.dk.live/?playChannel=4'
STREAM_DR_RAMASJANG = 'plugin://plugin.video.dr.dk.live/?playChannel=5'
STREAM_DR_HD = 'plugin://plugin.video.dr.dk.live/?playChannel=6'
STREAM_24_NORDJYSKE = 'plugin://plugin.video.dr.dk.live/?playChannel=200'

class Channel(object):
    def __init__(self, id, title, logo = None, streamUrl = None):
        self.id = id
        self.title = title
        self.logo = logo
        self.streamUrl = streamUrl

    def isPlayable(self):
        return hasattr(self, 'streamUrl') and self.streamUrl

    def __repr__(self):
        return 'Channel(id=%s, title=%s, logo=%s, streamUrl=%s)' \
               % (self.id, self.title, self.logo, self.streamUrl)

class Program(object):
    def __init__(self, channel, title, startDate, endDate, description, imageLarge = None, imageSmall=None):
        """

        @param channel:
        @type channel: source.Channel
        @param title:
        @param startDate:
        @param endDate:
        @param description:
        @param imageLarge:
        @param imageSmall:
        """
        self.channel = channel
        self.title = title
        self.startDate = startDate
        self.endDate = endDate
        self.description = description
        self.imageLarge = imageLarge
        self.imageSmall = imageSmall

    def __repr__(self):
        return 'Program(channel=%s, title=%s, startDate=%s, endDate=%s, description=%s, imageLarge=%s, imageSmall=%s)' % \
            (self.channel, self.title, self.startDate, self.endDate, self.description, self.imageLarge, self.imageSmall)


class SourceException(Exception):
    pass


class SourceUpdaterThread(threading.Thread):
    def __init__(self, source):
        """

        @param source:
        @type source: source.Source
        @return:
        """
        super(SourceUpdaterThread, self).__init__()
        self.source = source

    def run(self):
        channelList = None
        if self.source._isChannelListCacheExpired():
            channelList = self.source.updateChannelListCache()

        if self.source._isProgramListCacheExpired():
            if channelList is None:
                channelList = self.source.getChannelList()
            self.source.updateProgramListCaches(channelList)

class Source(object):
    KEY = "undefined"
    STREAMS = {}
    SOURCE_DB = 'source.db'

    def __init__(self, settings):
        self.updateInProgress = False
        self.cachePath = settings['cache.path']
        self.playbackUsingDanishLiveTV = False

        self.conn = sqlite3.connect(os.path.join(self.cachePath, self.SOURCE_DB), detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread = False)
        self.conn.execute('PRAGMA foreign_keys = ON')
        self.conn.row_factory = sqlite3.Row
        self._createTables()

        try:
            if settings['danishlivetv.playback'] == 'true':
                xbmcaddon.Addon(id = 'plugin.video.dr.dk.live') # raises Exception if addon is not installed
                self.playbackUsingDanishLiveTV = True
        except Exception:
            ADDON.setSetting('danishlivetv.playback', 'false')
            xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), strings(DANISH_LIVE_TV_MISSING_1),
                strings(DANISH_LIVE_TV_MISSING_2), strings(DANISH_LIVE_TV_MISSING_3))

    def __del__(self):
        self.conn.close()

    def isUpdateInProgress(self):
        return self.updateInProgress

    def updateChannelListCache(self):
        self.updateInProgress = True
        xbmc.log('[script.tvguide] Updating channel list caches...', xbmc.LOGDEBUG)
        try:
            channelList = self.getChannelListFromExternal()
        except Exception as ex:
            raise SourceException(ex)

        # Setup additional stream urls
        for channel in channelList:
            if channel.streamUrl:
                continue
            elif self.playbackUsingDanishLiveTV and self.STREAMS.has_key(channel.id):
                channel.streamUrl = self.STREAMS[channel.id]
        self._storeChannelListInDatabase(channelList)

        self.updateInProgress = False
        return channelList

    def updateProgramListCaches(self, channelList, date = datetime.datetime.now()):
        self.updateInProgress = True
        for channel in channelList:
            xbmc.log("[script.tvguide] Updating program list caches for channel " + channel.title.decode('iso-8859-1') + "...", xbmc.LOGDEBUG)
            programList = self.getProgramListFromExternal(channel, date)
            self._storeProgramListInDatabase(channel, programList, date, False)

        self.updateInProgress = False

    def getChannelList(self):
        return self._retrieveChannelListFromDatabase()

    def getChannelListFromExternal(self):
        """
        Retrieves the actual channel data from the external source.
        Must be implemented by each sub-class.
        """
        raise SourceException('getChannelListFromExternal(..) not implemented!')

    def _storeChannelListInDatabase(self, channelList):
        c = self.conn.cursor()
        for channel in channelList:
            c.execute('INSERT OR IGNORE INTO channels(id, title, logo, stream_url, source) VALUES(?, ?, ?, ?, ?)', [channel.id, channel.title, channel.logo, channel.streamUrl, self.KEY])
            c.execute('UPDATE channels SET title=?, logo=?, stream_url=? WHERE id=? AND source=?', [channel.title, channel.logo, channel.streamUrl, channel.id, self.KEY])

        c.execute("UPDATE sources SET channels_updated=DATETIME('now') WHERE id=?", [self.KEY])
        self.conn.commit()

    def _retrieveChannelListFromDatabase(self):
        c = self.conn.cursor()

        # check if data is up-to-date in database
        channelList = list()
        if self._isChannelListCacheExpired():
            channelList = self.updateChannelListCache()

        else:
            c.execute('SELECT * FROM channels WHERE source=?', [self.KEY])
            for row in c:
                channel = Channel(row['id'], row['title'],row['logo'], row['stream_url'])
                channelList.append(channel)

        return channelList

    def _isChannelListCacheExpired(self):
        return self._getLastUpdated() < datetime.datetime.now() - datetime.timedelta(days = 1)


    def getProgramList(self, channel, startTime):
        return self._retrieveProgramListFromDatabase(channel, startTime)

    def getProgramListFromExternal(self, channel, date):
        """
        Retrieves the actual program data from the external source.
        Must be implemented by each sub-class.
        """
        raise SourceException('getProgramListFromExternal(..) not implemented!')

    def _storeProgramListInDatabase(self, channel, programList, date, clearExistingProgramList = True):
        """
        Deletes any existing programs for the channel and creates the new one.
        @param channel:
        @param programList:
        @param clearExistingProgramList:
        @return:
        """
        c = self.conn.cursor()
        if clearExistingProgramList:
            c.execute('DELETE FROM programs WHERE channel=? AND source=?', [channel.id, self.KEY])
        for program in programList:
            c.execute('INSERT INTO programs(channel, title, start_date, end_date, description, image_large, image_small, source) VALUES(?, ?, ?, ?, ?, ?, ?, ?)',
                [channel.id, program.title, program.startDate, program.endDate, program.description, program.imageLarge, program.imageSmall, self.KEY])

        dateStr = date.strftime('%Y-%m-%d')
        c.execute("INSERT OR IGNORE INTO sources_updates(source, date, programs_updated) VALUES(?, ?, DATETIME('now'))", [self.KEY, dateStr])
        c.execute("UPDATE sources_updates SET programs_updated=DATETIME('now') WHERE source=? AND date=?", [self.KEY, dateStr])

        self.conn.commit()
        c.close()

    def _retrieveProgramListFromDatabase(self, channel, startTime):
        """

        @param channel:
        @type channel: source.Channel
        @param startTime:
        @type startTime: datetime.datetime
        @return:
        """
        if self._isProgramListCacheExpired(startTime):
            self.updateProgramListCaches(self.getChannelList(), startTime)

        endTime = startTime + datetime.timedelta(hours = 2)
        programList = list()

        c = self.conn.cursor()
        c.execute('SELECT * FROM programs WHERE channel=? AND source=? AND end_date >= ? AND start_date <= ?', [channel.id, self.KEY, startTime, endTime])
        for row in c:
            program = Program(channel, row['title'], row['start_date'], row['end_date'], row['description'], row['image_large'], row['image_small'])
            programList.append(program)

        return programList

    def _isProgramListCacheExpired(self, date = datetime.datetime.now()):
        # check if data is up-to-date in database
        dateStr = date.strftime('%Y-%m-%d')
        c = self.conn.cursor()
        c.execute('SELECT programs_updated FROM sources_updates WHERE source=? AND date=?', [self.KEY, dateStr])
        row = c.fetchone()
        expired = row is None or row['programs_updated'] < datetime.datetime.now() - datetime.timedelta(days = 1)
        c.close()
        return expired


    def _downloadUrl(self, url):
        u = urllib2.urlopen(url)
        content = u.read()
        u.close()
            
        return content

    def _getLastUpdated(self):
        c = self.conn.cursor()
        try:
            c.execute('SELECT channels_updated FROM sources WHERE id=?', [self.KEY])
            lastUpdated = c.fetchone()['channels_updated']
        except Exception:
            # make sure we have a record in sources for this Source
            c.execute("INSERT INTO sources(id, channels_updated) VALUES(?, DATETIME('now', '-1 day'))", [self.KEY])
            self.conn.commit()
            lastUpdated = datetime.datetime.now() - datetime.timedelta(days = 1)
        c.close()
        return lastUpdated

    def setCustomStreamUrl(self, channel, stream_url):
        c = self.conn.cursor()
        c.execute("DELETE FROM custom_stream_url WHERE channel=?", [channel.id])
        c.execute("INSERT INTO custom_stream_url(channel, stream_url) VALUES(?, ?)", [channel.id, stream_url])
        self.conn.commit()
        c.close()

    def getCustomStreamUrl(self, channel):
        c = self.conn.cursor()
        c.execute("SELECT stream_url FROM custom_stream_url WHERE channel=?", [channel.id])
        stream_url = c.fetchone()
        c.close()

        if stream_url:
            return stream_url[0]
        else:
            return None

    def deleteCustomStreamUrl(self, channel):
        c = self.conn.cursor()
        c.execute("DELETE FROM custom_stream_url WHERE channel=?", [channel.id])
        self.conn.commit()
        c.close()

    def isPlayable(self, channel):
        customStreamUrl = self.getCustomStreamUrl(channel)
        return customStreamUrl is not None or channel.isPlayable()

    def play(self, channel):
        customStreamUrl = self.getCustomStreamUrl(channel)
        if customStreamUrl:
            xbmc.log("Playing custom stream url: %s" % customStreamUrl)
            xbmc.Player().play(item = customStreamUrl)

        elif channel.isPlayable():
            xbmc.log("Playing : %s" % channel.streamUrl)
            xbmc.Player().play(item = channel.streamUrl)

    def _createTables(self):
        c = self.conn.cursor()

        try:
            c.execute('SELECT major, minor, patch FROM version')
            (major, minor, patch) = c.fetchone()
            version = [major, minor, patch]
            print version
        except sqlite3.OperationalError:
            version = [0, 0, 0]

        if version < [1, 3, 0]:
            c.execute('CREATE TABLE custom_stream_url(channel TEXT, stream_url TEXT)')
            c.execute('CREATE TABLE version (major INTEGER, minor INTEGER, patch INTEGER)')
            c.execute('INSERT INTO version(major, minor, patch) VALUES(1, 3, 0)')

            # For caching data
            c.execute('CREATE TABLE sources(id TEXT PRIMARY KEY, channels_updated TIMESTAMP)')
            c.execute('CREATE TABLE sources_updates(source TEXT, date TEXT, programs_updated TIMESTAMP)')
            c.execute('CREATE TABLE channels(id TEXT, title TEXT, logo TEXT, stream_url TEXT, source TEXT, visible INTEGER, weight INTEGER, PRIMARY KEY (id, source), FOREIGN KEY(source) REFERENCES sources(id) ON DELETE CASCADE)')
            c.execute('CREATE TABLE programs(channel TEXT, title TEXT, start_date TIMESTAMP, end_date TIMESTAMP, description TEXT, image_large TEXT, image_small TEXT, source TEXT, FOREIGN KEY(channel, source) REFERENCES channels(id, source) ON DELETE CASCADE)')

        self.conn.commit()
        c.close()


class DrDkSource(Source):
    KEY = 'drdk'
    CHANNELS_URL = 'http://www.dr.dk/tjenester/programoversigt/dbservice.ashx/getChannels?type=tv'
    PROGRAMS_URL = 'http://www.dr.dk/tjenester/programoversigt/dbservice.ashx/getSchedule?channel_source_url=%s&broadcastDate=%s'

    STREAMS = {
        'dr.dk/mas/whatson/channel/DR1' : STREAM_DR1,
        'dr.dk/mas/whatson/channel/DR2' : STREAM_DR2,
        'dr.dk/external/ritzau/ channel/dru' : STREAM_DR_UPDATE,
        'dr.dk/mas/whatson/channel/TVR' : STREAM_DR_RAMASJANG,
        'dr.dk/mas/whatson/channel/TVK' : STREAM_DR_K,
        'dr.dk/mas/whatson/channel/TV' : STREAM_DR_HD
    }

    def __init__(self, settings):
        Source.__init__(self, settings)

    def getChannelListFromExternal(self):
        jsonChannels = simplejson.loads(self._downloadUrl(self.CHANNELS_URL))
        channelList = list()

        for channel in jsonChannels['result']:
            c = Channel(id = channel['source_url'], title = channel['name'])
            channelList.append(c)

        return channelList

    def getProgramListFromExternal(self, channel, date):
        url = self.PROGRAMS_URL % (channel.id.replace('+', '%2b'), date.strftime('%Y-%m-%dT00:00:00'))
        jsonPrograms = simplejson.loads(self._downloadUrl(url))
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

    STREAMS = {
        1 : STREAM_DR1,
        2 : STREAM_DR2,
        889 : STREAM_DR_UPDATE,
        505: STREAM_DR_RAMASJANG,
        504 : STREAM_DR_K,
        503 : STREAM_DR_HD
    }

    def __init__(self, settings):
        Source.__init__(self, settings)
        self.date = datetime.datetime.today()
        self.channelCategory = settings['youseetv.category']
        self.ysApi = ysapi.YouSeeTVGuideApi()
        self.playbackUsingYouSeeWebTv = False

        try:
            if settings['youseewebtv.playback'] == 'true':
                xbmcaddon.Addon(id = 'plugin.video.yousee.tv') # raises Exception if addon is not installed
                self.playbackUsingYouSeeWebTv = True
        except Exception:
            ADDON.setSetting('youseewebtv.playback', 'false')
            xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), strings(YOUSEE_WEBTV_MISSING_1),
                strings(YOUSEE_WEBTV_MISSING_2), strings(YOUSEE_WEBTV_MISSING_3))

    def getChannelListFromExternal(self):
        channelList = list()
        for channel in self.ysApi.channelsInCategory(self.channelCategory):
            c = Channel(id = channel['id'], title = channel['name'], logo = channel['logo'])
            if self.playbackUsingYouSeeWebTv:
                c.streamUrl = 'plugin://plugin.video.yousee.tv/?channel=' + str(c.id)
            channelList.append(c)

        return channelList

    def getProgramListFromExternal(self, channel, date):
        programs = list()
        for program in self.ysApi.programs(channel.id, tvdate = date):
            description = program['description']
            if description is None:
                description = strings(NO_DESCRIPTION)

            imagePrefix = program['imageprefix']

            p = Program(
                channel,
                program['title'],
                self._parseDate(program['begin']),
                self._parseDate(program['end']),
                description,
                imagePrefix + program['images_sixteenbynine']['large'],
                imagePrefix + program['images_sixteenbynine']['small'],
            )
            programs.append(p)

        return programs

    def _parseDate(self, dateString):
        return datetime.datetime.fromtimestamp(dateString)


class TvTidSource(Source):
    KEY = 'tvtiddk'

    BASE_URL = 'http://tvtid.tv2.dk%s'
    CHANNELS_URL = BASE_URL % '/api/channels.php/'
    PROGRAMS_URL = BASE_URL % '/api/programs.php/date-%s.json'

    STREAMS = {
        11825154 : STREAM_DR1,
        11823606 : STREAM_DR2,
        11841417 : STREAM_DR_UPDATE,
        25995179 : STREAM_DR_RAMASJANG,
        26000893 : STREAM_DR_K,
        26005640 : STREAM_DR_HD
    }

    def __init__(self, settings):
        Source.__init__(self, settings)

    def getChannelListFromExternal(self):
        response = self._downloadUrl(self.CHANNELS_URL)
        channels = simplejson.loads(response)
        channelList = list()
        for channel in channels:
            logoFile = channel['images']['114x50']['url']

            c = Channel(id = channel['id'], title = channel['name'], logo = logoFile)
            channelList.append(c)

        return channelList

    def getProgramListFromExternal(self, channel, date):
        """

        @param channel:
        @param date:
        @type date: datetime.datetime
        @return:
        """
        dateString = date.strftime('%Y%m%d')
        cacheFile = os.path.join(self.cachePath, '%s-%s-%s.programlist.source' % (self.KEY, channel.id, dateString))
        json = None
        if os.path.exists(cacheFile):
            try:
                json = pickle.load(open(cacheFile))
            except Exception:
                pass

        if not os.path.exists(cacheFile) or json is None:
            response = self._downloadUrl(self.PROGRAMS_URL % date.strftime('%Y%m%d'))
            json = simplejson.loads(response)
            pickle.dump(json, open(cacheFile, 'w'))


        # assume we always find a channel
        programs = list()

        for program in json[str(channel.id)]:
            if program.has_key('review'):
                description = program['review']
            else:
                description = strings(NO_DESCRIPTION)

            programs.append(Program(channel, program['title'], datetime.datetime.fromtimestamp(program['sts']), datetime.datetime.fromtimestamp(program['ets']), description))

        return programs

class XMLTVSource(Source):
    KEY = 'xmltv'

    STREAMS = {
        'DR1.dr.dk' : STREAM_DR1,
        'www.ontv.dk/tv/1' : STREAM_DR1
    }

    def __init__(self, settings):
        self.logoFolder = settings['xmltv.logo.folder']
        self.time = time.time()

        super(XMLTVSource, self).__init__(settings)

        self.xmlTvFile = os.path.join(self.cachePath, '%s.xmltv' % self.KEY)
        if xbmcvfs.exists(settings['xmltv.file']):
            xbmc.log('[script.tvguide] Caching XMLTV file...')
            xbmcvfs.copy(settings['xmltv.file'], self.xmlTvFile)

        # calculate nearest hour
        self.time -= self.time % 3600

    def getChannelListFromExternal(self):
        doc = self._loadXml()
        channelList = list()
        for channel in doc.findall('channel'):
            title = channel.findtext('display-name')
            logo = None
            if self.logoFolder:
                logoFile = os.path.join(self.logoFolder, title + '.png')
                if xbmcvfs.exists(logoFile):
                    logo = logoFile
            if channel.find('icon'):
                logo = channel.find('icon').get('src')
            c = Channel(id = channel.get('id'), title = title, logo = logo)
            channelList.append(c)

        return channelList

    def getProgramListFromExternal(self, channel, date):
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

    def _isProgramListCacheExpired(self, startTime):
        # todo check sources.channel_updated and timestamp on xml file
        return True

    def _loadXml(self):
        f = open(self.xmlTvFile)
        xml = f.read()
        f.close()

        return ElementTree.fromstring(xml)


    def _parseDate(self, dateString):
        dateStringWithoutTimeZone = dateString[:-6]
        t = time.strptime(dateStringWithoutTimeZone, '%Y%m%d%H%M%S')
        return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)

