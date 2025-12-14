import os
from ruamel.yaml import YAML
from pathlib import Path
import glob

my_dir = os.path.realpath(os.path.dirname(__file__))
dances_sources_glob = os.path.realpath(os.path.join(my_dir, '..', 'sources', 'dances', "*.yaml"))

def clean_track_list(track_list):
    def unique_list(some_list):
        return list(set(some_list))

    sorted_track_list = sorted(track_list, key=lambda x: (x['artist'], x['track_name']))

    new_track_list = []
    new_track_list.append(sorted_track_list[0])
    for track in sorted_track_list[1:]:
        previous_track = new_track_list[-1]
        if track['artist'] == previous_track['artist'] and track['track_name'] == previous_track['track_name']:
            print(f"Merging records for {track['artist']} - {track['track_name']}")
            previous_track['from_playlist'] = unique_list(previous_track.get('from_playlist', []) + track.get('from_playlist', []))
            for track_link in track['links']:
                for track_link_in_previous_record in previous_track['links']:
                    if (track_link['portal'] == track_link_in_previous_record['portal']) and (
                            track_link['link'] == track_link_in_previous_record['link']):
                        print(f"Found duplicate link for {track_link['portal']}: {track_link['link']}")
                        break
                else:
                    previous_track['links'].append(track_link)
        else:
            new_track_list.append(track)

    return new_track_list


yaml = YAML()
for file_path in glob.glob(dances_sources_glob):
    print(f"Cleaning file {file_path}")
    file_reference = Path(file_path)
    data = yaml.load(file_reference)
    track_list = data.get('links', {}).get('tracks', [])
    if not track_list:
        continue

    data['links']['tracks'] = clean_track_list(track_list)
    yaml.dump(data, file_reference)
