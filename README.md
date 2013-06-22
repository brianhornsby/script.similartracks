SimilarTracks for XBMC
===========

A script that uses the currently playing track to generate a playlist of similar tracks in your XBMC music library.

Features
--------
- Create a playlist of tracks from your music library that are similar to the currently playing track.
- Uses Last.fm getSimilar API to find similar tracks.
- Runs in background.
- Can specify the maximum number of tracks to add to the playlist.

Screenshots
----------

<img alt="Get similar tracks progress dialog" src="https://raw.github.com/brianhornsby/www_brianhornsby_com/master/img/script_similartracks_get_dialog.png" height="128"/>
<img alt="Found similar tracks progress dialog" src="https://raw.github.com/brianhornsby/www_brianhornsby_com/master/img/script_similartracks_found_dialog.png" height="128"/>
<img alt="Added tracks to playlist progress dialog" src="https://raw.github.com/brianhornsby/www_brianhornsby_com/master/img/script_similartracks_added_dialog.png" height="128"/>
<img alt="Get similar tracks notification" src="https://raw.github.com/brianhornsby/www_brianhornsby_com/master/img/script_similartracks_get_notification.png" height="128"/>
<img alt="Added tracks to playlist notification" src="https://raw.github.com/brianhornsby/www_brianhornsby_com/master/img/script_similartracks_added_notification.png" height="128"/>

Installation
-----------
Download the latest zip file and install the addon. See http://wiki.xbmc.org/?title=Add-ons#How_to_install_from_a_ZIP_file for more details on installing addons from zip file.

Usage
-----
The SimilarTracks script can be accessed from the Programs menu or called using the RunScript builtin function (RunScript(script.similartracks))

Settings
--------
The following settings are available.

**Maximum tracks to add to playlist**: The maximum tracks that will be added to the playlist. Default: 25

**Run in background**: Script runs in the background. Default: false

**Playlist order**: The order that tracks should be added to the playlist. Random: Tracks are added at random. Last.FM: Tracks are added in the order they came back from Last.fm. Default: Random

License
-------
SimilarTracks for XBMC is licensed under the [GPL 3.0 license] [1].


[1]: http://www.gnu.org/licenses/gpl-3.0.html
