"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// registerInterface.v                                          ////
////                                                              ////
//// This file is part of the i2cSlave opencores effort.
//// <http://www.opencores.org/cores//>                           ////
////                                                              ////
//// Module Description:                                          ////
//// You will need to modify this file to implement your
//// interface.
//// Add your control and status bytes/bits to module inputs and outputs,
//// and also to the I2C read and write process blocks
////                                                              ////
//// To Do:                                                       ////
////
////                                                              ////
//// Author(s):                                                   ////
//// - Steve Fielding, sfielding@base2designs.com                 ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2008 Steve Fielding and OPENCORES.ORG          ////
////                                                              ////
//// This source file may be used and distributed without         ////
//// restriction provided that this copyright statement is not    ////
//// removed from the file and that any derivative work contains  ////
//// the original copyright notice and the associated disclaimer. ////
////                                                              ////
//// This source file is free software; you can redistribute it   ////
//// and/or modify it under the terms of the GNU Lesser General   ////
//// Public License as published by the Free Software Foundation; ////
//// either version 2.1 of the License, or (at your option) any   ////
//// later version.                                               ////
////                                                              ////
//// This source is distributed in the hope that it will be       ////
//// useful, but WITHOUT ANY WARRANTY; without even the implied   ////
//// warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR      ////
//// PURPOSE. See the GNU Lesser General Public License for more  ////
//// details.                                                     ////
////                                                              ////
//// You should have received a copy of the GNU Lesser General    ////
//// Public License along with this source; if not, download it   ////
//// from <http://www.opencores.org/lgpl.shtml>                   ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
//
"""

from myhdl import *


@block
def registerInterface(clk, addr, dataIn, writeEn, dataOut,
                      myReg0, myReg1, myReg2, myReg3, myReg4, myReg5, myReg6, myReg7):
    """

    :param clk:
    :param addr:
    :param dataIn:
    :param writeEn:
    :param dataOut:
    :param myReg0:
    :param myReg1:
    :param myReg2:
    :param myReg3:
    :param myReg4:
    :param myReg5:
    :param myReg6:
    :param myReg7:
    :return:

    input clk;
    input [7:0] addr;
    input [7:0] dataIn;
    input writeEn;
    output [7:0] dataOut;
    output [7:0] myReg0;
    output [7:0] myReg1;
    output [7:0] myReg2;
    output [7:0] myReg3;
    input [7:0] myReg4;
    input [7:0] myReg5;
    input [7:0] myReg6;
    input [7:0] myReg7;

    reg [7:0] dataOut;
    reg [7:0] myReg0;
    reg [7:0] myReg1;
    reg [7:0] myReg2;
    reg [7:0] myReg3;

    """
    # --- I2C Read
    @always(clk.posedge)
    def i2cread():
        if addr == intbv(0x00):
            dataOut.next = myReg0
        elif addr == intbv(0x01):
            dataOut.next = myReg1
        elif addr == intbv(0x02):
            dataOut.next = myReg2
        elif addr == intbv(0x03):
            dataOut.next = myReg3
        elif addr == intbv(0x04):
            dataOut.next = myReg4
        elif addr == intbv(0x05):
            dataOut.next = myReg5
        elif addr == intbv(0x06):
            dataOut.next = myReg6
        elif addr == intbv(0x07):
            dataOut.next = myReg7
        else:
            dataOut.next = intbv(0x00)[8:]

    # --- I2C Write
    @always(clk.posedge)
    def i2cwrite():
        if writeEn:
            if addr == intbv(0x00):
                myReg0.next = dataIn
            elif addr == intbv(0x01):
                myReg1.next = dataIn
            elif addr == intbv(0x02):
                myReg2.next = dataIn
            elif addr == intbv(0x03):
                myReg3.next = dataIn

    return i2cread, i2cwrite
