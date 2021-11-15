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
from PIL import Image,ImageDraw,ImageFont
import traceback
import requests

logging.basicConfig(level=logging.DEBUG)

epd = epd2in7.EPD()

epd.init()
epd.Clear(0xFF)

font100 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 100)
font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
font14 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 14)

try:
    while True:
        now = datetime.now()

        Himage = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the frame
        draw = ImageDraw.Draw(Himage)
#        draw.rectangle((0, 35, epd.height, 140), fill = 255)

        draw.text((5, 35), '{:%H:%M}'.format(now), font = font100, fill = 0)

        draw.text((80, 10), '{:%d/%m/%Y}'.format(now), font = font24, fill = 0)

        try:
            response = requests.get("https://api.darksky.net/forecast/dc89121d5a419b80c39b702d806f2d13/47.39889,8.44972?units=si&lang=en")
            currently = response.json()['currently']
            draw.text((20, 140), "Currently {:2.0f} C, {:2.0f}% chance of rain".format(currently['temperature'], currently['precipProbability'] * 100), font = font14, fill = 0)
        except Exception:
            logging.info("Got exception during weather loading, skipping...")

        epd.display(epd.getbuffer(Himage))

        time.sleep(60)

except KeyboardInterrupt:
    logging.info("Stopping...")
