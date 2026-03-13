import os
import requests

from icalendar import Calendar
from datetime import datetime, timedelta, timezone, date
from PIL import Image, ImageDraw, ImageFont


ICS_URL = "https://calendar.google.com/calendar/embed?src=b5bd045ab768cacc7e69760164c2b39299dffc214646d5db3e447dfeb7fdbc8a%40group.calendar.google.com&ctz=Asia%2FTaipei"

WIDTH = 1000
HEIGHT = 600

TAIWAN_TZ = timezone(timedelta(hours=8))


# 下載 ICS
def fetch_calendar():

    res = requests.get(ICS_URL)
    res.raise_for_status()

    return Calendar.from_ical(res.text)


# 解析 events
def parse_events(cal):

    events = []

    for component in cal.walk():

        if component.name != "VEVENT":
            continue

        start = component.get("dtstart").dt
        summary = str(component.get("summary"))

        # 處理全天事件
        if isinstance(start, date) and not isinstance(start, datetime):

            start = datetime.combine(
                start,
                datetime.min.time(),
                tzinfo=timezone.utc
            )

        if isinstance(start, datetime):

            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)

            start = start.astimezone(TAIWAN_TZ)

            events.append((start, summary))

    events.sort()

    return events


# 今日事件
def filter_today(events):

    today = datetime.now(TAIWAN_TZ).date()

    return [
        e for e in events
        if e[0].date() == today
    ]


# 本週事件
def filter_week(events):

    now = datetime.now(TAIWAN_TZ)
    end = now + timedelta(days=7)

    return [
        e for e in events
        if now <= e[0] <= end
    ]


# 生成圖片
def render_image(events, title, path):

    img = Image.new("RGB", (WIDTH, HEIGHT), "white")

    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("DejaVuSans.ttf", 40)
        font_text = ImageFont.truetype("DejaVuSans.ttf", 28)
    except:
        font_title = None
        font_text = None

    draw.text((50, 20), title, fill="black", font=font_title)

    y = 100

    if not events:

        draw.text((50, y), "No events", fill="gray", font=font_text)

    for start, summary in events[:10]:

        time_str = start.strftime("%m-%d %H:%M")

        text = f"{time_str}  {summary}"

        draw.text((50, y), text, fill="black", font=font_text)

        y += 45

    os.makedirs("output", exist_ok=True)

    img.save(path)


def main():

    cal = fetch_calendar()

    events = parse_events(cal)

    today_events = filter_today(events)
    week_events = filter_week(events)

    render_image(today_events, "Today's Schedule", "output/today.png")

    render_image(week_events, "This Week", "output/week.png")


if __name__ == "__main__":
    main()
