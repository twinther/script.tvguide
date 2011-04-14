import xbmcaddon

import source
import gui

ADDON = xbmcaddon.Addon(id = 'script.tvguide')

s = None
if ADDON.getSetting('source') == 'YouSee.tv':
    s = source.YouSeeTvSource()
elif ADDON.getSetting('source') == 'DR.dk':
    s = source.DrDkSource()
elif ADDON.getSetting('source') == 'TVTID.dk':
    s = source.TvTidSource()

w = gui.TVGuide('script-tvguide-main.xml', ADDON.getAddonInfo('path'), source = s)
w.doModal()
del w
