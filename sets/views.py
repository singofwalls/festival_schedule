from django.views.generic import TemplateView
from django.http import HttpResponse, HttpResponseRedirect
from yaml import load, Loader
from pathlib import Path
from sets.settings import BASE_DIR, STATIC_ROOT
from datetime import time, timedelta, datetime
import os
from html2image import Html2Image
from PIL import Image



class HomeView(TemplateView):

    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fests = []
        for fest in os.listdir(BASE_DIR / "set_times"):
            if fest.endswith(".yaml"):
                with open(BASE_DIR / 'set_times' / fest) as f:
                    set_times = load(f, Loader)
                    fest_name = set_times["text"]["title"]
                    fest_id = fest.removesuffix(".yaml")
                    fests.append((fest_name, fest_id))

        context['fests'] = sorted(fests, key=lambda f: f[0])
        return context


class ScheduleView(TemplateView):

    template_name = "schedule.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['fest'] = kwargs["fest"] if "fest" in kwargs else "snw23"
        context["times"], context["band_nums"], context["stage_colors"], context["text"] = parse_times(context['fest'])
        context['colsize'] = 12 // (len(context["stage_colors"]) + 1)

        bands = self.request.GET.get("bands", 0)
        context["preview_image"] = f"/{context['fest']}/preview?bands={bands}"

        return context


def generate_preview(request, fest):
    """Take a screenshot of the webpage and save it to an image."""
    bands = request.GET.get("bands")
    if bands is None:
        bands = 0

    path = STATIC_ROOT / Path(f"sets/previews/{fest}/{bands}.jpg")
    os.makedirs(path.parent, exist_ok=True)

    try:
        with open(path, "rb") as f:
            return HttpResponse(f.read(), content_type="image/jpeg")
    except FileNotFoundError:
        pass

    # Generate preview
    hti = Html2Image(output_path=str(path.parent), custom_flags=['--no-sandbox'])
    hti.browser_executable = "/opt/google/chrome/google-chrome"
    url = request.build_absolute_uri().replace("/preview", "")
    hti.screenshot(url=url, save_as=path.name)

    try:
        with Image.open(path) as im:
            im_crop = im.crop((300, 0, 1620, 1080))
        im_crop.save(path)
        with open(path, "rb") as f:
            return HttpResponse(f.read(), content_type="image/jpeg")
    except FileNotFoundError:
        raise


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
                elif i == min(len(slots) - 2, len(slots) // 2 + 1):
                    times[time_slot][stage].position = "middle"
                elif i == len(slots) - 1:
                    times[time_slot][stage].position = "top"

    return times, bands, stages, set_times["text"]
