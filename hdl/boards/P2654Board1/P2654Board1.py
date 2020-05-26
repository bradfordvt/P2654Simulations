"""
Copyright (c) 2020 Bradford G. Van Treuren
See the licence file in the top directory
"""
from myhdl import *
from hdl.boards.common.AbstractBoard import AbstractBoard
from hdl.devices.SN74ABT8244A.SN74ABT8244A import SN74ABT8244A
# from hdl.instruments.led.led import LED
from hdl.instruments.PseudoLED.PseudoLED import PseudoLED


class P2654Board1(AbstractBoard):
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        # # SYSCON Signals
        # self.clk_o = None
        # self.rst_o = None
        # # GPIO Signals
        # self.i_gpio = None
        # self.o_gpio = None
        # # JTAG Signals
        # self.tck = None
        # self.tms = None
        # self.trst = None
        # self.tdi = None
        # self.tdo = None
        # # I2C Signals
        # self.scl_o = None
        # self.scl_i = None
        # self.scl_e = None
        # self.sda_o = None
        # self.sda_i = None
        # self.sda_e = None
        # # SPI Signals
        # self.sclk = None
        # self.mosi = None
        # self.miso = None
        # self.ss = None
        # # TPSP Signals
        # self.tp_sck = None
        # self.tp_i = None
        # self.tp_o = None
        # self.tp_e = None

        self.sn74abt8244_device = None
        self.led0_inst = None
        self.led1_inst = None
        self.led2_inst = None
        self.led3_inst = None
        self.led4_inst = None
        self.led5_inst = None
        self.led6_inst = None
        self.led7_inst = None
        self.syscon = None

    def configure_syscon(self, clk_o, rst_o):
        self.clk_o = clk_o
        self.rst_o = rst_o

    # def configure_gpio(self, i_gpio, o_gpio):
    #     self.i_gpio = i_gpio
    #     self.o_gpio = o_gpio
    #
    # def configure_jtag(self, tdi, tck, tms, trst, tdo):
    #     self.tdi = tdi
    #     self.tck = tck
    #     self.tms = tms
    #     self.trst = trst
    #     self.tdo = tdo
    #
    # def configure_i2c(self, scl_o, scl_i, scl_e, sda_o, sda_i, sda_e):
    #     self.scl_o = scl_o
    #     self.scl_i = scl_i
    #     self.scl_e = scl_e
    #     self.sda_o = sda_o
    #     self.sda_i = sda_i
    #     self.sda_e = sda_e
    #
    # def configure_spi(self, sclk, mosi, miso, ss):
    #     self.sclk = sclk
    #     self.mosi = mosi
    #     self.miso = miso
    #     self.ss = ss

    @block
    def rtl(self):
        width = 4
        Y1 = [TristateSignal(False) for _ in range(width)]
        Y2 = [TristateSignal(False) for _ in range(width)]
        A1 = [Signal(bool(0)) for _ in range(width)]
        A2 = [Signal(bool(0)) for _ in range(width)]
        oe_neg1 = Signal(bool(0))
        oe_neg2 = Signal(bool(0))
        tdo_padoe_o = Signal(bool(0))
        led0 = Signal(bool(0))
        led1 = Signal(bool(0))
        led2 = Signal(bool(0))
        led3 = Signal(bool(0))
        led4 = Signal(bool(0))
        led5 = Signal(bool(0))
        led6 = Signal(bool(0))
        led7 = Signal(bool(0))

        self.sn74abt8244_device = SN74ABT8244A("TOP", "SN74ABT8245", oe_neg1, Y1, Y2, A1, A2, oe_neg2,
                                               tdo_padoe_o, self.tdi, self.tck, self.tms, self.tdo)
        # self.sn74abt8244_device.configure_jtag(self.tdi, self.tck, self.tms, self.trst, self.tdo)
        # self.led0_inst = LED("TOP", "LED0", led0)
        # self.led1_inst = LED("TOP", "LED1", led1)
        # self.led2_inst = LED("TOP", "LED2", led2)
        # self.led3_inst = LED("TOP", "LED3", led3)
        # self.led4_inst = LED("TOP", "LED4", led4)
        # self.led5_inst = LED("TOP", "LED5", led5)
        # self.led6_inst = LED("TOP", "LED6", led6)
        # self.led7_inst = LED("TOP", "LED7", led7)
        self.led0_inst = PseudoLED("TOP", "LED0", led0, color="RED")
        self.led1_inst = PseudoLED("TOP", "LED1", led1, color="GREEN")
        self.led2_inst = PseudoLED("TOP", "LED2", led2, color="YELLOW")
        self.led3_inst = PseudoLED("TOP", "LED3", led3, color="ORANGE")
        self.led4_inst = PseudoLED("TOP", "LED4", led4, color="BLUE")
        self.led5_inst = PseudoLED("TOP", "LED5", led5, color="VIOLET")
        self.led6_inst = PseudoLED("TOP", "LED6", led6, color="INDIGO")
        self.led7_inst = PseudoLED("TOP", "LED7", led7, color="WHITE")

        self.sn74abt8244_device.configure_jtag(self.tdi, self.tck, self.tms, self.trst, self.tdo)
        print("P2654Board1: self.tdo => ", hex(id(self.tdo)))

        # build up the netlist for the board here
        @always_comb
        def netlist():
            # Wire the LED to the buffer
            if Y1[0].val is None:
                led0.next = False
                self.i_gpio.next[0] = False
            else:
                led0.next = Y1[0]
                self.i_gpio.next[0] = Y1[0]
            if Y1[1].val is None:
                led1.next = False
                self.i_gpio.next[1] = False
            else:
                led1.next = Y1[1]
                self.i_gpio.next[1] = Y1[1]
            if Y1[2].val is None:
                led2.next = False
                self.i_gpio.next[2] = False
            else:
                led2.next = Y1[2]
                self.i_gpio.next[2] = Y1[2]
            if Y1[3].val is None:
                led3.next = False
                self.i_gpio.next[3] = False
            else:
                led3.next = Y1[3]
                self.i_gpio.next[3] = Y1[3]
            if Y2[0].val is None:
                led4.next = False
                self.i_gpio.next[4] = False
            else:
                led4.next = Y2[0]
                self.i_gpio.next[4] = Y2[0]
            if Y2[1].val is None:
                led5.next = False
                self.i_gpio.next[5] = False
            else:
                led5.next = Y2[1]
                self.i_gpio.next[5] = Y2[1]
            if Y2[2].val is None:
                led6.next = False
                self.i_gpio.next[6] = False
            else:
                led6.next = Y2[2]
                self.i_gpio.next[6] = Y2[2]
            if Y2[3].val is None:
                led7.next = False
                self.i_gpio.next[7] = False
            else:
                led7.next = Y2[3]
                self.i_gpio.next[7] = Y2[3]
            A1[0].next = self.o_gpio[0]
            A1[1].next = self.o_gpio[1]
            A1[2].next = self.o_gpio[2]
            A1[3].next = self.o_gpio[3]
            A2[0].next = self.o_gpio[4]
            A2[1].next = self.o_gpio[5]
            A2[2].next = self.o_gpio[6]
            A2[3].next = self.o_gpio[7]

        return netlist, \
               self.led0_inst.rtl(), self.led1_inst.rtl(), self.led2_inst.rtl(), \
               self.led3_inst.rtl(), self.led4_inst.rtl(), self.led5_inst.rtl(), \
               self.led6_inst.rtl(), self.led7_inst.rtl(), \
               self.sn74abt8244_device.rtl()
