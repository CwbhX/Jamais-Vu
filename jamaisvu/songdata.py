import acoustid
import spotipy
import pymsgbox
from spotipy.oauth2 import SpotifyClientCredentials


class SongDataFinder(object):

    def __init__(self, acoustid_apikey):
        self.acoustid_apikey = acoustid_apikey
        self.spotifysearch = SpotifySearch()

    def _topresult(self, filename):  # Use acoustID Webservice for basic information
        results = acoustid.match(self.acoustid_apikey, filename)
        try:
            for score, recording_id, title, artist in results:
                return (title, artist, score)
        except TypeError:  # If we could not identify a match with MusicBrains
            return None


    def matchFile(self, filename, userInput=True):
        try:
            title, artist, score = self._topresult(filename)
            print("")
            print("AcoustID Name: %s" % title)
            print("AcoustID Artist: %s" % artist)
            print("")
            self.spotifysearch.search("%s - %s" % (title, artist))  # Plug back in our acoustID results into spotify search

            return self.spotifysearch.selectResult(0)  # Return the resulting spotify track

        except TypeError:  # Again, If we could not identify a match
            # TODO: Work on the userInput exception handling... e.g. skip None Songs
            if userInput == True:
                pymsgbox.alert(text='Could not identify song automatically', title='Song ID Error', button='OK')
                userSongName = pymsgbox.prompt(text='Song Name', title='Enter Song Name')
                userSongArtist = pymsgbox.prompt(text='Artist', title='Enter Artist Name')

                self.spotifysearch.search("%s - %s" % (userSongName, userSongArtist))  # Search spotify with user entered values
                return self.spotifysearch.selectResult(0)  # Return the resulting spotify track
            else:
                return None


class SpotifySearch(object):

    def __init__(self):
        self.client_credentials_manager = SpotifyClientCredentials()
        self.spotify = spotipy.Spotify(client_credentials_manager=self.client_credentials_manager)

    def search(self, query):
        self.results = self.spotify.search(query)

    def selectResult(self, index):
        if index < self.getNumberOfResults():
            return SpotifyTrack(self.results["tracks"]["items"][index])
        else:
            print("Index is too high")
            return None

    def getNumberOfResults(self):
        return len(self.results["tracks"]["items"])

    def getTrackNames(self):
        trackNames = []
        for track in self.results["tracks"]["items"]:
            trackNames.append(track[name])

        return trackNames

    def getTrackAlbums(self):
        trackAlbums = []
        for track in self.results["tracks"]["items"]:
            trackAlbums.append(track["album"]["name"])

        return trackAlbums

    def getTrackArtists(self):
        trackArtists = []
        for track in self.results["tracks"]["items"]:
            trackArtists.append(track["artists"]["name"][0])  # There might be more than one artist, figure how to handle this

        return trackArtists

    def getExplicitRatings(self):
        explicitRatings = []
        for track in self.results["tracks"]["items"]:
            explicitRatings.append[track["explicit"]]

        return explicitRatings

    def getTrackIDs(self):
        trackIDs = []
        for track in self.results["tracks"]["items"]:
            trackIDs.append(track["id"])

class SpotifyTrack(object):

    def __init__(self, trackJSON):
        self.trackdata = trackJSON

    def getName(self):
        return self.trackdata["name"]

    def getAlbum(self):
        return self.trackdata["album"]["name"]

    def getAlbumArt(self):
        return self.trackdata["album"]["images"][0]["url"]

    def getArtists(self):
        return self.trackdata["artists"]

    def getMainArtist(self):
        return self.trackdata["artists"][0]["name"]

    def getMainArtistGenre(self):
        uri = self.trackdata["artists"][0]["uri"]
        client_credentials_manager = SpotifyClientCredentials()
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        artistdata = spotify.artist(uri)
        try:
            return artistdata["genres"][0]
        except IndexError:
            return None

    def getTrackNumber(self):
        return self.trackdata["track_number"]

    def getLength(self):
        return self.trackdata["duration_ms"]

    def getExplicitRating(self):
        return bool(self.trackdata["explicit"])

    def getSpotifyID(self):
        return self.trackdata["id"]
