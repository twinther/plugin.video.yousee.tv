import os
import sys
import cgi as urlparse
import urllib2
import StringIO

import ysapi

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

class YouSeeTv(object):
    def showOverview(self):
        iconImage = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

        item = xbmcgui.ListItem(ADDON.getLocalizedString(30000), iconImage = iconImage)
        item.setProperty('Fanart_Image', FANART_IMAGE)
        url = PATH + '?area=livetv'
        xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        item = xbmcgui.ListItem(ADDON.getLocalizedString(30001), iconImage = iconImage)
        item.setProperty('Fanart_Image', FANART_IMAGE)
        url = PATH + '?area=movie-genre'
        xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        item = xbmcgui.ListItem(ADDON.getLocalizedString(30002), iconImage = iconImage)
        item.setProperty('Fanart_Image', FANART_IMAGE)
        url = PATH + '?area=movie-theme'
        xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        item = xbmcgui.ListItem(ADDON.getLocalizedString(30003), iconImage = iconImage)
        item.setProperty('Fanart_Image', FANART_IMAGE)
        url = PATH + '?area=movie-search'
        xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        xbmcplugin.endOfDirectory(HANDLE)

    def showLiveTVChannels(self):
        api = ysapi.YouSeeLiveTVApi()
        channels = api.allowedChannels()

        try:
            self._generateChannelIcons(channels)
        except Exception:
            xbmc.log("Caught exception whil generating channel icons!")

        for channel in channels:
            iconImage = os.path.join(CACHE_PATH, str(channel['id']) + '.png')
            if not os.path.exists(iconImage):
                iconImage = channel['logos']['large']
            item = xbmcgui.ListItem(channel['nicename'], iconImage = iconImage, thumbnailImage = iconImage)
            item.setProperty('Fanart_Image', FANART_IMAGE)
            item.setProperty('IsPlayable', 'true')
            url = PATH + '?channel=' + str(channel['id'])
            xbmcplugin.addDirectoryItem(HANDLE, url, item)

        xbmcplugin.endOfDirectory(HANDLE, succeeded = len(channels) > 0)

    def playLiveTVChannel(self, channelId):
        try:
            api = ysapi.YouSeeLiveTVApi()
            url = api.streamUrl(channelId)
            item = xbmcgui.ListItem(path = url)
            xbmcplugin.setResolvedUrl(HANDLE, True, item)
        except ysapi.YouSeeApiException, ex:
            item = xbmcgui.ListItem()
            xbmcplugin.setResolvedUrl(HANDLE, False, item)
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(30050), ADDON.getLocalizedString(30051),
                ADDON.getLocalizedString(30052), ex.description)


    def showMovieGenres(self):
        api = ysapi.YouSeeMovieApi()
        genres = api.genres()

        for genre in genres:
            item = xbmcgui.ListItem(genre['name'] + ' (' + str(genre['count']) + ')')
            item.setProperty('Fanart_Image', FANART_IMAGE)
            url = PATH + '?genre=' + genre['url_id']
            xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder = True, totalItems = int(genre['count']))

        xbmcplugin.endOfDirectory(HANDLE)

    def showMoviesInGenre(self, genre):
        api = ysapi.YouSeeMovieApi()
        moviesInGenre = api.moviesInGenre(genre)

        for movie in moviesInGenre['movies']:
            self._addMovieDirectoryItem(movie)

        xbmcplugin.setContent(HANDLE, 'movies')
        xbmcplugin.endOfDirectory(HANDLE)


    def showMovieThemes(self):
        api = ysapi.YouSeeMovieApi()
        themes = api.themes()

        for theme in themes:
            item = xbmcgui.ListItem(theme['name'] + ' (' + str(theme['count']) + ')')
            item.setProperty('Fanart_Image', FANART_IMAGE)
            url = PATH + '?genre=' + theme['url_id']
            xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder = True, totalItems = int(theme['count']))

        xbmcplugin.endOfDirectory(HANDLE)

    def showMoviesInTheme(self, theme):
        api = ysapi.YouSeeMovieApi()
        moviesInTheme= api.moviesInTheme(theme)

        for movie in moviesInTheme['movies']:
            self._addMovieDirectoryItem(movie)

        xbmcplugin.setContent(HANDLE, 'movies')
        xbmcplugin.endOfDirectory(HANDLE)

    def searchMovies(self):
        kbd = xbmc.Keyboard('', 'Search movies')
        kbd.doModal()
        if kbd.isConfirmed():
            api = ysapi.YouSeeMovieApi()
            movies = api.search(kbd.getText())

            for movie in movies['movies']:
                self._addMovieDirectoryItem(movie)

            xbmcplugin.setContent(HANDLE, 'movies')
            xbmcplugin.endOfDirectory(HANDLE)

    def _addMovieDirectoryItem(self, movie):
        infoLabels = dict()
        infoLabels['plot'] = movie['summary_medium']
        infoLabels['plotoutline'] = movie['summary_short']
        infoLabels['year'] = movie['year']
        infoLabels['duration'] = str(movie['length_in_minutes'])
        infoLabels['cast'] = movie['cast']
        infoLabels['director'] = ' / '.join(movie['directors'])
        infoLabels['mpaa'] = str(movie['age_rating'])
        infoLabels['code'] = str(movie['imdb_id'])
        infoLabels['genre'] = ' / '.join(movie['genres'])

        iconImage = movie['cover_prefix'] + movie['covers']['big']

        item = xbmcgui.ListItem(movie['title'] + ' (DKK ' + str(movie['price']) + ')', iconImage = iconImage)
        item.setInfo('video', infoLabels = infoLabels)
        item.setProperty('Fanart_Image', FANART_IMAGE)
        url = PATH + '?movie=' + movie['url_id']
        xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder = False)

    def _anyChannelIconsMissing(self, channels):
        for channel in channels:
            path = os.path.join(CACHE_PATH, str(channel['id']) + '.png')
            if not os.path.exists(path):
                return True
        return False

    def _generateChannelIcons(self, channels):
        """
        Generates a pretty 256x256 channel icon by downloading the channel graphics
        and pasting in onto the channel_bg.png. The result is cached.

        In case the PIL library is not available the URL
        for the channel graphics is used directly.
        """

        if self._anyChannelIconsMissing(channels):
            import PIL.Image
            sys.modules['Image'] = PIL.Image # http://projects.scipy.org/scipy/ticket/1374

            for channel in channels:
                path = os.path.join(CACHE_PATH, str(channel['id']) + '.png')
                xbmc.log("Generating image for " + channel['nicename'] + "...")
                
                u = urllib2.urlopen(channel['logos']['large'])
                data = u.read()
                u.close()

                image = PIL.Image.open(StringIO.StringIO(data))
                (width, height) = image.size

                iconImage = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'channel_bg.png')
                out = PIL.Image.open(iconImage)

                x = (256 - width) / 2
                y = (256 - height) / 2
                if image.mode == 'RGBA':
                    out.paste(image, (x, y), image)
                else:
                    out.paste(image, (x, y))

                out.save(path)


    def _showWarning(self):
        title = ADDON.getLocalizedString(39000)
        line1 = ADDON.getLocalizedString(39001)
        line2 = ADDON.getLocalizedString(39002)
        line3 = ADDON.getLocalizedString(39003)
        xbmcgui.Dialog().ok(title, line1, line2, line3)

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id = 'plugin.video.yousee.tv')
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    FANART_IMAGE = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    CACHE_PATH = xbmc.translatePath(ADDON.getAddonInfo("Profile"))
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)

    ytv = YouSeeTv()
    if PARAMS.has_key('area') and PARAMS['area'][0] == 'livetv':
        ytv.showLiveTVChannels()
    elif PARAMS.has_key('channel'):
        ytv.playLiveTVChannel(PARAMS['channel'][0])

    elif PARAMS.has_key('area') and PARAMS['area'][0] == 'movie-genre':
        ytv.showMovieGenres()
    elif PARAMS.has_key('genre'):
        ytv.showMoviesInGenre(PARAMS['genre'][0])

    elif PARAMS.has_key('area') and PARAMS['area'][0] == 'movie-theme':
        ytv.showMovieThemes()
    elif PARAMS.has_key('theme'):
        ytv.showMoviesInTheme(PARAMS['theme'][0])

    elif PARAMS.has_key('area') and PARAMS['area'][0] == 'movie-search':
        ytv.searchMovies()

    elif ADDON.getSetting('hide.movie.area') == 'true':
        ytv.showLiveTVChannels()
    else:
        ytv._showWarning()
        ytv.showOverview()
