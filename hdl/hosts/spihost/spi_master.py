"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
Ported from: https://opencores.org/websvn/filedetails?repname=spi_verilog_master_slave&path=%2Fspi_verilog_master_slave%2Ftrunk%2Frtl%2Fspi_master.v
////  This file is part of the Ethernet IP core project                     ////
////  http://opencores.com/project,spi_verilog_master_slave                 ////
/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  SPI MODE 3
        CHANGE DATA @ NEGEDGE
        read data @posedge

 RSTB-active low asyn reset, CLK-clock, T_RB=0-rx  1-TX, mlb=0-LSB 1st 1-msb 1st
 START=1- starts data transmission cdiv 0=clk/4 1=/8   2=/16  3=/32
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
"""

from myhdl import *


def spi_master(rstb, clk, mlb,start, tdat, cdiv, din, ss, sck, dout, done, rdata,
               idle=intbv('00')[2:], send=intbv('10')[2:], finish=intbv('11')[2:]):
    cur = Signal(intbv('00')[2:])
    nxt = Signal(intbv('00')[2:])
    treg = Signal(intbv(0)[8:])
    rreg = Signal(intbv(0)[8:])
    nbit = Signal(intbv(0)[4:])
    mid = Signal(intbv(0)[5:])
    cnt = Signal(intbv(0)[5:])
    shift = Signal(bool(0))
    clr = Signal(bool(0))

    # FSM i/o
    @always_comb
    def comb0():
        nxt.next = cur
        shift.next = False
        if cur == idle:
            if start:
                if cdiv == intbv('00')[2:]:
                    mid.next = 2
                elif cdiv == intbv('01')[2:]:
                    mid.next = 4
                elif cdiv == intbv('10')[2:]:
                    mid.next = 8
                elif cdiv == intbv('11')[2:]:
                    mid.next = 16
                shift.next = True
                done.next = False
                nxt.next = send
        elif cur == send:
            ss.next = False
            if nbit != 8:
                shift.next = True
            else:
                rdata.next = rreg
                done.next = True
                nxt.next = finish
        elif cur == finish:
            shift.next = False
            ss.next = True
            clr.next = True
            nxt.next = idle
        else:
            nxt.next = finish

    # state transistion
    @always(clk.negedge, rstb.negedge)
    def logic0():
        if not rstb:
            cur.next = finish
        else:
            cur.next = nxt

    # setup falling edge (shift dout) sample rising edge (read din)
    @always(clk.negedge, clr.posedge)
    def logic1():
        if clr:
            cnt.next = False
            sck.next = True
        else:
            if shift:
                cnt.next = cnt + 1
                if cnt == mid:
                    sck.next = ~sck
                    cnt.next = 0

    # sample @ rising edge (read din)
    @always(sck.posedge, clr.posedge)
    def logic2():
        if clr:
            nbit.next = 0
            rreg.next = intbv(0xFF)[8:]
        else:
            if mlb == 0:  # LSB first, din @ msb -> right shift
                rreg.next = concat(din, rreg[8:1])
            else:  # MSB first, din@lsb -> left shift
                rreg.next = concat(rreg[7:0], din)
            nbit.next = nbit + 1

    @always(sck.negedge, clr.posedge)
    def logic3():
        if clr:
            treg.next = intbv(0xFF)[8:]
            dout.next = True
        else:
            if nbit == 0:  # load data into TREG
                if mlb == 0:  # LSB first, shift right
                    treg.next = concat(Signal(bool(1)), tdat[8:1])
                    dout.next = tdat[0]
                else:  # MSB first shift LEFT
                    treg.next = concat(tdat[7:0], bool(1))
                    dout.next = tdat[7]
            else:
                if mlb == 0:  # LSB first, shift right
                    treg.next = concat(Signal(bool(1)), treg[8:1])
                    dout.next = treg[0]
                else:  # MSB first shift LEFT
                    treg.next = concat(treg[7:0], bool(1))
                    dout.next = treg[7]

    return comb0, logic0, logic1, logic2, logic3
