import math
import time

import uasyncio
import neopixel
from machine import Pin

from colorsys import hls_to_rgb


def run_neopixel_rgb():
    p = Pin(5, Pin.OUT)
    n = neopixel.NeoPixel(p, 1)

    k_r = 3 / 100 * 2 * math.pi
    k_g = 11 / 100 * 2 * math.pi
    k_b = 8 / 100 * 2 * math.pi

    p_r = 0
    p_g = 0
    p_b = 0

    while True:
        p_r = (p_r + k_r) % math.pi
        p_g = (p_g + k_g) % math.pi
        p_b = (p_b + k_b) % math.pi

        brightness = 0.95
        r = int(brightness * (127 * math.sin(p_r)))
        g = int(brightness * (127 * math.sin(p_g)))
        b = int(brightness * (127 * math.sin(p_b)))

        n.fill((r, g, b))
        n.write()

        time.sleep_ms(80)


async def run_neopixel_hsl(k_h, k_s, k_l):
    p = Pin(5, Pin.OUT)
    n = neopixel.NeoPixel(p, 1)

    p_h = 0
    p_s = 0

    while True:
        p_h = p_h + k_h
        p_s = (p_s + 0.016 * k_s / 1000) % 0.6

        h = 0.5 + math.sin(p_h * math.pi / 180) / 2
        s = 0.2 + p_s

        # s = k_s

        assert 0 <= h <= 1.0
        assert 0 <= k_l <= 1.0
        assert 0 <= s <= 1.0

        rgb = tuple(map(lambda x: int(127 * x), hls_to_rgb(h, k_l, s)))

        n.fill(rgb)
        n.write()

        await uasyncio.sleep_ms(50)
