def write_file(contents, file_path):
    with open(file_path, 'w') as file_obj:
        file_obj.write(contents)

def link(link_text, link_path):
    return f"[{link_text}]({link_path})"

def secondary_header(text):
    return f"## {text}"

def render_dance(loaded_dance, loaded_translation, all_dances, directory_structure):
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

    if loaded_dance.get('tags') or loaded_dance.get('variants'):
        lines.append(f"## {loaded_translation.get_keyword('tags')}\n- " + '\n- '.join([
            loaded_translation.get_translated_tag(tag_name)
            for tag_name in loaded_dance.get('tags', [])
        ]))
        if loaded_dance.get('variants'):
            lines.append(f"### {loaded_translation.get_keyword('variants')}\n- " + '\n- '.join([
                loaded_translation.get_translated_tag(tag_name)
                for tag_name in loaded_dance.get('variants', [])
            ]))

    if loaded_examples := loaded_dance.get_examples():
        lines.append(secondary_header(loaded_translation.get_keyword('examples')))
        for example in loaded_examples:
            lines.append(example.link)

    if loaded_instructions := loaded_dance.get_instruction_link():
        lines.append(secondary_header(loaded_translation.get_keyword('how_to_dance')))
        for instruction in loaded_instructions:
            lines.append(instruction['link'])

    if loaded_dance.get('connected_dances'):
        lines.append(f"### {loaded_translation.get_keyword('connected_dances')}")
        for similar_dance_name in loaded_dance.get('connected_dances', []):
            dance_to_link = [
                searched_dance for searched_dance in all_dances if searched_dance.get('id') == similar_dance_name
            ][0]
            lines.append(
                "- " + link(
                    dance_to_link.get('name'),
                    directory_structure.get_dance_file_path(
                        dance_to_link,
                        relative_to=directory_structure.get_dance_file_path(loaded_dance)
                    ))
            )

    if loaded_music := loaded_dance.get_music_links():
        not_blacklisted_tracks = [
            track_record for track_record in loaded_music if not track_record.blacklist
        ]

        lines.append(secondary_header(loaded_translation.get_keyword('tracks') + f" ({len(not_blacklisted_tracks)})"))
        for track_record in not_blacklisted_tracks:
            lines.append(
                f"{track_record.artist} - **{track_record.track_name}**" +
                " ".join([
                    f"({loaded_translation.get_translated_tag(tag_obj)})" for tag_obj in track_record.tags
                ]) + " " +
                " ".join([
                    f"({link(music_link.portal, music_link.link)})" for music_link in track_record.music_links
                ])
            )

    write_file('\n\n'.join(lines), directory_structure.get_dance_file_path(loaded_dance))

def render_aggregated_dances(all_dances, loaded_translation, directory_structure):
    write_file(
        "\n\n".join([
           f"# {loaded_translation.get_page_name('aggregated_list_of_dances') }"
        ] + [
            link(
                dance.get('name'),
                directory_structure.get_dance_file_path(dance, directory_structure.get_aggregated_dances_path())
            ) for dance in sorted(all_dances, key=lambda x: x.get('name'))
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
