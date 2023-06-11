# https://forum.micropython.org/viewtopic.php?t=12837
import time

# --------------------------------------------------------
# Table based implementation

PRESET = 0xFFFF
POLYNOMIAL = 0xA001  # bit reverse of 0x8005


# create a single entry to the CRC table
def _initial(c):
    crc = c
    for j in range(8):
        if crc & 0x01:
            crc = (crc >> 1) ^ POLYNOMIAL
        else:
            crc = crc >> 1

    return crc


# Create the table
import array

_tab = array.array("H", [_initial(i) for i in range(256)])


# Checksum calculation
def crc16t(str):
    crc = PRESET
    for c in str:
        crc = (crc >> 8) ^ _tab[(crc ^ c) & 0xff]
    return crc


# Test case

print("\nCRC Table:")
for _ in range(256):
    if (_ % 8) == 0:
        print()
    print("0x%04x " % _tab[_], end="")
print()

start = time.time_ns()
data = b'\xFF\x03\x02\x15\x28\x9F\x1E'
crc = crc16t(data)
end = time.time_ns()
print("\nCRC Test result: ", hex(crc), len(data))
print(f"time: {(end - start) / 1e3} us")

