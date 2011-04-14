import danishaddons
import danishaddons.web


if __name__ == '__main__':
    danishaddons.init(sys.argv)

    TEXTURE_BUTTON_NOFOCUS = os.path.join(danishaddons.ADDON_PATH, 'resources', 'skins', 'Default', 'media', 'cell-bg.png')
    TEXTURE_BUTTON_FOCUS = os.path.join(danishaddons.ADDON_PATH, 'resources', 'skins', 'Default', 'media', 'cell-bg-selected.png')

    # load source plugin based on settings
    if danishaddons.ADDON.getSetting('source') == 'YouSee.tv':
        import youseetv as source
    elif danishaddons.ADDON.getSetting('source') == 'DR.dk':
        import drdk as source

    w = TVGuide('script-tvguide-main.xml', danishaddons.ADDON_PATH)
    w.doModal()
    del w
