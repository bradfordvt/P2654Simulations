"""
Class to define and initialize a Two-Pin Serial Port (TPSP) interface for a connection to a board from a host

Copyright (c) 2020 Bradford G. Van Treuren
See the licence file in the top directory
"""
from myhdl import Signal


class BoardTPSPInterface:
    def __init__(self):
        self.TP_SCK = Signal(bool(0))
        self.TP_I = Signal(bool(0))
        self.TP_O = Signal(bool(0))
        self.TP_E = Signal(bool(0))
