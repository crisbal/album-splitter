def update_time_change(time_elapsed, track_time):
    elapsed = time_elapsed.split(":")
    if len(elapsed) == 2:
        elapsed_h = 0
        elapsed_m = int(elapsed[0])
        elapsed_s = int(elapsed[1])
    if len(elapsed) == 3:
        elapsed_h = int(elapsed[0])
        elapsed_m = int(elapsed[1])
        elapsed_s = int(elapsed[2])

    track = track_time.split(":")
    # get track length
    if len(track) == 2:
        track_h = 0
        track_m = int(track[0])
        track_s = int(track[1])
    if len(track) == 3:
        track_h = int(track[0])
        track_m = int(track[1])
        track_s = int(track[2])

    # add track length to elapsed time
    elapsed_h = elapsed_h + track_h
    elapsed_m = elapsed_m + track_m
    elapsed_s = elapsed_s + track_s

    if elapsed_m >= 60:
        elapsed_m -= 60
        elapsed_h += 1
    elif elapsed_s >= 60:
        elapsed_s -= 60
        elapsed_m += 1

    str_h = ""
    str_m = ""
    str_s = ""
    # 1 -> 01
    if elapsed_h < 10:
        str_h = "0" + str(elapsed_h)
    else:
        str_h = str(elapsed_h)

    if elapsed_m < 10:
        str_m = "0" + str(elapsed_m)
    else:
        str_m = str(elapsed_m)

    if elapsed_s < 10:
        str_s = "0" + str(elapsed_s)
    else:
        str_s = str(elapsed_s)

    return '{}:{}:{}'.format(str_h, str_m, str_s)
