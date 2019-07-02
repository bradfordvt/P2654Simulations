"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *


class IJTAGInterface:
    def __init__(self):
        self.SELECT = Signal(bool(0))
        self.CAPTURE = Signal(bool(0))
        self.SHIFT = Signal(bool(0))
        self.UPDATE = Signal(bool(0))
        self.RESET = Signal(bool(0))
        self.CLOCK = Signal(bool(0))
        # self.SI = Signal(bool(0))
        # self.SO = Signal(bool(0))
