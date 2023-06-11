from esp32 import NVS

nvs = NVS("_network")

nvs.set_blob("ssid", b"5G Hotspot")
nvs.set_blob("wifi_key", b"579-parker-street")

nvs.commit()
