#/*
# *
# * Similar Tracks: SimilarTracks add-on for XBMC.
# *
# * Copyright (C) 2012 Brian Hornsby
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

import os, sys, urllib
import xbmc, xbmcgui, xbmcplugin
from urllib2 import urlopen
from BeautifulSoup import BeautifulStoneSoup
import resources.lib.xbmcsettings as xbmcsettings

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

__addonid__  = 'script.similartracks'
__settings__ = xbmcsettings.Settings(__addonid__, sys.argv)

pDialog = xbmcgui.DialogProgress()
pDialog.create(__settings__.get_string(1000), __settings__.get_string(3000))

__maxcount__ = __settings__['maxcount']
__playlisttracks__ = []

def get_next_track_to_add(prev_artist):
	index = 0
	for track in __playlisttracks__:
		if track["artist"] != prev_artist:
			if track["added"] == False:
				return index
		index = index + 1
	index = 0
	for track in __playlisttracks__:
		if track["added"] == False:
			return index
		index = index + 1
	return -1

def get_track_index_in_playlist(filename):
	index = 0
	for track in __playlisttracks__:
		if track["filename"] == filename:
			return index
		index = index + 1
	return 0

def get_lastfm_similar_tracks(artist, track):
	base_url = 'http://ws.audioscrobbler.com/2.0/?'
	params = {'method': 'track.getsimilar', 'artist': artist, 'track': track, 'api_key': '5da513b631898f5372a5e5f863651212'}
	url = '%s%s' % (base_url, urllib.urlencode(params))
	f = urlopen(url)
	soup = BeautifulStoneSoup(f.read(), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
	f.close()
	lastfmtracks = []
	for track in soup.lfm.similartracks.findAll('track'):
		lastfmtracks.append({'title': track.find('name').string, 'artist': track.artist.find('name').string})
	return lastfmtracks

def get_similar_tracks(artist, title):
	lastfmtracks = get_lastfm_similar_tracks(artist, title)
	pDialog.update(75, __settings__.get_string(3002), __settings__.get_string(3003) % (len(lastfmtracks)))
	count = 0
	no = 1
	
	json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "params": {"properties": [], "sort": { "method": "label" } }, "id": 1}')
	json_query = unicode(json_query, 'utf-8', errors='ignore')
	json_response = simplejson.loads(json_query)
	
	artists = []
	if (json_response['result'] != None) and (json_response['result'].has_key('artists')):
		for artist in json_response['result']['artists']:
			artists.append({'artist': artist['artist'], 'id': artist['artistid']})
	
	for track in lastfmtracks:
		tracktitle = track['title'].encode('utf-8')
		trackartist = track['artist'].encode('utf-8')
		no = no + 1
		artistid = None
		for artist in artists:
			if artist.has_key('artist') and artist['artist'] == trackartist:
				artistid = artist['id']
				break
		if artistid:
			json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs", "params": {"properties": ["title", "artist", "album", "track", "file"], "sort": { "method": "label" }, "artistid":%s }, "id": 1}' % artistid)
			json_query = unicode(json_query, 'utf-8', errors='ignore')
			json_response = simplejson.loads(json_query)
			if (json_response['result'] != None) and (json_response['result'].has_key('songs')):
				for song in json_response['result']['songs']:
					if song.has_key('title') and song['title'] == tracktitle:
						__playlisttracks__.append({'artist': trackartist, 'title': tracktitle, 'file': song['file'], 'added': False})
						count = count + 1
						pDialog.update(85, __settings__.get_string(3004) % ('%s - %s' % (trackartist, tracktitle)) , __settings__.get_string(3001) % count)
						break
	return count

tag = xbmc.Player().getMusicInfoTag()
if xbmc.Player().isPlayingAudio():            
	playlist = xbmc.PlayList(0)
	currenttrackpos = playlist.getposition()
	currenttrack = playlist[currenttrackpos].getfilename()
	pDialog.update(25, __settings__.get_string(3005) % (tag.getArtist(), tag.getTitle()))
	count = get_similar_tracks(tag.getArtist(), tag.getTitle())
	if count > 0:
		trackpos = currenttrackpos + 1
		while xbmc.PlayList(0).size() > trackpos:
			xbmc.PlayList(0).remove(xbmc.PlayList(0)[trackpos].getfilename())
		index = 0
		playlist_len = len(__playlisttracks__)
		previous_artist = tag.getArtist()
		while index < playlist_len:
			i = get_next_track_to_add(previous_artist)
			if i == -1:
				break
			previous_artist = __playlisttracks__[i]['artist']
			listitem = xbmcgui.ListItem(__playlisttracks__[i]['title'])
			xbmc.PlayList(0).add(__playlisttracks__[i]['file'], listitem)
			__playlisttracks__[i]['added'] = True
			index = index + 1
	pDialog.close()
	if count == 0:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok(__settings__.get_string(1000), __settings__.get_string(3006), '%s - %s' % (tag.getArtist(), tag.getTitle()))
