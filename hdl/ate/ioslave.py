"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
#########
TPSP
#########
Address 0x00001C10 TPSP
#########
SPI
#########
Address 0x00001C30 SPI Tx
Address 0x00001C31 SPI Rx
#########
I2C
#########
Address 0x00001C00 I2C Data Transmit Register
Address 0x00001C01 I2C Data Receive Register
Address 0x00001C02 I2C Control Register
Address 0x00001C03 I2C Status Register
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
from hdl.buses.wishbone.wbi2c.wbi2chost import wbi2chost
from hdl.buses.wishbone.wbspi.wbspi import wbspi


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
            # I2C wires
            sck_o,
            sck_i,
            sck_e,
            sda_o,
            sda_i,
            sda_e,
            # SPI wires
            sclk,
            mosi,
            miso,
            ss,
            # parameters
            # GPIO parameters
            NGPO=15, NGPI=15,
            monitor=False):
    gpio_data = Signal(intbv(0)[32:])
    jtag_data = Signal(intbv(0)[32:])
    i2c_data = Signal(intbv(0)[32:])
    spi_data = Signal(intbv(0)[32:])
    r_wb_data = Signal(intbv(0)[32:])
    gpio_int = Signal(bool(0))
    r_wb_ack = Signal(bool(0))
    gpio_ack = Signal(bool(0))
    jtag_ack = Signal(bool(0))
    i2c_ack = Signal(bool(0))
    spi_ack = Signal(bool(0))
    gpio_cyc = Signal(bool(0))
    jtag_cyc = Signal(bool(0))
    i2c_cyc = Signal(bool(0))
    spi_cyc = Signal(bool(0))
    gpio_stb = Signal(bool(0))
    jtag_stb = Signal(bool(0))
    i2c_stb = Signal(bool(0))
    spi_stb = Signal(bool(0))

    gpiodev = wbgpio(i_clk, gpio_cyc, gpio_stb,
                     i_wb_we, i_wb_data, gpio_data, i_gpio, o_gpio, gpio_ack, gpio_int, NIN=NGPI, NOUT=NGPO)
    jtagdev = wbjtag(i_clk, i_reset, jtag_cyc, jtag_stb,
                     i_wb_we, i_wb_addr, i_wb_data, jtag_data, jtag_ack,
                     tdi, tdo, tck, tms, trst, monitor=False)
    i2cdev = wbi2chost(i_clk, i_reset, i2c_cyc, i2c_stb,
                       i_wb_we, i_wb_addr, i_wb_data, i2c_data, i2c_ack,
                       sck_o, sck_i, sck_e, sda_o, sda_i, sda_e)
    spidev = wbspi(i_clk, i_reset, spi_cyc, spi_stb, i_wb_we, i_wb_addr, i_wb_data, spi_data, spi_ack,
                   ss, sclk, mosi, miso, N=32)

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
                elif i_wb_addr[10:] == intbv(0x31)[10:]:  # SPI receiver register
                    r_wb_data.next = spi_data
                elif i_wb_addr[11] == 1 and i_wb_addr[10] == 1:  # I2C register
                    r_wb_data.next = i2c_data
                else:
                    r_wb_data.next = intbv(0)[32:]

    @always(i_clk.posedge)
    def comb1():
        if i_wb_addr[32:12] == intbv(1)[20:]:  # Address is in range of IO block
            if i_wb_addr[11] == 0:  # JTAGCtrlMaster block of registers
                # print("ioslave.comb1: jtag_ack = ", jtag_ack)
                r_wb_ack.next = jtag_ack
            elif i_wb_addr[9:] == intbv(0)[9:] and i_wb_addr[10] == 0:  # GPIO register
                # print("ioslave.comb1: gpio_ack = ", gpio_ack)
                r_wb_ack.next = gpio_ack
            elif i_wb_addr[10:] == intbv(0x30)[10:]:  # SPI register
                r_wb_ack.next = spi_ack
            elif i_wb_addr[10:] == intbv(0x31)[10:]:  # SPI register
                r_wb_ack.next = spi_ack
            elif i_wb_addr[11] == 1 and i_wb_addr[10] == 1:  # I2C register
                # print("ioslave.comb1: i2c_ack = ", i2c_ack)
                r_wb_ack.next = i2c_ack

    @always(i_clk.posedge)
    def comb2():
        gpio_cyc.next = False
        jtag_cyc.next = False
        i2c_cyc.next = False
        if i_wb_addr[32:12] == intbv(1)[20:]:  # Address is in range of IO block
            if i_wb_addr[11] == 0:  # JTAGCtrlMaster block of registers
                jtag_cyc.next = i_wb_cyc
            elif i_wb_addr[9:] == intbv(0)[9:] and i_wb_addr[10] == 0:  # GPIO register
                gpio_cyc.next = i_wb_cyc
            elif i_wb_addr[10:] == intbv(0x30)[10:]:  # SPI register
                spi_cyc.next = i_wb_cyc
            elif i_wb_addr[10:] == intbv(0x31)[10:]:  # SPI register
                spi_cyc.next = i_wb_cyc
            elif i_wb_addr[11] == 1 and i_wb_addr[10] == 1:  # I2C register
                i2c_cyc.next = i_wb_cyc

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
        i2c_stb.next = i_wb_stb and (i_wb_addr[32:] > intbv(0x00001BFF)) and (i_wb_addr[32:] < intbv(0x00001C05))
        spi_stb.next = i_wb_stb and (i_wb_addr[32:] > intbv(0x00001C2F)) and (i_wb_addr[32:] < intbv(0x00001C32))

    return logic0, logic1, comb3, comb0, comb1, comb2, gpiodev, jtagdev, i2cdev, spidev
