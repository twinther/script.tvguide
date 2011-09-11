import datetime
import os
import xbmc

from strings import *

try:
    # Used by Eden/external python
    from sqlite3 import dbapi2 as sqlite3
except ImportError:
    # Used by Dharma/internal python
    from pysqlite2 import dbapi2 as sqlite3

class Notification(object):
    NOTIFICATION_DB = 'notification.db'

    def __init__(self, source, addonPath, dataPath):
        self.source = source
        self.addonPath = addonPath

        self.conn = sqlite3.connect(os.path.join(dataPath, self.NOTIFICATION_DB), check_same_thread = False)
        self._createTables()

    def __del__(self):
        self.conn.close()

    def scheduleNotifications(self):
        print "Scheduling program notifications"
        programs = self.getPrograms()
        icon = os.path.join(self.addonPath, 'icon.png')
        now = datetime.datetime.now()

        for channel in self.source.getChannelList():
            for program in self.source.getProgramList(channel):
                for nChannel, nProgram in programs:
                    if nChannel == channel.id and nProgram == program.title and (program.startDate - now).days == 0:
                        timeToNotification = (program.startDate - now).seconds / 60

                        id = 'tvguide-%s-%s' % (channel.id, program.startDate)
                        description = strings(NOTIFICATION_TEMPLATE, channel.title)

                        xbmc.executebuiltin("AlarmClock(%s,Notification(%s,%s,10000,%s),%d,True)" %
                            (id, program.title, description, icon, timeToNotification - 5))

    def addProgram(self, program):
        """
        @type program: source.program
        """
        c = self.conn.cursor()
        c.execute("INSERT INTO notification(channel, program) VALUES(?, ?)", [program.channel.id, program.title])
        self.conn.commit()
        c.close()

    def delProgram(self, program):
        """
        @type program: source.program
        """
        c = self.conn.cursor()
        c.execute("DELETE FROM notification WHERE channel=? AND program=?", [program.channel.id, program.title])
        self.conn.commit()
        c.close()

    def getPrograms(self):
        c = self.conn.cursor()
        c.execute("SELECT DISTINCT channel, program FROM notification")
        programs = c.fetchall()
        c.close()

        return [program[0] for program in programs]

    def isNotificationRequiredForProgram(self, program):
        """
        @type program: source.program
        """
        c = self.conn.cursor()
        c.execute("SELECT 1 FROM notification WHERE channel=? AND program=?", [program.channel.id, program.title])
        result = c.fetchone()
        c.close()

        return result

    def _createTables(self):
        c = self.conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS notification (channel TEXT, program TEXT)")
        c.close()