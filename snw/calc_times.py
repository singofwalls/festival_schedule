from datetime import datetime, time, timedelta

def gen_times(start_time=datetime.combine(datetime.today(), time(hour=11, minute=35)), length=None):
    if length is None:
        end_time = start_time.replace(hour=0, minute=1) + timedelta(days=1)
    else:
        end_time = start_time + timedelta(minutes=length)

    current_time = start_time
    while current_time < end_time:
        yield current_time
        current_time += timedelta(minutes=35)


for current_time in list(gen_times()):
    print(current_time.strftime("%-I:%M%p").lower() + ": ")