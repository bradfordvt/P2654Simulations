"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
#########
SPI
#########
Address 0x00001C30 SPI Tx Register
Address 0x00001C31 SPI Rx Register
"""

from myhdl import *
from hdl.hosts.spihost.spi2.spi_interface import spi_if
from hdl.clients.spislave.spi_slave import spi_slave
from hdl.clients.spislave.registerInterface import registerInterface


period = 20  # clk frequency = 50 MHz


class SPIDevice:
    def __init__(self, clk_o, rst_o):
        self.clk_o = clk_o
        self.rst_o = rst_o
        # SPI Signals
        self.sclk = None
        self.mosi = None
        self.miso = None
        self.ss = None

        # SPI Client signals for attached client of interface
        self.reset_n = ResetSignal(1, 0, True)
        self.device_address = Signal(intbv(0x55)[7::0])
        self.write_address = Signal(intbv(0)[8:])
        self.write_data = Signal(intbv(0)[8:])
        self.update = Signal(bool(0))
        self.read_address = Signal(intbv(0)[8:])
        self.read_data = Signal(intbv(0)[8:])
        self.capture = Signal(bool(0))

    def configure_spi(self, sclk, mosi, miso, ss):
        self.sclk = sclk
        self.mosi = mosi
        self.miso = miso
        self.ss = ss

    @block
    def rtl(self):
        N = 32
        spi_interface_c = spi_if(self.clk_o, self.rst_o)
        myReg0 = Signal(intbv(0)[24:])
        myReg1 = Signal(intbv(0)[24:])
        myReg2 = Signal(intbv(0)[24:])
        di_req_o = Signal(bool(0))
        wren_i = Signal(bool(0))
        wr_ack_o = Signal(bool(0))
        do_valid_o = Signal(bool(0))
        do_transfer_o = Signal(bool(0))
        wren_o = Signal(bool(0))
        rx_bit_next_o = Signal(bool(0))
        state_dbg_o = Signal(intbv(0)[N:])
        sh_reg_dbg_o = Signal(intbv(0)[N:])
        di_i = Signal(intbv(0)[32:])
        do_o = Signal(intbv(0)[32:])
        regAddr = Signal(modbv(0)[8:])
        spi_slave_inst = spi_slave(self.clk_o, spi_interface_c.ss, spi_interface_c.sclk,
                                   spi_interface_c.mosi, spi_interface_c.miso,
                                   di_req_o, di_i, do_valid_o, wr_ack_o, do_valid_o, do_o,
                                   do_transfer_o, wren_o, rx_bit_next_o, state_dbg_o, sh_reg_dbg_o,
                                   N=N, CPOL=False, CPHA=False, PREFETCH=3)
        register_interface_inst = registerInterface(self.clk_o, regAddr, do_o, do_valid_o, di_i,
                                                    myReg0, myReg1, myReg2)

        @instance
        def power_on_reset_gen():
            self.reset_n.next = False
            yield delay(10)
            self.reset_n.next = True

        # build up the netlist for the device here
        @always_comb
        def netlist():
            spi_interface_c.sclk.next = self.sclk
            spi_interface_c.ss.next = self.ss
            spi_interface_c.mosi.next = self.mosi
            self.miso.next = spi_interface_c.miso

        return netlist, spi_slave_inst, power_on_reset_gen, register_interface_inst

