"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import threading

from hdl.instruments.PseudoLED.PseudoLED import PseudoLED
from hdl.boards.common.AbstractBoard import AbstractBoard


class GPIOTest(AbstractBoard):
    def __init__(self):
        super().__init__()

        self.clk = Signal(bool(0))
        self.state0 = Signal(bool(0))
        self.state1 = Signal(bool(0))
        self.state2 = Signal(bool(0))
        self.state3 = Signal(bool(0))
        self.state4 = Signal(bool(0))

        self.led0 = None
        self.led1 = None
        self.led2 = None
        self.led3 = None
        self.led4 = None

    def configure_syscon(self, clk_o, rst_o):
        self.clk_o = clk_o
        self.rst_o = rst_o


    @block
    def rtl(self):

        self.led0 = PseudoLED("GPIOTest", "LED0", self.state0, color="WHITE")
        self.led1 = PseudoLED("GPIOTest", "LED1", self.state1, color="RED")
        self.led2 = PseudoLED("GPIOTest", "LED2", self.state2, color="GREEN")
        self.led3 = PseudoLED("GPIOTest", "LED3", self.state3, color="YELLOW")
        self.led4 = PseudoLED("GPIOTest", "LED4", self.state4, color="BLUE")

        # build up the netlist for the board here
        @always_comb
        def netlist():
            # Wire the LEDs to the GPIO Signals
            self.state0.next = self.o_gpio[0]
            self.state1.next = self.o_gpio[1]
            self.state2.next = self.o_gpio[2]
            self.state3.next = self.o_gpio[3]
            self.state4.next = self.o_gpio[4]
            self.i_gpio.next = self.o_gpio
            # Wire the LED controller clock to the WB clock
            self.clk.next = self.clk_o

        return self.led0.rtl(), self.led1.rtl(), self.led2.rtl(), self.led3.rtl(), self.led4.rtl(), netlist
