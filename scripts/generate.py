import os
import requests

from icalendar import Calendar
from datetime import datetime, timedelta, timezone, date
from PIL import Image, ImageDraw, ImageFont


ICS_URL = "https://calendar.google.com/calendar/ical/b5bd045ab768cacc7e69760164c2b39299dffc214646d5db3e447dfeb7fdbc8a%40group.calendar.google.com/public/basic.ics"

WIDTH = 1000
HEIGHT = 600

TAIWAN_TZ = timezone(timedelta(hours=8))


TAIWAN_TZ = timezone(timedelta(hours=8))

WIDTH = 1200
HEIGHT = 630


def fetch_calendar():

    res = requests.get(ICS_URL)
    res.raise_for_status()

    return Calendar.from_ical(res.text)


def parse_events(cal):

    events = []

    now = datetime.now(TAIWAN_TZ)
    limit = now + timedelta(days=60)

    for component in cal.walk():

        if component.name != "VEVENT":
            continue

        start = component.get("dtstart").dt
        summary = str(component.get("summary"))

        if isinstance(start, date) and not isinstance(start, datetime):

            start = datetime.combine(
                start,
                datetime.min.time(),
                tzinfo=timezone.utc
            )

        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        start = start.astimezone(TAIWAN_TZ)

        exdates = set()

        if component.get("exdate"):

            for ex in component.get("exdate").dts:

                exdt = ex.dt

                if isinstance(exdt, date) and not isinstance(exdt, datetime):

                    exdt = datetime.combine(
                        exdt,
                        datetime.min.time(),
                        tzinfo=timezone.utc
                    )

                if exdt.tzinfo is None:
                    exdt = exdt.replace(tzinfo=timezone.utc)

                exdates.add(exdt.astimezone(TAIWAN_TZ))

        if component.get("rrule"):

            rule_str = component["rrule"].to_ical().decode()

            rule = rrulestr(rule_str, dtstart=start)

            occ = rule.between(now, limit, inc=True)

            for o in occ:

                o = o.astimezone(TAIWAN_TZ)

                if o not in exdates:

                    events.append((o, summary))

        else:

            events.append((start, summary))

    events.sort()

    return events


def filter_range(events, start, end):

    return [
        e for e in events
        if start <= e[0] <= end
    ]


def render_card(events, title, path):

    img = Image.new("RGB", (WIDTH, HEIGHT), "#f5f6fa")

    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 64)
        text_font = ImageFont.truetype("DejaVuSans.ttf", 34)
    except:
        title_font = None
        text_font = None

    draw.text((80, 60), title, fill="#222", font=title_font)

    y = 200

    if not events:

        draw.text((80, y), "No events", fill="#888", font=text_font)

    for start, summary in events[:10]:

        time_str = start.strftime("%m-%d %H:%M")

        text = f"{time_str}   {summary}"

        draw.text((80, y), text, fill="#333", font=text_font)

        y += 60

    os.makedirs("output", exist_ok=True)

    img.save(f"output/{path}")


def main():

    cal = fetch_calendar()

    events = parse_events(cal)

    now = datetime.now(TAIWAN_TZ)

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    tomorrow_start = today_end
    tomorrow_end = tomorrow_start + timedelta(days=1)

    week_end = now + timedelta(days=7)

    month_end = now + timedelta(days=30)

    today = filter_range(events, today_start, today_end)

    tomorrow = filter_range(events, tomorrow_start, tomorrow_end)

    week = filter_range(events, now, week_end)

    month = filter_range(events, now, month_end)

    render_card(today, "Today", "today.png")

    render_card(tomorrow, "Tomorrow", "tomorrow.png")

    render_card(week, "This Week", "week.png")

    render_card(month, "This Month", "month.png")


if __name__ == "__main__":
    main()
