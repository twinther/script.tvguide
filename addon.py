# coding=utf-8
import sys
import os
import datetime
import time
import math

import xbmc
import xbmcgui
import xbmcplugin


from danishaddons import *
import drdk as source

ACTION_PREVIOUS_MENU = 10

CELL_HEIGHT = 50
CELL_WIDTH = 275
CELL_WIDTH_CHANNELS = 180

HALF_HOUR = datetime.timedelta(minutes = 30)

LABEL_TITLE = 4020
LABEL_TIME = 4021
LABEL_DESCRIPTION = 4022

TEXTURE_BUTTON_NOFOCUS = os.path.join(os.getcwd(), 'resources', 'skins', 'Default', 'media', 'cell-bg.png')
TEXTURE_BUTTON_FOCUS = os.path.join(os.getcwd(), 'resources', 'skins', 'Default', 'media', 'cell-bg-selected.png')

class TVGuide(xbmcgui.WindowXML):

	def __init__(self, xmlFilename, scriptPath):
		self.source = source.Source()
		self.controlToProgramMap = {}
		self.focusControl = None

	def onInit(self):
		print "onInit"

		# nearest half hour
		self.date = datetime.datetime.today()
		self.date -= datetime.timedelta(minutes = self.date.minute % 30)

		self.channel = 0
	
		self._redraw(self.channel, self.date)

	def _redraw(self, startChannel, startTime):
		for id in self.controlToProgramMap.keys():
			self.removeControl(self.getControl(id))

		self.controlToProgramMap.clear()

		# move timebar to current time
		timeDelta = datetime.datetime.today() - self.date
		c = self.getControl(4100)
		(x, y) = c.getPosition()
		c.setPosition(self._secondsToXposition(timeDelta.seconds), y)

		try:
			xbmcgui.lock()

			# date and time row
			self.getControl(4000).setLabel(self.date.strftime('%a, %d. %b'))
			for col in range(1, 5):
				self.getControl(4000 + col).setLabel(startTime.strftime('%H:%M'))
				startTime += HALF_HOUR

			# channels
			for idx, channel in enumerate(self.source.getChannelList()[startChannel : startChannel + 8]):
				self.getControl(4010 + idx).setLabel(channel['title'])

				previousControl = None
				for program in self.source.getProgramList(channel['id']):
					if(program['end_date'] <= self.date):
						continue

					startDelta = program['start_date'] - self.date
					stopDelta = program['end_date'] - self.date

					cellStart = self._secondsToXposition(startDelta.seconds)
					if(startDelta.days < 0):
						cellStart = CELL_WIDTH_CHANNELS
					cellWidth = self._secondsToXposition(stopDelta.seconds) - cellStart
					if(cellStart + cellWidth > 1280):
						cellWidth = 1280 - cellStart

					if(cellWidth > 1):
						control = xbmcgui.ControlButton(cellStart, 25 + CELL_HEIGHT * (1 + idx), cellWidth, CELL_HEIGHT, program['title'], noFocusTexture = TEXTURE_BUTTON_NOFOCUS, focusTexture = TEXTURE_BUTTON_FOCUS)
						self.addControl(control)
						self.controlToProgramMap[control.getId()] = program

						if(not(previousControl == None)):
							control.controlLeft(previousControl)
							previousControl.controlRight(control)

						previousControl = control

			for idx, id in enumerate(self.controlToProgramMap.keys()):
				c = self.getControl(id)

				below = self._findNearestControlBelow(c)
				above = self._findNearestControlAbove(c)
				if(not(below == None)):
					c.controlDown(below)
				if(not(above == None)):
					c.controlUp(above)

			self.setFocus(self.getControl(self.controlToProgramMap.keys()[0]))

		finally:
			xbmcgui.unlock()

	

	def _findNearestControlBelow(self, control):
		(x, y) = control.getPosition()
		nearestControl = None
		minX = 10000
		minY = None
		for id in self.controlToProgramMap.keys():
			c = self.getControl(id)
			(cx, cy) = c.getPosition()
			if(y >= cy):
				continue

			if(not(minY == None) and abs(cy - y) > minY):
				break

			minY = abs(cy - y)
			deltaX = abs(cx - x)

			if(deltaX < minX):
				minX = deltaX
				nearestControl = c

		return nearestControl

	def _findNearestControlAbove(self, control):
		(x, y) = control.getPosition()
		nearestControl = None
		minX = 10000
		minY = None
		keys = self.controlToProgramMap.keys()
		keys.reverse()
		for id in keys:
			c = self.getControl(id)
			(cx, cy) = c.getPosition()
			if(y <= cy):
				continue

			if(not(minY == None) and abs(cy - y) > minY):
				break

			minY = abs(cy - y)
			deltaX = abs(cx - x)

			if(deltaX < minX):
				minX = deltaX
				nearestControl = c

		return nearestControl


	def onAction(self, action):
		print "onAction"
		print "action.id = %d" % action.getId()
		print action.getButtonCode()

		control = self.getFocus()
		print control
		print self.focusControl

		if(action.getId() == 9):
			self.close()
		elif(self.focusControl == control):
			# focus didn't change, reload the grid
			if(action.getId() == 1): # Left
				self.date -= datetime.timedelta(hours = 2)
				self._redraw(self.channel, self.date)

			elif(action.getId() == 2): # Right
				self.date += datetime.timedelta(hours = 2)
				self._redraw(self.channel, self.date)

			elif(action.getId() == 3): # Up
				self.channel -= 8
				if(self.channel < 0):
					self.channel = 0
				self._redraw(self.channel, self.date)
				
			elif(action.getId() == 4): # Down
				self.channel += 8
				self._redraw(self.channel, self.date)

		try:
			self.focusControl = self.getFocus()
		except TypeError:
			pass


	def onClick(self, controlId):
		print "onClick"
		print controlId

		program = self.controlToProgramMap[controlId]
		url = self.source.getStreamURL(program['channel_id'])
		if(url == None):
			xbmcgui.Dialog().ok('Ingen live stream tilgængelig', 'Kanalen kan ikke afspilles, da der ingen live stream', 'er tilgængelig.')
		else:
				item = xbmcgui.ListItem(program['title'])
				item.setProperty("IsLive", "true")
				xbmc.Player().play(url, item)


	def onFocus(self, controlId):
		print "onFocus"
		print controlId

		program = self.controlToProgramMap[controlId]

		self.getControl(LABEL_TITLE).setLabel('[B]%s[/B]' % program['title'])
		self.getControl(LABEL_TIME).setLabel('%s - %s' % (program['start_date'].strftime('%H:%M'), program['end_date'].strftime('%H:%M')))
		self.getControl(LABEL_DESCRIPTION).setLabel(program['description'])

	def _secondsToXposition(self, seconds):
		return CELL_WIDTH_CHANNELS + (seconds * CELL_WIDTH / 1800)
		
w = TVGuide('script-tvguide-main.xml', os.getcwd())
w.doModal()
del w
