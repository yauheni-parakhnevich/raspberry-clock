# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Raspberry Pi e-ink clock that displays time, date, and weather on a Waveshare 2.7inch e-Paper HAT. Runs on a Raspberry Pi (deployed to `/home/pi/e-Hat`).

## Architecture

- **`hat.py`** — Main application. Initializes the e-paper display, then loops every 60 seconds to render current time (HH:MM), date (DD/MM/YYYY), and weather data fetched from an external API. Uses Pillow (`PIL`) for image rendering.
- **`lib/waveshare_epd/`** — Vendored Waveshare e-Paper driver library (not tracked in git via `.gitignore`). The project uses `epd2in7` (2.7" display). The `lib/` directory is added to `sys.path` at runtime.
- **`pic/`** — Static assets: font file (`Font.ttc`) and test bitmaps.
- **`launcher.sh`** — Startup script that runs `hat.py` with sudo on boot (configured via system cron/rc.local).

## Running

```bash
# On the Raspberry Pi:
sudo python3 hat.py

# Or via the launcher:
./launcher.sh
```

## Dependencies

- Python 3 (tested on Python 3.7 / Raspbian)
- `Pillow` (PIL) — image rendering
- `requests` — HTTP weather API calls
- `RPi.GPIO` / `spidev` — hardware GPIO/SPI (required by waveshare_epd driver on the Pi)

## Key Details

- Display resolution: 264×176 pixels, rendered in landscape mode (`epd.height` x `epd.width`)
- Images are 1-bit (black/white): `Image.new('1', ...)` with fill 0 = black, 255 = white
- The display is fully cleared (`epd.Clear(0xFF)`) on startup before entering the render loop
- Weather API uses coordinates for Zurich area (47.39889, 8.44972)
