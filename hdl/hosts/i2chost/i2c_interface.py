"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
Interface bus definition for I2C.
"""

from myhdl import *


class i2c_if:
    def __init__(self, clk, rst):
        self.rst_i = rst
        self.clk_i = clk
        self.scl_i = Signal(bool(0))
        self.scl_o = Signal(bool(0))
        self.scl_e = Signal(bool(0))
        self.sda_i = Signal(bool(0))
        self.sda_o = Signal(bool(0))
        self.sda_e = Signal(bool(0))
