# main imports
import sys
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import array
import urllib
from urllib2 import urlopen
import xml.dom
from xml.dom import minidom
import re

pDialog = xbmcgui.DialogProgress()
pDialog.create('Similar Tracks', 'Initializing script...')

__settings__      = xbmcaddon.Addon(id='script.similartracks')
__language__      = __settings__.getLocalizedString
__version__       = __settings__.getAddonInfo('version')
__cwd__           = __settings__.getAddonInfo('path')
__maxcount__      = __settings__.getSetting('maxcount')

__lastfmtracks__ = {}
__playlisttracks__ = {}

def get_next_track_to_add(index, prev_artist):
   for i in __playlisttracks__:
      if __playlisttracks__[i]["artist"] != prev_artist:
         if __playlisttracks__[i]["added"] == False:
            return i
   for i in __playlisttracks__:
      if __playlisttracks__[i]["added"] == False:
         return i
   return -1

def get_track_index_in_playlist(filename):
   for index in __playlisttracks__:
      if __playlisttracks__[index]["filename"] == filename:
         return index
   return 0

def get_lastfm_similar_tracks(artist, track):
   url = "http://ws.audioscrobbler.com/2.0/?method=track.getsimilar&artist=" + urllib.quote_plus(artist) + "&track=" + urllib.quote_plus(track) + "&api_key=b25b959554ed76058ac220b7b2e0a026"
   xmlhandle = urlopen(url)
   xmldoc = minidom.parse(xmlhandle)
   xmlhandle.close()

   trackcount = 0
   __lastfmtracks__.clear()

   pDialog.update(50, "Processing similar tracks...", "", "")

   for node in xmldoc.childNodes:
      if node.nodeName == "lfm":
         for node in node.childNodes:
            if node.nodeName == "similartracks":
               for node in node.childNodes:
                  if node.nodeName == "track":
                     track = {}
                     for node in node.childNodes:
                        if node.nodeName == "name":
                           track["title"] = node.firstChild.nodeValue
                        elif node.nodeName == "artist":
                           for node in node.childNodes:
                              if node.nodeName == "name":
                                 track["artist"] = node.firstChild.nodeValue
                     __lastfmtracks__[trackcount] = track
                     trackcount = trackcount + 1

def get_similar_tracks(artist, title):
   get_lastfm_similar_tracks(artist, title)
   pDialog.update(75, "Creating playlist...", "Received %d similar tracks to" % (len(__lastfmtracks__)), "%s - %s" % (artist, title))
   count = 0

   for index in __lastfmtracks__:
      if count >= int(__maxcount__):
         break

      track = __lastfmtracks__[index]
      sql_music = "select distinct strTitle, strArtist, strFilename, strPath from songview where idSong = (select idSong from song where strTitle = \'%s\') and idArtist = (select idArtist from artist where strArtist = '%s')" % ( track["title"].replace("'", "''"), track["artist"].replace("'", "''"))
      music_xml = xbmc.executehttpapi( "QueryMusicDatabase(%s)" % urllib.quote_plus( sql_music.encode('utf-8')), )
      if len(music_xml) > 0 and (not music_xml.startswith("<li>Error")):
         fields = re.findall( "<field>(.*?)</field>", music_xml, re.DOTALL )
         if len(fields) == 4:
            path = fields[3] + fields[2]
            if path != currenttrack and get_track_index_in_playlist(path) == 0:
               track = {}
               track["title"] = fields[0]
               track["artist"] = fields[1]
               track["filename"] = path
               track["added"] = False
               __playlisttracks__[count] = track
               count = count + 1
               pDialog.update(85, "Creating playlist. Adding %s" % fields[1])
   return count

tag = xbmc.Player().getMusicInfoTag()
if xbmc.Player().isPlayingAudio():            
   playlist = xbmc.PlayList(0)
   currenttrackpos = playlist.getposition()
   currenttrack = playlist[currenttrackpos].getfilename()
   pDialog.update(25, "Getting similar tracks for %s - %s" % (tag.getArtist(), tag.getTitle()), "")
   count = get_similar_tracks(tag.getArtist(), tag.getTitle())

   print "Found %d similar tracks" % count

   if count > 0:
      trackpos = currenttrackpos + 1
      while xbmc.PlayList(0).size() > trackpos:
         xbmc.PlayList(0).remove(xbmc.PlayList(0)[trackpos].getfilename())

      index = 0
      playlist_len = len(__playlisttracks__)
      previous_artist = tag.getArtist()
      while index < playlist_len:
         i = get_next_track_to_add(index, previous_artist)
         if i == -1:
            break
         previous_artist = __playlisttracks__[i]["artist"]
         listitem = xbmcgui.ListItem(__playlisttracks__[i]["title"])
         xbmc.PlayList(0).add(__playlisttracks__[i]["filename"], listitem)
         __playlisttracks__[i]["added"] = True
         index = index + 1
  
   pDialog.close()

   if count == 0:
      dialog = xbmcgui.Dialog()
      ok = dialog.ok('Similar Tracks', 'Unable to find any similar tracks for',  '%s - %s' % (tag.getArtist(), tag.getTitle()))
