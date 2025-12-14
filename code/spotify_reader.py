import os
import requests
import yaml


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


token_id = os.environ.get('SPOTIFY_TOKEN_ID')
playlist_id = os.environ.get('SPOTIFY_PLAYLIST_ID')

print(yaml.dump(SpotifyCaller(token_id=os.environ.get('SPOTIFY_TOKEN_ID')).get_tracks(os.environ.get('SPOTIFY_PLAYLIST_ID')), allow_unicode=True))
