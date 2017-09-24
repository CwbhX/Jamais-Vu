from songdata import SongDataFinder
import sys

def main(acoustid_apikey, file):
    sdf = SongDataFinder(acoustid_apikey)
    songdata = sdf.matchFile(file)

    if(songdata != None):
        print("Song Name: %s" % songdata.getName())
        print("Song Artist: %s" % songdata.getMainArtist())
        print("Song Album: %s" % songdata.getAlbum())
        print("Song Genre: %s" % songdata.getMainArtistGenre())
        print("Song Explicit: %s" % songdata.getExplicitRating())
        print("Song Length: %s" % songdata.getLength())

    else:
        print("Could not identify the song with AcoustID/MusicBrains")

if __name__ == '__main__':
    apikey = sys.argv[1]
    testfile = sys.argv[2]
    main(apikey, testfile)
