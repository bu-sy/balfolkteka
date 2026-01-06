def merge_music(all_music):
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
        if music_list[i].artist == music_list[i + 1].artist and music_list[i].track_name == music_list[i + 1].track_name:
            print(
                f"Found {music_list[i].artist} - '{music_list[i].track_name}' for {music_list[i].get_dances()} and {music_list[i + 1].get_dances()}. Merging")
            all_music_filtered[-1].add_dances(music_list[i + 1].dances)
            all_music_filtered[-1].merge_music_links(music_list[i + 1])
        else:
            all_music_filtered.append(music_list[i + 1])

    assert len(all_music_filtered) == len(set(all_music_filtered))
    return all_music_filtered