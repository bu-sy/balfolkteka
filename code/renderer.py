from unidecode import unidecode

def normalize(string_val):
    return unidecode(string_val.lower())

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

def embed_soundcloud(link_text):
    return '''<iframe width="100%" height="166" scrolling="no" frameborder="no" allow="autoplay" src="''' + link_text + '''&auto_play=false&hide_related=false&show_comments=true&show_user=true&show_reposts=false&show_teaser=true" loading="lazy"></iframe>'''

def embed_bandcamp(link_text):
    return '''<iframe style="border: 0; width: 100%; height: 42px;" src="''' + link_text + '''" seamless></iframe>'''

def embed_audio_file(link_text):
    return '''<audio controls preload="none" src="''' + link_text + '''"></audio>'''

def collapsible(summary, contents):
    return f"<details>\n<summary><big>{summary}</big></summary>\n{contents}\n</details>"

def embed_track(link_object):
    embedding_method = {
        'spotify': get_spotify_embed,
        'youtube': embed_youtube,
        'soundcloud': embed_soundcloud,
        'bandcamp': embed_bandcamp,
        'audiofile': embed_audio_file
    }.get(link_object.portal.lower())
    if embedding_method:
        return embedding_method(link_object.link)
    else:
        return link_object.link

def secondary_header(text):
    return f"## {text}"

def music_collapsible_section(music, display_dance_name, number_in_order=None):
    prefix = ""
    if number_in_order:
        prefix = f"{number_in_order}. "
    return "\n\n".join([
        "<hr>",
        f"<h3>{prefix}{music.artist} - <b>{music.track_name}</b>" + (f" ({music.get_dances()})" if display_dance_name else "") + "</h3>"
    ] + [
        collapsible(music_link.portal, embed_track(music_link))
        for music_link
        in sorted(music.music_links, key=lambda x: (x.portal, x.link))
    ] + ([
        collapsible("Text", music.lyrics.replace('\n', '<br>\n'))
    ] if music.lyrics else []))

def render_dance(loaded_dance, loaded_translation, all_dances, directory_structure):
    lines = [
        f"# {loaded_dance.get('name')}",
        link(
            loaded_translation.get_keyword('back_to_list_of_dances'),
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
        # lines.extend(
        #     music_collapsible_section(track_record, False) for track_record in not_blacklisted_tracks
        # )
        lines.append(link(
            loaded_translation.get_page_name('music_for_dance'),
            directory_structure.get_music_by_dance(loaded_dance, relative_to=directory_structure.get_dance_file_path(loaded_dance))
        ))

    write_file('\n\n'.join(lines), directory_structure.get_dance_file_path(loaded_dance))

def render_music_by_dance(all_dances, directory_structure):
    number_of_tracks = {}

    for loaded_dance in all_dances:
        lines = []

        if loaded_music := loaded_dance.get_music_links():
            not_blacklisted_tracks = sorted([
                track_record for track_record in loaded_music if not track_record.blacklist
            ], key=lambda x: (normalize(x.artist), normalize(x.track_name)))

            number_of_tracks[loaded_dance.get('id')] = len(not_blacklisted_tracks)
            lines.append(secondary_header(loaded_dance.get('name') + f" ({len(not_blacklisted_tracks)})"))
            lines.extend(
                music_collapsible_section(track_record, False) for track_record in not_blacklisted_tracks
            )
        write_file(
            "\n\n".join(lines), directory_structure.get_music_by_dance(loaded_dance)
        )

    current_file = directory_structure.get_aggregated_music_by_dance()
    write_file(
        "\n\n".join([
            link(f"{dance.get('name')} ({number_of_tracks[dance.get('id')]})", directory_structure.get_music_by_dance(
                dance,
                relative_to=current_file)
             ) for dance in sorted(all_dances, key=lambda x: x.get('id'))
        ]),
        current_file
    )

def render_aggregated_dances(all_dances, loaded_translation, directory_structure):
    def dance_line(dance_obj):
        dance_name = dance_obj.get('name')
        dance_alt_name = loaded_translation.get_alt_name(dance_obj.get('id'))
        return f"{dance_name} ({dance_alt_name})" if dance_alt_name else dance_name

    current_file = directory_structure.get_aggregated_dances_path()
    write_file(
        "\n\n".join([
           f"# {loaded_translation.get_page_name('aggregated_list_of_dances') } ({len(all_dances)})"
        ] + [
            link(
                loaded_translation.get_keyword('back_to_the_list_of_pages'),
                directory_structure.get_home_page_path(relative_to=current_file)
            )
        ] + [
            link(
                dance_line(dance),
                directory_structure.get_dance_file_path(dance, directory_structure.get_aggregated_dances_path())
            ) for dance in sorted(all_dances, key=lambda x: normalize(x.get('name')))
        ]),
        current_file
    )

def render_aggregated_music(all_music, directory_structure):
    current_file = directory_structure.get_aggregated_music_path()
    write_file(
        "\n\n".join([
            music_collapsible_section(music, display_dance_name=True)
            for music
            in sorted(all_music, key=lambda x: (normalize(x.artist), normalize(x.track_name)))
        ]),
        current_file
    )

def render_music_by_artist(all_music, directory_structure):
    artists = {}
    for music in all_music:
        artists_for_that_music = [record.strip() for record in music.artist.split(',')]
        for found_artist in artists_for_that_music:
            artists[found_artist] = artists.get(found_artist, []) + [music]
    ## Clean records of artists
    artists_names = sorted(artists.keys(), key=lambda x: unidecode(x.lower()))
    for i in range(0, len(artists_names)-1):
        if directory_structure.get_music_by_artist(artists_names[i]) == directory_structure.get_music_by_artist(artists_names[i+1]):
            print(f"Found duplicate artists: {artists_names[i]}, {artists_names[i+1]}. Merging")
            artists[artists_names[i+1]] = artists[artists_names[i+1]] + artists[artists_names[i]]
            artists.pop(artists_names[i])

    for artist, artists_music in artists.items():
        current_file = directory_structure.get_music_by_artist(artist)
        write_file(
            "\n\n".join([
                f"# {artist} ({len(artists_music)})"
            ] + [
                music_collapsible_section(music, True) for music in sorted(artists_music, key=lambda x: normalize(x.track_name))
            ]),
            current_file
        )

    current_file = directory_structure.get_aggregated_music_by_artist()
    write_file(
        "\n\n".join([
            link(f"{artist} ({len(artists_music)})", directory_structure.get_music_by_artist(
                artist,
                relative_to=directory_structure.get_aggregated_music_by_artist())
             ) for artist, artists_music in sorted(artists.items(), key=lambda x: normalize(x[0]))
        ]),
        current_file
    )

    return artists

def render_home_page(loaded_translation, directory_structure, number_of_tracks, number_of_dances, number_of_artists):
    def get_text_to_display(text_to_load_from_translation, number_to_display):
        return f"{loaded_translation.get_page_name(text_to_load_from_translation)} ({number_to_display})"

    write_file(
        '\n\n'.join([
        link(
            get_text_to_display('aggregated_list_of_dances', number_of_dances),
            directory_structure.get_aggregated_dances_path(directory_structure.get_home_page_path())
        ),
        link(
            get_text_to_display('aggregated_list_of_music', number_of_tracks),
            directory_structure.get_aggregated_music_path(directory_structure.get_home_page_path())
        ),
        link(
            get_text_to_display('list_of_music_by_artist', number_of_artists),
            directory_structure.get_aggregated_music_by_artist(directory_structure.get_home_page_path())
        ),
        link(
            get_text_to_display('list_of_music_by_dance', number_of_dances),
            directory_structure.get_aggregated_music_by_dance(directory_structure.get_home_page_path())
        )
        ]),
        directory_structure.get_home_page_path()
    )
