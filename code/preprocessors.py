def merge_music(all_music):
    def _merge_records(record_A, record_B):
        record_A.add_dances(record_B.dances)
        record_A.merge_music_links(record_B)

    music_not_to_merge = []
    music_to_merge = []
    for music in all_music:
        if music.merge_with:
            music_to_merge.append(music)
        else:
            music_not_to_merge.append(music)

    music_list = sorted(music_not_to_merge, key=lambda x: (x.artist.lower(), x.track_name.lower()))

    # First merge - based on the same artist/track_name combination
    all_music_filtered = music_list[0:1]
    for music in music_list[1:]:
        if all_music_filtered[-1].same_metadata(music, case_sensitive_check=False):
            print(
                f"Found {all_music_filtered[-1].print_metadata()} for {all_music_filtered[-1].get_dances_as_string()} and {music.get_dances_as_string()}. Merging")

            _merge_records(all_music_filtered[-1], music)
        else:
            all_music_filtered.append(music)

    assert len(all_music_filtered) == len(set(all_music_filtered))
    return all_music_filtered