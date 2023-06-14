from util.timeit import timeit

import micropython


@micropython.viper
def crc8_buf(data) -> int:
    # https://stackoverflow.com/questions/72556517/8-bit-crc-calcuation-in-micropython
    crc: uint = 0xFF
    ptr = ptr8(data)
    for i in range(2):
        crc ^= ptr[i]
        for j in range(8):
            crc = (crc << 1) ^ 0x31 if crc & 0x80 else crc << 1
        crc &= 0xff
    return crc


@micropython.viper
def crc8(data: uint) -> int:
    # https://stackoverflow.com/questions/72556517/8-bit-crc-calcuation-in-micropython
    crc: uint = 0xFF
    for i in range(2):
        crc ^= ((data >> 8 * (1 - i)) & 0xFF)
        for j in range(8):
            crc = (crc << 1) ^ 0x31 if crc & 0x80 else crc << 1
        crc &= 0xff
    return crc


_data = b'\xBE\xEF'

for _ in range(3):
    with timeit(unit="us", suppress=__name__ != "__main__"):
        crc = crc8_buf(_data)

for _ in range(3):
    with timeit(unit="us", suppress=__name__ != "__main__"):
        crc = crc8(0xBEEF)

if crc8(0xBEEF) != 0x92:
    print("!!! FAILED CRC CHECK !!!")
