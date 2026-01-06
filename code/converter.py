import os
import yaml
import glob
from renderer import render_dance, render_aggregated_dances, render_home_page,\
    render_music_by_artist, render_music_by_dance, render_music_redirect_page, render_music_by_track_name
from unidecode import unidecode
import re

def remove_suffix(text, suffix):
    if text.endswith(suffix):
        return text[:-len(suffix)]
    raise RuntimeError(f"{text} does not end with {suffix}, cannot cut it.")

class ExampleRecord(object):
    VALID_TYPES = ['example_video']
    def __init__(self, link, tags):
        self.link = link
        self.tags = tags

    @classmethod
    def from_dict(cls, dict_obj):
        return ExampleRecord(
            link=dict_obj.get('link'),
            tags=dict_obj.get('tags', [])
        )

class MusicLinkRecord(object):
    def __init__(self, portal, link):
        self.portal = portal
        self.link = link

    @classmethod
    def from_dict(cls, dict_obj):
        return MusicLinkRecord(
            portal=dict_obj.get('portal'),
            link=dict_obj.get('link')
        )

class TrackRecord(object):
    def __init__(self, artist, track_name, music_links, tags, lyrics, blacklist):
        self.artist = artist
        self.track_name = track_name
        self.music_links = music_links
        self.tags = tags
        self.blacklist = blacklist
        self.dances = set()
        self.lyrics = lyrics

    @classmethod
    def from_dict(cls, dict_obj):
        return TrackRecord(
            artist=dict_obj.get('artist'),
            track_name=dict_obj.get('track_name'),
            music_links=[
                MusicLinkRecord.from_dict(music_link_record_dict) for music_link_record_dict in dict_obj.get('links')
            ],
            tags=dict_obj.get('tags') or [],
            lyrics=dict_obj.get('lyrics'),
            blacklist=dict_obj.get('blacklist', False)
        )

    def merge_music_links(self, another_track_record):
        for another_music_link in another_track_record.music_links:
            if not any(another_music_link.link == music_link.link for music_link in self.music_links):
                self.music_links.append(another_music_link)

    def add_dances(self, dances):
        self.dances.update(dances)

    def get_dances(self):
        return ", ".join(sorted(list(self.dances)))


class YamlDefinedEntity(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.name = remove_suffix(os.path.basename(file_path), '.yaml')
        self.contents = None

    def load(self):
        if not self.contents:
            with open(self.file_path) as file_obj:
                self.contents = yaml.safe_load(file_obj.read())

    def get(self, value, default_value=None):
        return self.contents.get(value, default_value)

class DanceFile(YamlDefinedEntity):
    def __init__(self, file_path):
        super(DanceFile, self).__init__(file_path)
        self.music_links = None

    def get_readable_name(self):
        return self.get('name')

    def get_links(self):
        return self.get('links', {})

    def get_examples(self):
        return [
            ExampleRecord.from_dict(example) for example in self.get_links().get('examples', [])
        ]

    def get_music_links(self):
        if not self.music_links:
            self.music_links = [
                TrackRecord.from_dict(track_obj) for track_obj in self.get_links().get('tracks', [])
            ]
        return self.music_links

    def get_instruction_link(self):
        return [
            link for link in self.get_links().get('instructions', [])
        ]

class TranslationFile(YamlDefinedEntity):
    def __init__(self, file_path):
        super(TranslationFile, self).__init__(file_path)

    def get_keyword(self, keyword):
        return self.contents['keywords'][keyword]

    def get_page_name(self, page_name):
        return self.contents['pages'][page_name]

    def get_alt_name(self, dance_name):
        return self.contents['alt_names'].get(dance_name)

    def get_translated_tag(self, tag_name):
        return self.contents['translatable'].get(tag_name)

    def get_translated_video_tag(self, tag_name):
        return self.contents['video_tags'].get(tag_name)


class DirectoryStructure(object):
    def __init__(self):
        script_path = os.path.realpath(__file__)
        self.toplevel_path = os.path.realpath(os.path.join(script_path, '..', '..'))
        self.sources_path = os.path.join(self.toplevel_path, 'sources')
        self.dances_path = os.path.join(self.sources_path, 'dances')
        self.translations_path = os.path.join(self.sources_path, 'translations')
        self.documentations_path = os.path.join(self.toplevel_path, 'documentation')
        self.global_path = os.path.join(self.documentations_path, 'no_lang')
        self.global_aggregated = os.path.join(self.global_path, 'aggregated')
        self.music_by_artist_directory = os.path.join(self.global_aggregated, 'music_by_artist')
        self.music_by_dance_directory = os.path.join(self.global_aggregated, 'music_by_dance')
        self.music_alphabetically_directory = os.path.join(self.global_aggregated, 'music_alphabetically')

    def _get_path(self, full_path, relative_to=None):
        if not relative_to:
            return full_path
        else:
            return self._get_relative_path(relative_to, full_path)

    def _get_relative_path(self, from_path, to_path):
        if from_path.endswith('.md'):  # Assuming this is only possible file extension
            return os.path.relpath(to_path, os.path.dirname(from_path))
        else:  # This is directory
            return os.path.relpath(to_path, from_path)

    def get_directories_to_create(self):
        return [
            self.global_path,
            self.global_aggregated,
            self.music_by_artist_directory,
            self.music_by_dance_directory,
            self.music_alphabetically_directory
        ]

    def get_aggregated_music_by_artist(self, relative_to=None):
        return self._get_path(os.path.join(self.global_aggregated, 'music_by_artist.md'), relative_to)

    def get_aggregated_music_by_dance(self, relative_to=None):
        return self._get_path(os.path.join(self.global_aggregated, 'music_by_dance.md'), relative_to)

    def get_aggregated_music_alphabetically(self, relative_to=None):
        return self._get_path(os.path.join(self.global_aggregated, 'music_alphabetically.md'), relative_to)

    def get_music_by_artist(self, artist, relative_to=None):
        file_name = re.sub(r'\W+', '_', unidecode(artist.lower()))
        if file_name.startswith('_'):
            file_name = '0' + file_name
        return self._get_path(os.path.join(self.music_by_artist_directory, f"{file_name}.md"), relative_to)

    def get_music_by_dance(self, dance, relative_to=None):
        file_name = dance.get('id')
        return self._get_path(os.path.join(self.music_by_dance_directory, f"{file_name}.md"), relative_to)

    def get_music_alphabetically(self, letter, relative_to=None):
        return self._get_path(os.path.join(self.music_alphabetically_directory, f"on_letter_{letter}.md"), relative_to)

class DirectoryStructureForTranslation(DirectoryStructure):
    def __init__(self, translation):
        super(DirectoryStructureForTranslation, self).__init__()
        self.translation_toplevel_path = os.path.join(self.documentations_path, translation.name)
        self.translated_dances_directory = os.path.join(self.translation_toplevel_path, 'dances')
        self.aggregated_pages_directory = os.path.join(self.translation_toplevel_path, 'aggregated')

    def get_directories_to_create(self):
        return [
            self.translation_toplevel_path,
            self.translated_dances_directory,
            self.aggregated_pages_directory,
            self.music_by_artist_directory
        ]

    def get_dance_file_path(self, dance_obj, relative_to=None):
        return self._get_path(os.path.join(self.translated_dances_directory, dance_obj.name + '.md'), relative_to)

    def get_music_redirect_page(self, relative_to=None):
        return self._get_path(os.path.join(self.translated_dances_directory, 'music_redirect.md'), relative_to)

    def get_home_page_path(self, relative_to=None):
        return self._get_path(os.path.join(self.translation_toplevel_path, 'home.md'), relative_to)

    def get_aggregated_dances_path(self, relative_to=None):
        return self._get_path(os.path.join(self.aggregated_pages_directory, 'aggregated_dances.md'), relative_to)


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

all_music = sorted(all_music, key=lambda x: (x.artist, x.track_name))
all_music_filtered = all_music[0:1]  # Finding duplicates, track that were categorized as multiple dances
for i in range(0, len(all_music)-1):
    if all_music[i].artist == all_music[i+1].artist and all_music[i].track_name == all_music[i+1].track_name  :
        print(f"Found {all_music[i].artist} - '{all_music[i].track_name}' for {all_music[i].get_dances()} and {all_music[i+1].get_dances()}. Merging")
        all_music_filtered[-1].add_dances(all_music[i+1].dances)
        all_music_filtered[-1].merge_music_links(all_music[i+1])
    else:
        all_music_filtered.append(all_music[i+1])

assert len(all_music_filtered) == len(set(all_music_filtered))
all_music = all_music_filtered

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
for music in all_music_filtered:
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

