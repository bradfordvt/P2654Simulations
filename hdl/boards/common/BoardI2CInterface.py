"""
Class to define and initialize a SPI interface for a connection to a board from a host

Copyright (c) 2020 Bradford G. Van Treuren
See the licence file in the top directory
"""
from myhdl import Signal


class BoardI2CInterface:
    def __init__(self):
        self.SCL_O = Signal(bool(1))
        self.SCL_I = Signal(bool(1))
        self.SCL_E = Signal(bool(1))
        self.SDA_O = Signal(bool(1))
        self.SDA_I = Signal(bool(1))
        self.SDA_E = Signal(bool(1))
