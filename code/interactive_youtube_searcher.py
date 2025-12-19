import os
import requests
from ruamel.yaml import YAML
from pathlib import Path
import webbrowser

NO_YOUTUBE_LINK_MARKER = 'no_youtube_link'

def get_youtube_results(spotify_link):
    response = requests.get(f"https://ytm2spotify.com/convert?url={spotify_link}&to_service=youtube_ytm")
    response.raise_for_status()
    return response.json()

def get_y_n_answer(prompt):
    answer = ''
    while answer not in ('y', 'n'):
        answer = input(prompt + '(y/n)')
    return answer == 'y'

def get_spotify_link(track):
    for link in track['links']:
        if link['portal'].lower() == 'spotify':
            return link['link']

def search_youtube_video(track):
    print("Searching for:")
    print(f"  Track: {track['track_name']}")
    print(f"  Artist: {track['artist']}")
    for result in get_youtube_results(get_spotify_link(track))['results'][:4]:
        tested_url = result['url']
        if tested_url.startswith('https://youtube.com'):
            tested_url = tested_url.replace('https://youtube.com', 'https://www.youtube.com')
        print(f"Checking {tested_url}")
        webbrowser.open(tested_url)
        if get_y_n_answer('Is this the correct url?'):
            track['links'].append({
                'portal': 'YouTube',
                'link': tested_url
            })
            return

    if get_y_n_answer('Should I mark that track does not exist on YouTube?'):
        track[NO_YOUTUBE_LINK_MARKER] = True



def interactive_youtube_searcher(track_list):
    def has_spotify_link(track_to_check):
        for link in track_to_check.get('links'):
            if link['portal'].lower() == 'spotify':
                return True
        return False

    def has_youtube_link(track_to_check):
        for link in track_to_check.get('links'):
            if link['portal'].lower() == 'youtube':
                return True
        return False

    def is_track_to_be_processed(track_to_check):
        return has_spotify_link(track_to_check) and not has_youtube_link(track_to_check) and not track_to_check.get(NO_YOUTUBE_LINK_MARKER, False)

    number_of_tracks_to_process = len(
        [track for track in track_list if is_track_to_be_processed(track)]
    )
    print(f"In this file there are {number_of_tracks_to_process} tracks to process")
    #TODO wrap in try to support gentle interrupt via Ctrl+C
    try:
        for track in track_list:
            if is_track_to_be_processed(track):
                search_youtube_video(track)
    except:
        print("Some error occurred. Saving and exiting")
    return track_list

file_path = os.environ.get('FILE_PATH')
assert file_path
print(f"Processing {file_path}")
yaml = YAML()
yaml.width = 4096
file_reference = Path(file_path)
data = yaml.load(file_reference)
track_list = data.get('links', {}).get('tracks', [])
playlists = data.get('links', {}).get('playlists', [])
data['links']['tracks'] = interactive_youtube_searcher(track_list)
print("Saving")
yaml.dump(data, file_reference)
