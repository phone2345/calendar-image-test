import requests
from icalendar import Calendar
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from dateutil import tz
import os

ICS_URL = "https://calendar.google.com/calendar/ical/b5bd045ab768cacc7e69760164c2b39299dffc214646d5db3e447dfeb7fdbc8a%40group.calendar.google.com/public/basic.ics"

WIDTH = 1000
HEIGHT = 600

def fetch_events():

    res = requests.get(ICS_URL)
    cal = Calendar.from_ical(res.text)

    events = []

    for component in cal.walk():
        if component.name == "VEVENT":

            start = component.get('dtstart').dt
            summary = str(component.get('summary'))

            if isinstance(start, datetime):
                events.append((start, summary))

    events.sort()

    return events


def filter_today(events):

    today = datetime.now().date()

    return [
        e for e in events
        if e[0].date() == today
    ]


def filter_week(events):

    now = datetime.now()
    end = now + timedelta(days=7)

    return [
        e for e in events
        if now <= e[0] <= end
    ]


def render(events, title, path):

    img = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(img)

    y = 60

    draw.text((50,20), title, fill="black")

    for start, summary in events[:10]:

        time = start.strftime("%m-%d %H:%M")

        text = f"{time}   {summary}"

        draw.text((50,y), text, fill="black")

        y += 40

    os.makedirs("output", exist_ok=True)

    img.save(path)


def main():

    events = fetch_events()

    today = filter_today(events)
    week = filter_week(events)

    render(today, "Today's Schedule", "output/today.png")
    render(week, "This Week", "output/week.png")


if __name__ == "__main__":
    main()
