# Spotify Playlist Downloader

Downloads songs from a Spotify playlist, complete with album art and metadata. 

## Usage
1. Clone the repository
2. Open the terminal and run the following command to download the required libraries:
```bash
python3 install -r requirements.txt
```
3. Open download.py, and add the playlist url, your spotify client ID and secret key (which you can obtain from here: https://developer.spotify.com/dashboard/ . Log in, make an app and get the spotify client ID and secret key), the directory where the songs should be installed, the name of the folder that the songs would be installed in (the folder will be created in inside the directory) and the genre of the songs (if any). download.py should look something like this:
```python
# 
from playlist_dl import download

url = 'https://open.spotify.com/playlist/abc123'
client_id = 'abc123'
client_secret = 'abc123'

working_dir = 'folder'
folder_name = 'metal'
genre = 'Metal'

download(url, client_id, client_secret, working_dir, folder_name, genre)

```
Note that the places I've written as 'abc123' above should instead be some alphanumeric string.

4. Run download.py
```bash
python3 download.py
```
You'll find the songs in a folder in the directory that was given by the user.

The MusicDL.py file and the 'core' directory have been taken from https://github.com/gumob/music-dl.
