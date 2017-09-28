from jamaisvu.database import get_database, Database
from songdata import SongDataFinder
import jamaisvu.decoder as decoder
import fingerprint


class Jamaisvu(object):

    SONG_ID = "song_id"
    SONG_NAME = 'song_name'

    SONG_ARTIST = "song_artist"
    SONG_ALBUM = "song_album"
    SONG_GENRE = "song_genre"
    SONG_EXPLICIT = "song_explicit"
    SONG_LENGTH = "song_length"

    CONFIDENCE = 'confidence'
    MATCH_TIME = 'match_time'
    OFFSET = 'offset'
    OFFSET_SECS = 'offset_seconds'

    def __init__(self, config):
        super(Jamaisvu, self).__init__()

        self.config = config

        # initialize db
        db_cls = get_database(config.get("database_type", None))

        self.db = db_cls(**config.get("database", {}))
        self.db.setup()  # Change this with an if condition

        # if we should limit seconds fingerprinted,
        # None|-1 means use entire track
        self.limit = self.config.get("fingerprint_limit", None)
        if self.limit == -1:  # for JSON compatibility
            self.limit = None

        self.songdatafinder = SongDataFinder(self.config.get("acoustid_apikey"))

        self.get_fingerprinted_songs()

    def get_fingerprinted_songs(self):
        # get songs previously indexed
        self.songs = self.db.get_songs()
        self.songhashes_set = set()  # to know which ones we've computed before
        for song in self.songs:
            song_hash = song[Database.FIELD_FILE_SHA1]
            self.songhashes_set.add(song_hash)

    def fingerprint_file(self, filepath):
        songdata = self.songdatafinder.matchFile(filepath)

        song_name = songdata.getName()
        song_artist = songdata.getMainArtist()
        song_album = songdata.getAlbum()
        song_artist_genre = songdata.getMainArtistGenre()
        song_explicit = songdata.getExplicitRating()
        song_length = songdata.getLength()

        song_hash = decoder.unique_hash(filepath)

        # don't refingerprint already fingerprinted files
        if song_hash in self.songhashes_set:
            print "%s has already been fingerprinted." % song_name

            return False
        else:
            hashes, file_hash = _fingerprint_worker(filepath, self.limit)
            # Insert our song data into the songs table and return its location
            sid = self.db.insert_song(song_name,
                                      song_artist,
                                      song_album,
                                      song_artist_genre,
                                      song_explicit,
                                      song_length,
                                      file_hash)

            self.db.insert_hashes(sid, hashes)
            self.db.set_song_fingerprinted(sid)
            self.get_fingerprinted_songs() # Why is this being run after every call... with two nested for loops

            return True

    def fingerprint_directory(self, path, extensions):
        # TODO: Make this use the fingerprint_file, can't do multiple processes due to API limits
        # This shouldn't be an issue once gpu acceleration is implemented

        filenames_to_fingerprint = []
        for filename, _ in decoder.find_files(path, extensions):
            # don't refingerprint already fingerprinted files
            if decoder.unique_hash(filename) in self.songhashes_set:
                print "%s already fingerprinted, continuing..." % filename
            else:
                filenames_to_fingerprint.append(filename)

        print(filenames_to_fingerprint)

        for filename in filenames_to_fingerprint:
            self.fingerprint_file(filename)

        return True

    def find_matches(self, samples, Fs=fingerprint.DEFAULT_FS):
        hashes = fingerprint.fingerprint(samples, Fs=Fs)
        return self.db.return_matches(hashes)

    def align_matches(self, matches):
        """
            Finds hash matches that align in time with other matches and finds
            consensus about which hashes are "true" signal from the audio.

            Returns a dictionary with match information.
        """
        # align by diffs
        diff_counter = {}
        largest = 0
        largest_count = 0
        song_id = -1
        for tup in matches:
            sid, diff = tup
            if diff not in diff_counter:
                diff_counter[diff] = {}
            if sid not in diff_counter[diff]:
                diff_counter[diff][sid] = 0
            diff_counter[diff][sid] += 1

            if diff_counter[diff][sid] > largest_count:
                largest = diff
                largest_count = diff_counter[diff][sid]
                song_id = sid

        # extract idenfication
        song = self.db.get_song_by_id(song_id)
        if song:
            # TODO: Clarify what `get_song_by_id` should return.
            songname = song.get(Jamaisvu.SONG_NAME, None)
            songartist = song.get(Jamaisvu.SONG_ARTIST, None)
            songalbum = song.get(Jamaisvu.SONG_ALBUM, None)
            songgenre = song.get(Jamaisvu.SONG_GENRE, None)
            songexplicit = song.get(Jamaisvu.SONG_EXPLICIT, True)  # Default to yes to explicit if there is no data, we don't want explicit songs on air
            songlength = song.get(Jamaisvu.SONG_LENGTH, 0)
        else:
            return None

        # return match info
        nseconds = round(float(largest) / fingerprint.DEFAULT_FS *
                         fingerprint.DEFAULT_WINDOW_SIZE *
                         fingerprint.DEFAULT_OVERLAP_RATIO, 5)
        song = {  # TODO: Replace this variable...
            Jamaisvu.SONG_ID: song_id,
            Jamaisvu.SONG_NAME: songname,
            Jamaisvu.SONG_ARTIST: songartist,
            Jamaisvu.SONG_ALBUM: songalbum,
            Jamaisvu.SONG_GENRE: songgenre,
            Jamaisvu.SONG_EXPLICIT: songexplicit,
            Jamaisvu.SONG_LENGTH: songlength,

            Jamaisvu.CONFIDENCE: largest_count,
            Jamaisvu.OFFSET: int(largest),
            Jamaisvu.OFFSET_SECS: nseconds,
            Database.FIELD_FILE_SHA1: song.get(Database.FIELD_FILE_SHA1, None)
            }

        return song

    def recognize(self, recognizer, *options, **kwoptions):
        r = recognizer(self)
        return r.recognize(*options, **kwoptions)


def _fingerprint_worker(filename, limit=None):
    # I only want the hashes. This function should not has any songdata otherwise
    try:
        filename, limit = filename
    except ValueError:
        pass

    channels, Fs, file_hash = decoder.read(filename, limit)
    result = set()
    channel_amount = len(channels)

    for channeln, channel in enumerate(channels):
        # TODO: Remove prints or change them into optional logging.
        print("Fingerprinting channel %d/%d for %s" % (channeln + 1,
                                                       channel_amount,
                                                       filename))
        hashes = fingerprint.fingerprint(channel, Fs=Fs)
        print("Finished channel %d/%d for %s" % (channeln + 1, channel_amount,
                                                 filename))
        result |= set(hashes)

    return result, file_hash


def chunkify(lst, n):
    """
    Splits a list into roughly n equal parts.
    http://stackoverflow.com/questions/2130016/splitting-a-list-of-arbitrary-size-into-only-roughly-n-equal-parts
    """
    return [lst[i::n] for i in xrange(n)]
