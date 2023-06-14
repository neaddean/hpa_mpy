import machine

from tb_mqtt_client import get_app_type
from util import gc_collect

if machine.reset_cause() == machine.WDT_RESET:
    x = input("\033[0;31mERROR: WDT RESET DETECTED!!\033[0m")
    if x == "y":
        machine.soft_reset()

app_type = get_app_type()
if app_type == 1:
    # noinspection PyUnresolvedReferences
    import app1
gc_collect()
