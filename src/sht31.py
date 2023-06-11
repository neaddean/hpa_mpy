from util.crc import crc8


class SHT31:
    def __init__(self, i2c, addr=0x44):
        self.addr = 0x44
        self.i2c = i2c

    def read(self, v=False, f=False):
        """
        Nonblocking read
        :return: temperature_c, humidity_perc
        """
        try:
            assert self.i2c.writeto(self.addr, b'\x2C\x06') == 2
        except Exception as e:
            print()

        # with timeit(desc="sht31 read"):
        try:
            resp_raw = self.i2c.readfrom(self.addr, 6)
        except Exception as e:
            print(f"Error encountered during read! `{e}`")

        temperature = int.from_bytes(resp_raw[0:2], 'big')
        assert crc8(temperature) == resp_raw[2]
        humidity = int.from_bytes(resp_raw[3:5], 'big')
        assert crc8(humidity) == resp_raw[5]

        temperature_c = -45 + 175 * temperature / 0xFFFF
        humidity_perc = 100 * humidity / 0xFFFF

        if f:
            temperature_c = 1.8 * temperature_c + 32

        if v:
            print(f"temperature: {temperature_c:0.1f} C",
                  f"humidity:    {humidity_perc :0.1f} %", sep="\n")

        return temperature_c, humidity_perc

    def heater(self, en: bool):
        print(f"setting heater {en}")
        if en:
            assert self.i2c.writeto(self.addr, b'\x30\x6D') == 2
        else:
            assert self.i2c.writeto(self.addr, b'\x30\x66') == 2

    def get_status(self):
        assert self.i2c.writeto(self.addr, b'\xF3\x2D') == 2
        try:
            resp_raw = self.i2c.readfrom(self.addr, 3)
        except Exception as e:
            print(f"Error encountered during read! `{e}`")

        status = int.from_bytes(resp_raw[0:2], 'big')

        assert crc8(status) == resp_raw[2]

        status = {
            "alert": (status >> 15) & 0x1,
            "heater": (status >> 13) & 0x1,
            "hum alert": (status >> 11) & 0x1,
            "temp alert": (status >> 10) & 0x1,
            "sys reset": (status >> 4) & 0x1,
            "command status": (status >> 1) & 0x1,
            "write data checksum": (status >> 0) & 0x1,
        }

        return status
