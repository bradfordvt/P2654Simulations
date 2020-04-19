"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import threading
from time import sleep

from hdl.buses.wishbone.wbsyscon.wbsyscon import wbsyscon
from hdl.ate.ioslave import ioslave
from hdl.buses.wishbone.wishbone_master import WishboneMaster
from hdl.buses.wishbone.wishbone_if import wishbone_if


class ATE:
    def __init__(self, board_inst):
        self.board_inst = board_inst
        # Wishbone SYSCON signals
        self.clk_o = Signal(bool(0))
        self.rst_o = Signal(bool(0))
        # Wishbone Master/Slave Signals
        self.i_wb_cyc = Signal(bool(0))
        self.i_wb_stb = Signal(bool(0))
        self.i_wb_we = Signal(bool(0))
        self.i_wb_addr = Signal(intbv(0)[32:])
        self.i_wb_data = Signal(intbv(0)[32:])
        self.o_wb_ack = Signal(bool(0))
        self.o_wb_stall = Signal(bool(0))
        self.o_wb_data = Signal(intbv(0)[32:])
        # GPIO Signals
        self.i_gpio = Signal(intbv(0)[16:])
        self.o_gpio = Signal(intbv(0)[16:])
        # JTAG Signals
        self.tck = Signal(bool(0))
        self.tms = Signal(bool(1))
        self.trst = Signal(bool(1))
        self.tdi = Signal(bool(1))
        self.tdo = Signal(bool(1))
        # I2C Signals
        self.sck_o = Signal(bool(1))
        self.sck_i = Signal(bool(1))
        self.sck_e = Signal(bool(1))
        self.sda_o = Signal(bool(1))
        self.sda_i = Signal(bool(1))
        self.sda_e = Signal(bool(1))
        # SPI Signals
        self.sclk = Signal(bool(0))
        self.mosi = Signal(bool(0))
        self.miso = Signal(bool(0))
        self.ss = Signal(bool(0))
        # TPSP Signals
        self.tp_sck = Signal(bool(0))
        self.tp_i = Signal(bool(0))
        self.tp_o = Signal(bool(0))
        self.tp_e = Signal(bool(0))

        self.wb_if = None
        self.master_inst = None
        self.wb_syscon = None
        self.slave_inst = None

        self.board_inst.configure_syscon(self.clk_o, self.rst_o)
        self.board_inst.configure_gpio(self.i_gpio, self.o_gpio)
        self.board_inst.configure_jtag(self.tdi, self.tck, self.tms, self.trst, self.tdo)
        self.board_inst.configure_i2c(self.sck_o, self.sck_i, self.sck_e, self.sda_o, self.sda_i, self.sda_e)
        self.board_inst.configure_spi(self.sclk, self.mosi, self.miso, self.ss)

    def start_simulation(self):
        x = threading.Thread(target=self.__worker)
        x.start()
        sleep(1)

    def write(self, addr, data):
        return self.master_inst.write(addr, data)

    def read(self, addr):
        return self.master_inst.read(addr)

    def terminate(self):
        return self.master_inst.terminate()

    def get_value(self):
        return self.master_inst.get_value()

    def get_error(self):
        return self.master_inst.get_error()

    def __worker(self):
        tb = self.__rtl()
        tb.config_sim(trace=True)
        tb.run_sim()

    @block
    def __rtl(self):
        self.wb_if = wishbone_if(self.clk_o, self.rst_o)
        self.master_inst = WishboneMaster("ATE", "WBM0", self.wb_if, monitor=False)
        self.wb_syscon = wbsyscon(self.clk_o, self.rst_o)
        self.slave_inst = ioslave(self.clk_o, self.rst_o,
                                  # Wishbone control
                                  # self.i_wb_cyc, self.i_wb_stb, self.i_wb_we, self.i_wb_addr, self.i_wb_data,
                                  # self.o_wb_ack, self.o_wb_stall, self.o_wb_data,
                                  self.wb_if.cyc, self.wb_if.stb, self.wb_if.we, self.wb_if.adr, self.wb_if.dat_i,
                                  self.wb_if.ack, self.wb_if.stall, self.wb_if.dat_o,
                                  # GPIO wires
                                  self.i_gpio,
                                  self.o_gpio,
                                  # JTAG wires
                                  self.tck,
                                  self.tms,
                                  self.trst,
                                  self.tdi,
                                  self.tdo,
                                  # I2C wires
                                  self.sck_o,
                                  self.sck_i,
                                  self.sck_e,
                                  self.sda_o,
                                  self.sda_i,
                                  self.sda_e,
                                  # SPI wires
                                  self.sclk,
                                  self.mosi,
                                  self.miso,
                                  self.ss,
                                  # parameters
                                  # GPIO parameters
                                  NGPO=16, NGPI=16,
                                  monitor=False)

        return self.slave_inst, self.wb_syscon, self.master_inst.rtl(), self.board_inst.rtl()

