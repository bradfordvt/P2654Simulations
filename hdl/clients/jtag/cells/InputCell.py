"""
/**********************************************************************************
*                                                                                 *
*  This verilog file is a part of the Boundary Scan Implementation and comes in   *
*  a pack with several other files. It is fully IEEE 1149.1 compliant.            *
*  For details check www.opencores.org (pdf files, bsdl file, etc.)               *
*                                                                                 *
*  Copyright (C) 2000 Igor Mohor (igorm@opencores.org) and OPENCORES.ORG          *
*                                                                                 *
*  This program is free software; you can redistribute it and/or modify           *
*  it under the terms of the GNU General Public License as published by           *
*  the Free Software Foundation; either version 2 of the License, or              *
*  (at your option) any later version.                                            *
*                                                                                 *
*  See the file COPYING for the full details of the license.                      *
*                                                                                 *
*  OPENCORES.ORG is looking for new open source IP cores and developers that      *
*  would like to help in our mission.                                             *
*                                                                                 *
**********************************************************************************/



/**********************************************************************************
*                                                                                 *
*	  Input Cell:                                                                   *
*                                                                                 *
*	  InputPin: Value that comes from on-chip logic	and goes to pin                 *
*	  FromPreviousBSCell: Value from previous boundary scan cell                    *
*	  ToNextBSCell: Value for next boundary scan cell                               *
*	  CaptureDR, ShiftDR: TAP states                                                *
*	  TCK: Test Clock                                                               *
*                                                                                 *
**********************************************************************************/
"""
from myhdl import *


# This is not a top module
class InputCell:
    def __init__(self, InputPin, FromPreviousBSCell, CaptureDR, ShiftDR, TCK, ToNextBSCell):
        self.InputPin = InputPin
        self.FromPreviousBSCell = FromPreviousBSCell
        self.CaptureDR = CaptureDR
        self.ShiftDR = ShiftDR
        self.TCK = TCK
        self.ToNextBSCell = ToNextBSCell
        self.tms = None
        self.trst = None

    def configure_jtag(self, tdi, tck, tms, trst, tdo):
        self.FromPreviousBSCell = tdi
        self.TCK = tck
        self.tms = tms
        self.trst = trst
        self.ToNextBSCell = tdo

    @block
    def rtl(self):
        Latch = Signal(bool(0))
        SelectedInput = Signal(bool(0))

        @always_comb
        def sel_process():
            if self.CaptureDR:
                SelectedInput.next = self.InputPin
            else:
                SelectedInput.next = self.FromPreviousBSCell

        @always(self.TCK.posedge)
        def latch_logic():
            if self.CaptureDR or self.ShiftDR:
                Latch.next = SelectedInput

        @always(self.TCK.negedge)
        def to_logic():
            self.ToNextBSCell.next = Latch

        return sel_process, latch_logic, to_logic
