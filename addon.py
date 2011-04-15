import xbmcaddon

import source
import gui

ADDON = xbmcaddon.Addon(id = 'script.tvguide')

SOURCES = {
    'YouSee.tv' : source.YouSeeTvSource,
    'DR.dk' : source.DrDkSource,
    'TVTID.dk' : source.TvTidSource
    }

sourceRef = SOURCES[ADDON.getSetting('source')]

cachePath = ADDON.getAddonInfo('profile')
w = gui.TVGuide('script-tvguide-main.xml', ADDON.getAddonInfo('path'), source = sourceRef(cachePath))
w.doModal()
del w
