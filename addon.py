import xbmc
import xbmcaddon

import source
import gui


SOURCES = {
    'YouSee.tv' : source.YouSeeTvSource,
    'DR.dk' : source.DrDkSource,
    'TVTID.dk' : source.TvTidSource,
    'XMLTV' : source.XMLTVSource
    }

ADDON = xbmcaddon.Addon(id = 'script.tvguide')
sourceRef = SOURCES[ADDON.getSetting('source')]

if ADDON.getSetting('source') == 'XMLTV':
    path = ADDON.getSetting('xmltv.file')
else:
    path = xbmc.translatePath(ADDON.getAddonInfo('profile'))

w = gui.TVGuide('script-tvguide-main.xml', ADDON.getAddonInfo('path'), source = sourceRef(path))
w.doModal()
del w
