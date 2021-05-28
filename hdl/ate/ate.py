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
from hdl.boards.common.BoardGPIOInterface import BoardGPIOInterface
from hdl.boards.common.BoardI2CInterface import BoardI2CInterface
from hdl.boards.common.BoardJTAGInterface import BoardJTAGInterface
from hdl.boards.common.BoardSPIInterface import BoardSPIInterface
from hdl.boards.common.BoardTPSPInterface import BoardTPSPInterface


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
        # self.i_gpio = Signal(intbv(0)[16:])
        # self.o_gpio = Signal(intbv(0)[16:])
        self.gpio_if = BoardGPIOInterface()
        # JTAG Signals
        # self.tck = Signal(bool(0))
        # self.tms = Signal(bool(1))
        # self.trst = Signal(bool(1))
        # self.tdi = Signal(bool(1))
        # self.tdo = Signal(bool(1))
        # self.tck2 = Signal(bool(0))
        # self.tms2 = Signal(bool(1))
        # self.trst2 = Signal(bool(1))
        # self.tdi2 = Signal(bool(1))
        # self.tdo2 = Signal(bool(1))
        self.jtag_if = BoardJTAGInterface()
        self.jtag_if2 = BoardJTAGInterface()
        # I2C Signals
        # self.sck_o = Signal(bool(1))
        # self.sck_i = Signal(bool(1))
        # self.sck_e = Signal(bool(1))
        # self.sda_o = Signal(bool(1))
        # self.sda_i = Signal(bool(1))
        # self.sda_e = Signal(bool(1))
        self.i2c_if = BoardI2CInterface()
        # SPI Signals
        # self.sclk = Signal(bool(0))
        # self.mosi = Signal(bool(0))
        # self.miso = Signal(bool(0))
        # self.ss = Signal(bool(0))
        self.spi_if = BoardSPIInterface()
        # TPSP Signals
        # self.tp_sck = Signal(bool(0))
        # self.tp_i = Signal(bool(0))
        # self.tp_o = Signal(bool(0))
        # self.tp_e = Signal(bool(0))
        self.tp_if = BoardTPSPInterface()

        self.wb_if = None
        self.master_inst = None
        self.wb_syscon = None
        self.slave_inst = None

    def configure_syscon(self, clk, rst):
        self.clk_o = clk
        self.rst_o = rst

    def configure_gpio(self, gpio_if):
        self.gpio_if = gpio_if

    def configure_jtag(self, jtag_if):
        self.jtag_if = jtag_if

    def configure_jtag2(self, jtag_if):
        self.jtag_if2 = jtag_if

    def configure_i2c(self, i2c_if):
        self.i2c_if = i2c_if

    def configure_spi(self, spi_if):
        self.spi_if = spi_if

    def configure_tpsp(self, tp_if):
        self.tp_if = tp_if

    def start_simulation(self):
        x = threading.Thread(target=self.__worker)
        x.start()
        sleep(10)

    def sim_status(self):
        if self.master_inst is None:
            return False
        else:
            return True

    def write(self, addr, data):
        while self.master_inst is None:
            print("wb write: master task has not started yet!")
            sleep(1)
        return self.master_inst.write(addr, data)

    def read(self, addr):
        while self.master_inst is None:
            print("wb read: master task has not started yet!")
            sleep(1)
        return self.master_inst.read(addr)

    def terminate(self):
        while self.master_inst is None:
            print("wb terminate: master task has not started yet!")
            sleep(1)
        return self.master_inst.terminate()

    def get_value(self):
        while self.master_inst is None:
            print("wb get_value: master task has not started yet!")
            sleep(1)
        return self.master_inst.get_value()

    def get_error(self):
        while self.master_inst is None:
            print("wb get_error: master task has not started yet!")
            sleep(1)
        return self.master_inst.get_error()

    def reset_bus(self):
        while self.master_inst is None:
            print("wb reset_bus: master task has not started yet!")
            sleep(1)
        return self.master_inst.reset_bus()

    def __worker(self):
        tb = self.__rtl()
        tb.config_sim(trace=True)
        tb.run_sim()
        self.master_inst = None

    @block
    def __rtl(self):
        self.wb_if = wishbone_if(self.clk_o, self.rst_o)
        print("Setting self.master_inst")
        self.master_inst = WishboneMaster("ATE", "WBM0", self.wb_if, monitor=False)
        self.wb_syscon = wbsyscon(self.clk_o, self.rst_o)
        self.slave_inst = ioslave(self.clk_o, self.rst_o,
                                  # Wishbone control
                                  # self.i_wb_cyc, self.i_wb_stb, self.i_wb_we, self.i_wb_addr, self.i_wb_data,
                                  # self.o_wb_ack, self.o_wb_stall, self.o_wb_data,
                                  self.wb_if.cyc, self.wb_if.stb, self.wb_if.we, self.wb_if.adr, self.wb_if.dat_i,
                                  self.wb_if.ack, self.wb_if.stall, self.wb_if.dat_o,
                                  # GPIO wires
                                  self.gpio_if.i_gpio,
                                  self.gpio_if.o_gpio,
                                  # JTAG wires
                                  self.jtag_if.TCK,
                                  self.jtag_if.TMS,
                                  self.jtag_if.TRST,
                                  self.jtag_if.TDI,
                                  self.jtag_if.TDO,
                                  self.jtag_if2.TCK,
                                  self.jtag_if2.TMS,
                                  self.jtag_if2.TRST,
                                  self.jtag_if2.TDI,
                                  self.jtag_if2.TDO,
                                  # I2C wires
                                  self.i2c_if.SCL_O,
                                  self.i2c_if.SCL_I,
                                  self.i2c_if.SCL_E,
                                  self.i2c_if.SDA_O,
                                  self.i2c_if.SDA_I,
                                  self.i2c_if.SDA_E,
                                  # SPI wires
                                  self.spi_if.SCLK,
                                  self.spi_if.MOSI,
                                  self.spi_if.MISO,
                                  self.spi_if.SS,
                                  # parameters
                                  # GPIO parameters
                                  NGPO=16, NGPI=16,
                                  monitor=False)

        self.board_inst.configure_syscon(self.clk_o, self.rst_o)
        # self.board_inst.configure_gpio(self.i_gpio, self.o_gpio)
        # self.board_inst.configure_jtag(self.tdi, self.tck, self.tms, self.trst, self.tdo)
        # self.board_inst.configure_i2c(self.sck_o, self.sck_i, self.sck_e, self.sda_o, self.sda_i, self.sda_e)
        # self.board_inst.configure_spi(self.sclk, self.mosi, self.miso, self.ss)
        return self.slave_inst, self.wb_syscon, self.master_inst.rtl(), self.board_inst.rtl()

