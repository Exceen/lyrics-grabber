#!/usr/bin/python
from ScriptingBridge import SBApplication
import tweepyutils
import urllib2
import re

iTunes = SBApplication.applicationWithBundleIdentifier_("com.apple.Music")

# enter artist
# (enter album name)
# (enter track)
# check if website has lyrics
# write lyrics to songs, do not overwrite
# compare with lyrics from other website and note it somewhere that lyrics differ

def find_and_set_lyrics(tracks):
    for track in tracks:
        if len(track.lyrics()) == 0:
            __find_and_set_lyrics(track)
        else:
            print 'Skipping', track.name()

def __find_and_set_lyrics(track):
    try:
        print 'Retrieving lyrics for "' + str(track.name()) + '"'
        lyrics = get_lyrics_for_track(track)
        track.setLyrics_(lyrics)
        # print '-'*10
        # print lyrics
        # print (('-'*20) + '\n')*3        
    except Exception as e:
        print e

def load(url):
    req = urllib2.Request(url, headers={'User-Agent': 'lyrics browser'})
    return urllib2.urlopen(req).read()

def get_tracks(iTunes):
    query = raw_input('Artist: ')
    query_tracks = []
    for track in iTunes.tracks():
        if query in track.artist():
            if len(track.lyrics()) == 0:
                query_tracks.append(track)
    return query_tracks

def prepare_for_url(s):
    s = s.lower()
    s = s.replace(' ', '')
    s = re.sub('[\W_]+', '', s)
    return s

def clean_raw_html(raw_html):
    cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    s = re.sub(cleanr, '', raw_html)
    s = s.strip()
    return s

def get_lyrics_for_track(track):
    url_template = 'https://www.azlyrics.com/lyrics/%s/%s.html'

    url = url_template % (prepare_for_url(track.artist()), prepare_for_url(track.name()))

    # print url
    content = load(url)

    regex = 'Usage of azlyrics\.com content.*?\-\-\>((?:.|\n)*?)\<\/div\>'
    lyrics = re.findall(regex, content)[0]
    return clean_raw_html(lyrics)

def choose_tracks():    
    album_map = {}
    for track in get_tracks(iTunes):
        if album_map.get(track.album()) == None:
            album_map[track.album()] = []
        album_tracks = album_map.get(track.album())
        album_tracks.append(track)

    albums = album_map.keys()

    i = 0
    for album in albums:
        print i, album
        i += 1

    chosen_album_index = raw_input('Choose an album (leave empty for all): ')
    all_albums = chosen_album_index == ''

    if all_albums:
        queried_tracks = []
        for album in albums:
            for track in album_map[album]:
                if len(track.lyrics()) == 0:
                    queried_tracks.append(track)
    else:
        queried_tracks = album_map[albums[int(chosen_album_index)]]

    return queried_tracks

def main():
    if iTunes.isRunning():
        queried_tracks = choose_tracks()

        longest_album_length = 0
        for item in queried_tracks:
            if len(item.album()) > longest_album_length:
                longest_album_length = len(item.album())

        for item in queried_tracks:
            print item.artist(), '-', item.album().rjust(longest_album_length), '-', str(item.trackNumber()).ljust(2), '-', item.name()
        search_right = raw_input('Tracks alright? (y/n): ')
        if search_right != 'y':
            print 'Aborted.'
        else:
            find_and_set_lyrics(queried_tracks)


    else:
        print 'iTunes is not running'


if __name__ == '__main__':
    main()
