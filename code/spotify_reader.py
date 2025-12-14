import os
import requests
import yaml

# TODO add authorization flow
# assert os.environ.get('SPOTIFY_CLIENT_ID') and os.environ.get('SPOTIFY_CLIENT_SECRET')

token_id = os.environ.get('SPOTIFY_TOKEN_ID')
playlist_id = os.environ.get('SPOTIFY_PLAYLIST_ID')

request_headers = {
    'Authorization': f'Bearer {token_id}',
}

response = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", headers=request_headers)
response.raise_for_status()

result = response.json()
all_tracks = []

for item_in_the_list in result['items']:
    track = item_in_the_list['track']
    all_tracks.append({
        'artist': ', '.join(sorted([artist['name'] for artist in track['artists']])),
        'track_name': track['name'],
        'links': [{
            'portal': 'Spotify',
            'link': track['external_urls']['spotify']
        }]
    })

print(yaml.dump(all_tracks, allow_unicode=True))
