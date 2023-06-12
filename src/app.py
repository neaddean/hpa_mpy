import _thread
import binascii
import json
import math
import time

import uasyncio
from esp32 import NVS
from machine import I2C, Pin, SPI, unique_id, ADC
from umqtt.simple import MQTTClient

import util
from display import Display
from led import run_neopixel_hsl
from primitives import RingbufQueue
from sht31 import SHT31
from util.nvs import nvs_get_str
from util.timeit import timeit


class App:
    def __init__(self):
        print("initing app...")
        self.UID = binascii.hexlify(unique_id())
        self.last_received_rpc_id = None
        self._rsp_queue = RingbufQueue([0 for _ in range(10)])

        # noinspection PyArgumentList
        i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=400_000, timeout=500_000)
        # reset i2c devices
        i2c.writeto(0x00, b'\x06')

        self.sht31 = SHT31(i2c)

        assert self.sht31.addr in i2c.scan()

        self.sht31.read(True)

        spi2 = SPI(2, baudrate=30_000_000, polarity=1, sck=Pin(18), mosi=Pin(23))

        self.display = Display(spi2)
        self.display.init()

        self.keyboard_adc = ADC(Pin(36, Pin.IN), atten=ADC.ATTN_11DB)
        self.sound_adc = ADC(Pin(39, Pin.IN), atten=ADC.ATTN_0DB)

        self.mqtt_client = self._create_mqtt_client()
        uasyncio.create_task(self._mqtt_dispatch())

        self.mqtt_client.publish("v1/devices/me/attributes/request/0", "{'sharedKeys': 'app'}")

        self._init_flag = False

    def wait_for_ready(self):
        while not self._init_flag:
            time.sleep_ms(100)

    def _create_mqtt_client(self):
        nvs = NVS("_config")

        mqtt_broker = nvs_get_str(nvs, "mqtt_broker")
        access_token = nvs_get_str(nvs, "access_token")

        mqtt_client = MQTTClient(self.UID,
                                 mqtt_broker,
                                 user=access_token,
                                 password='')

        mqtt_client.connect()
        mqtt_client.set_callback(self._mqtt_sub_cb)
        mqtt_client.subscribe("v1/devices/me/rpc/request/+")
        mqtt_client.subscribe("v1/devices/me/attributes/response/+")

        return mqtt_client

    def _mqtt_sub_cb(self, topic, msg):
        topic = topic.decode()
        self.last_received_rpc_id = topic.split("/")[-1]
        msg = json.loads(msg)
        print((topic, msg))

        if "method" in msg:
            if msg["method"] == "setHeater":
                self.sht31.heater(msg["params"])
            elif msg["method"] == "getHeater":
                heater_status = bool(self.sht31.get_status()["heater"])
                self.mqtt_client.publish(f"v1/devices/me/rpc/response/{self.last_received_rpc_id}",
                                         json.dumps(heater_status))
            else:
                print("ERROR: Unhandled RPC!")
        else:
            self._rsp_queue.put_nowait((topic, msg))

    async def _sht31_telem(self):
        now = time.ticks_ms()
        while True:
            temperature, humidity = self.sht31.read(v=util.verbose)

            d = {"temperature": temperature, "humidity": humidity}

            if time.ticks_diff(time.ticks_ms(), now) > 30:
                self.mqtt_client.publish("v1/devices/me/telemetry", json.dumps(d))
                now = time.time()

            # display.display.fill(st7789.RED)
            self.display.text(f"temp: {temperature:0.1f} C", 40)
            self.display.text(f"hum : {humidity:0.1f} %", 50)

            await uasyncio.sleep(1)

    async def _sound_telem(self):
        window_len = 5
        vals = [0] * window_len
        now = time.ticks_ms()
        while True:
            with timeit(suppress=True):
                sound = self.get_sound()
                vals[window_len - 1] = sound

                for i in range(window_len):
                    vals[i], vals[window_len - 1] = vals[window_len - 1], vals[i]

                # if time.time() - now > 0.5:
                #     print(vals)

                if time.ticks_diff(time.ticks_ms(), now) > 0.5:
                    self.display.text(f"mic : {sound:5.0f} mV", 60)
                    self.display.text(f"mic : {10 * math.log10(sound):5.2f} dB", 70)
                    now = time.time()

            await uasyncio.sleep_ms(100)

    async def _mqtt_dispatch(self):
        while True:
            self.mqtt_client.check_msg()
            await uasyncio.sleep_ms(50)

    def get_keyboard(self):
        return self.keyboard_adc.read_u16()

    def get_sound(self):
        return self.sound_adc.read_uv() // 1000

    async def _read_keyboard(self):
        while True:
            print(self.get_keyboard())
            print(self.get_sound())
            await uasyncio.sleep_ms(400)

    def display_off(self):
        self.display.display.off()

    def display_on(self):
        self.display.display.on()

    async def wait_for_mqtt_response(self, sleep=0):
        t, rsp = None, None
        await uasyncio.sleep(sleep)
        async for t, rsp in self._rsp_queue:
            break
        return rsp, t.split("/")[-1]

    # noinspection PyAsyncCall
    async def _main(self):
        uasyncio.create_task(run_neopixel_hsl(6, 0.5, 0.25))
        uasyncio.create_task(self._sht31_telem())
        uasyncio.create_task(self._sound_telem())
        uasyncio.create_task(self._mqtt_dispatch())

        # uasyncio.create_task(self.read_keyboard())

        # self.display_off()
        # self.button = Pushbutton(Pin(27, Pin.IN))
        # self.button.double_func(self.display_off)
        # self.button.long_func(self.display_on)

        app_type, _ = await uasyncio.wait_for(self.wait_for_mqtt_response(3), 5)
        print(f"App type: {app_type['shared']['app']}")

        print("Beginning App.main()")
        self._init_flag = True

        while True:
            await uasyncio.sleep_ms(100)

    def go(self):
        _thread.start_new_thread(uasyncio.run, (self._main(),))
