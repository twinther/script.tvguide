import xbmc
import xbmcaddon

import source
import gui


SOURCES = {
    'YouSee.tv' : source.YouSeeTvSource,
    'DR.dk' : source.DrDkSource,
    'TVTID.dk' : source.TvTidSource
    }

ADDON = xbmcaddon.Addon(id = 'script.tvguide')
sourceRef = SOURCES[ADDON.getSetting('source')]

cachePath = xbmc.translatePath(ADDON.getAddonInfo('profile'))
w = gui.TVGuide('script-tvguide-main.xml', ADDON.getAddonInfo('path'), source = sourceRef(cachePath))
w.doModal()
del w
