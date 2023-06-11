# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
# import webrepl
# webrepl.start()


def do_connect():
    import network
    from esp32 import NVS
    from util.nvs import nvs_get_str

    nvs = NVS("_network")

    ssid = nvs_get_str(nvs, "ssid")
    key = nvs_get_str(nvs, "wifi_key")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f'connecting to network {ssid}...')
        wlan.connect(ssid, key)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())


do_connect()
