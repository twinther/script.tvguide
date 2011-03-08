# coding=utf-8
import datetime
import os
import sys
import threading

import xbmc
import xbmcgui
import xbmcplugin

import danishaddons
import danishaddons.web
import navigation

CHANNELS_PER_PAGE = 8

CELL_HEIGHT = 50
CELL_WIDTH = 275
CELL_WIDTH_CHANNELS = 180

HALF_HOUR = datetime.timedelta(minutes = 30)

LABEL_TITLE = 4020
LABEL_TIME = 4021
LABEL_DESCRIPTION = 4022

class TVGuide(xbmcgui.WindowXML):

    def __init__(self, xmlFilename, scriptPath):
        self.source = source.Source()
        self.navigation = navigation.Navigation()
        self.controlToProgramMap = {}

    def onInit(self):
        print "onInit"

        # find nearest half hour
        self.date = datetime.datetime.today()
        self.date -= datetime.timedelta(minutes = self.date.minute % 30)

        self._redraw(0, self.date)


    def _redraw(self, startChannel, startTime):
        print "--- redrawing ---"

        for id in self.controlToProgramMap.keys():
            self.removeControl(self.getControl(id))

        self.controlToProgramMap.clear()
        self.getControl(4200).setVisible(True)
        xbmc.sleep(250)
        try:
            xbmcgui.lock()

            # move timebar to current time
            timeDelta = datetime.datetime.today() - self.date
            c = self.getControl(4100)
            (x, y) = c.getPosition()
            c.setPosition(self._secondsToXposition(timeDelta.seconds), y)

            self.getControl(4500).setVisible(not(self.source.hasChannelIcons()))
            self.getControl(4501).setVisible(self.source.hasChannelIcons())

            # date and time row
            self.getControl(4000).setLabel(self.date.strftime('%a, %d. %b'))
            for col in range(1, 5):
                self.getControl(4000 + col).setLabel(startTime.strftime('%H:%M'))
                startTime += HALF_HOUR

            # channels
            channels = self.source.getChannelList()
            if startChannel < 0:
                startChannel = len(channels) - CHANNELS_PER_PAGE
            elif startChannel > len(channels) - CHANNELS_PER_PAGE:
                startChannel = 0

            for idx, channel in enumerate(channels[startChannel : startChannel + CHANNELS_PER_PAGE]):
                if self.source.hasChannelIcons():
                    self.getControl(4110 + idx).setImage(channel['logo'])
                    print channel['logo']
                else:
                    self.getControl(4010 + idx).setLabel(channel['title'])

                for program in self.source.getProgramList(channel['id']):
                    if program['end_date'] <= self.date:
                        continue

                    startDelta = program['start_date'] - self.date
                    stopDelta = program['end_date'] - self.date

                    cellStart = self._secondsToXposition(startDelta.seconds)
                    if startDelta.days < 0:
                        cellStart = CELL_WIDTH_CHANNELS
                    cellWidth = self._secondsToXposition(stopDelta.seconds) - cellStart
                    if cellStart + cellWidth > 1260:
                        cellWidth = 1260 - cellStart

                    if cellWidth > 1:
                        control = xbmcgui.ControlButton(
                            cellStart,
                            25 + CELL_HEIGHT * (1 + idx),
                            cellWidth,
                            CELL_HEIGHT,
                            program['title'],
                            noFocusTexture = TEXTURE_BUTTON_NOFOCUS,
                            focusTexture = TEXTURE_BUTTON_FOCUS
                        )
                        self.addControl(control)
                        self.controlToProgramMap[control.getId()] = program

            try:
                self.getFocus()
            except TypeError:
                if len(self.controlToProgramMap.keys()) > 0:
                    self.setFocus(self.getControl(self.controlToProgramMap.keys()[0]))

            self.getControl(4200).setVisible(False)

        finally:
            xbmcgui.unlock()

        return startChannel


    def onAction(self, action):
        self.navigation.onAction(action, self, self.controlToProgramMap.keys())

    def onClick(self, controlId):
        print "--- onClick ---"
        print controlId

        program = self.controlToProgramMap[controlId]
        url = self.source.getStreamURL(program['channel_id'])
        if url is None:
            xbmcgui.Dialog().ok('Ingen live stream tilgængelig', 'Kanalen kan ikke afspilles, da der ingen live stream', 'er tilgængelig.')
        else:
                item = xbmcgui.ListItem(program['title'])
                item.setProperty("IsLive", "true")
                xbmc.Player().play(url, item)


    def onFocus(self, controlId):
        print "--- onFocus ---"
        print controlId

        self.navigation.onFocus(self.getControl(controlId))

        program = self.controlToProgramMap[controlId]
        self.getControl(LABEL_TITLE).setLabel('[B]%s[/B]' % program['title'])
        self.getControl(LABEL_TIME).setLabel('[B]%s - %s[/B]' % (program['start_date'].strftime('%H:%M'), program['end_date'].strftime('%H:%M')))
        self.getControl(LABEL_DESCRIPTION).setText(program['description'])


    def _secondsToXposition(self, seconds):
        return CELL_WIDTH_CHANNELS + (seconds * CELL_WIDTH / 1800)

if __name__ == '__main__':
    danishaddons.init(sys.argv)

    TEXTURE_BUTTON_NOFOCUS = os.path.join(danishaddons.ADDON_PATH, 'resources', 'skins', 'Default', 'media', 'cell-bg.png')
    TEXTURE_BUTTON_FOCUS = os.path.join(danishaddons.ADDON_PATH, 'resources', 'skins', 'Default', 'media', 'cell-bg-selected.png')

    # load source plugin based on settings
    if danishaddons.ADDON.getSetting('source') == 'YouSee.tv':
        import youseetv as source
    elif danishaddons.ADDON.getSetting('source') == 'DR.dk':
        import drdk as source

    w = TVGuide('script-tvguide-main.xml', danishaddons.ADDON_PATH)
    w.doModal()
    del w
