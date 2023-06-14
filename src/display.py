# import st7789py as st7789
import time

import romanp as font_v
import st7789
import vga2_8x16 as font
from machine import Pin, PWM


class Display:
    def __init__(self, spi):
        self._cs = Pin(14, Pin.OUT)
        self._dc = Pin(25, Pin.OUT)
        self._spi = spi

        pc = 2
        pr = 2
        self.columns = 128 + pc
        self.rows = 160 + pr
        self._brightness_pwm = PWM(Pin(12), freq=100, duty_u16=0)

        # noinspection PyUnresolvedReferences
        self.display = st7789.ST7789(self._spi,
                                     self.columns,
                                     self.rows,
                                     # buffer_size=(self.rows + px) * (self.columns + py) * 2,
                                     cs=self._cs,
                                     reset=Pin(26, Pin.OUT),
                                     dc=self._dc,
                                     # backlight=Pin(12, Pin.OUT),
                                     color_order=st7789.RGB)

    def init(self):
        self.dim(0.2)
        self.display.inversion_mode(False)

        self.display.init()
        # self.display.bounding(True)
        time.sleep_ms(15)
        self.display.fill(st7789.color565(0, 0, 0))
        time.sleep_ms(15)
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

    def textv(self, text, line):
        self.display.draw(
            font_v,
            text,
            8,
            line,
            st7789.color565(0, 127, 0),
            1,
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

    def off(self):
        self.display.off()

    def on(self):
        self.display.on()

    def _write(self, command=None, data=None):
        print(command, data)
        """SPI write to the device: commands and data."""
        if self._cs:
            self._cs.off()

        if command is not None:
            self._dc.off()
            self._spi.write(bytes([command]))
        if data is not None:
            self._dc.on()
            self._spi.write(data)
            if self._cs:
                self._cs.on()

    def dim(self, setting):
        self._brightness_pwm.duty_u16(int(setting * 0xFFFF))
