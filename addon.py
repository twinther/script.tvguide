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
import buggalo
import xbmc
import xbmcaddon
import xbmcgui
import source as src
import gui
import notification

buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'

try:
    ADDON = xbmcaddon.Addon()
    SOURCE = src.instantiateSource(ADDON)
    xbmc.log("[script.tvguide] Using source: %s" % str(type(SOURCE)), xbmc.LOGDEBUG)

    n = notification.Notification(SOURCE, ADDON.getAddonInfo('path'), xbmc.translatePath(ADDON.getAddonInfo('profile')))
    w = gui.TVGuide(source = SOURCE, notification = n)
    w.doModal()
    del w

except src.SourceUpdateInProgressException:
    xbmcgui.Dialog().ok('error', 'database update in progress...')

except Exception:
    buggalo.onExceptionRaised()
