from youtubesearchpython import SearchVideos
from MusicDL import MusicDL

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import json
import os

import eyed3
from mutagen.easyid3 import EasyID3
from mutagen.flac import Picture, FLAC
from mutagen import File

import shutil
import subprocess



url = 'playlist_url'
client_id = 'your-client-id'
client_secret = 'your-client-secret-key'

working_dir = 'path/to/folder'
folder_name = 'folder_name'
genre = 'Genre'

auth_manager = SpotifyClientCredentials(client_id, client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)
playlists = sp.playlist_items(url) 


playlist_songs = playlists['items']

os.makedirs(f'{working_dir}/{folder_name}/albumart')

for i in playlist_songs:
    song = i['track']['name']
    artist = i['track']['album']['artists'][0]['name']
    album = i['track']['album']['name']
    search = SearchVideos(f"{song} {artist}", offset = 1, mode = "json", max_results = 10)

    results = json.loads(search.result())["search_result"]
    # results.reverse()


    searches = []
    titles=[]
    for result in results:
        title = result['title']

        if (title == song or title == f'{artist} - {song}') and ((artist.replace(' ', '')).lower() in (result['channel'].replace(' ', '')).lower()):
            searches.insert(0, result['link'])
            titles.insert(0, title)            
            break
        else:
            if title == f'{artist} - {song}' or (f'{artist} - {song}'.lower() in title.lower() and 'audio' in title.lower()) and 'video' not in title.lower():
                searches.insert(0, result['link'])
                titles.insert(0, title)

            elif 'audio' in title.lower() or 'lyric' in title.lower() or (song in title and 'video' not in title.lower()):
                searches.append(result['link'])
                titles.append(title)
    if not searches:
        print('Unable to download song')
        continue
    download_url = searches[0]
    

    mdl = MusicDL(
        download_url=download_url,
        working_dir=working_dir,
        folder_name=folder_name
    )

    song_downloaded = False
    while not song_downloaded:
        try:
            mdl.download()
            song_downloaded = True
        except:
            continue
    
    response = requests.get(i['track']['album']['images'][0]['url'])

    files = open(f"{working_dir}/{folder_name}/albumart/{titles[0]}.png", "wb")
    files.write(response.content)
    files.close()


    audio = FLAC(f'{working_dir}/{folder_name}/{titles[0]}.flac')
    audio['genre'] = genre
    audio['title'] = song
    audio['artist'] = artist  
    audio['album'] = album
    audio.save()
    
    audiofile = File(f'{working_dir}/{folder_name}/{titles[0]}.flac')

    image = Picture()
    image.type = 3
    
    mime = 'image/png'
    image.desc = 'front cover'
    with open(f'{working_dir}/{folder_name}/albumart/{titles[0]}.png', 'rb') as f: # better than open(albumart, 'rb').read() ?
        image.data = f.read()

    audiofile.add_picture(image)
    audiofile.save()

    os.rename(f'{working_dir}/{folder_name}/{titles[0]}.flac', f'{folder_name}/{artist} - {song}.flac')
    

non_flac_files = [x for x in os.listdir(folder_name) if not x.endswith(".flac")]
print(non_flac_files)
for f in non_flac_files:
    os.rename(f, f'{working_dir}/{folder_name}/albumart/'+f)


shutil.rmtree(f"{working_dir}/{folder_name}/albumart")
    print()
