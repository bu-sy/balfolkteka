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

    music_list = sorted(music_not_to_merge, key=lambda x: (x.artist, x.track_name))
    all_music_filtered = music_list[0:1]  # Finding duplicates, track that were categorized as multiple dances
    for i in range(0, len(music_list) - 1):
        if music_list[i].same_metadata(music_list[i+1]):
            print(
                f"Found {music_list[i].artist} - '{music_list[i].track_name}' for {music_list[i].get_dances_as_string()} and {music_list[i + 1].get_dances_as_string()}. Merging")

            _merge_records(all_music_filtered[-1], music_list[i + 1])
        else:
            all_music_filtered.append(music_list[i + 1])

    assert len(all_music_filtered) == len(set(all_music_filtered))
    return all_music_filtered