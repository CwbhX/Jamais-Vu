import acoustid
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
client_credentials_manager = SpotifyClientCredentials()


class SongDataFinder(object):

    def __init__(self, acoustid_apikey):
        self.acoustid_apikey = acoustid_apikey
        self.spotifysearch = SpotifySearch()

    def _topresult(self, filename):  # Use acoustID Webservice for basic information
        results = acoustid.match(self.acoustid_apikey, filename)
        for score, recording_id, title, artist in results:
            return (title, artist, score)

    def matchFile(self, filename):
        title, artist, score = self._topresult(filename)
        self.spotifysearch.search("%s - %s" % (title, artist))  # Plug back in our acoustID results into spotify search

        return self.spotifysearch.selectResult(0)  # Return the resulting spotify track


class SpotifySearch(object):

    def __init__(self):
        self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def search(self, query):
        self.results = self.spotify.search(query)

    def selectResult(self, index):
        if index < getNumberOfResults:
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
        return self.trackdata["artists"][0]

    def getMainArtistGenre(self):
        uri = self.trackdata["artists"][0]["uri"]
        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        artistdata = spotify.artist(uri)
        return artistdata["genres"][0]

    def getTrackNumber(self):
        return self.trackdata["track_number"]

    def getLength(self):
        return self.trackdata["duration_ms"]

    def getExplicitRating(self):
        return bool(self.trackdata["explicit"])

    def getSpotifyID(self):
        return self.trackdata["id"]
