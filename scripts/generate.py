import os
import requests

from icalendar import Calendar
from dateutil.rrule import rrulestr
from datetime import datetime, timedelta, timezone, date
from PIL import Image, ImageDraw, ImageFont

#ICS_URL = "https://calendar.google.com/calendar/ical/f5682t1g68e42n1ij023o8dk2o%40group.calendar.google.com/public/basic.ics"
ICS_URL = "https://calendar.google.com/calendar/ical/b5bd045ab768cacc7e69760164c2b39299dffc214646d5db3e447dfeb7fdbc8a%40group.calendar.google.com/public/basic.ics"
FONT_PATH = "fonts/NotoSansTC-VariableFont_wght.ttf"

WIDTH = 1200
HEIGHT = 630

BG = "#f5f6fa"
CARD = "#ffffff"
TEXT = "#222222"
SUB = "#666666"

TAIWAN_TZ = timezone(timedelta(hours=8))

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
        end = component.get("dtend")
        if end:
            duration = end.dt - start
            duration = str(duration)
        else:
            duration = ""
            
        summary = str(component.get("summary"))
        location = str(component.get("location", ""))

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

                    events.append((o, summary, duration, location))

        else:

            events.append((start, summary, duration, location))

    events.sort()

    return events


def filter_range(events, start, end):

    return [
        e for e in events
        if start <= e[0] <= end
    ]

def render_card(events, title, path):

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    BLUE = "#2F6FDB"
    WHITE = "#FFFFFF"
    BLACK = "#222222"
    GRID = "#D0D0D0"    

    title_font = ImageFont.truetype(FONT_PATH, 52)
    header_font = ImageFont.truetype(FONT_PATH, 30)
    text_font = ImageFont.truetype(FONT_PATH, 28)
    small_font = ImageFont.truetype(FONT_PATH, 24)

    # title
    draw.text((80, 40), title, fill=BLACK, font=title_font)

    table_x = 80
    table_y = 140

    col1 = 220
    col2 = WIDTH - 160 - col1

    row_h = 70

    rows = min(len(events), 8) + 1

    table_w = col1 + col2
    table_h = row_h * rows

    # header row
    draw.rectangle(
        [table_x, table_y, table_x + table_w, table_y + row_h],
        fill=BLUE
    )

    # vertical line
    draw.line(
        [table_x + col1, table_y, table_x + col1, table_y + table_h],
        fill=GRID,
        width=2
    )

    # header text
    draw.text(
        (table_x + 20, table_y + 18),
        "開始時間",
        fill=WHITE,
        font=header_font
    )

    draw.text(
        (table_x + col1 + 20, table_y + 18),
        "活動內容",
        fill=WHITE,
        font=header_font
    )

    for i, (start, summary, duration, location) in enumerate(events[:8]):

        y = table_y + (i + 1) * row_h

        # 左側時間 cell
        draw.rectangle(
            [table_x, y, table_x + col1, y + row_h],
            fill=BLUE
        )

        # 右側內容 cell
        draw.rectangle(
            [table_x + col1, y, table_x + table_w, y + row_h],
            fill=WHITE
        )

        # grid line
        draw.line(
            [table_x, y, table_x + table_w, y],
            fill=GRID
        )

        time_str = start.strftime("%H:%M")

        draw.text(
            (table_x + 20, y + 20),
            time_str,
            fill=WHITE,
            font=text_font
        )

        # event title
        draw.text(
            (table_x + col1 + 20, y + 8),
            summary,
            fill=BLACK,
            font=text_font
        )

        # duration
        draw.text(
            (table_x + col1 + 20, y + 34),
            f"時長：{duration}",
            fill=BLACK,
            font=small_font
        )

        # location
        draw.text(
            (table_x + col1 + 180, y + 34),
            f"地點：{location or ''}",
            fill=BLACK,
            font=small_font
        )

    os.makedirs("output", exist_ok=True)

    img.save(f"output/{path}")
    
def render_card_old(events, title, path):

    img = Image.new("RGB", (WIDTH, HEIGHT), "#f5f6fa")

    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype(FONT_PATH, 64)
        text_font = ImageFont.truetype(FONT_PATH, 34)
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
