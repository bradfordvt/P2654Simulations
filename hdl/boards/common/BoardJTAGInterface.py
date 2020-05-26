"""
Class to define and initialize a JTAG interface for a connection to a board from a host

Copyright (c) 2020 Bradford G. Van Treuren
See the licence file in the top directory
"""
from myhdl import Signal


class BoardJTAGInterface:
    def __init__(self):
        self.TCK = Signal(bool(0))
        self.TMS = Signal(bool(1))
        self.TRST = Signal(bool(1))
        self.TDO = Signal(bool(1))
        self.TDI = Signal(bool(0))
