
#/*
# *
# * SimilarTracks for XBMC.
# *
# * Copyright (C) 2013 Brian Hornsby
# *
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation, either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program.  If not, see <http://www.gnu.org/licenses/>.
# *
# */

import random
import sys
import urllib
import xbmc
import xbmcgui
from urllib2 import urlopen, URLError

import resources.lib.xbmcsettings as xbmcsettings
import resources.lib.xbmcutils as utils

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

_addonid = 'script.similartracks'
_settings = xbmcsettings.XBMCSettings(_addonid, sys.argv)

# Get addon information and settings.
_addonname = _settings.get_name()
_version = _settings.get_version()
_maxcount = _settings['maxcount']
if not _maxcount:
    _maxcount = -1
_runinbackground = (_settings['background'] == 'true')
_order = int(_settings['order'])


def log_debug(msg):
    if _settings['debug'] == 'true':
        print '%s: DEBUG: %s' % (_addonid, msg)


def log_error(msg):
    print '%s: ERROR: %s' % (_addonid, msg)

log_debug('Addon Id:   [%s]' % (_addonid))
log_debug('Addon Name: [%s]' % (_addonname))
log_debug('Version:    [%s]' % (_version))

log_debug('maxcount: %d' % _maxcount)
log_debug('runinbackground: %d' % _runinbackground)
log_debug('order: %d' % _order)

if not _runinbackground:
    pDialog = xbmcgui.DialogProgress()
    pDialog.create(
        _settings.get_string(1000), _settings.get_string(3000))


def display_notification(header, message):
    image = _settings.get_path('icon.png')
    utils.notification(header, message, image=image)


def get_lastfm_similar_tracks(artist, track):
    base_url = 'http://ws.audioscrobbler.com/2.0/?'
    params = {'method': 'track.getsimilar', 'artist': artist, 'track':
              track, 'api_key': '5da513b631898f5372a5e5f863651212', 'format': 'json',
              'autocorrect': 1}
    url = '%s%s' % (base_url, urllib.urlencode(params))
    log_debug('Last.fm URL: %s' % url)

    try:
        f = urlopen(url)
    except URLError as exception:
        log_error(exception)
        utils.ok(_settings.get_string(1000), _settings.get_string(3007))
        return []

    json_query = unicode(f.read(), 'ascii', errors='ignore')
    f.close()
    json_response = simplejson.loads(json_query)
    lastfmtracks = []
    for track in json_response['similartracks']['track']:
        lastfmtracks.append({'title': track[
                            'name'], 'artist': track['artist']['name']})
    return lastfmtracks


def get_similar_tracks(artist, title):
    log_debug('Looking for similar tracks to %s - %s' % (artist, title))
    lastfmtracks = get_lastfm_similar_tracks(artist, title)
    message = (_settings.get_string(3003) % (len(lastfmtracks)))
    if _runinbackground:
        display_notification(_settings.get_string(1000), message)
    else:
        pDialog.update(75, _settings.get_string(3002), message)
    log_debug('Last.fm returned %d similar tracks' % (len(lastfmtracks)))

    if not _runinbackground and pDialog.iscanceled():
        return (0, [])

    json_query = xbmc.executeJSONRPC(
        '{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "params": {"properties": [], "sort": { "method": "label" } }, "id": 1}')
    json_query = unicode(json_query, 'ascii', errors='ignore')
    json_response = simplejson.loads(json_query)

    artists = []
    if (json_response['result'] is not None) and ('artists' in json_response['result']):
        for artist in json_response['result']['artists']:
            artists.append(
                {'artist': artist['artist'], 'id': artist['artistid']})

    count = 0
    playlisttracks = []
    for track in lastfmtracks:
        tracktitle = track['title'].encode('ascii', 'ignore')
        trackartist = track['artist'].encode('ascii', 'ignore')
        artistid = None
        for artist in artists:
            if 'artist' in artist and artist['artist'].encode('ascii', 'ignore') == trackartist:
                artistid = artist['id']
                break
        if artistid:
            json_query = xbmc.executeJSONRPC(
                '{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs", "params": {"properties": ["title", "artist"], "sort": { "method": "label" },  "filter": {"artistid": %s} }, "id": 1}' % artistid)
            json_query = unicode(json_query, 'ascii', errors='ignore')
            json_response = simplejson.loads(json_query)
            if (json_response['result'] is not None) and ('songs' in json_response['result']):
                for song in json_response['result']['songs']:
                    if 'title' in song and song['title'] == tracktitle:
                        playlisttracks.append({'songid': song[
                                               'songid'], 'artist': song['artist'], 'title': song['title']})
                        count = count + 1
                        if not _runinbackground:
                            pDialog.update(85, _settings.get_string(3004) % ('%s - %s' % (
                                trackartist, tracktitle)), _settings.get_string(3001) % count)
                        break

    return (count, playlisttracks)


def get_next_track_to_add(previous_artist, playlisttracks):
    if len(playlisttracks) == 0:
        return -1

    if _order == 0:
        return random.randrange(len(playlisttracks))
    elif _order == 2:
        for track in playlisttracks:
            if track['artist'][0] != previous_artist:
                return index
            index = index + 1
    if len(playlisttracks) > 0:
        return 0
    return -1


def add_tracks_to_playlist(artist, playlisttracks):
    index = 0
    previous_artist = artist
    while index < _maxcount or _maxcount < 0:
        i = get_next_track_to_add(previous_artist, playlisttracks)
        if i == -1:
            break
        previous_artist = playlisttracks[i]['artist']
        json_query = xbmc.executeJSONRPC(
            '{ "jsonrpc": "2.0", "method": "Playlist.Add", "params": { "playlistid": 0, "item": { "songid": %d } }, "id": 1 }' % playlisttracks[i]['songid'])
        json_query = unicode(json_query, 'ascii', errors='ignore')
        json_response = simplejson.loads(json_query)
        playlisttracks.pop(i)
        index = index + 1
    return index


if xbmc.Player().isPlayingAudio():
    tag = xbmc.Player().getMusicInfoTag()
    artist = tag.getArtist()
    title = tag.getTitle()
    playlist = xbmc.PlayList(0)
    currenttrackpos = playlist.getposition() + 1
    if currenttrackpos <= len(playlist):
        if _runinbackground:
            display_notification(_settings.get_string(1000), _settings.get_string(4000) % (artist.decode('ascii', 'ignore'), title.decode('ascii', 'ignore')))
        else:
            pDialog.update(25, _settings.get_string(3005), '%s - %s' % (artist.decode('ascii', 'ignore'), title.decode('ascii', 'ignore')))

        count, playlisttracks = get_similar_tracks(artist, title)
        log_debug('Found %d similar tracks in XBMC library' % count)

        if _runinbackground or not pDialog.iscanceled():
            index = 0
            if count > 0:
                while xbmc.PlayList(0).size() > currenttrackpos:
                    xbmc.PlayList(0).remove(xbmc.PlayList(0)[currenttrackpos].getfilename())
                index = add_tracks_to_playlist(artist, playlisttracks)

            if not _runinbackground:
                pDialog.close()

            log_debug('Added %d songs to playlist' % index)
            if _runinbackground:
                display_notification(_settings.get_string(1000), _settings.get_string(4001) % (index, artist.decode('ascii', 'ignore'), title.decode('ascii', 'ignore')))
            else:
                utils.ok(_settings.get_string(1000), _settings.get_string(3006) % index, '%s - %s' % (artist.decode('ascii', 'ignore'), title.decode('ascii', 'ignore')))
        else:
            log_debug('Script was cancelled')
    else:
        log_debug('Unable to get currently playing track')
else:
    utils.ok(_settings.get_string(1000), _settings.get_string(3008))
