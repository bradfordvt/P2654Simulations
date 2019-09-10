"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *


class wsp:
    """
    This class implements the Wrapper Serial Port (WSP) interface of IEEE Std 1500 standard.
    """
    def __init__(self):
        self.AUXCKn = Signal(bool(0))
        self.WRCK = Signal(bool(0))
        self.WRSTN = Signal(bool(1))
        self.TransferDR = Signal(bool(0))
        self.UpdateWR = Signal(bool(0))
        self.ShiftWR = Signal(bool(0))
        self.CaptureWR = Signal(bool(0))
        self.SelectWIR = Signal(bool(0))
        # Do not add the serial in and out to this interface as these get daisy chained and not bussed.
        # self.WSI = Signal(bool(0))
        # self.WSO = Signal(bool(0))
