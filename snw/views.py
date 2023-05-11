from django.views.generic import TemplateView
from yaml import load, Loader
from snw.settings import BASE_DIR
from datetime import time, timedelta, datetime

stages = {"purple": "rgb(101, 4, 150)", "green": "rgb(10, 95, 7)", "striped": "rgb(77, 77, 77)", "sick": "rgb(173, 54, 163)"}


class ScheduleView(TemplateView):

    template_name = "schedule.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["times"] = parse_times()
        context["stages"] = stages

        return context


def gen_times(start_time=datetime.combine(datetime.today(), time(hour=11, minute=35)), length=None):
    if length is None:
        end_time = start_time.replace(hour=0, minute=1) + timedelta(days=1)
    else:
        end_time = start_time + timedelta(minutes=length)

    current_time = start_time
    while current_time < end_time:
        yield current_time
        current_time += timedelta(minutes=5)


class Band:
    def __init__(self, name=""):
        self.name = name
        self.position = ""


def parse_times():
    with open(BASE_DIR / "set_times.yaml") as f:
        set_times = load(f, Loader)

    times = {t: {stage: Band() for stage in stages} for t in list(gen_times())[::-1]}
    for stage, sets in set_times.items():
        for time, band in sets.items():
            time = datetime.combine(datetime.today(), datetime.strptime(time, "%I:%M%p").time())
            slots = list(gen_times(time, band["length"]))
            for i, time_slot in enumerate(slots):
                times[time_slot][stage].name = band["name"]
                if i == 0:
                    times[time_slot][stage].position = "bottom"
                elif i == min(len(slots) - 1, len(slots) // 2 + 1):
                    times[time_slot][stage].position = "middle"
                elif i == len(slots) - 1:
                    times[time_slot][stage].position = "top"

    return times
