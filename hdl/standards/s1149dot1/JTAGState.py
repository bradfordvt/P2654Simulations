"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *


class JTAGState:
    def __init__(self):
        self.value = Signal(intbv(15, min=0, max=16))
