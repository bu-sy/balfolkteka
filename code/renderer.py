from unidecode import unidecode

def write_file(contents, file_path):
    with open(file_path, 'w') as file_obj:
        file_obj.write(contents)

def link(link_text, link_path):
    return f"[{link_text}]({link_path})"

def get_spotify_embed(link_text):
    assert 'spotify' in link_text
    track_id = link_text.split('/')[-1]
    return '''<iframe data-testid="embed-iframe" style="border-radius:12px" src="https://open.spotify.com/embed/track/''' + track_id + '''?utm_source=generator" width="100%" height="352" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>'''

def embed_youtube(link_text):
    prefix = 'https://www.youtube.com/watch?v='
    assert link_text.startswith(prefix), link_text
    video_id = link_text[len(prefix):]
    return '''<iframe width="100%" height="315" src="https://www.youtube.com/embed/''' + video_id + '''?si=o5m25aE8fmLWDh3B" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen  loading="lazy"></iframe>'''

def collapsible(summary, contents):
    return f"<details>\n<summary><big>{summary}</big></summary>\n{contents}\n</details>"

def embed_track(link_object):
    if link_object.portal.lower() == 'spotify':
        return get_spotify_embed(link_object.link)
    elif link_object.portal.lower() == 'youtube':
        return embed_youtube(link_object.link)
    else:
        return f"({link(link_object.portal, link_object.link)})"


def secondary_header(text):
    return f"## {text}"

def music_collapsible_section(music, display_dance_name):
    return collapsible(
        f"{music.artist} - <b>{music.track_name}</b>" + (f" ({music.dance})" if display_dance_name else ""),
        "\n".join([
            f"\n{embed_track(music_link)}" for music_link in music.music_links
        ])
    )

def render_dance(loaded_dance, loaded_translation, all_dances, directory_structure):
    lines = [
        f"# {loaded_dance.get('name')}",
        link(
            loaded_translation.get_page_name('aggregated_list_of_dances'),
            directory_structure.get_aggregated_dances_path(directory_structure.get_dance_file_path(loaded_dance))
        ),
        f"**{loaded_translation.get_keyword('name')}**: {loaded_dance.get('name')}"
    ]
    if alt_name := loaded_translation.get_alt_name(loaded_dance.get('id')):
        lines.append(f"**{loaded_translation.get_keyword('alt_name')}**: {alt_name}")

    # if loaded_dance.get('tags') or loaded_dance.get('variants'):
    #     lines.append(f"## {loaded_translation.get_keyword('tags')}\n- " + '\n- '.join([
    #         loaded_translation.get_translated_tag(tag_name)
    #         for tag_name in loaded_dance.get('tags', [])
    #     ]))
    #     if loaded_dance.get('variants'):
    #         lines.append(f"### {loaded_translation.get_keyword('variants')}\n- " + '\n- '.join([
    #             loaded_translation.get_translated_tag(tag_name)
    #             for tag_name in loaded_dance.get('variants', [])
    #         ]))

    if loaded_examples := loaded_dance.get_examples():
        lines.append(secondary_header(loaded_translation.get_keyword('examples')))
        lines.append(collapsible(
            loaded_translation.get_keyword('click_to_expand'),
            '\n'.join([embed_youtube(example.link) for example in loaded_examples])
        ))
        lines.append('<br>')

    if loaded_instructions := loaded_dance.get_instruction_link():
        lines.append(secondary_header(loaded_translation.get_keyword('how_to_dance')))
        lines.append(collapsible(
            loaded_translation.get_keyword('click_to_expand'),
            '\n'.join([embed_youtube(instruction['link']) for instruction in loaded_instructions])
        ))
        lines.append('<br>')

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
        lines.extend(
            music_collapsible_section(track_record, False) for track_record in not_blacklisted_tracks
        )

    write_file('\n\n'.join(lines), directory_structure.get_dance_file_path(loaded_dance))

def render_aggregated_dances(all_dances, loaded_translation, directory_structure):
    def dance_line(dance_obj):
        dance_name = dance_obj.get('name')
        dance_alt_name = loaded_translation.get_alt_name(dance_obj.get('id'))
        return f"{dance_name} ({dance_alt_name})" if dance_alt_name else dance_name

    write_file(
        "\n\n".join([
           f"# {loaded_translation.get_page_name('aggregated_list_of_dances') } ({len(all_dances)})"
        ] + [
            link(
                dance_line(dance),
                directory_structure.get_dance_file_path(dance, directory_structure.get_aggregated_dances_path())
            ) for dance in sorted(all_dances, key=lambda x: x.get('name'))
        ]),
        directory_structure.get_aggregated_dances_path()
    )

def render_aggregated_music(all_music, loaded_translation, directory_structure):
    write_file(
        "\n\n".join([
            f"# {loaded_translation.get_page_name('aggregated_list_of_music')} ({len(all_music)})"
        ] + [
            music_collapsible_section(music, True)
            for music
            in sorted(all_music, key=lambda x: (x.artist.lower(), x.track_name.lower()))
        ]),
        directory_structure.get_aggregated_music_path()
    )

def render_music_by_artist(all_music, loaded_translation, directory_structure):
    artists = {}
    for music in all_music:
        artists_for_that_music = [record.strip() for record in music.artist.split(',')]
        for found_artist in artists_for_that_music:
            artists[found_artist] = artists.get(found_artist, []) + [music]
    for artist, artists_music in artists.items():
        write_file(
            "\n\n".join([
                f"# {artist} ({len(artists_music)})"
            ] + [
                music_collapsible_section(music, True) for music in sorted(artists_music, key=lambda x: unidecode(x.track_name.lower()))
            ]),
            directory_structure.get_music_by_artist(artist)
        )

    write_file(
        "\n\n".join([
            link(f"{artist} ({len(artists_music)})", directory_structure.get_music_by_artist(
                artist,
                relative_to=directory_structure.get_aggregated_music_by_artist())
             ) for artist, artists_music in sorted(artists.items(), key=lambda x: unidecode(x[0].lower()))
        ]),
        directory_structure.get_aggregated_music_by_artist()
    )

def render_home_page(loaded_translation, directory_structure):
    write_file(
        '\n\n'.join([
        link(
            loaded_translation.get_page_name('aggregated_list_of_dances'),
            directory_structure.get_aggregated_dances_path(directory_structure.get_home_page_path())
        ),
        link(
            loaded_translation.get_page_name('aggregated_list_of_music'),
            directory_structure.get_aggregated_music_path(directory_structure.get_home_page_path())
        ),
        link(
            loaded_translation.get_page_name('list_of_music_by_artist'),
            directory_structure.get_aggregated_music_by_artist(directory_structure.get_home_page_path())
        )
        ]),
        directory_structure.get_home_page_path()
    )
