"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *


@block
def registerInterface(clk, addr, dataIn, writeEn, dataOut, myReg0, myReg1, myReg2):
    """

    :param clk:
    :param addr:
    :param dataIn:
    :param writeEn:
    :param dataOut:
    :param myReg0:
    :param myReg1:
    :param myReg2:
    :return:
    """
    @always_comb
    def addr_proc():
        addr.next = dataIn[32:24]

    # --- SPI Read
    @always(clk.posedge)
    def spiread():
        if addr == intbv(0x00):
            dataOut.next = concat(addr, myReg0)
        elif addr == intbv(0x01):
            dataOut.next = concat(addr, myReg1)
        elif addr == intbv(0x02):
            dataOut.next = concat(addr, myReg2)
        else:
            dataOut.next = intbv(0x00)[32:]

    # --- SPI Write
    @always(clk.posedge)
    def spiwrite():
        if writeEn:
            if addr == intbv(0x00):
                myReg0.next = dataIn[24:]
            elif addr == intbv(0x01):
                myReg1.next = dataIn[24:]
            elif addr == intbv(0x02):
                myReg2.next = dataIn[24:]

    return addr_proc, spiread, spiwrite
