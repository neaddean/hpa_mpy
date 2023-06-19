import machine


import micropython; micropython.alloc_emergency_exception_buf(256)


def _do_connect():
    import network
    from esp32 import NVS
    from util.nvs import nvs_get_str

    nvs = NVS("_network")

    ssid = nvs_get_str(nvs, "ssid")
    key = nvs_get_str(nvs, "wifi_key")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print()
        print(f'connecting to network {ssid}...')
        wlan.connect(ssid, key)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

# display backlight? doesn't work here
machine.Pin(12, machine.Pin.OUT).off()
# machine.freq(240_000_000)

_do_connect()
