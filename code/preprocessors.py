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
    # Second merge - based on the manually defined duplicates
    for music in music_to_merge:
        for music_to_compare_to in all_music_filtered:
            if music.merge_with.same_metadata(music_to_compare_to):
                print(f"Merging manually {music_to_compare_to.print_metadata()} and {music.print_metadata()}")
                _merge_records(music_to_compare_to, music)
                break
        else:
            raise RuntimeError(f"When merging failed to find music with metadata {music.merge_with.print_metadata()}")
    return all_music_filtered