import math
import time

class SI7006A20:
    def __init__(self, pysense=None):
        self.i2c = pysense.i2c
        self.addr = 0x40

    def temperature(self):
        self.i2c.writeto(self.addr, b'\xF3')
        time.sleep(0.5)
        data = self.i2c.readfrom(self.addr, 2)
        raw_temp = (data[0] << 8) + data[1]
        temp = ((175.72 * raw_temp) / 65536) - 46.85
        return temp

    def humidity(self):
        self.i2c.writeto(self.addr, b'\xF5')
        time.sleep(0.5)
        data = self.i2c.readfrom(self.addr, 2)
        raw_hum = (data[0] << 8) + data[1]
        hum = ((125 * raw_hum) / 65536) - 6
        return hum
