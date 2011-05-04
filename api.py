__author__ = 'tommy'

CHANNEL_DK_DR1, \
CHANNEL_DK_DR2, \
CHANNEL_DK_DRK, \
CHANNEL_DK_DR_UPDATE, \
CHANNEL_DK_DR_RAMASJANG, \
CHANNEL_DK_DRHD, \
CHANNEL_DK_TV2, \
CHANNEL_DK_TV2ZULU, \
CHANNEL_DK_TV2CHARLIE, \
CHANNEL_DK_TV2NEWS, \
CHANNEL_DK_TV3, \
CHANNEL_DK_TV3PLUS, \
CHANNEL_DK_TV3PULS, \
CHANNEL_DK_DK4, \
CHANNEL_DK_KANAL4, \
CHANNEL_DK_KANAL5, \
CHANNEL_DK_KANAL5HD, \
CHANNEL_DK_6EREN, \
CHANNEL_DK_CANAL9, \
CHANNEL_DK_FOLKETINGET, \
CHANNEL_SV_SVT1, \
CHANNEL_SV_SVT2, \
CHANNEL_SV_TV4, \
CHANNEL_NO_NRK1, \
CHANNEL_DE_ARD, \
CHANNEL_DE_ZDF, \
CHANNEL_DE_RTL, \
CHANNEL_DE_NDR, \
  = range(28)

class WebTvLookup(dict):
    """
    a dictionary which can lookup value by key, or keys by value
    """
    def __init__(self, items=[]):
        """items can be a list of pair_lists or a dictionary"""
        dict.__init__(self, items)

    def get_key(self, value):
        """find the key(s) as a list given a value"""
        for item in self.items():
            if item[1] == value:
                return item[0]
        return None

    def get_value(self, key):
        """find the value given a key"""
        if self.has_key(key):
            return self[key]
        else:
            return None

    def has_value(self, key):
        return self.get_value(key) is not None

class WebTvProvider(object):

    def getAvailableChannels(self):
        """Returns a list of CHANNEL_* values"""
        raise Exception('Not implemented')

    def playChannel(self, id):
        raise Exception('Not implemented')
  