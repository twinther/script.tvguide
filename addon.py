# coding=utf-8
# http://www.dr.dk/tjenester/programoversigt/dbservice.ashx/getChannels?type=tv
# http://www.dr.dk/tjenester/programoversigt/dbservice.ashx/getSchedule?channel_source_url=dr.dk/mas/whatson/channel/DR1&broadcastDate=2010-10-22T00:00:00
import sys
import os
import datetime
import time
import math

import xbmc
import xbmcgui
import xbmcplugin

from danishaddons import *

import simplejson

ACTION_PREVIOUS_MENU = 10

CELL_HEIGHT = 50
CELL_WIDTH = 275

HALF_HOUR = datetime.timedelta(minutes = 30)

class TVGuide(xbmcgui.WindowXML):

	def __init__(self, xmlFilename, scriptPath):
		self.channels = simplejson.loads(web.downloadAndCacheUrl('http://www.dr.dk/tjenester/programoversigt/dbservice.ashx/getChannels?type=tv', '/tmp/channels.json', 60))
		self.controlToProgramMap = {}

	def onInit(self):
		print "onInit"

		# nearest half hour
#		self.date = datetime.datetime(2010, 10, 24, 18, 45)
		self.date = datetime.datetime.today()
		self.date -= datetime.timedelta(minutes = self.date.minute % 30)
		
		self.startTime = self.date

#		xbmcgui.lock()

		# date and time row
		self.getControl(4000).setLabel(self.date.strftime('%a, %d. %b'))
		for col in range(1, 5):
			self.getControl(4000 + col).setLabel(self.startTime.strftime('%H:%M'))
			self.startTime += HALF_HOUR

		# channels
		for idx, channel in enumerate(self.channels['result']):
			if(idx == 8):
				break

			self.getControl(4010 + idx).setLabel(channel['name'])

			programs = self._loadProgramJson(channel['source_url'])
			for program in programs['result']:
				pgStart = self._parseDate(program['pg_start'])
				pgStop = self._parseDate(program['pg_stop'])
				if(pgStop <= self.date):
					continue

				startDelta = pgStart - self.date
				stopDelta = pgStop - self.date

				cellStart = 180 + (startDelta.seconds * CELL_WIDTH / 1800)
				if(startDelta.days < 0):
					cellStart = 180
				cellWidth = 180 + (stopDelta.seconds * CELL_WIDTH / 1800) - cellStart
				if(cellStart + cellWidth > 1280):
					cellWidth = 1280 - cellStart

				if(cellWidth > 1):
					control = xbmcgui.ControlButton(cellStart, CELL_HEIGHT * (2 + idx), cellWidth, CELL_HEIGHT, program['pro_title'])
					self.addControl(control)
					self.controlToProgramMap[control.getId()] = program


		self.numberOfControls = control.getId()

		for i in range(1, self.numberOfControls + 1):
			c = self.getControl(i)
			if(i > 1):
				c.controlLeft(self.getControl(i - 1))
			if(i < control.getId()):
				c.controlRight(self.getControl(i + 1))

			below = self._findNearestControlBelow(c)
			above = self._findNearestControlAbove(c)
			if(not(below == None)):
				c.controlDown(below)
			if(not(above == None)):
				c.controlUp(above)


#		xbmcgui.unlock()

	def _findNearestControlBelow(self, control):
		(x, y) = control.getPosition()
		nearestControl = None
		minX = 10000
		minY = None
		for i in range(1, self.numberOfControls + 1):
			c = self.getControl(i)
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
		for i in range(self.numberOfControls, 0, -1):
			c = self.getControl(i)
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
		print action
		if(action.getId() == 9):
			self.close()

		pass

	def onClick(self, controlId):
		print "onClick"
		print controlId


	def onFocus(self, controlId):
		print "onFocus"
		print controlId

		program = self.controlToProgramMap[controlId]

		self.getControl(4020).setLabel(program['pro_title'])
		if(program.has_key('ppu_description')):
			self.getControl(4021).setLabel(program['ppu_description'])
		else:
			self.getControl(4021).setLabel('Ingen beskrivelse')

	def _parseDate(self, dateString):
		t = time.strptime(dateString, '%Y-%m-%dT%H:%M:%S.0000000+02:00')
		return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
		
	def _loadProgramJson(self, slug):
		url = 'http://www.dr.dk/tjenester/programoversigt/dbservice.ashx/getSchedule?channel_source_url=%s&broadcastDate=%s' % (slug, self.date.strftime('%Y-%m-%dT%H:%M:%S'))
		content = web.downloadAndCacheUrl(url, '/tmp/' + slug.replace('/', ''), 60)
		return simplejson.loads(content)
		
w = TVGuide('script-tvguide-main.xml', os.getcwd())
w.doModal()
del w
