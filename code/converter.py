import os
import yaml
import glob

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

class TranslationFile(YamlDefinedEntity):
    def __init__(self, file_path):
        super(TranslationFile, self).__init__(file_path)

    def get_keyword(self, keyword):
        return self.contents['keywords'][keyword]

    def get_alt_name(self, dance_name):
        return self.contents['alt_names'].get(dance_name)

def render_dance(loaded_dance, loaded_translation):
    lines = [
        f"# {loaded_dance.contents['name']}",
        f"**{loaded_translation.get_keyword('name')}**: {loaded_dance.contents['name']}"
    ]
    if alt_name := loaded_translation.get_alt_name(loaded_dance.contents['id']):
        lines.append(f"**{loaded_translation.get_keyword('alt_name')}**: {alt_name}")
    return '\n\n'.join(lines)

#TODO group paths in one object with all paths
my_path = os.path.realpath(__file__)
toplevel_path = os.path.realpath(os.path.join(my_path, '..', '..'))
sources_path = os.path.join(toplevel_path, 'sources')
dances_path = os.path.join(sources_path, 'dances')
translations_path = os.path.join(sources_path, 'translations')

documentations_path = os.path.join(toplevel_path, 'documentation')

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
    translation_parent_path = os.path.join(documentations_path, translation.name)
    os.makedirs(translation_parent_path, exist_ok=True)
    translated_dances_path = os.path.join(translation_parent_path, 'dances')
    os.makedirs(translated_dances_path, exist_ok=True)
    for dance in all_dances:
        dance.load()
        dance_path = os.path.join(translated_dances_path, dance.name + '.md')
        with open(dance_path, 'w') as file_obj:
            file_obj.write(
                render_dance(dance, translation)
            )
    print(f"Done translation {translation.name}")
