#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd2in7
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import requests

logging.basicConfig(level=logging.INFO)

WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=47.39889&longitude=8.44972"
    "&current=temperature_2m,apparent_temperature,precipitation_probability,weather_code"
    "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset"
    "&timezone=auto&forecast_days=4"
)

# Screen width/height in landscape mode
W = 264
H = 176

# Alternate between clock and forecast every cycle (2 minutes per screen)
SCREEN_CLOCK = 0
SCREEN_FORECAST = 1


def draw_weather_icon(draw, x, y, code, size=24):
    """Draw a simple weather icon based on WMO weather code."""
    if code <= 1:
        # Clear: sun (circle with rays)
        r = size // 3
        cx, cy = x + size // 2, y + size // 2
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=0)
        ray = r + 4
        for angle_pair in [(-ray, 0, ray, 0), (0, -ray, 0, ray)]:
            draw.line([cx + angle_pair[0], cy + angle_pair[1],
                       cx + angle_pair[2], cy + angle_pair[3]], fill=0)
    elif code <= 3:
        # Partly cloudy / overcast: cloud
        _draw_cloud(draw, x, y, size)
    elif code <= 48:
        # Fog: three horizontal lines
        for i in range(3):
            ly = y + size // 4 + i * (size // 4)
            draw.line([x + 2, ly, x + size - 2, ly], fill=0)
    elif code <= 67:
        # Drizzle / Rain: cloud + drops
        _draw_cloud(draw, x, y - 4, size)
        for dx in [size // 4, size // 2, 3 * size // 4]:
            draw.line([x + dx, y + size - 6, x + dx, y + size], fill=0)
    elif code <= 77:
        # Snow: cloud + dots
        _draw_cloud(draw, x, y - 4, size)
        for dx in [size // 4, size // 2, 3 * size // 4]:
            draw.ellipse([x + dx - 1, y + size - 4, x + dx + 1, y + size - 2], fill=0)
    elif code <= 82:
        # Rain showers: cloud + heavy drops
        _draw_cloud(draw, x, y - 4, size)
        for dx in [size // 5, 2 * size // 5, 3 * size // 5, 4 * size // 5]:
            draw.line([x + dx, y + size - 6, x + dx, y + size], fill=0)
    elif code >= 95:
        # Thunderstorm: cloud + zigzag
        _draw_cloud(draw, x, y - 4, size)
        zx = x + size // 2
        zy = y + size - 8
        draw.line([zx, zy, zx - 3, zy + 4, zx + 3, zy + 4, zx, zy + 8], fill=0)
    else:
        # Fallback: cloud
        _draw_cloud(draw, x, y, size)


def _draw_cloud(draw, x, y, size):
    """Draw a simple cloud shape."""
    w, h = size, size // 2
    cy = y + size // 3
    draw.ellipse([x + w // 4, cy - h // 3, x + 3 * w // 4, cy + h // 2], outline=0)
    draw.ellipse([x, cy, x + w // 2, cy + h], outline=0)
    draw.ellipse([x + w // 2 - 2, cy + 2, x + w, cy + h], outline=0)


def fetch_weather():
    """Fetch weather data from Open-Meteo. Returns dict or None."""
    try:
        response = requests.get(WEATHER_URL, timeout=10)
        return response.json()
    except Exception:
        logging.info("Got exception during weather loading, skipping...")
        return None


def draw_clock_screen(draw, now, weather, fonts):
    """Draw the main clock screen with time, date, and current weather."""
    font100, font24, font18, font14 = fonts

    # Date with day of week, centered
    date_str = '{:%a %d/%m/%Y}'.format(now)
    bbox = font24.getbbox(date_str)
    date_w = bbox[2] - bbox[0]
    draw.text(((W - date_w) // 2, 2), date_str, font=font24, fill=0)

    # Separator
    draw.line([10, 28, W - 10, 28], fill=0)

    # Time, centered
    time_str = '{:%H:%M}'.format(now)
    bbox = font100.getbbox(time_str)
    time_w = bbox[2] - bbox[0]
    draw.text(((W - time_w) // 2, 30), time_str, font=font100, fill=0)

    # Separator
    draw.line([10, 132, W - 10, 132], fill=0)

    if weather:
        current = weather.get('current', {})
        daily = weather.get('daily', {})
        temp = current.get('temperature_2m', 0)
        feels = current.get('apparent_temperature', 0)
        precip = current.get('precipitation_probability', 0)
        code = current.get('weather_code', 0)

        # Weather icon
        draw_weather_icon(draw, 5, 136, code, size=20)

        # Current conditions
        draw.text((28, 136), "{:.0f}C (feels {:.0f}C) {}% rain".format(temp, feels, precip), font=font14, fill=0)

        # Bottom line: sunrise/sunset + daily min/max
        sunrise = daily.get('sunrise', [''])[0]
        sunset = daily.get('sunset', [''])[0]
        t_min = daily.get('temperature_2m_min', [0])[0]
        t_max = daily.get('temperature_2m_max', [0])[0]

        sun_rise_str = sunrise[-5:] if sunrise else '--:--'
        sun_set_str = sunset[-5:] if sunset else '--:--'
        bottom = "^{} v{}  L{:.0f} H{:.0f}C".format(sun_rise_str, sun_set_str, t_min, t_max)
        draw.text((20, 156), bottom, font=font14, fill=0)


def draw_forecast_screen(draw, weather, fonts):
    """Draw a 4-day forecast screen."""
    _, font24, font18, font14 = fonts
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    # Title
    title = "Forecast"
    bbox = font24.getbbox(title)
    title_w = bbox[2] - bbox[0]
    draw.text(((W - title_w) // 2, 2), title, font=font24, fill=0)
    draw.line([10, 28, W - 10, 28], fill=0)

    if not weather:
        draw.text((20, 60), "No weather data", font=font18, fill=0)
        return

    daily = weather.get('daily', {})
    times = daily.get('time', [])
    codes = daily.get('weather_code', [])
    t_maxs = daily.get('temperature_2m_max', [])
    t_mins = daily.get('temperature_2m_min', [])
    precips = daily.get('precipitation_probability_max', [])

    num_days = min(4, len(times))
    row_h = 35
    start_y = 33

    for i in range(num_days):
        y = start_y + i * row_h
        # Parse day name
        try:
            dt = datetime.strptime(times[i], '%Y-%m-%d')
            day_name = days[dt.weekday()]
            if i == 0:
                day_name = "Today"
        except (ValueError, IndexError):
            day_name = "---"

        draw.text((5, y + 4), day_name, font=font18, fill=0)
        draw_weather_icon(draw, 60, y + 2, codes[i] if i < len(codes) else 0, size=22)
        draw.text((90, y + 4), "{:.0f}/{:.0f}C".format(
            t_mins[i] if i < len(t_mins) else 0,
            t_maxs[i] if i < len(t_maxs) else 0
        ), font=font18, fill=0)
        draw.text((190, y + 4), "{}%".format(
            int(precips[i]) if i < len(precips) else 0
        ), font=font18, fill=0)

        if i < num_days - 1:
            draw.line([5, y + row_h - 2, W - 5, y + row_h - 2], fill=0, width=1)


epd = epd2in7.EPD()

try:
    epd.init()
    epd.Clear(0xFF)

    font100 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 100)
    font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
    font18 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 18)
    font14 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 14)
    fonts = (font100, font24, font18, font14)

    screen = SCREEN_CLOCK
    weather = None

    while True:
        now = datetime.now()

        # Refresh weather data every cycle
        weather = fetch_weather() or weather

        Himage = Image.new('1', (W, H), 255)
        draw = ImageDraw.Draw(Himage)

        if screen == SCREEN_CLOCK:
            draw_clock_screen(draw, now, weather, fonts)
        else:
            draw_forecast_screen(draw, weather, fonts)

        epd.display(epd.getbuffer(Himage))

        # Alternate screen
        screen = SCREEN_FORECAST if screen == SCREEN_CLOCK else SCREEN_CLOCK

        # Sleep until the next full minute
        seconds_to_next_minute = 60 - datetime.now().second
        time.sleep(seconds_to_next_minute)

except KeyboardInterrupt:
    logging.info("Stopping...")
finally:
    epd.sleep()
