import os
from ruamel.yaml import YAML
from pathlib import Path
import glob

my_dir = os.path.realpath(os.path.dirname(__file__))
dances_sources_glob = os.path.realpath(os.path.join(my_dir, '..', 'sources', 'dances', "*.yaml"))

yaml = YAML()
for file_path in glob.glob(dances_sources_glob):
    print(f"Cleaning file {file_path}")
    file_reference = Path(file_path)
    data = yaml.load(file_reference)
    track_list = data.get('links', {}).get('tracks', [])
    if not track_list:
        continue
    track_list = sorted(track_list, key=lambda x: (x['artist'], x['track_name']))
    data['links']['tracks'] = track_list
    yaml.dump(data, file_reference)

    links = [
        link['link'] for track in track_list for link in track['links']
    ]

    assert len(links) == len(set(links)), f"Found duplicate links in {file_path}!"
