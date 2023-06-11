# import st7789py as st7789
import st7789
from machine import Pin

import vga1_8x8 as font


class Display:
    def __init__(self, spi):
        self.columns = 128
        self.rows = 160
        self.display = st7789.ST7789(spi,
                                     self.columns,
                                     self.rows,
                                     cs=Pin(14, Pin.OUT),
                                     reset=Pin(26, Pin.OUT),
                                     dc=Pin(25, Pin.OUT),
                                     backlight=Pin(12, Pin.OUT),
                                     color_order=st7789.RGB)

    def init(self):
        self.display.init()
        self.display.inversion_mode(False)

        self.display.fill(st7789.color565(0, 0, 0))

    def text(self, text, line):
        self.display.text(
            font,
            text,
            8,
            line,
            st7789.color565(0, 127, 0),
            st7789.color565(0, 0, 0),
        )

    def center(self, text, line):
        col = (self.columns >> 1) - (len(text) * font.WIDTH >> 1)
        self.display.text(
            font,
            text,
            col,
            line,
            st7789.color565(0, 127, 0),
            st7789.color565(0, 0, 0),
        )
