import addon
import notification
import xbmc

if addon.SETTINGS['cache.data.on.xbmc.startup'] == 'true':
    try:
        addon.SOURCE.updateChannelAndProgramListCaches()
    except Exception:
        xbmc.log('[script.tvguide] Unable to update caches!')

if addon.SETTINGS['notifications.enabled'] == 'true':
    try:
        n = notification.Notification(addon.SOURCE, addon.ADDON.getAddonInfo('path'),
            xbmc.translatePath(addon.ADDON.getAddonInfo('profile')))
        n.scheduleNotifications()
    except Exception:
        xbmc.log('[script.tvguide] Unable to schedules notifications!')