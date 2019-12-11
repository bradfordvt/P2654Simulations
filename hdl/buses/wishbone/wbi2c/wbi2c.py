"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Purpose: This is the wishbone interface to the i2c_master_top
hdl.hosts.i2chost.i2c_master_top

Register Map: (3-bit address)
Address: 000 prer [low byte] (clock prescale register)
Address: 001 prer [high byte] (clock prescale register)
Address: 010 ctr (control register)
Address: 011 rxr (receive register)
Address: 100 sr (status register)
Address: 101 txr (transmit register)
Address: 110 cr (command register)
Address: 111 reserved
"""

from myhdl import *
from hdl.hosts.i2chost.i2c_master_top import i2c_master_top


@block
def wbi2c(i_clk, i_reset, i_wb_cyc, i_wb_stb, i_wb_we, i_wb_addr, i_wb_data, o_wb_data, o_wb_ack,
          sck_o, sck_i, sck_e, sda_o, sda_i, sda_e, monitor=False):
    arst_i = Signal(bool(1))
    wb_inta_o = Signal(bool(0))
    i2c_host = i2c_master_top(i_clk, i_reset, arst_i, i_wb_addr, i_wb_data, o_wb_data,
                              i_wb_we, i_wb_stb, i_wb_cyc, o_wb_ack, wb_inta_o,
                              sck_i, sck_o, sck_e, sda_i, sda_o, sda_e,
                              ARST_LVL=False)
    return i2c_host
