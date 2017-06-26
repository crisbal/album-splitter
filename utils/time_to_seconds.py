def time_to_seconds(time):
    parts = time.split(":")
    seconds = None
    if len(parts) == 3:  # h:m:s
        seconds = int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
    elif len(parts) == 2:  # m:s
        seconds = int(parts[0])*60 + int(parts[1])
    return seconds
