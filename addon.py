# coding=utf-8
# http://www.dr.dk/tjenester/programoversigt/dbservice.ashx/getChannels?type=tv
# http://www.dr.dk/tjenester/programoversigt/dbservice.ashx/getSchedule?channel_source_url=dr.dk/mas/whatson/channel/DR1&broadcastDate=2010-10-22T00:00:00
import sys
import os
import datetime
import time

import xbmc
import xbmcgui
import xbmcplugin

from danishaddons import *

import simplejson

ACTION_PREVIOUS_MENU = 10

CELL_HEIGHT = 50
CELL_WIDTH = 275

HALF_HOUR = datetime.timedelta(minutes = 30)

class TVGuide(xbmcgui.Window):

	def __init__(self):
		self.channels = simplejson.loads(web.downloadAndCacheUrl('http://www.dr.dk/tjenester/programoversigt/dbservice.ashx/getChannels?type=tv', '/tmp/channels.json', 60))
		self.controlToProgramMap = {}

		# nearest half hour
#		self.date = datetime.datetime(2010, 10, 24, 18, 45)
		self.date = datetime.datetime.today()
		self.date -= datetime.timedelta(minutes = self.date.minute % 30)
		
		self.startTime = self.date
		self.setCoordinateResolution(1) # 720p

#		xbmcgui.lock()

		# date and time row
		self.addControl(xbmcgui.ControlLabel(0, CELL_HEIGHT, 180, CELL_HEIGHT, self.date.strftime('%a, %d. %b')))
		for col in range(0, 4):
			self.addControl(xbmcgui.ControlLabel(180 + CELL_WIDTH * col, CELL_HEIGHT, CELL_WIDTH, CELL_HEIGHT, self.startTime.strftime('%H:%M')))
			self.startTime += HALF_HOUR

		# channels
		for idx, channel in enumerate(self.channels['result']):
			if(idx == 8):
				break

			self.addControl(xbmcgui.ControlLabel(0, CELL_HEIGHT * (idx + 2), 180, CELL_HEIGHT, channel['name']))

			programs = self._loadProgramJson(channel['source_url'])
			print channel['source_url']
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
					self.controlToProgramMap[str(control)] = program

		self.titleControl = xbmcgui.ControlLabel(10, 500, 1260, CELL_HEIGHT, 'Title', 'font18')
		self.addControl(self.titleControl)
		self.descriptionControl = xbmcgui.ControlLabel(10, 550, 1280, 160, 'description')
		self.addControl(self.descriptionControl)

#		xbmcgui.unlock()

	def onAction(self, action):
		if(action == 9):
			self.close()

	def onControl(self, control):
		program = self.controlToProgramMap[str(control)]

		self.titleControl.setLabel(program['pro_title'])
		if(program.has_key('ppu_description')):
			self.descriptionControl.setLabel(program['ppu_description'])
		else:
			self.descriptionControl.setLabel('Ingen beskrivelse')


	def _parseDate(self, dateString):
		t = time.strptime(dateString, '%Y-%m-%dT%H:%M:%S.0000000+02:00')
		return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
		
	def _loadProgramJson(self, slug):
		url = 'http://www.dr.dk/tjenester/programoversigt/dbservice.ashx/getSchedule?channel_source_url=%s&broadcastDate=%s' % (slug, self.date.strftime('%Y-%m-%dT%H:%M:%S'))
		content = web.downloadAndCacheUrl(url, '/tmp/' + slug.replace('/', ''), 60)
		return simplejson.loads(content)
		
w = TVGuide()
w.doModal()
del w
