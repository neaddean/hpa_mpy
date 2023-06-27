import binascii
import json
import time

import micropython
import uasyncio
from esp32 import NVS
from machine import I2C, Pin, unique_id, ADC, WDT
from uarray import array
from ucollections import deque
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

        self.UID = binascii.hexlify(unique_id())
        print(f"initing app for UID {self.UID} ...")

        self.last_received_rpc_id = None
        self._rsp_queue = RingbufQueue([0 for _ in range(10)])

        # # noinspection PyArgumentList
        # i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=400_000, timeout=500_000)
        # # reset i2c devices
        # i2c.writeto(0x00, b'\x06')
        #
        # self.sht31 = SHT31(i2c)
        #
        # assert self.sht31.addr in i2c.scan()
        #
        # self.sht31.read(True)

        print("adc init")
        # self.keyboard_adc = ADC(Pin(36, Pin.IN), atten=ADC.ATTN_11DB)

        print("mqtt init")
        self.mqtt_client = self._create_mqtt_client()

        self._init_flag = False

        self._telem_queue = deque((None, None), 16)

        print("init complete")

    @staticmethod
    async def _wdt_task():
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

    async def _mqtt_task(self):
        while True:
            try:
                self.mqtt_client.check_msg()
            except Exception as e:
                print(e)
                pass
            await uasyncio.sleep_ms(50)

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
                print(e)
                # raise e
                pass
            await uasyncio.sleep_ms(100)

    async def wait_for_mqtt_response(self, sleep=0):
        await uasyncio.sleep(sleep)
        async for t, rsp in self._rsp_queue:
            return rsp, t.split("/")[-1]

    async def _main(self):
        # uasyncio.create_task(self._wdt_task())

        uasyncio.create_task(run_neopixel_hsl(6, 0.5, 0.25))
        # uasyncio.create_task(self._sht31_task())
        uasyncio.create_task(self._mqtt_task())

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
    # https://github.com/micropython/micropython/pull/5796
    # context["message"] will always be there; but context["exception"] may not
    print(context)
    print(context["message"])
    print(context["exception"])
    msg = context.get("exception", context["message"])
    print("Caught: {}{}".format(type(context["exception"]), msg))
    print("done")

# _thread.start_new_thread(_App().go, ())
