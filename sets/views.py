from django.views.generic import TemplateView
from yaml import load, Loader
from sets.settings import BASE_DIR
from datetime import time, timedelta, datetime


class ScheduleView(TemplateView):

    template_name = "schedule.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['fest'] = kwargs["fest"] if "fest" in kwargs else "snw"
        context["times"], context["band_nums"], context["stage_colors"], context["text"] = parse_times(context['fest'])
        context['colsize'] = 12 // (len(context["stage_colors"]) + 1)

        return context


def gen_times(start_time, length=None, end_time=None):
    start_time = datetime.combine(datetime.today(), start_time)
    if length is None and end_time is None:
        end_time = start_time.replace(hour=0, minute=1) + timedelta(days=1)
    elif end_time is None:
        end_time = start_time + timedelta(minutes=length)
    else:
        end_time = datetime.combine(datetime.today(), end_time)

    current_time = start_time
    while current_time < end_time:
        yield current_time
        current_time += timedelta(minutes=5)


class Band:
    def __init__(self, name=""):
        self.name = name
        self.position = ""
        self.period = ""


def parse_times(fest_name):
    try:
        with open(BASE_DIR / "set_times" / f"{fest_name}.yaml") as f:
            set_times = load(f, Loader)
    except Exception:
        return {}, {}, {}, {"title": "Not Found", "subtitle": ""}

    stages = set_times["stages"]

    bands = []

    # Find start and end times
    earliest_time = None
    latest_time = None
    for stage, sets in set_times.items():
        if stage in ("stages", "text"):
            continue
        for time in sets:
            length = sets[time]["length"]
            time = datetime.strptime(time, "%I:%M%p")
            earliest_time = time if earliest_time is None else min(earliest_time, time)
            time = time + timedelta(minutes=length)
            latest_time = time if latest_time is None else max(latest_time, time)

    if latest_time.hour == 0:
        # Midnight of next day
        latest_time = earliest_time.replace(hour=23, minute=59)

    times = {t: {stage: Band() for stage in stages} for t in list(gen_times(earliest_time.time(), end_time=latest_time.time()))[::-1]}
    for stage, sets in set_times.items():
        if stage in ("stages", "text"):
            continue
        for time, band in sets.items():
            time = datetime.strptime(time, "%I:%M%p").time()
            slots = list(gen_times(time, band["length"]))
            bands.append(band["name"].replace(" ", "").strip())
            for i, time_slot in enumerate(slots):
                times[time_slot][stage].name = band["name"]
                times[time_slot][stage].period = slots[0].strftime("%I:%M%p") + " - " + (slots[-1] + timedelta(minutes=5)).strftime("%I:%M%p")
                if i == 0:
                    times[time_slot][stage].position = "bottom"
                elif i == min(len(slots) - 1, len(slots) // 2 + 1):
                    times[time_slot][stage].position = "middle"
                elif i == len(slots) - 1:
                    times[time_slot][stage].position = "top"

    return times, bands, stages, set_times["text"]
