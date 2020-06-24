"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *

from hdl.instruments.PseudoLED.PseudoLED import PseudoLED
from hdl.boards.i2ctest.i2cdevice import I2CDevice
from hdl.boards.spitest.spidevice import SPIDevice
from hdl.boards.common.AbstractBoard import AbstractBoard


class SPITest(AbstractBoard):
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
        self.i2c_device = None
        self.spi_device = None

    def configure_syscon(self, clk_o, rst_o):
        self.clk_o = clk_o
        self.rst_o = rst_o

    @block
    def rtl(self):

        self.led0 = PseudoLED("SPITest", "LED0", self.state0, color="WHITE")
        self.led1 = PseudoLED("SPITest", "LED1", self.state1, color="RED")
        self.led2 = PseudoLED("SPITest", "LED2", self.state2, color="GREEN")
        self.led3 = PseudoLED("SPITest", "LED3", self.state3, color="YELLOW")
        self.led4 = PseudoLED("SPITest", "LED4", self.state4, color="BLUE")
        self.i2c_device = I2CDevice(self.clk_o, self.rst_o)
        self.i2c_device.configure_i2c(self.scl_o, self.scl_i, self.scl_e, self.sda_o, self.sda_i, self.sda_e)
        self.spi_device = SPIDevice(self.clk_o, self.rst_o)
        self.spi_device.configure_spi(self.sclk, self.mosi, self.miso, self.ss)

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

        return self.led0.rtl(), self.led1.rtl(), self.led2.rtl(), self.led3.rtl(), self.led4.rtl(), netlist, \
               self.i2c_device.rtl(), self.spi_device.rtl()
