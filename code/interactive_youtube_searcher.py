import os
import requests
from ruamel.yaml import YAML
from pathlib import Path
import webbrowser
import glob
import sys

my_dir = os.path.realpath(os.path.dirname(__file__))
dances_sources_glob = os.path.realpath(os.path.join(my_dir, '..', 'sources', 'dances', "*.yaml"))

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

class Action(object):
    ACCEPT = 'a'
    VERIFY = 'v'
    DECLINE = 'd'
    @classmethod
    def all_options(cls):
        return (cls.ACCEPT, cls.VERIFY, cls.DECLINE)

    @classmethod
    def accept_decline(cls):
        return (cls.ACCEPT, cls.DECLINE)

    @classmethod
    def get_action(cls, prompt, accept_verify=True):
        answer = ''
        if accept_verify:
            valid_options = cls.all_options()
        else:
            valid_options = cls.accept_decline()

        while answer not in valid_options:
            answer = input(prompt + f"({'/'.join(valid_options)})")
        return answer


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
        print("Found:")
        if 'description1' in result:
            print(f"  Track: {result['description1']}")
        if 'description3' in result:
            print(f"  Artist: {result['description3']}")
        print(f"Under {tested_url}.")

        what_to_do = Action.get_action('How to proceed? Accept/Verify/Decline?')
        if what_to_do == Action.VERIFY:
            webbrowser.open(tested_url)
            what_to_do = Action.get_action('How to proceed? Accept/Decline?', accept_verify=False)

        if what_to_do == Action.ACCEPT:
            track['links'].append({
                'portal': 'YouTube',
                'link': tested_url
            })
            return

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
        return track_list, 1
    return track_list, 0


def update_file(file_path):
    print(f"Processing {file_path}")
    dance_name = file_path.split('/')[-1].split('.')[0]
    print(" ".join([dance_name.upper()] * 5))
    yaml = YAML()
    yaml.width = 4096
    file_reference = Path(file_path)
    data = yaml.load(file_reference)
    track_list = data.get('links', {}).get('tracks', [])
    data['links']['tracks'], rc = interactive_youtube_searcher(track_list)
    print(f"Saving {dance_name}")
    yaml.dump(data, file_reference)
    if rc == 1:
        print("Exiting prematurely")
        sys.exit(1)


file_path = os.environ.get('FILE_PATH')
if file_path:
    update_file(file_path)
else:
    for file_path in glob.glob(dances_sources_glob):
        update_file(file_path)
