buf = bytearray(256)


def nvs_get_str(nvs, key):
    sz = nvs.get_blob(key, buf)
    return buf[:sz].decode()
