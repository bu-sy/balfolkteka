def write_file(contents, file_path):
    with open(file_path, 'w') as file_obj:
        file_obj.write(contents)

def link(link_text, link_path):
    return f"[{link_text}]({link_path})"

def render_dance(loaded_dance, loaded_translation, directory_structure):
    lines = [
        f"# {loaded_dance.get('name')}",
        link(
            loaded_translation.get_page_name('main_page'),
            directory_structure.get_home_page_path(directory_structure.get_dance_file_path(loaded_dance))
        ) + '/' + link(
            loaded_translation.get_page_name('aggregated_list_of_dances'),
            directory_structure.get_aggregated_dances_path(directory_structure.get_dance_file_path(loaded_dance))
        ),
        f"**{loaded_translation.get_keyword('name')}**: {loaded_dance.get('name')}"
    ]
    if alt_name := loaded_translation.get_alt_name(loaded_dance.get('id')):
        lines.append(f"**{loaded_translation.get_keyword('alt_name')}**: {alt_name}")

    if loaded_dance.get('tags'):
        lines.append(f"**{loaded_translation.get_keyword('tags')}**:\n- " + '\n- '.join([
            loaded_translation.get_translated_tag(tag_name)
            for tag_name in loaded_dance.get('tags')
        ]))

    if loaded_examples := loaded_dance.get_examples():
        if len(loaded_examples) != 1:
            raise RuntimeError(f"Error parsing {loaded_dance.get('name')}: ATM supporting only one example of the dance.")

        lines.append(f"## {loaded_translation.get_keyword('examples')}")
        for example in loaded_examples:
            lines.append(link(
                loaded_translation.get_keyword(example.type), example.link
            ))

    write_file('\n\n'.join(lines), directory_structure.get_dance_file_path(loaded_dance))

def render_aggregated_dances(all_dances, loaded_translation, directory_structure):
    write_file(
        "\n\n".join([
           f"# {loaded_translation.get_page_name('aggregated_list_of_dances') }"
        ] + [
            link(
                dance.get('name'),
                directory_structure.get_dance_file_path(dance, directory_structure.get_aggregated_dances_path())
            ) for dance in all_dances
        ]),
        directory_structure.get_aggregated_dances_path()
    )

def render_home_page(loaded_translation, directory_structure):
    write_file(
        link(
            loaded_translation.get_page_name('aggregated_list_of_dances'),
            directory_structure.get_aggregated_dances_path(directory_structure.get_home_page_path())
        ),
        directory_structure.get_home_page_path()
    )
