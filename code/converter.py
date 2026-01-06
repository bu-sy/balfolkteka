import os
import glob
from renderer import *
from preprocessors import merge_music
from helper_classes import *


directoryStructure = DirectoryStructure()
all_dances = [
    DanceFile(dance_file) for dance_file in glob.glob(os.path.join(directoryStructure.dances_path, '*.yaml'))
]
all_translations = [
    TranslationFile(translation_file) for translation_file in glob.glob(os.path.join(directoryStructure.translations_path, '*.yaml'))
]

for dance in all_dances:
    dance.load()

print(f"Found {len(all_dances)} dance files.")
print(f"Found {len(all_translations)} translations.")

all_music = []
for dance in all_dances:
    for music in dance.get_music_links():
        if not music.blacklist:
            music.add_dances([dance.get_readable_name()])
            all_music.append(music)

all_music = merge_music(all_music)

#Adding tracks to the dances back after merging
dance_name_to_object = {}
for dance in all_dances:
    dance.music_links = []
    dance_name_to_object[dance.get_readable_name()] = dance

for music in all_music:
    for dance_readable_name in music.dances:
        dance_name_to_object[dance_readable_name].music_links.append(music)

#VERIFY FOR DUPLICATE LINKS
youtube_links = {}
for music in all_music:
    for link in music.music_links:
        if link.portal.lower() == 'youtube':
            youtube_links[link.link] = youtube_links.get(link.link, []) + [f"{music.artist} - {music.track_name}"]


for link, track_descriptions in youtube_links.items():
    if len(track_descriptions) > 1:
        print(f"Found YouTube link {link} in following tracks")
        for description in track_descriptions:
            print(description)

for directory_to_create in directoryStructure.get_directories_to_create():
    os.makedirs(directory_to_create, exist_ok=True)

all_artists = render_music_by_artist(all_music, directoryStructure)
render_music_by_track_name(all_music, directoryStructure)
render_music_by_dance(all_dances, directoryStructure)

for translation in all_translations:
    print(f"Processing translation {translation.name}")
    translation.load()
    directory_structure_for_translation = DirectoryStructureForTranslation(translation)
    for directory_to_create in directory_structure_for_translation.get_directories_to_create():
        os.makedirs(directory_to_create, exist_ok=True)

    for dance in all_dances:
        render_dance(dance, translation, all_dances, directory_structure_for_translation)

    render_aggregated_dances(all_dances, translation, directory_structure_for_translation)
    render_music_redirect_page(
        translation,
        directory_structure_for_translation,
        number_of_dances=len(all_dances),
        number_of_artists=len(all_artists)
    )
    render_home_page(
        translation,
        directory_structure_for_translation,
        number_of_tracks=len(all_music),
        number_of_dances=len(all_dances)
    )

    print(f"Done translation {translation.name}")

