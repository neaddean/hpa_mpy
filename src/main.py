import _thread

import machine
import time
import uasyncio
import app1
from tb_mqtt_client import get_app_type
from util import gc_collect

uasyncio.new_event_loop()  # Clear retained state

if machine.reset_cause() == machine.WDT_RESET:
    # x = input("\033[0;31mERROR: WDT RESET DETECTED!!\033[0m")
    # if x == "y":
    #     machine.soft_reset()
    print("\033[0;31mERROR: WDT RESET DETECTED!!\033[0m")
    time.sleep_ms("1_000")

app_type = get_app_type()

if app_type == 1:
    app = app1.App()
    _thread.start_new_thread(app.go, ())
    # app.wait_for_ready()

gc_collect()
