import os
import yaml
import glob
from renderer import render_dance, render_aggregated_dances, render_home_page

def remove_suffix(text, suffix):
    if text.endswith(suffix):
        return text[:-len(suffix)]
    raise RuntimeError(f"{text} does not end with {suffix}, cannot cut it.")

class ExampleRecord(object):
    VALID_TYPES = ['example_video']
    def __init__(self, type, link):
        if type not in self.VALID_TYPES:
            raise RuntimeError(f"Example record creation failed! Type {type} is invalid")
        self.type = type
        self.link = link

    @classmethod
    def from_dict(cls, dict_obj):
        return ExampleRecord(
            type=dict_obj.get('type'),
            link=dict_obj.get('link')
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
    def __init__(self, artist, track_name, music_links, tags):
        self.artist = artist
        self.track_name = track_name
        self.music_links = music_links
        self.tags = tags

    @classmethod
    def from_dict(cls, dict_obj):
        return TrackRecord(
            artist=dict_obj.get('artist'),
            track_name=dict_obj.get('track_name'),
            music_links=[
                MusicLinkRecord.from_dict(music_link_record_dict) for music_link_record_dict in dict_obj.get('links')
            ],
            tags=dict_obj.get('tags') or []
        )


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

    def get_links(self):
        return self.get('links', {})

    def get_examples(self):
        return [
            ExampleRecord.from_dict(example) for example in self.get_links().get('examples', [])
        ]

    def get_music_links(self):
        return [
            TrackRecord.from_dict(track_obj) for track_obj in self.get_links().get('tracks', [])
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


#TODO group paths in one object with all paths, have also class to have all paths per translation
my_path = os.path.realpath(__file__)
toplevel_path = os.path.realpath(os.path.join(my_path, '..', '..'))
sources_path = os.path.join(toplevel_path, 'sources')
dances_path = os.path.join(sources_path, 'dances')
translations_path = os.path.join(sources_path, 'translations')

documentations_path = os.path.join(toplevel_path, 'documentation')

class DirectoryStructureForTranslation(object):
    def __init__(self, translation):
        self.translation_toplevel_path = os.path.join(documentations_path, translation.name)
        self.translated_dances_directory = os.path.join(self.translation_toplevel_path, 'dances')
        self.aggregated_pages_directory = os.path.join(self.translation_toplevel_path, 'aggregated')

    def get_directories_to_create(self):
        return [
            self.translation_toplevel_path,
            self.translated_dances_directory,
            self.aggregated_pages_directory
        ]

    def get_dance_file_path(self, dance_obj, relative_to=None):
        if not relative_to:
            return os.path.join(self.translated_dances_directory, dance_obj.name + '.md')
        else:
            return self._get_relative_path(relative_to, self.get_dance_file_path(dance_obj))

    def get_home_page_path(self, relative_to=None):
        if not relative_to:
            return os.path.join(self.translation_toplevel_path, 'home.md')
        else:
            return self._get_relative_path(relative_to, self.get_home_page_path())

    def get_aggregated_dances_path(self, relative_to=None):
        if not relative_to:
            return os.path.join(self.aggregated_pages_directory, 'aggregated_dances.md')
        else:
            return self._get_relative_path(relative_to, self.get_aggregated_dances_path())

    def _get_relative_path(self, from_path, to_path):
        if from_path.endswith('.md'):  # Assuming this is only possible file extension
            return os.path.relpath(to_path, os.path.dirname(from_path))
        else:  # This is directory
            return os.path.relpath(to_path, from_path)

all_dances = [
    DanceFile(dance_file) for dance_file in glob.glob(os.path.join(dances_path, '*.yaml'))
]
all_translations = [
    TranslationFile(translation_file) for translation_file in glob.glob(os.path.join(translations_path, '*.yaml'))
]

print(f"Found {len(all_dances)} dance files.")
print(f"Found {len(all_translations)} translations.")

for translation in all_translations:
    print(f"Processing translation {translation.name}")
    translation.load()
    directory_structure_for_translation = DirectoryStructureForTranslation(translation)
    for directory_to_create in directory_structure_for_translation.get_directories_to_create():
        os.makedirs(directory_to_create, exist_ok=True)

    for dance in all_dances:
        dance.load()
        render_dance(dance, translation, directory_structure_for_translation)

    render_aggregated_dances(all_dances, translation, directory_structure_for_translation)
    render_home_page(translation, directory_structure_for_translation)

    print(f"Done translation {translation.name}")

