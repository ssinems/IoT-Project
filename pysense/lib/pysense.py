from machine import I2C

class Pysense:
    def __init__(self, i2c=None, sda='P22', scl='P21'):
        if i2c is None:
            self.i2c = I2C(0, mode=I2C.MASTER, pins=(sda, scl))
        else:
            self.i2c = i2c
