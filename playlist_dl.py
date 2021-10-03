from youtubesearchpython import SearchVideos
from MusicDL import MusicDL

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import json
import os
import shutil

import eyed3
from mutagen.easyid3 import EasyID3
from mutagen.flac import Picture, FLAC
from mutagen import File


# Search youtube to pick the best results for the song.
# Downloading the first result that comes up isn't a great idea since it may be a different song with a similar name,
# or it might be a music video which often have sounds that aren't a part of the song.
# To tackle this, we go through the first 10 results and enter the relevant results with the following priorities:
# 1. Videos with only the song name as the video title and and uploaded by the artist are given the first priority.
#    These tend to be audio tracks, which is what we want.
#    In this case, we insert the video title and url in the beginning of their respective lists and break from the loop to directly return these.
# 2. Videos with the song name in the title, and containing 'audio' and not containing 'video' or 'live' in the title are given the second priority.
#    In this case, we insert the video title and url in the beginning of their respective lists and proceed with the next iteration.
# 3. Videos with 'audio' or 'lyric' in the title, or the song name without 'video' or 'live' is given the least priority.
#    In this case, we insert the video title and url in the end of their respective lists and proceed with the next iteration.
# After going through the results, we return the best result i.e. the one at the beginning of the lists.
def find_best_video(song, artist):
    search = SearchVideos(f"{song} {artist}", offset=1,
                          mode="json", max_results=10)

    results = json.loads(search.result())["search_result"]

    searches = []
    titles = []
    for result in results:
        title = result['title']

        if (title == song or title == f'{artist} - {song}') and ((artist.replace(' ', '')).lower() in (result['channel'].replace(' ', '')).lower()):
            searches.insert(0, result['link'])
            titles.insert(0, title)
            break
        elif title == f'{artist} - {song}' or (f'{artist} - {song}'.lower() in title.lower() and 'audio' in title.lower()) and 'video' not in title.lower() and 'live' not in title.lower():
            searches.insert(0, result['link'])
            titles.insert(0, title)
        elif 'audio' in title.lower() or 'lyric' in title.lower() or (song in title and 'video' not in title.lower() and 'live' not in title.lower()):
            searches.append(result['link'])
            titles.append(title)

    if not searches:
        return {}

    return {"url": searches[0], "title": titles[0]}


# Download the song via MusicDL
def download_song(download_url, working_dir, folder_name):
    # Make a class object.
    mdl = MusicDL(
        download_url=download_url,
        working_dir=working_dir,
        folder_name=folder_name
    )

    # Sometimes, an error pops up while downloading. So we'll keep try 5 times to downlaod the song.
    song_downloaded = False
    k = 0
    while not song_downloaded and k <= 5:
        k += 1
        try:
            # Try downloading the song.
            mdl.download()

            # If successful, set song_downloaded to True so the loop would break and we can move on.
            song_downloaded = True
        except:
            # If an error occurs, try again.
            continue


# Download the album art.
def download_albumart(working_dir, folder_name, song, title):
    response = requests.get(song['track']['album']['images'][0]['url'])

    files = open(os.path.join(working_dir, folder_name,
                              'albumart', f'{title}.png'), "wb")
    files.write(response.content)
    files.close()


# Add the metadata to the audio file.
def add_metadata(working_dir, folder_name, title, genre, song, artist, album):
    audio = FLAC(os.path.join(working_dir, folder_name, f'{title}.flac'))
    audio['title'] = song
    audio['artist'] = artist
    audio['album'] = album

    if genre:
        audio['genre'] = genre
    audio.save()


# Add the album art that we have previously downloaded to the audio file.
def add_albumart(working_dir, folder_name, title):
    audio = File(os.path.join(working_dir, folder_name, f'{title}.flac'))

    image = Picture()
    image.type = 3

    mime = 'image/png'
    image.desc = 'front cover'

    # better than open(albumart, 'rb').read() ?
    with open(os.path.join(working_dir, folder_name,
                           'albumart', f'{title}.png'), 'rb') as f:
        image.data = f.read()

    audio.add_picture(image)
    audio.save()


# When downloading from MusicDL, some unnecessary files download as well. So we'll try to remove those by transferring
# them to the albumart folder, and deleting the folder with all of its contents so only the songs remain.
def clean_up(working_dir, folder_name):
    # Get all the files that aren't audio files.
    non_flac_files = [x for x in os.listdir(
        os.path.join(working_dir, folder_name)) if not x.endswith(".flac") and os.path.isfile(os.path.join(working_dir, folder_name, x))]

    # Move them to the albumart folder.
    for f in non_flac_files:
        os.rename(os.path.join(working_dir, folder_name, f),
                  os.path.join(working_dir, folder_name, 'albumart', f))

    # Delete the albumart folder.
    shutil.rmtree(os.path.join(working_dir, folder_name, 'albumart'))


def download(url, client_id, client_secret, working_dir, folder_name, genre):
    # Do some authorisation stuff that spotipy requires.
    auth_manager = SpotifyClientCredentials(client_id, client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)

    # Get the playlist songs from the passed url.
    playlists = sp.playlist_items(url)
    playlist_songs = playlists['items']

    # Make the folder to store the album art images.
    # os.makedirs(f'{working_dir}/{folder_name}/albumart')
    os.makedirs(os.path.join(working_dir, folder_name, 'albumart'))

    # Iterate across all songs in the playlist.
    for i in playlist_songs:

        # Extract the song name, artist name and album name from the spotify song.
        song = i['track']['name']
        artist = i['track']['album']['artists'][0]['name']
        album = i['track']['album']['name']

        # Get the details (namely the url and the title as in the youtube video) in the form of a dictionary.
        # song url: video["url"]
        # song title: video["title"]
        video = find_best_video(song, artist)

        # If we're unable to find a good match, move on to the next song.
        if "url" not in video:
            print('Unable to download song')
            continue

        download_url = video["url"]
        title = video["title"]

        # Download the song.
        download_song(download_url, working_dir, folder_name)

        # Downlaod the album art.
        download_albumart(working_dir, folder_name, i, title)

        # Add metadata to the audio file.
        add_metadata(working_dir, folder_name, title,
                     genre, song, artist, album)

        # Add album art to the audio file.
        add_albumart(working_dir, folder_name, title)

        # All this while, we have kept the name of the song as the title of the youtube video that it was downloaded from.
        # The reason it was kept that way was to prevent any naming clashes with some other song with the same name.
        # Now that all the processes are done, we'll name the file with the song name and artist name that we have extracted from the spotify playlist.
        # Should any error occur, the song would have still been downloaded.
        try:
            os.rename(os.path.join(working_dir, folder_name, f'{title}.flac'),
                      os.path.join(working_dir, folder_name, f'{artist} - {song}.flac'))
        except:
            # If a naming clash / some other error does occur, move on with the downloading of the next song.
            continue
    clean_up(working_dir, folder_name)
