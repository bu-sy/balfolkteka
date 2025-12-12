
def render_dance(loaded_dance, loaded_translation):
    lines = [
        f"# {loaded_dance.get('name')}",
        f"**{loaded_translation.get_keyword('name')}**: {loaded_dance.get('name')}"
    ]
    if alt_name := loaded_translation.get_alt_name(loaded_dance.get('id')):
        lines.append(f"**{loaded_translation.get_keyword('alt_name')}**: {alt_name}")
    return '\n\n'.join(lines)

def render_aggregated_dances(all_dances, loaded_translation):
    return "\n\n".join([
       f"# {loaded_translation.get_keyword('aggregated_list_of_dances') }"
    ] + [
        f"[{dance.get('name')}](../dances/{dance.name}.md)" for dance in all_dances
    ])
