import addon
import notification
import xbmc

addon.SOURCE.updateChannelAndProgramListCaches()

if addon.SETTINGS['notifications.enabled'] == 'true':
    n = notification.Notification(addon.SOURCE, addon.ADDON.getAddonInfo('path'),
        xbmc.translatePath(addon.ADDON.getAddonInfo('profile')))
    n.scheduleNotifications()