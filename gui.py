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
import datetime

import xbmc
import xbmcgui

import source
from strings import *
import buggalo

ACTION_LEFT = 1
ACTION_RIGHT = 2
ACTION_UP = 3
ACTION_DOWN = 4
ACTION_PAGE_UP = 5
ACTION_PAGE_DOWN = 6
ACTION_SELECT_ITEM = 7
ACTION_PARENT_DIR = 9
ACTION_PREVIOUS_MENU = 10
ACTION_SHOW_INFO = 11
ACTION_NEXT_ITEM = 14
ACTION_PREV_ITEM = 15


KEY_NAV_BACK = 92
KEY_CONTEXT_MENU = 117

CHANNELS_PER_PAGE = 9

CELL_HEIGHT = 50
CELL_WIDTH = 275
CELL_WIDTH_CHANNELS = 180

HALF_HOUR = datetime.timedelta(minutes = 30)

ADDON = xbmcaddon.Addon(id = 'script.tvguide')
TEXTURE_BUTTON_NOFOCUS = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), 'resources', 'skins', 'Default', 'media', 'tvguide-program-grey.png')
TEXTURE_BUTTON_FOCUS = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), 'resources', 'skins', 'Default', 'media', 'tvguide-program-grey-focus.png')
TEXTURE_BUTTON_NOFOCUS_NOTIFY = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), 'resources', 'skins', 'Default', 'media', 'tvguide-program-red.png')
TEXTURE_BUTTON_FOCUS_NOTIFY = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), 'resources', 'skins', 'Default', 'media', 'tvguide-program-red-focus.png')

class TVGuide(xbmcgui.WindowXML):
    C_MAIN_TITLE = 4020
    C_MAIN_TIME = 4021
    C_MAIN_DESCRIPTION = 4022
    C_MAIN_IMAGE = 4023
    C_MAIN_LOGO = 4024
    C_MAIN_LOADING = 4200
    C_MAIN_BACKGROUND = 4600

    def __new__(cls, source, notification):
        return super(TVGuide, cls).__new__(cls, 'script-tvguide-main.xml', ADDON.getAddonInfo('path'))

    def __init__(self,  source, notification):
        """
        @param source: the source of EPG data
        @type source: source.Source
        @type notification: notification.Notification
        """
        super(TVGuide, self).__init__()
        self.source = source
        self.notification = notification
        self.controlToProgramMap = dict()
        self.focusX = 0
        self.page = 0

        # find nearest half hour
        self.viewStartDate = datetime.datetime.today()
        self.viewStartDate -= datetime.timedelta(minutes = self.viewStartDate.minute % 30)

    def onInit(self):
        try:
            self.onRedrawEPG(0, self.viewStartDate)
            self.getControl(self.C_MAIN_IMAGE).setImage('tvguide-logo-%s.png' % self.source.KEY)
        except Exception:
            buggalo.onExceptionRaised()

    def onAction(self, action):
        try:
            if action.getId() in [ACTION_PARENT_DIR, KEY_NAV_BACK]:
                self.close()
                return

            control = None
            controlInFocus = None
            try:
                controlInFocus = self.getFocus()
                (left, top) = controlInFocus.getPosition()
                currentX = left + (controlInFocus.getWidth() / 2)
                currentY = top + (controlInFocus.getHeight() / 2)
            except TypeError:
                currentX = None
                currentY = None

            if action.getId() == ACTION_LEFT:
                control = self._left(currentX, currentY)
            elif action.getId() == ACTION_RIGHT:
                control = self._right(currentX, currentY)
            elif action.getId() == ACTION_UP:
                control = self._up(currentY)
            elif action.getId() == ACTION_DOWN:
                control = self._down(currentY)
            elif action.getId() == ACTION_NEXT_ITEM:
                control= self._nextDay( currentY)
            elif action.getId() == ACTION_PREV_ITEM:
                control= self._previousDay(currentY)
            elif action.getId() == ACTION_PAGE_UP:
                control = self._pageUp()
            elif action.getId() == ACTION_PAGE_DOWN:
                control = self._pageDown()
            elif action.getId() in [KEY_CONTEXT_MENU, ACTION_PREVIOUS_MENU] and controlInFocus is not None:
                program = self._getProgramFromControlId(controlInFocus.getId())
                if program is not None:
                    self._showContextMenu(program, controlInFocus)

            if control is not None:
                self.setFocus(control)

        except Exception:
            buggalo.onExceptionRaised()


    def onClick(self, controlId):
        try:
            program = self._getProgramFromControlId(controlId)
            if program is None:
                return

            if self.source.isPlayable(program.channel):
                self.source.play(program.channel)
            else:
                self._showContextMenu(program, self.getControl(controlId))

        except Exception:
            buggalo.onExceptionRaised()

    def _showContextMenu(self, program, control):
        isNotificationRequiredForProgram = self.notification.isNotificationRequiredForProgram(program)

        d = PopupMenu(self.source, program, not isNotificationRequiredForProgram)
        d.doModal()
        buttonClicked = d.buttonClicked
        del d

        if buttonClicked == PopupMenu.C_POPUP_REMIND:
            if isNotificationRequiredForProgram:
                self.notification.delProgram(program)
            else:
                self.notification.addProgram(program)

            (left, top) = control.getPosition()
            y = top + (control.getHeight() / 2)
            self.onRedrawEPG(self.page, self.viewStartDate, autoChangeFocus = False)
            self.setFocus(self._findControlOnRight(left, y))

        elif buttonClicked == PopupMenu.C_POPUP_CHOOSE_STRM:
            filename = xbmcgui.Dialog().browse(1, ADDON.getLocalizedString(30304), 'video', '.strm')
            if filename:
                self.source.setCustomStreamUrl(program.channel, filename)

        elif buttonClicked == PopupMenu.C_POPUP_PLAY:
            if self.source.isPlayable(program.channel):
                self.source.play(program.channel)

        elif buttonClicked == PopupMenu.C_POPUP_CHANNELS:
            d = ChannelsMenu(self.source)
            d.doModal()
            del d
            self.onRedrawEPG(self.page, self.viewStartDate)

    def onFocus(self, controlId):
        try:
            try:
                controlInFocus = self.getControl(controlId)
            except TypeError:
                return

            program = self._getProgramFromControlId(controlId)
            if program is None:
                return

            (left, top) = controlInFocus.getPosition()
            if left > self.focusX or left + controlInFocus.getWidth() < self.focusX:
                self.focusX = left

            self.getControl(self.C_MAIN_TITLE).setLabel('[B]%s[/B]' % program.title)
            self.getControl(self.C_MAIN_TIME).setLabel('[B]%s - %s[/B]' % (program.startDate.strftime('%H:%M'), program.endDate.strftime('%H:%M')))
            self.getControl(self.C_MAIN_DESCRIPTION).setText(program.description)

            if program.channel.logo is not None:
                self.getControl(self.C_MAIN_LOGO).setImage(program.channel.logo)

            if program.imageSmall is not None:
                self.getControl(self.C_MAIN_IMAGE).setImage(program.imageSmall)

            if ADDON.getSetting('program.background.enabled') == 'true' and program.imageLarge is not None:
                self.getControl(self.C_MAIN_BACKGROUND).setImage(program.imageLarge)

        except Exception:
            buggalo.onExceptionRaised()

    def _left(self, currentX, currentY):
        control = self._findControlOnLeft(currentX, currentY)
        if control is None:
            self.viewStartDate -= datetime.timedelta(hours = 2)
            self.onRedrawEPG(self.page, self.viewStartDate)
            control = self._findControlOnLeft(1280, currentY)

        if control is not None:
            (left, top) = control.getPosition()
            self.focusX = left
        return control

    def _right(self, currentX, currentY):
        control = self._findControlOnRight(currentX, currentY)
        if control is None:
            self.viewStartDate += datetime.timedelta(hours = 2)
            self.onRedrawEPG(self.page, self.viewStartDate)
            control = self._findControlOnRight(0, currentY)

        if control is not None:
            (left, top) = control.getPosition()
            self.focusX = left
        return control

    def _up(self, currentY):
        control = self._findControlAbove(currentY)
        if control is None:
            self.page = self.onRedrawEPG(self.page - 1, self.viewStartDate)
            control = self._findControlAbove(720)
        return control

    def _down(self, currentY):
        control = self._findControlBelow(currentY)
        if control is None:
            self.page = self.onRedrawEPG(self.page + 1, self.viewStartDate)
            control = self._findControlBelow(0)
        return control

    def _nextDay(self, currentY):
        self.viewStartDate += datetime.timedelta(days = 1)
        self.page = self.onRedrawEPG(self.page, self.viewStartDate)
        return self._findControlOnLeft(0, currentY)

    def _previousDay(self, currentY):
        self.viewStartDate -= datetime.timedelta(days = 1)
        self.page = self.onRedrawEPG(self.page, self.viewStartDate)
        return self._findControlOnLeft(1280, currentY)

    def _pageUp(self):
        self.page = self.onRedrawEPG(self.page - 1, self.viewStartDate)
        return self._findControlAbove(720)

    def _pageDown(self):
        self.page = self.onRedrawEPG(self.page+ 1, self.viewStartDate)
        return self._findControlBelow(0)

    def onRedrawEPG(self, page, startTime, autoChangeFocus = True):
        self.getControl(self.C_MAIN_LOADING).setVisible(False)
        for controlId in self.controlToProgramMap:
            self.removeControl(self.getControl(controlId))

        self.controlToProgramMap.clear()

        # move timebar to current time
        timeDelta = datetime.datetime.today() - self.viewStartDate
        c = self.getControl(4100)
        (x, y) = c.getPosition()
        c.setPosition(self._secondsToXposition(timeDelta.seconds), y)

        # date and time row
        self.getControl(4000).setLabel(self.viewStartDate.strftime('%a, %d. %b'))
        for col in range(1, 5):
            self.getControl(4000 + col).setLabel(startTime.strftime('%H:%M'))
            startTime += HALF_HOUR

        # channels
        try:
            channels = self.source.getChannelList()
        except source.SourceException:
            self.onEPGLoadError()
            return page

        totalPages = len(channels) / CHANNELS_PER_PAGE
        if not len(channels) % CHANNELS_PER_PAGE:
            totalPages -= 1

        if page < 0:
            page = totalPages
        elif page > totalPages:
            page = 0

        channelStart = page * CHANNELS_PER_PAGE
        channelEnd = page * CHANNELS_PER_PAGE + CHANNELS_PER_PAGE

        controlsToAdd = list()
        viewChannels = channels[channelStart : channelEnd]
        for idx, channel in enumerate(viewChannels):
            try:
                programs = self.source.getProgramList(channel, self.viewStartDate)
            except source.SourceException:
                self.onEPGLoadError()
                return page

            if programs is None:
                self.onEPGLoadError()
                return page

            for program in programs:
                startDelta = program.startDate - self.viewStartDate
                stopDelta = program.endDate - self.viewStartDate

                cellStart = self._secondsToXposition(startDelta.seconds)
                if startDelta.days < 0:
                    cellStart = CELL_WIDTH_CHANNELS
                cellWidth = self._secondsToXposition(stopDelta.seconds) - cellStart
                if cellStart + cellWidth > 1260:
                    cellWidth = 1260 - cellStart

                if cellWidth > 1:
                    if self.notification.isNotificationRequiredForProgram(program):
                        noFocusTexture = TEXTURE_BUTTON_NOFOCUS_NOTIFY
                        focusTexture = TEXTURE_BUTTON_FOCUS_NOTIFY
                    else:
                        noFocusTexture = TEXTURE_BUTTON_NOFOCUS
                        focusTexture = TEXTURE_BUTTON_FOCUS

                    if cellWidth < 25:
                        title = '' # Text will overflow outside the button if it is too narrow
                    else:
                        title = program.title

                    control = xbmcgui.ControlButton(
                        cellStart,
                        60 + CELL_HEIGHT * idx,
                        cellWidth - 2,
                        CELL_HEIGHT - 2,
                        title,
                        noFocusTexture = noFocusTexture,
                        focusTexture = focusTexture
                    )

                    controlsToAdd.append([control, program])

        # add program controls
        for control, program in controlsToAdd:
            self.addControl(control)
            self.controlToProgramMap[control.getId()] = program

        try:
            self.getFocus()
        except TypeError:
            if len(self.controlToProgramMap.keys()) > 0 and autoChangeFocus:
                self.setFocusId(self.controlToProgramMap.keys()[0])

        # set channel logo or text
        channelsToShow = channels[channelStart : channelEnd]
        for idx in range(0, CHANNELS_PER_PAGE):
            if idx >= len(channelsToShow):
                self.getControl(4110 + idx).setImage('')
                self.getControl(4010 + idx).setLabel('')
            else:
                channel = channelsToShow[idx]
                self.getControl(4010 + idx).setLabel(channel.title)
                if channel.logo is not None:
                    self.getControl(4110 + idx).setImage(channel.logo)
                else:
                    self.getControl(4110 + idx).setImage('')

        self.getControl(self.C_MAIN_LOADING).setVisible(True)
        return page

    def onEPGLoadError(self):
        self.getControl(self.C_MAIN_LOADING).setVisible(True)
        xbmcgui.Dialog().ok(strings(LOAD_ERROR_TITLE), strings(LOAD_ERROR_LINE1), strings(LOAD_ERROR_LINE2))
        self.close()

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

            if currentX < x and currentY == y:
                distance = abs(currentX - x)
                if distance < distanceToNearest:
                    distanceToNearest = distance
                    nearestControl = control

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
            (leftEdge, top) = control.getPosition()
            y = top + (control.getHeight() / 2)

            if currentY < y:
                rightEdge = leftEdge + control.getWidth()
                if(leftEdge <= self.focusX < rightEdge
                   and (nearestControl is None or nearestControl.getPosition()[1] > top)):
                    nearestControl = control

        return nearestControl

    def _findControlAbove(self, currentY):
        nearestControl = None

        for controlId in self.controlToProgramMap.keys():
            control = self.getControl(controlId)
            (leftEdge, top) = control.getPosition()
            y = top + (control.getHeight() / 2)

            if currentY > y:
                rightEdge = leftEdge + control.getWidth()
                if(leftEdge <= self.focusX < rightEdge
                   and (nearestControl is None or nearestControl.getPosition()[1] < top)):
                    nearestControl = control

        return nearestControl

    def _getProgramFromControlId(self, controlId):
        if self.controlToProgramMap.has_key(controlId):
            return self.controlToProgramMap[controlId]
        return None


class PopupMenu(xbmcgui.WindowXMLDialog):
    C_POPUP_PLAY = 4000
    C_POPUP_CHOOSE_STRM = 4001
    C_POPUP_REMIND = 4002
    C_POPUP_CHANNELS = 4003
    C_POPUP_CHANNEL_LOGO = 4100
    C_POPUP_CHANNEL_TITLE = 4101
    C_POPUP_PROGRAM_TITLE = 4102

    def __new__(cls, source, program, showRemind):
        return super(PopupMenu, cls).__new__(cls, 'script-tvguide-menu.xml', ADDON.getAddonInfo('path'))

    def __init__(self, source, program, showRemind):
        """

        @type source: source.Source
        @param program:
        @type program: source.Program
        @param showRemind:
        """
        super(PopupMenu, self).__init__()
        self.source = source
        self.program = program
        self.showRemind = showRemind
        self.buttonClicked = None

    def onInit(self):
        try:
            playControl = self.getControl(self.C_POPUP_PLAY)
            remindControl = self.getControl(self.C_POPUP_REMIND)
            channelLogoControl = self.getControl(self.C_POPUP_CHANNEL_LOGO)
            channelTitleControl = self.getControl(self.C_POPUP_CHANNEL_TITLE)
            programTitleControl = self.getControl(self.C_POPUP_PROGRAM_TITLE)

            playControl.setLabel(strings(WATCH_CHANNEL, self.program.channel.title))
            if not self.source.isPlayable(self.program.channel):
                playControl.setEnabled(False)
                self.setFocusId(self.C_POPUP_CHOOSE_STRM)
            if self.source.getCustomStreamUrl(self.program.channel):
                chooseStrmControl = self.getControl(self.C_POPUP_CHOOSE_STRM)
                chooseStrmControl.setLabel(strings(REMOVE_STRM_FILE))

            if self.program.channel.logo is not None:
                channelLogoControl.setImage(self.program.channel.logo)
                channelTitleControl.setVisible(False)
            else:
                channelTitleControl.setLabel(self.program.channel.title)
                channelLogoControl.setVisible(False)

            programTitleControl.setLabel(self.program.title)

            if self.showRemind:
                remindControl.setLabel(strings(REMIND_PROGRAM))
            else:
                remindControl.setLabel(strings(DONT_REMIND_PROGRAM))

        except Exception:
            buggalo.onExceptionRaised()

    def onAction(self, action):
        try:
            if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK, KEY_CONTEXT_MENU]:
                self.close()
                return
        except Exception:
            buggalo.onExceptionRaised()

    def onClick(self, controlId):
        try:
            if controlId == self.C_POPUP_CHOOSE_STRM and self.source.getCustomStreamUrl(self.program.channel):
                self.source.deleteCustomStreamUrl(self.program.channel)
                chooseStrmControl = self.getControl(self.C_POPUP_CHOOSE_STRM)
                chooseStrmControl.setLabel(strings(CHOOSE_STRM_FILE))

                print self.source.isPlayable(self.program.channel)
                if not self.source.isPlayable(self.program.channel):
                    playControl = self.getControl(self.C_POPUP_PLAY)
                    playControl.setEnabled(False)

            else:
                self.buttonClicked = controlId
                self.close()
        except Exception:
            buggalo.onExceptionRaised()

    def onFocus(self, controlId):
        pass


class ChannelsMenu(xbmcgui.WindowXMLDialog):
    C_CHANNELS_LIST = 6000
    C_CHANNELS_SELECTION_VISIBLE = 6001
    C_CHANNELS_SELECTION = 6002
    C_CHANNELS_SAVE = 6003
    C_CHANNELS_CANCEL = 6004

    def __new__(cls, source):
        return super(ChannelsMenu, cls).__new__(cls, 'script-tvguide-channels.xml', ADDON.getAddonInfo('path'))

    def __init__(self, source):
        """

        @type source: source.Source
        """
        super(ChannelsMenu, self).__init__()
        self.source = source
        self.channelList = source._retrieveChannelListFromDatabase(False)

    def onInit(self):
        try:
            self.updateChannelList()
            self.setFocusId(self.C_CHANNELS_LIST)

        except Exception:
            buggalo.onExceptionRaised()

    def onAction(self, action):
        try:
            if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK, KEY_CONTEXT_MENU]:
                self.close()
                return

            if self.getFocusId() == self.C_CHANNELS_LIST and action.getId() == ACTION_LEFT:
                listControl = self.getControl(self.C_CHANNELS_LIST)
                idx = listControl.getSelectedPosition()
                buttonControl = self.getControl(self.C_CHANNELS_SELECTION)
                buttonControl.setLabel('[B]%s[/B]' % self.channelList[idx].title)

                self.getControl(self.C_CHANNELS_SELECTION_VISIBLE).setVisible(False)
                self.setFocusId(self.C_CHANNELS_SELECTION)

            elif self.getFocusId() == self.C_CHANNELS_SELECTION and action.getId() in [ACTION_RIGHT, ACTION_SELECT_ITEM]:
                self.getControl(self.C_CHANNELS_SELECTION_VISIBLE).setVisible(True)
                xbmc.sleep(350)
                self.setFocusId(self.C_CHANNELS_LIST)

            elif self.getFocusId() == self.C_CHANNELS_SELECTION and action.getId() == ACTION_UP:
                listControl = self.getControl(self.C_CHANNELS_LIST)
                idx = listControl.getSelectedPosition()
                self.swapChannels(idx, idx - 1)
                listControl.selectItem(idx - 1)

            elif self.getFocusId() == self.C_CHANNELS_SELECTION and action.getId() == ACTION_DOWN:
                listControl = self.getControl(self.C_CHANNELS_LIST)
                idx = listControl.getSelectedPosition()
                self.swapChannels(idx, idx + 1)
                listControl.selectItem(idx + 1)

        except Exception:
            buggalo.onExceptionRaised()

    def onClick(self, controlId):
        try:
            if controlId == self.C_CHANNELS_LIST:
                listControl = self.getControl(self.C_CHANNELS_LIST)
                item = listControl.getSelectedItem()
                channel = self.channelList[int(item.getProperty('idx'))]
                channel.visible = not channel.visible

                if channel.visible:
                    iconImage = 'tvguide-channel-visible.png'
                else:
                    iconImage = 'tvguide-channel-hidden.png'
                item.setIconImage(iconImage)

            elif controlId == self.C_CHANNELS_SAVE:
                self.source._storeChannelListInDatabase(self.channelList)
                self.close()

            elif controlId == self.C_CHANNELS_CANCEL:
                self.close()

        except Exception:
            buggalo.onExceptionRaised()

    def onFocus(self, controlId):
        pass

    def updateChannelList(self):
        listControl = self.getControl(self.C_CHANNELS_LIST)
        listControl.reset()
        for idx, channel in enumerate(self.channelList):
            if channel.visible:
                iconImage = 'tvguide-channel-visible.png'
            else:
                iconImage = 'tvguide-channel-hidden.png'

            item = xbmcgui.ListItem('%3d. %s' % (idx+1, channel.title), iconImage = iconImage)
            item.setProperty('idx', str(idx))
            listControl.addItem(item)

    def updateListItem(self, idx, item = None):
        if item is None:
            item = xbmcgui.ListItem()
        channel = self.channelList[idx]
        item.setLabel('%3d. %s' % (idx+1, channel.title))

        if channel.visible:
            iconImage = 'tvguide-channel-visible.png'
        else:
            iconImage = 'tvguide-channel-hidden.png'
        item.setIconImage(iconImage)
        item.setProperty('idx', str(idx))

    def swapChannels(self, fromIdx, toIdx):
        c = self.channelList[fromIdx]
        self.channelList[fromIdx] = self.channelList[toIdx]
        self.channelList[toIdx] = c

        # recalculate weight
        for idx, channel in enumerate(self.channelList):
            channel.weight = idx

        listControl = self.getControl(self.C_CHANNELS_LIST)
        self.updateListItem(fromIdx, listControl.getListItem(fromIdx))
        self.updateListItem(toIdx, listControl.getListItem(toIdx))



