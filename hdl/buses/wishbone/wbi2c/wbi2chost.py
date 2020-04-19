"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Purpose: This is the wishbone interface to the i2chost
hdl.hosts.i2chost.i2chost

Register Map:
Address: 0 Data Transmit Register
Address: 1 Data Receive Register
Address: 2 Control Register
Address: 3 Status Register
"""

from myhdl import *
from hdl.hosts.i2chost.i2chost import i2chost


@block
def wbi2chost(i_clk, i_reset, i_wb_cyc, i_wb_stb, i_wb_we, i_wb_addr, i_wb_data, o_wb_data, o_wb_ack,
          scl_o, scl_i, scl_oen, sda_o, sda_i, sda_oen):
    data_wr = Signal(intbv(0)[8:])
    data_rd = Signal(intbv(0)[8:])
    control_register = Signal(intbv(0)[8:])
    status_register = Signal(intbv(0)[8:])
    tx_register_cycle = Signal(bool(0))
    rx_register_cycle = Signal(bool(0))
    addr_register_cycle = Signal(bool(0))
    reg_index_register_cycle = Signal(bool(0))
    control_register_cycle = Signal(bool(0))
    status_register_cycle = Signal(bool(0))

    i2chost_inst = i2chost(i_clk, i_reset, data_wr, data_rd, control_register, status_register,
                           scl_i, scl_o, scl_oen, sda_i, sda_o, sda_oen)

    @always(i_clk.posedge)
    def addr_decode():
        tx_register_cycle.next = False
        rx_register_cycle.next = False
        addr_register_cycle.next = False
        control_register_cycle.next = False
        status_register_cycle.next = False
        reg_index_register_cycle.next = False
        if i_wb_cyc and i_wb_stb and (i_wb_addr[10] == 1):  # Register cycle
            if i_wb_addr[10:] == intbv(0)[10:]:  # Data Transmit Register
                tx_register_cycle.next = True
            elif i_wb_addr[10:] == intbv(1)[10:]:  # Data Receive Register
                rx_register_cycle.next = True
            elif i_wb_addr[10:] == intbv(2)[10:]:  # Control Register
                control_register_cycle.next = True
            elif i_wb_addr[10:] == intbv(3)[10:]:  # Status Register
                status_register_cycle.next = True
            else:
                pass

    @always(i_clk.posedge)
    def io_cycle():
        if (tx_register_cycle == True) and i_wb_we:
            data_wr.next = i_wb_data[8:]
        if (rx_register_cycle == True) and i_wb_we:
            data_rd.next = i_wb_data[8:]
        if (control_register_cycle == True) and i_wb_we:
            control_register.next = i_wb_data[8:]
        else:
            control_register.next[0] = False  # reset execute signal
        if (status_register_cycle == True) and i_wb_we:
            status_register.next = i_wb_data[8:]

    @always(i_clk.posedge)
    def o_cycle():
        if tx_register_cycle == True:
            o_wb_data.next = concat(Signal(intbv(0)[28:]), data_wr)
        if rx_register_cycle == True:
            o_wb_data.next = concat(Signal(intbv(0)[28:]), data_rd)
        if control_register_cycle == True:
            o_wb_data.next = concat(Signal(intbv(0)[28:]), control_register)
        if status_register_cycle == True:
            o_wb_data.next = concat(Signal(intbv(0)[28:]), status_register)

    @always(i_clk.posedge)
    def ack():
        if tx_register_cycle or rx_register_cycle or control_register_cycle or status_register_cycle:
            o_wb_ack.next = True
        else:
            o_wb_ack.next = False

    return i2chost_inst, addr_decode, io_cycle, o_cycle, ack
