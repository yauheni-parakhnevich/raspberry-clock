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
    "&current=temperature_2m,precipitation_probability"
)

epd = epd2in7.EPD()

try:
    epd.init()
    epd.Clear(0xFF)

    font100 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 100)
    font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
    font14 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 14)

    while True:
        now = datetime.now()

        Himage = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(Himage)

        draw.text((5, 35), '{:%H:%M}'.format(now), font=font100, fill=0)
        draw.text((80, 10), '{:%d/%m/%Y}'.format(now), font=font24, fill=0)

        try:
            response = requests.get(WEATHER_URL, timeout=10)
            current = response.json()['current']
            temp = current['temperature_2m']
            precip = current.get('precipitation_probability', 0)
            draw.text((20, 140), "Currently {:2.0f} C, {:2.0f}% chance of rain".format(temp, precip), font=font14, fill=0)
        except Exception:
            logging.info("Got exception during weather loading, skipping...")

        epd.display(epd.getbuffer(Himage))

        # Sleep until the next full minute
        seconds_to_next_minute = 60 - datetime.now().second
        time.sleep(seconds_to_next_minute)

except KeyboardInterrupt:
    logging.info("Stopping...")
finally:
    epd.sleep()
