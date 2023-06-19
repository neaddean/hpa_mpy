import binascii
import json
import time

import micropython
import uasyncio
from esp32 import NVS
from machine import I2C, Pin, unique_id, ADC, WDT
from uarray import array
from umqtt.simple import MQTTClient

import util
from display import Display
from led import run_neopixel_hsl
from primitives import RingbufQueue
from sht31 import SHT31
from util import atimeit
from util.nvs import nvs_get_str
from util.statistics import mean
from util.timeit import timeit


class App:
    def __init__(self):
        self.is_init = False

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

        print("create display")
        self.display = Display()
        print("display init")
        self.display.init()

        print("adc init")
        self.keyboard_adc = ADC(Pin(36, Pin.IN), atten=ADC.ATTN_11DB)
        self.sound_adc = ADC(Pin(39, Pin.IN), atten=ADC.ATTN_0DB)

        print("mqtt init")
        self.mqtt_client = self._create_mqtt_client()

        self._init_flag = False

        self._display_lines = ['' for _ in range(160 // 10)]

        print("init complete")

    async def _wdt_task(self):
        wdt = WDT(timeout=60_000)
        wdt.feed()
        async for _delta in (atimeit()):
            wdt.feed()
            # print(delta)
            await uasyncio.sleep_ms(50)

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

        mqtt_client.connect(clean_session=False)
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

    async def _sht31_task(self):
        now = time.ticks_ms()
        async for _delta in atimeit():
            try:
                temperature, humidity = self.sht31.read(v=util.verbose)

                self._text(f"temp: %.1f C" % temperature, 0)
                self._text(f"hum : %.1f %%" % humidity, 2)

                if time.ticks_diff(time.ticks_ms(), now) > 20_000:
                    self.mqtt_client.publish("v1/devices/me/telemetry",
                                             json.dumps({"temperature": temperature, "humidity": humidity}))
                    now = time.time()

            except Exception as e:
                # print(e)
                raise e
                pass
            await uasyncio.sleep_ms(100)

    @micropython.native
    async def _sound_task(self):
        window_len: int = 10
        vals = array('I', [0 for i in range(window_len)])
        old_time: int = time.ticks_ms()
        while True:
            sound = self.get_sound()
            with timeit(suppress=True):
                vals[window_len - 1] = sound

                for i in range(window_len):
                    vals[i], vals[window_len - 1] = vals[window_len - 1], vals[i]

                # if time.time() - now > 0.5:
                #     print(vals)

                if time.ticks_diff(time.ticks_ms(), old_time) > 100:
                    sound = max(vals)
                    u_sound = mean(vals)
                    self._text(f"mic : %5.0f mV" % sound, 4)
                    self._text(f"u   : %5.0f mV" % u_sound, 6)
                    if u_sound > 0.0:
                        self._text(f"mic : %5.2f dB" % util.dB(sound / 75), 8)
                        self._text(f"u   : %5.2f dB" % util.dB(u_sound / 75), 10)
                    old_time = time.ticks_ms()

            await uasyncio.sleep_ms(100 // window_len)

    async def _mqtt_task(self):
        while True:
            try:
                self.mqtt_client.check_msg()
            except Exception as e:
                print(e)
                pass
            await uasyncio.sleep_ms(50)

    def get_keyboard(self):
        return self.keyboard_adc.read_u16()

    def get_sound(self) -> float:
        return self.sound_adc.read_uv() // 1000

    async def _read_keyboard(self):
        while True:
            print(self.get_keyboard())
            print(self.get_sound())
            await uasyncio.sleep_ms(400)

    async def wait_for_mqtt_response(self, sleep=0):
        await uasyncio.sleep(sleep)
        async for t, rsp in self._rsp_queue:
            return rsp, t.split("/")[-1]

    def _text(self, line, row):
        self._display_lines[row] = line

    @micropython.native
    async def _refresh_display_task(self):
        _max_chars = 128 // 8
        display_lines = self._display_lines
        current_lines = ['' for _ in range(160 // 10)]
        while True:
            start = time.ticks_ms()
            try:
                for row, line in enumerate(display_lines):
                    current_line = current_lines[row]

                    if line == current_line:
                        continue

                    idx: int = 0
                    for idx in range(min(len(line), len(current_line))):
                        if line[idx] != current_line[idx]:
                            break

                    self.display.text(line[idx:], row * 10, col=idx * 8)
                    current_lines[row] = line

            except Exception as e:
                print(e)
                raise e
            diff = time.ticks_diff(time.ticks_ms(), start)
            if diff > 35:
                print(f"\033[0;31mWARNING: Display refresh took {diff} ms!!!\033[0m")
            await uasyncio.sleep_ms(100)

    # noinspection PyAsyncCall
    async def _main(self):
        # uasyncio.create_task(self._wdt_task())

        uasyncio.create_task(run_neopixel_hsl(6, 0.5, 0.25))
        uasyncio.create_task(self._sht31_task())
        uasyncio.create_task(self._sound_task())
        uasyncio.create_task(self._mqtt_task())
        uasyncio.create_task(self._refresh_display_task())

        # uasyncio.create_task(self.read_keyboard())

        # self.display_off()
        # self.button = Pushbutton(Pin(27, Pin.IN))
        # self.button.double_func(self.display_off)
        # self.button.long_func(self.display_on)

        self._init_flag = True
        print("Beginning App.main()")

        while True:
            sleep_time = 10_000
            threshold = 150
            old = time.ticks_ms()
            await uasyncio.sleep_ms(sleep_time)
            new = time.ticks_ms()
            diff = time.ticks_diff(new, old)
            if diff > (sleep_time + threshold):
                print(f"Ran over! {diff}")

    def go(self):
        # give time for print buffer to flush because apps run in a thread
        # time.sleep_ms(100)
        # _thread.start_new_thread(uasyncio.run, (self._main(),))

        loop = uasyncio.get_event_loop()
        # loop.set_exception_handler(_handle_exception)

        uasyncio.run(self._main())


def _handle_exception(_loop, context):
    # context["message"] will always be there; but context["exception"] may not
    print(context)
    print(context["message"])
    print(context["exception"])
    msg = context.get("exception", context["message"])
    print("Caught: {}{}".format(type(context["exception"]), msg))
    print("done")

# _thread.start_new_thread(_App().go, ())
