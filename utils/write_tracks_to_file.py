from .update_time_change import update_time_change


def write_tracks_to_file(track_times, track_titles, track_filename):
    time_elapsed = "00:00:00"
    text = ""
    for title, time in zip(track_titles, track_times):
        text += '{} - {}\n'.format(time_elapsed, str(title))
        time_elapsed = update_time_change(time_elapsed, time)

    with open(track_filename, "w") as text_file:
        text_file.write(text)
