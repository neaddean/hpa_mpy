# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
# import webrepl
# webrepl.start()

def do_connect():
    import network
    from esp32 import NVS

    nvs = NVS("_network")
    buf = bytearray(256)

    def nvs_get_str(key):
        sz = nvs.get_blob(key, buf)
        return buf[:sz].decode()

    ssid = nvs_get_str(b"ssid")
    key = nvs_get_str(b"wifi_key")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f'connecting to network {ssid}...')
        wlan.connect(ssid, key)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())


do_connect()
