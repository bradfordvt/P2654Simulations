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
*	  Output Cell:                                                                  *
*                                                                                 *
*	  FromCore: Value that comes from on-chip logic	and goes to pin                 *
*	  FromPreviousBSCell: Value from previous boundary scan cell                    *
*	  ToNextBSCell: Value for next boundary scan cell                               *
*	  CaptureDR, ShiftDR, UpdateDR: TAP states                                      *
*	  extest: Instruction Register Command                                          *
*	  TCK: Test Clock                                                               *
*	  TristatedPin: Signal from core is connected to this output pin via BS         *
*	  FromOutputEnable: This pin comes from core or ControlCell                     *
*                                                                                 *
*	  Signal that is connected to TristatedPin comes from core or BS chain.         *
*	  Tristate control is generated in core or BS chain (ControlCell).              *
*                                                                                 *
**********************************************************************************/
"""
from myhdl import *


# This is not a top module
class OutputCell:
    def __init__(self, FromCore, FromPreviousBSCell, CaptureDR, ShiftDR, UpdateDR, extest,
                TCK, ToNextBSCell, FromOutputEnable, OutPad, EnablePad):
        self.FromCore = FromCore
        self.FromPreviousBSCell = FromPreviousBSCell
        self.CaptureDR = CaptureDR
        self.ShiftDR = ShiftDR
        self.UpdateDR = UpdateDR
        self.extest = extest
        self.TCK = TCK
        self.ToNextBSCell = ToNextBSCell
        self.FromOutputEnable = FromOutputEnable
        self.OutPad = OutPad
        self.EnablePad = EnablePad
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
        ShiftedControl = Signal(bool(0))
        SelectedInput = Signal(bool(0))

        @always_comb
        def sel_process():
            if self.CaptureDR:
                SelectedInput.next = self.FromCore
            else:
                SelectedInput.next = self.FromPreviousBSCell

        @always(self.TCK.posedge)
        def latch_logic():
            if self.CaptureDR or self.ShiftDR:
                Latch.next = SelectedInput

        @always(self.TCK.negedge)
        def to_logic():
            self.ToNextBSCell.next = Latch

        @always(self.TCK.negedge)
        def update_logic():
            if self.UpdateDR:
                ShiftedControl.next = self.ToNextBSCell

        MuxedSignal = Signal(bool(0))

        @always_comb
        def mux_process1():
            if self.extest:
                MuxedSignal.next = ShiftedControl
            else:
                MuxedSignal.next = self.FromCore

        @always_comb
        def mux_process2():
            if self.FromOutputEnable:
                self.OutPad.next = MuxedSignal
                self.EnablePad.next = True
            else:
                self.OutPad.next = False
                self.EnablePad.next = False

        return sel_process, latch_logic, to_logic, update_logic, mux_process1, mux_process2
