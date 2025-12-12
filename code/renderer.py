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
    return '\n\n'.join(lines)

def render_aggregated_dances(all_dances, loaded_translation, directory_structure):
    return "\n\n".join([
       f"# {loaded_translation.get_page_name('aggregated_list_of_dances') }"
    ] + [
        f"[{dance.get('name')}](../dances/{dance.name}.md)" for dance in all_dances
    ])

def render_home_page(loaded_translation, directory_structure):
    return link(
            loaded_translation.get_page_name('aggregated_list_of_dances'),
            directory_structure.get_aggregated_dances_path(directory_structure.get_home_page_path())
        )
