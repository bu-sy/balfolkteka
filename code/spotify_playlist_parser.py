import os
import requests
import json
from ruamel.yaml import YAML
from pathlib import Path
import glob

my_dir = os.path.realpath(os.path.dirname(__file__))
dances_sources_glob = os.path.realpath(os.path.join(my_dir, '..', 'sources', 'dances', "*.yaml"))

class SpotifyCaller(object):
    def __init__(self, token_id):# TODO add authorization flow with client_id and client_secret
        self.request_headers = {
            'Authorization': f'Bearer {token_id}'
        }

    def get_tracks(self, playlist_id):
        response = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", headers=self.request_headers)
        response.raise_for_status()
        result = response.json()
        all_tracks = []
        for item_in_the_list in result['items']:
            track = item_in_the_list['track']
            if not track['external_urls'].get('spotify'):# Omit -> track is pulled from spotify
                continue
            all_tracks.append({
                'artist': ', '.join(sorted([artist['name'] for artist in track['artists']])),
                'track_name': track['name'],
                'links': [{
                    'portal': 'Spotify',
                    'link': track['external_urls']['spotify']
                }],
                'from_playlist': [f"https://open.spotify.com/playlist/{playlist_id}"]
            })
        return all_tracks


client_id = os.environ.get('SPOTIFY_CLIENT_ID')
client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')

assert (client_id and client_secret) or os.environ.get('ONLY_CLEAN')

token_id = None
if client_id and client_secret:
    response = requests.post(
        'https://accounts.spotify.com/api/token',
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        params={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
    )
    response.raise_for_status()
    token_id = response.json()['access_token']

spotify_caller = SpotifyCaller(token_id)


def clean_track_list(track_list):
    def unique_sorted_list(some_list):
        return sorted(list(set(some_list)))

    sorted_track_list = sorted(track_list, key=lambda x: (x['artist'], x['track_name']))

    new_track_list = []
    new_track_list.append(sorted_track_list[0])
    for track in sorted_track_list[1:]:
        previous_track = new_track_list[-1]
        if track['artist'] == previous_track['artist'] and track['track_name'] == previous_track['track_name']:
            previous_track['from_playlist'] = unique_sorted_list(previous_track.get('from_playlist', []) + track.get('from_playlist', []))
            for track_link in track['links']:
                for track_link_in_previous_record in previous_track['links']:
                    if (track_link['portal'] == track_link_in_previous_record['portal']) and (
                            track_link['link'] == track_link_in_previous_record['link']):
                        break
                else:
                    previous_track['links'].append(track_link)
        else:
            new_track_list.append(track)

    return new_track_list


yaml = YAML()
yaml.width = 4096

for file_path in glob.glob(dances_sources_glob):
    print(f"Processing file {file_path}")
    file_reference = Path(file_path)
    data = yaml.load(file_reference)
    track_list = data.get('links', {}).get('tracks', [])
    playlists = data.get('links', {}).get('playlists', [])

    if not os.getenv('ONLY_CLEAN'):
        if playlists:
            for playlist in playlists:
                playlist_id = playlist['link'].split('/')[-1]
                track_list.extend(
                    spotify_caller.get_tracks(playlist_id)
                )

    if not track_list:
        continue

    data['links']['tracks'] = clean_track_list(track_list)
    yaml.dump(data, file_reference)
