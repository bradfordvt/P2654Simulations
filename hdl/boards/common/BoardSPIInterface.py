"""
Class to define and initialize a SPI interface for a connection to a board from a host

Copyright (c) 2020 Bradford G. Van Treuren
See the licence file in the top directory
"""
from myhdl import Signal


class BoardSPIInterface:
    def __init__(self):
        self.SCLK = Signal(bool(0))
        self.MOSI = Signal(bool(0))
        self.MISO = Signal(bool(0))
        self.SS = Signal(bool(0))
