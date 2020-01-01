"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *


WB_ADR_WIDTH = 32
WB_BTE_WIDTH = 2
WB_CTI_WIDTH = 3
WB_DAT_WIDTH = 32
WB_TGA_WIDTH = 8
WB_TGD_WIDTH = 8
WB_TGC_WIDTH = 4
WB_SEL_WIDTH = 4


class wishbone_if:
    def __init__(self, clk, rst):
        self.rst_i = rst
        self.clk_i = clk
        self.adr = Signal(intbv(0)[WB_ADR_WIDTH:])
        self.tga = Signal(intbv(0)[WB_TGA_WIDTH:])
        self.dat_i = Signal(intbv(0)[WB_DAT_WIDTH:])
        self.tgd_i = Signal(intbv(0)[WB_TGD_WIDTH:])
        self.dat_o = Signal(intbv(0)[WB_DAT_WIDTH:])
        self.tgd_o = Signal(intbv(0)[WB_TGD_WIDTH:])
        self.we = Signal(bool(0))
        self.sel = Signal(intbv(0)[WB_SEL_WIDTH:])
        self.stb = Signal(bool(0))
        self.ack = Signal(bool(0))
        self.cyc = Signal(bool(0))
        self.err = Signal(bool(0))
        self.lock = Signal(bool(0))
        self.bte = Signal(intbv(0)[WB_BTE_WIDTH:])
        self.rty = Signal(bool(0))
        self.cti = Signal(intbv(0)[WB_CTI_WIDTH:])
        self.tgc = Signal(intbv(0)[WB_TGC_WIDTH:])
        self.stall = Signal(bool(0))
