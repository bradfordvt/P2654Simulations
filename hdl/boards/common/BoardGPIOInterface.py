"""
Class to define and initialize a GPIO interface for a connection to a board from a host

Copyright (c) 2020 Bradford G. Van Treuren
See the licence file in the top directory
"""
from myhdl import Signal, intbv


class BoardGPIOInterface:
    def __init__(self):
        self.i_gpio = Signal(intbv(0)[16:])
        self.o_gpio = Signal(intbv(0)[16:])
