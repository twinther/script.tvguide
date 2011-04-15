# coding=utf-8

import os
import datetime

import xbmc
import xbmcaddon
import xbmcgui

KEY_LEFT = 1
KEY_RIGHT = 2
KEY_UP = 3
KEY_DOWN = 4
KEY_PAGE_UP = 5
KEY_PAGE_DOWN = 6
KEY_BACK = 9
KEY_MENU = 10

CHANNELS_PER_PAGE = 8

CELL_HEIGHT = 50
CELL_WIDTH = 275
CELL_WIDTH_CHANNELS = 180

HALF_HOUR = datetime.timedelta(minutes = 30)

LABEL_TITLE = 4020
LABEL_TIME = 4021
LABEL_DESCRIPTION = 4022

ADDON = xbmcaddon.Addon(id = 'script.tvguide')
TEXTURE_BUTTON_NOFOCUS = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), 'resources', 'skins', 'Default', 'media', 'cell-bg.png')
TEXTURE_BUTTON_FOCUS = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), 'resources', 'skins', 'Default', 'media', 'cell-bg-selected.png')


class TVGuide(xbmcgui.WindowXML):
    def __init__(self, xmlFilename, scriptPath, source):
        xbmcgui.WindowXML.__init__(self, xmlFilename, scriptPath)
        
        self.source = source
        self.controlToProgramMap = {}
        self.controlInFocus = None
        self.focusX = 0
        self.channelIndex = 0


    def onInit(self):
        print "onInit"

        # find nearest half hour
        self.date = datetime.datetime.today()
        self.date -= datetime.timedelta(minutes = self.date.minute % 30)

        self._redraw(0, self.date)

    def onAction(self, action):
        print "--- onAction ---"
        print "action.id = %d" % action.getId()
        print "self.focusX = %d" % self.focusX

        if action.getId() == KEY_BACK or action.getId() == KEY_MENU:
            self.close()
            return

        (left, top) = self.controlInFocus.getPosition()
        currentX = left + (self.controlInFocus.getWidth() / 2)
        currentY = top + (self.controlInFocus.getHeight() / 2)

        print "currentX = %d, currentY = %d" % (currentX, currentY)

        control = None

        if action.getId() == KEY_LEFT:
            control = self._left(currentX, currentY)
        elif action.getId() == KEY_RIGHT:
            control = self._right(currentX, currentY)
        elif action.getId() == KEY_UP:
            control = self._up(currentY)
        elif action.getId() == KEY_DOWN:
            control = self._down(currentY)
        elif action.getId() == KEY_PAGE_UP:
            control = self._pageUp()
        elif action.getId() == KEY_PAGE_DOWN:
            control = self._pageDown()

        if control is not None:
            self.setFocus(control)


    def onClick(self, controlId):
        print "--- onClick ---"
        print controlId

        program = self.controlToProgramMap[controlId]
        url = program.streamUrl
        if url is None:
            xbmcgui.Dialog().ok('Ingen live stream tilgængelig', 'Kanalen kan ikke afspilles, da der ingen live stream', 'er tilgængelig.')
        else:
            item = xbmcgui.ListItem(program.title)
            item.setProperty("IsLive", "true")
            xbmc.Player().play(url, item)


    def onFocus(self, controlId):
        print "--- onFocus ---"
        print controlId

        self.controlInFocus = self.getControl(controlId)
        (left, top) = self.controlInFocus.getPosition()
        if left > self.focusX or left + self.controlInFocus.getWidth() < self.focusX:
            self.focusX = left


        program = self.controlToProgramMap[controlId]
        self.getControl(LABEL_TITLE).setLabel('[B]%s[/B]' % program.title)
        self.getControl(LABEL_TIME).setLabel('[B]%s - %s[/B]' % (program.startDate.strftime('%H:%M'), program.endDate.strftime('%H:%M')))
        self.getControl(LABEL_DESCRIPTION).setText(program.description)

    def _left(self, currentX, currentY):
        control = self._findControlOnLeft(currentX, currentY)
        if control is None:
            self.date -= datetime.timedelta(hours = 2)
            self._redraw(self.channelIndex, self.date)
            control = self._findControlOnLeft(1280, currentY)

        (left, top) = control.getPosition()
        self.focusX = left
        return control

    def _right(self, currentX, currentY):
        control = self._findControlOnRight(currentX, currentY)
        if control is None:
            self.date += datetime.timedelta(hours = 2)
            self._redraw(self.channelIndex, self.date)
            control = self._findControlOnRight(0, currentY)

        (left, top) = control.getPosition()
        self.focusX = left
        return control

    def _up(self, currentY):
        control = self._findControlAbove(currentY)
        if control is None:
            self.channelIndex = self._redraw(self.channelIndex - CHANNELS_PER_PAGE, self.date)
            control = self._findControlAbove(720)
        return control

    def _down(self, currentY):
        control = self._findControlBelow(currentY)
        if control is None:
            self.channelIndex = self._redraw(self.channelIndex + CHANNELS_PER_PAGE, self.date)
            control = self._findControlBelow(0)
        return control

    def _pageUp(self):
        self.channelIndex = self._redraw(self.channelIndex - CHANNELS_PER_PAGE, self.date)
        return self._findControlAbove(720)

    def _pageDown(self):
        self.channelIndex = self._redraw(self.channelIndex + CHANNELS_PER_PAGE, self.date)
        return self._findControlBelow(0)

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
                    self.getControl(4110 + idx).setImage(channel.logoUrl)
                    print channel.logoUrl
                else:
                    self.getControl(4010 + idx).setLabel(channel.title)

                for program in self.source.getProgramList(channel):
                    if program.endDate <= self.date:
                        continue

                    startDelta = program.startDate - self.date
                    stopDelta = program.endDate - self.date

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
                            program.title,
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


    def _secondsToXposition(self, seconds):
        return CELL_WIDTH_CHANNELS + (seconds * CELL_WIDTH / 1800)

    def _findControlOnRight(self, currentX, currentY):
        distanceToNearest = 10000
        nearestControl = None

        for controlId in self.controlToProgramMap.keys():
            control = self.getControl(controlId)
            (left, top) = control.getPosition()
            x = left + (control.getWidth() / 2)
            y = top + (control.getHeight() / 2)

            print "x = %d, y = %d" % (x, y)

            if currentX < x and currentY == y:
                distance = abs(currentX - x)
                print "distance = %d" % distance
                if distance < distanceToNearest:
                    distanceToNearest = distance
                    nearestControl = control

        print "nearestControl = %s" % nearestControl
        return nearestControl


    def _findControlOnLeft(self, currentX, currentY):
        distanceToNearest = 10000
        nearestControl = None

        for controlId in self.controlToProgramMap.keys():
            control = self.getControl(controlId)
            (left, top) = control.getPosition()
            x = left + (control.getWidth() / 2)
            y = top + (control.getHeight() / 2)

            if currentX > x and currentY == y:
                distance = abs(currentX - x)
                if distance < distanceToNearest:
                    distanceToNearest = distance
                    nearestControl = control

        return nearestControl

    def _findControlBelow(self, currentY):
        nearestControl = None

        for controlId in self.controlToProgramMap.keys():
            control = self.getControl(controlId)
            (left, top) = control.getPosition()
            y = top + (control.getHeight() / 2)

            if currentY < y:
                if(left <= self.focusX and left + control.getWidth() > self.focusX
                    and (nearestControl is None or nearestControl.getPosition()[1] > top)):
                    nearestControl = control
                    print "nearestControl = %s" % nearestControl

        return nearestControl

    def _findControlAbove(self, currentY):
        nearestControl = None

        for controlId in self.controlToProgramMap.keys():
            control = self.getControl(controlId)
            (left, top) = control.getPosition()
            y = top + (control.getHeight() / 2)

            if currentY > y:
                if(left <= self.focusX and left + control.getWidth() > self.focusX
                    and (nearestControl is None or nearestControl.getPosition()[1] < top)):
                    nearestControl = control
                    print "nearestControl = %s" % nearestControl

        return nearestControl
