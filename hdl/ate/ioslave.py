"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
#########
JTAG
#########
Address 0x00001000 - 0x000013FF JTAG Vector Buffer Memory (8-bit data bus as lowest 8 bits)
Address 0x00001400 JTAG Start State Register (4-bit lowest 4 bits)
Address 0x00001401 JTAG End State Register (4-bit lowest 4 bits)
Address 0x00001402 JTAG Bit Count (16-bit lowest 16 bits)
Address 0x00001403 JTAG Control Register (bit 0: Scan start/stop: 1=start scan, 0=stop scan)
Address 0x00001404 JTAG Status Register (bit 0: 1=busy scanning, 0=done scanning)
#########
GPIO
#########
Address 0x00001800 GPIO register
"""

from myhdl import *
from hdl.buses.wishbone.wbgpio.wbgpio import wbgpio
from hdl.buses.wishbone.wbjtag.wbjtag import wbjtag


@block
def ioslave(i_clk, i_reset,
            # Wishbone control
            i_wb_cyc, i_wb_stb, i_wb_we, i_wb_addr, i_wb_data,
            o_wb_ack, o_wb_stall, o_wb_data,
            # GPIO wires
            i_gpio,
            o_gpio,
            # JTAG wires
            tck,
            tms,
            trst,
            tdi,
            tdo,
            # parameters
            # GPIO parameters
            NGPO=15, NGPI=15,
            monitor=False):
    gpio_data = Signal(intbv(0)[32:])
    jtag_data = Signal(intbv(0)[32:])
    r_wb_data = Signal(intbv(0)[32:])
    gpio_int = Signal(bool(0))
    r_wb_ack = Signal(bool(0))
    gpio_ack = Signal(bool(0))
    jtag_ack = Signal(bool(0))
    gpio_cyc = Signal(bool(0))
    jtag_cyc = Signal(bool(0))
    gpio_stb = Signal(bool(0))
    jtag_stb = Signal(bool(0))

    gpiodev = wbgpio(i_clk, i_wb_cyc, gpio_stb,
                     i_wb_we, i_wb_data, gpio_data, i_gpio, o_gpio, gpio_ack, gpio_int, NIN=NGPI, NOUT=NGPO)
    jtagdev = wbjtag(i_clk, i_reset, i_wb_cyc, jtag_stb,
                     i_wb_we, i_wb_addr, i_wb_data, jtag_data, jtag_ack,
                     tdi, tdo, tck, tms, trst, monitor=False)

    @always(i_clk.posedge)
    def comb0():
        # if i_wb_stb and (~i_wb_we):
        if i_wb_stb and not i_wb_we:
            # print("comb0: i_wb_addr = ", hex(i_wb_addr), ", ", bin(i_wb_addr))
            if i_wb_addr[32:12] == intbv(1)[20:]:  # Address is in range of IO block
                if i_wb_addr[11] == 0:  # JTAGCtrlMaster block of registers
                    r_wb_data.next = jtag_data
                elif i_wb_addr[9:] == intbv(0)[9:] and i_wb_addr[10] == 0:  # GPIO register
                    r_wb_data.next = gpio_data
                else:
                    r_wb_data.next = intbv(0)[32:]

    @always(i_clk.posedge)
    def comb1():
        gpio_cyc.next = False
        jtag_cyc.next = False
        if i_wb_addr[32:12] == intbv(1)[20:]:  # Address is in range of IO block
            if i_wb_addr[11] == 0:  # JTAGCtrlMaster block of registers
                # print("ioslave.comb1: jtag_ack = ", jtag_ack)
                r_wb_ack.next = jtag_ack
            elif i_wb_addr[9:] == intbv(0)[9:] and i_wb_addr[10] == 0:  # GPIO register
                # print("ioslave.comb1: gpio_ack = ", gpio_ack)
                r_wb_ack.next = gpio_ack

    @always(i_clk.posedge)
    def comb2():
        gpio_cyc.next = False
        jtag_cyc.next = False
        if i_wb_addr[32:12] == intbv(1)[20:]:  # Address is in range of IO block
            if i_wb_addr[11] == 0:  # JTAGCtrlMaster block of registers
                jtag_cyc.next = i_wb_cyc
            elif i_wb_addr[9:] == intbv(0)[9:] and i_wb_addr[10] == 0:  # GPIO register
                gpio_cyc.next = i_wb_cyc

    @always(i_clk.posedge)
    def logic0():
        # o_wb_ack.next = i_wb_stb and i_wb_cyc
        if i_wb_addr[32:12] == intbv(1)[20:]:
            o_wb_data.next = r_wb_data
        o_wb_stall.next = False

    @always(i_clk.posedge)
    def logic1():
        # print("ioslave.logic1: i_wb_addr[32:12] = ", i_wb_addr[32:12], ", compval = ", intbv(1)[20:])
        # print("ioslave.logic1: r_wb_ack = ", r_wb_ack)
        if i_wb_addr[32:12] == intbv(1)[20:]:
            # print("o_wb_ack.next = r_wb_ack")
            o_wb_ack.next = r_wb_ack

    @always_comb
    def comb3():
        gpio_stb.next = i_wb_stb and (i_wb_addr[32:] == intbv(0x00001800))
        jtag_stb.next = i_wb_stb and (i_wb_addr[32:] > intbv(0x00000FFF)) and (i_wb_addr[32:] < intbv(0x00001405))

    return logic0, logic1, comb3, comb0, comb1, comb2, gpiodev, jtagdev
