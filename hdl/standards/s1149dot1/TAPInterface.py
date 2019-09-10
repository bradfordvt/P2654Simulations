"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *


class TAPInterface:
    def __init__(self):
        self.Reset = Signal(bool(1))
        self.Enable = Signal(bool(0))
        self.ShiftIR = Signal(bool(0))
        self.CaptureIR = Signal(bool(0))
        self.ClockIR = Signal(bool(0))
        self.UpdateIR = Signal(bool(0))
        self.ShiftDR = Signal(bool(0))
        self.CaptureDR = Signal(bool(0))
        self.ClockDR = Signal(bool(0))
        self.UpdateDR = Signal(bool(0))
        self.UpdateDRState = Signal(bool(0))
        self.Select = Signal(bool(0))
