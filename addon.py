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

settings = {
    'cache.path' : xbmc.translatePath(ADDON.getAddonInfo('profile')),
    'xmltv.file' : ADDON.getSetting('xmltv.file'),
    'youseetv.category' : ADDON.getSetting('youseetv.category')
}

w = gui.TVGuide(source = sourceRef(settings))
w.doModal()
del w
