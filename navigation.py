import datetime

KEY_LEFT = 1
KEY_RIGHT = 2
KEY_UP = 3
KEY_DOWN = 4
KEY_BACK = 9
KEY_MENU = 10

CHANNELS_PER_PAGE = 8

class Navigation:

	def __init__(self):
		self.controlInFocus = None
		self.focusX = 0

		self.channelIndex = 0

	def onFocus(self, currentControl):
		self.controlInFocus = currentControl

		(left, top) = currentControl.getPosition()
		if left > self.focusX or left + currentControl.getWidth() < self.focusX:
			self.focusX = left

	def onAction(self, action, window, controlIds):
			print "--- onAction ---"
			print "action.id = %d" % action.getId()
			print "self.focusX = %d" % self.focusX

			if action.getId() == KEY_BACK or action.getId() == KEY_MENU:
				window.close()
				return

			(left, top) = self.controlInFocus.getPosition()
			currentX = left + (self.controlInFocus.getWidth() / 2)
			currentY = top + (self.controlInFocus.getHeight() / 2)

			print "currentX = %d, currentY = %d" % (currentX, currentY)

			if action.getId() == KEY_LEFT:
				control = self.findControlOnLeft(window, controlIds, currentX, currentY)
				if control is None:
					window.date -= datetime.timedelta(hours = 2)
					window._redraw(self.channelIndex, window.date)
					control = self.findControlOnLeft(window, window.controlToProgramMap.keys(), 1280, currentY)

				print "setFocus = %s" % control
				(left, top) = control.getPosition()
				self.focusX = left

			elif action.getId() == KEY_RIGHT:
				control = self.findControlOnRight(window, controlIds, currentX, currentY)
				if control is None:
					window.date += datetime.timedelta(hours = 2)
					window._redraw(self.channelIndex, window.date)
					control = self.findControlOnRight(window, window.controlToProgramMap.keys(), 0, currentY)

				print "setFocus = %s" % control
				(left, top) = control.getPosition()
				self.focusX = left

			elif action.getId() == KEY_UP:
				control = self.findControlAbove(window, controlIds, currentX, currentY)
				if control is None:
					self.channelIndex = window._redraw(self.channelIndex - CHANNELS_PER_PAGE, window.date)
					control = self.findControlAbove(window, window.controlToProgramMap.keys(), currentX, 720)

			elif action.getId() == KEY_DOWN:
				control = self.findControlBelow(window, controlIds, currentX, currentY)
				if control is None:
					self.channelIndex = window._redraw(self.channelIndex + CHANNELS_PER_PAGE, window.date)
					control = self.findControlBelow(window, window.controlToProgramMap.keys(), currentX, 0)

			if control is not None:
				window.setFocus(control)


	def findControlOnRight(self, window, controlIds, currentX, currentY):
		distanceToNearest = 10000
		nearestControl = None

		for controlId in controlIds:
			control = window.getControl(controlId)
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


	def findControlOnLeft(self, window, controlIds, currentX, currentY):
		distanceToNearest = 10000
		nearestControl = None

		for controlId in controlIds:
			control = window.getControl(controlId)
			(left, top) = control.getPosition()
			x = left + (control.getWidth() / 2)
			y = top + (control.getHeight() / 2)

			if currentX > x and currentY == y:
				distance = abs(currentX - x)
				if distance < distanceToNearest:
					distanceToNearest = distance
					nearestControl = control

		return nearestControl

	def findControlBelow(self, window, controlIds, currentX, currentY):
		nearestControl = None

		for controlId in controlIds:
			control = window.getControl(controlId)
			(left, top) = control.getPosition()
			x = left + (control.getWidth() / 2)
			y = top + (control.getHeight() / 2)

			if currentY < y:
				if(left <= self.focusX and left + control.getWidth() > self.focusX
					and (nearestControl is None or nearestControl.getPosition()[1] > top)):
					nearestControl = control
					print "nearestControl = %s" % nearestControl

		return nearestControl

	def findControlAbove(self, window, controlIds, currentX, currentY):
		nearestControl = None

		for controlId in controlIds:
			control = window.getControl(controlId)
			(left, top) = control.getPosition()
			x = left + (control.getWidth() / 2)
			y = top + (control.getHeight() / 2)

			if currentY > y:
				if(left <= self.focusX and left + control.getWidth() > self.focusX
					and (nearestControl is None or nearestControl.getPosition()[1] < top)):
					nearestControl = control
					print "nearestControl = %s" % nearestControl

		return nearestControl
