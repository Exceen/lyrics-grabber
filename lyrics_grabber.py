#!/usr/bin/python
from ScriptingBridge import SBApplication
import tweepyutils
import urllib2
import re
import time

iTunes = SBApplication.applicationWithBundleIdentifier_("com.apple.Music")

mediaKindMusic = 1800234067

prefixes = ['The', 'A', '\.'] #regex

# TODO:
#    compare with lyrics from other website and note it somewhere that lyrics differ

def find_and_set_lyrics(tracks):
    for track in tracks:
        __find_and_set_lyrics(track)

        # ddos detection protection
        time.sleep(2)

def __find_and_set_lyrics(track):
    try:
        print 'Retrieving lyrics for "' + str(track.name()) + '"'
        lyrics = get_lyrics_for_track(track)
        track.setLyrics_(lyrics)
    except Exception as e:
        print e

def load(url):
    req = urllib2.Request(url, headers = {
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,like Gecko) Chrome/68.0.3440.75 Safari/537.36',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US;q=0.5,en;q=0.3',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1'
        })
    return urllib2.urlopen(req).read()

def binary_search(arr, target):
    return __binary_search(arr, 0, len(arr), target)

def __binary_search(arr, low, high, x):
    # print '-' * 10
    # print high, low, high >= low
    if high >= low: 
        mid = low + (high - low) / 2
        # print high, mid, low


        # if low == high and low == mid:
        #     return mid
        artist = remove_prefix(arr[mid].artist().lower(), prefixes)

        # If element is present at the middle itself
        if artist == x:
            return mid

        # If element is smaller than mid, then it can only 
        # be present in left subarray
        elif artist > x:
            return __binary_search(arr, low, mid - 1, x) 
        # Else the element can only be present in right subarray     
        return __binary_search(arr, mid + 1, high, x) 

    else: 
        # Element is not present in the array 
        x_wo_prefix = remove_prefix(x, prefixes)
        if x != x_wo_prefix:
            return binary_search(arr, x_wo_prefix)
        return -1

def remove_prefix(text, prefixes):
    for prefix in prefixes:
        text = re.sub('^' + prefix.lower() + ' ?', '', text)
    return text

def get_tracks(iTunes):
    query = ''
    while len(query) == 0:
        query = raw_input('Artist: ').lower()

    query_tracks = []
    all_tracks = iTunes.tracks()

    full_search = raw_input('Do you want to make a full search? This takes much longer but includes searching by album artist as well (y/n): ').lower()
    if full_search != 'y':
        print 'Performing binary search... (fast)'
        result = binary_search(all_tracks, query)
        if result != -1:

            start_idx = result
            while all_tracks[start_idx].artist().lower() == query:
                start_idx -= 1
            start_idx += 1

            end_idx = result
            while all_tracks[end_idx].artist().lower() == query:
                end_idx += 1


            for i in xrange(start_idx, end_idx):
                track = all_tracks[i]
                if track.mediaKind() == mediaKindMusic and (track.lyrics() == None or len(track.lyrics()) == 0):
                    query_tracks.append(track)

        if len(query_tracks) > 0:
            return query_tracks
        else:
            print 'Unable to find any tracks via binary search. Searching iterative, this may take a while.'

    print 'Performing full search...'
    i = 1
    for track in iTunes.tracks():
        print str(i) + '/' + str(len(iTunes.tracks())), track.artist(), track.name()
        i += 1
        if track.mediaKind() == mediaKindMusic and (track.lyrics() == None or len(track.lyrics()) == 0) and (query in track.artist().lower() or query in track.albumArtist().lower()):
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

    content = ''
    try:
        url = url_template % (prepare_for_url(track.artist()), prepare_for_url(track.name()))
        content = load(url)

    # and open it to return a handle on the url
    except urllib2.HTTPError as e:
        if e.code == 403:
            print 'Blocked by lyrics provider, try again later or try to enter captcha in your browser.'
            print url
            quit()
    except Exception as e:
        url = url_template % (prepare_for_url(track.artist().split('The')[1]), prepare_for_url(track.name()))
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

    print '-' * 10
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
                queried_tracks.append(track)
        return queried_tracks
    else:
        return album_map[albums[int(chosen_album_index)]]

def main():
    if iTunes.isRunning():
        queried_tracks = choose_tracks()

        longest_album_length = 0
        for item in queried_tracks:
            if len(item.album()) > longest_album_length:
                longest_album_length = len(item.album())

        print '-' * 10
        for item in queried_tracks:
            print item.artist(), '-', item.album().rjust(longest_album_length), '-', str(item.trackNumber()).ljust(2), '-', item.name()
        search_right = raw_input('Tracks alright? (y/n): ').lower()
        if search_right != 'y':
            print 'Aborted.'
        else:
            find_and_set_lyrics(queried_tracks)


    else:
        print 'iTunes is not running'


if __name__ == '__main__':
    main()
