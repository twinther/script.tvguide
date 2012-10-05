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
import xbmc
from xml.etree import ElementTree
from xml.parsers.expat import ExpatError
import ConfigParser
import os
import xbmcaddon

class StreamsService(object):
    def __init__(self):
        path = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'addons.ini')
        self.addonsParser = ConfigParser.ConfigParser()
        self.addonsParser.optionxform = lambda option: option
        self.addonsParser.read(path)

    def loadFavourites(self):
        entries = list()
        path = xbmc.translatePath('special://userdata/favourites.xml')
        if os.path.exists(path):
            f = open(path)
            xml = f.read()
            f.close()

            try:
                doc = ElementTree.fromstring(xml)
                for node in doc.findall('favourite'):
                    value = node.text
                    if value[0:11] == 'PlayMedia("':
                        value = value[11:-2]
                    elif value[0:10] == 'PlayMedia(':
                        value = value[10:-1]
                    else:
                        continue

                    entries.append((node.get('name'), value))
            except ExpatError:
                pass

        return entries

    def getAddons(self):
        return self.addonsParser.sections()

    def getAddonStreams(self, id):
        return self.addonsParser.items(id)

    def detectStream(self, channel):
        """
        @param channel:
        @type channel: source.Channel
        """
        favourites = self.loadFavourites()

        # First check favourites, if we get exact match we use it
        for label, stream in favourites:
            if label == channel.title:
                return stream


        # Second check all addons and return all matches
        matches = list()
        for id in self.getAddons():
            try:
                xbmcaddon.Addon(id)
            except Exception:
                continue # ignore addons that are not installed

            for (label, stream) in self.getAddonStreams(id):
                if label == channel.title:
                    matches.append((id, label, stream))

        if len(matches) == 1:
            return matches[0][2]
        else:
            return matches


