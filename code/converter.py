import os
import yaml
import glob
from renderer import render_dance, render_aggregated_dances, render_home_page

def remove_suffix(text, suffix):
    if text.endswith(suffix):
        return text[:-len(suffix)]
    raise RuntimeError(f"{text} does not end with {suffix}, cannot cut it.")

class YamlDefinedEntity(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.name = remove_suffix(os.path.basename(file_path), '.yaml')
        self.contents = None

    def load(self):
        if not self.contents:
            with open(self.file_path) as file_obj:
                self.contents = yaml.safe_load(file_obj.read())

    def get(self, value):
        return self.contents[value]


class TranslationFile(YamlDefinedEntity):
    def __init__(self, file_path):
        super(TranslationFile, self).__init__(file_path)

    def get_keyword(self, keyword):
        return self.contents['keywords'][keyword]

    def get_page_name(self, page_name):
        return self.contents['pages'][page_name]

    def get_alt_name(self, dance_name):
        return self.contents['alt_names'].get(dance_name)


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
    YamlDefinedEntity(dance_file) for dance_file in glob.glob(os.path.join(dances_path, '*.yaml'))
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

