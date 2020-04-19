"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *

from hdl.experimental.pseudo_led import pseudo_led
from hdl.boards.i2ctest.i2cdevice import I2CDevice
from hdl.boards.spitest.spidevice import SPIDevice


class SPITest:
    def __init__(self):
        # SYSCON Signals
        self.clk_o = None
        self.rst_o = None
        # GPIO Signals
        self.i_gpio = None
        self.o_gpio = None
        # JTAG Signals
        self.tck = None
        self.tms = None
        self.trst = None
        self.tdi = None
        self.tdo = None
        # I2C Signals
        self.scl_o = None
        self.scl_i = None
        self.scl_e = None
        self.sda_o = None
        self.sda_i = None
        self.sda_e = None
        # SPI Signals
        self.sclk = None
        self.mosi = None
        self.miso = None
        self.ss = None
        # TPSP Signals
        self.tp_sck = None
        self.tp_i = None
        self.tp_o = None
        self.tp_e = None

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

    def configure_gpio(self, i_gpio, o_gpio):
        self.i_gpio = i_gpio
        self.o_gpio = o_gpio

    def configure_jtag(self, tdi, tck, tms, trst, tdo):
        self.tdi = tdi
        self.tck = tck
        self.tms = tms
        self.trst = trst
        self.tdo = tdo

    def configure_i2c(self, scl_o, scl_i, scl_e, sda_o, sda_i, sda_e):
        self.scl_o = scl_o
        self.scl_i = scl_i
        self.scl_e = scl_e
        self.sda_o = sda_o
        self.sda_i = sda_i
        self.sda_e = sda_e

    def configure_spi(self, sclk, mosi, miso, ss):
        self.sclk = sclk
        self.mosi = mosi
        self.miso = miso
        self.ss = ss

    @block
    def rtl(self):

        self.led0 = pseudo_led(self.clk, self.state0, color="WHITE")
        self.led1 = pseudo_led(self.clk, self.state1, color="RED")
        self.led2 = pseudo_led(self.clk, self.state2, color="GREEN")
        self.led3 = pseudo_led(self.clk, self.state3, color="YELLOW")
        self.led4 = pseudo_led(self.clk, self.state4, color="BLUE")
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
            # JTAG loopback
            self.tdo.next = self.tdi

        return self.led0, self.led1, self.led2, self.led3, self.led4, netlist, \
               self.i2c_device.rtl(), self.spi_device.rtl()
