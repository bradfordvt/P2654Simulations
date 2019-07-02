"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *


class JTAGInterface:
    def __init__(self):
        self.TCK = Signal(bool(0))
        self.TMS = Signal(bool(1))
        self.TRST = Signal(bool(1))
        # self.TDO = Signal(bool(0))
        # self.TDI = Signal(bool(0))
