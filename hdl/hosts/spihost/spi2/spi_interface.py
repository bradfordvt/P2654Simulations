"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
Interface bus definition for SPI.
"""

from myhdl import *


class spi_if:
    def __init__(self, clk, rst):
        self.rst_i = rst
        self.clk_i = clk
        self.sclk = Signal(bool(0))
        self.mosi = Signal(bool(0))
        self.miso = Signal(bool(0))
        self.ss = Signal(bool(0))
