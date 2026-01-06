from unidecode import unidecode
import os
import re
import yaml


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

class TrackRecordMetadata(object):
    def __init__(self, artist, track_name):
        self.artist = artist
        self.track_name = track_name

    @classmethod
    def from_dict(cls, dict_obj):
        return TrackRecordMetadata(
            artist=dict_obj.get('artist'),
            track_name=dict_obj.get('track_name')
        )

    def same_metadata(self, other):
        return self.artist == other.artist and self.track_name == other.track_name


class TrackRecord(TrackRecordMetadata):
    def __init__(self, artist, track_name, music_links, tags, lyrics, blacklist, merge_with=None):
        super(TrackRecord, self).__init__(artist, track_name)
        self.music_links = music_links
        self.tags = tags
        self.blacklist = blacklist
        self.dances = set()
        self.lyrics = lyrics
        self.merge_with = merge_with

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
            blacklist=dict_obj.get('blacklist', False),
            merge_with=TrackRecordMetadata.from_dict(dict_obj.get('merge_with')) if 'merge_with' in dict_obj else None
        )

    def merge_music_links(self, another_track_record):
        for another_music_link in another_track_record.music_links:
            if not any(another_music_link.link == music_link.link for music_link in self.music_links):
                self.music_links.append(another_music_link)

    def add_dances(self, dances):
        self.dances.update(dances)

    def get_dances_as_string(self):
        return ", ".join(sorted(list(self.dances)))


class YamlDefinedEntity(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.name = self._remove_suffix(os.path.basename(file_path), '.yaml')
        self.contents = None

    def _remove_suffix(self, text, suffix):
        if text.endswith(suffix):
            return text[:-len(suffix)]
        raise RuntimeError(f"{text} does not end with {suffix}, cannot cut it.")

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
