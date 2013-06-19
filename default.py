
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

import sys
import urllib
import xbmc
import xbmcgui
from urllib2 import urlopen

import resources.lib.xbmcsettings as xbmcsettings
import resources.lib.xbmcutils as utils

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

_addonid = 'script.similartracks'
_settings = xbmcsettings.XBMCSettings(_addonid, sys.argv)

_maxcount = _settings['maxcount']
_recursive = (_settings['recursive'] == 'true')
_runinbackground = (_settings['background'] == 'true')
_playlisttracks = []

if not _runinbackground:
    pDialog = xbmcgui.DialogProgress()
    pDialog.create(
        _settings.get_string(1000), _settings.get_string(3000))


def display_notification(header, message):
    image = _settings.get_path('icon.png')
    utils.notification(header, message, image=image)


def get_next_track_to_add(prev_artist):
    index = 0
    for track in _playlisttracks:
        if track["artist"] != prev_artist:
            if track["added"] == False:
                return index
        index = index + 1
    index = 0
    for track in _playlisttracks:
        if track["added"] == False:
            return index
        index = index + 1
    return -1


def get_track_index_in_playlist(filename):
    index = 0
    for track in _playlisttracks:
        if track["filename"] == filename:
            return index
        index = index + 1
    return 0


def get_lastfm_similar_tracks(artist, track):
    base_url = 'http://ws.audioscrobbler.com/2.0/?'
    params = {'method': 'track.getsimilar', 'artist': artist, 'track':
              track, 'api_key': '5da513b631898f5372a5e5f863651212', 'format': 'json'}
    url = '%s%s' % (base_url, urllib.urlencode(params))
    f = urlopen(url)
    json_query = unicode(f.read(), 'utf-8', errors='ignore')
    f.close()
    json_response = simplejson.loads(json_query)
    lastfmtracks = []
    for track in json_response['similartracks']['track']:
        lastfmtracks.append({'title': track['name'], 'artist': track['artist']['name']})
    return lastfmtracks


def get_similar_tracks(artist, title):
    lastfmtracks = get_lastfm_similar_tracks(artist, title)
    message = (_settings.get_string(3003) % (len(lastfmtracks)))
    if _runinbackground:
        display_notification(_settings.get_string(1000), message)
    else:
        pDialog.update(75, _settings.get_string(3002), message)
    count = 0
    no = 1

    json_query = xbmc.executeJSONRPC(
        '{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "params": {"properties": [], "sort": { "method": "label" } }, "id": 1}')
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    json_response = simplejson.loads(json_query)

    artists = []
    if (json_response['result'] is not None) and ('artists' in json_response['result']):
        for artist in json_response['result']['artists']:
            artists.append(
                {'artist': artist['artist'], 'id': artist['artistid']})

    for track in lastfmtracks:
        tracktitle = track['title'].encode('ascii', 'ignore')
        trackartist = track['artist'].encode('ascii', 'ignore')
        no = no + 1
        artistid = None
        for artist in artists:
            if 'artist' in artist and artist['artist'].encode('ascii', 'ignore') == trackartist:
                artistid = artist['id']
                break
        if artistid:
            json_query = xbmc.executeJSONRPC(
                '{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs", "params": {"properties": ["title", "artist", "album", "genre", "track", "file", "thumbnail"], "sort": { "method": "label" },  "filter": {"artistid": %s} }, "id": 1}' % artistid)
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_response = simplejson.loads(json_query)
            if (json_response['result'] is not None) and ('songs' in json_response['result']):
                for song in json_response['result']['songs']:
                    if 'title' in song and song['title'] == tracktitle:
                        _playlisttracks.append({'songid': song[
                                               'songid'], 'artist': trackartist, 'added': False})
                        count = count + 1
                        if not _runinbackground:
                            pDialog.update(85, _settings.get_string(3004) % ('%s - %s' % (
                                trackartist, tracktitle)), _settings.get_string(3001) % count)
                        break
    return count

if xbmc.Player().isPlayingAudio():
    tag = xbmc.Player().getMusicInfoTag()
    playlist = xbmc.PlayList(0)
    currenttrackpos = playlist.getposition()
    currenttrack = playlist[currenttrackpos].getfilename()
    message = (_settings.get_string(3005) % (tag.getArtist().decode(
        'utf-8', 'ignore'), tag.getTitle().decode('utf-8', 'ignore')))
    if _runinbackground:
        display_notification(_settings.get_string(1000), message)
    else:
        pDialog.update(25, message)
    count = get_similar_tracks(tag.getArtist(), tag.getTitle())
    index = 0
    if count > 0:
        trackpos = currenttrackpos + 1
        while xbmc.PlayList(0).size() > trackpos:
            xbmc.PlayList(0).remove(xbmc.PlayList(0)[trackpos].getfilename())
        index = 0
        previous_artist = tag.getArtist()
        while index < _maxcount:
            i = get_next_track_to_add(previous_artist)
            if i == -1:
                break
            previous_artist = _playlisttracks[i]['artist']
            json_query = xbmc.executeJSONRPC(
                '{ "jsonrpc": "2.0", "method": "Playlist.Add", "params": { "playlistid": 0, "item": { "songid": %d } }, "id": 1 }' % _playlisttracks[i]['songid'])
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_response = simplejson.loads(json_query)
            _playlisttracks[i]['added'] = True
            index = index + 1
    if not _runinbackground:
        pDialog.close()

    message = (_settings.get_string(3006) % (index, tag.getArtist().decode(
        'utf-8', 'ignore'), tag.getTitle().decode('utf-8', 'ignore')))
    if _runinbackground:
        display_notification(_settings.get_string(1000), message)
    else:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(_settings.get_string(1000), message)
