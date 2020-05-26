"""
//////////////////////////////////////////////////////////////////////
////                                                              ////
////  tap_top.v                                                   ////
////                                                              ////
////                                                              ////
////  This file is part of the JTAG Test Access Port (TAP)        ////
////  http://www.opencores.org/projects/jtag/                     ////
////                                                              ////
////  Author(s):                                                  ////
////       Igor Mohor (igorm@opencores.org)                       ////
////                                                              ////
////                                                              ////
////  All additional information is avaliable in the README.txt   ////
////  file.                                                       ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2000 - 2003 Authors                            ////
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
//// PURPOSE.  See the GNU Lesser General Public License for more ////
//// details.                                                     ////
////                                                              ////
//// You should have received a copy of the GNU Lesser General    ////
//// Public License along with this source; if not, download it   ////
//// from http://www.opencores.org/lgpl.shtml                     ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
//
// CVS Revision History
//
// $Log: not supported by cvs2svn $
// Revision 1.5  2004/01/18 09:27:39  simons
// Blocking non blocking assignmenst fixed.
//
// Revision 1.4  2004/01/17 17:37:44  mohor
// capture_dr_o added to ports.
//
// Revision 1.3  2004/01/14 13:50:56  mohor
// 5 consecutive TMS=1 causes reset of TAP.
//
// Revision 1.2  2004/01/08 10:29:44  mohor
// Control signals for tdo_pad_o mux are changed to negedge.
//
// Revision 1.1  2003/12/23 14:52:14  mohor
// Directory structure changed. New version of TAP.
//
// Revision 1.10  2003/10/23 18:08:01  mohor
// MBIST chain connection fixed.
//
// Revision 1.9  2003/10/23 16:17:02  mohor
// CRC logic changed.
//
// Revision 1.8  2003/10/21 09:48:31  simons
// Mbist support added.
//
// Revision 1.7  2002/11/06 14:30:10  mohor
// Trst active high. Inverted on higher layer.
//
// Revision 1.6  2002/04/22 12:55:56  mohor
// tdo_padoen_o changed to tdo_padoe_o. Signal is active high.
//
// Revision 1.5  2002/03/26 14:23:38  mohor
// Signal tdo_padoe_o changed back to tdo_padoen_o.
//
// Revision 1.4  2002/03/25 13:16:15  mohor
// tdo_padoen_o changed to tdo_padoe_o. Signal was always active high, just
// not named correctly.
//
// Revision 1.3  2002/03/12 14:30:05  mohor
// Few outputs for boundary scan chain added.
//
// Revision 1.2  2002/03/12 10:31:53  mohor
// tap_top and dbg_top modules are put into two separate modules. tap_top
// contains only tap state machine and related logic. dbg_top contains all
// logic necessery for debugging.
//
// Revision 1.1  2002/03/08 15:28:16  mohor
// Structure changed. Hooks for jtag chain added.
//
//
//
//
"""

# synopsys translate_off
# from timescale import *
# synopsys translate_on
from .tap_defines import *
from myhdl import *


# Top module
class tap_top:
    def __init__(self,
                 # JTAG pads
                 tms_pad_i,  # JTAG test mode select pad
                 tck_pad_i,  # JTAG test clock pad
                 trst_pad_i,  # JTAG test reset pad
                 tdi_pad_i,  # JTAG test data input pad
                 tdo_pad_o,  # JTAG test data output pad
                 tdo_padoe_o,  # Output enable for JTAG test data output pad

                 # TAP states
                 shift_dr_o,
                 pause_dr_o,
                 update_dr_o,
                 capture_dr_o,

                 # Select signals for boundary scan or mbist
                 extest_select_o,
                 sample_preload_select_o,
                 mbist_select_o,
                 debug_select_o,

                 # TDO signal that is connected to TDI of sub-modules.
                 tdo_o,

                 # TDI signals from sub-modules
                 debug_tdi_i,  # from debug module
                 bs_chain_tdi_i,  # from Boundary Scan Chain
                 mbist_tdi_i  # from Mbist Chain
                 ):
        self.tms_pad_i = tms_pad_i
        self.tck_pad_i = tck_pad_i
        self.trst_pad_i = trst_pad_i
        self.tdi_pad_i = tdi_pad_i
        self.tdo_pad_o = tdo_pad_o
        self.tdo_padoe_o = tdo_padoe_o
        self.shift_dr_o = shift_dr_o
        self.pause_dr_o = pause_dr_o
        self.update_dr_o = update_dr_o
        self.capture_dr_o = capture_dr_o
        self.extest_select_o = extest_select_o
        self.sample_preload_select_o = sample_preload_select_o
        self.mbist_select_o = mbist_select_o
        self.debug_select_o = debug_select_o
        self.tdo_o = tdo_o
        self.debug_tdi_i = debug_tdi_i
        self.bs_chain_tdi_i = bs_chain_tdi_i
        self.mbist_tdi_i = mbist_tdi_i

    def configure_jtag(self, tdi, tck, tms, trst, tdo):
        self.tdi_pad_i = tdi
        self.tck_pad_i = tck
        self.tms_pad_i = tms
        self.trst_pad_i = trst
        self.tdo_pad_o = tdo

    @block
    def rtl(self):
        # Registers
        test_logic_reset = Signal(bool(1))
        run_test_idle = Signal(bool(0))
        select_dr_scan = Signal(bool(0))
        capture_dr = Signal(bool(0))
        shift_dr = Signal(bool(0))
        exit1_dr = Signal(bool(0))
        pause_dr = Signal(bool(0))
        exit2_dr = Signal(bool(0))
        update_dr = Signal(bool(0))
        select_ir_scan = Signal(bool(0))
        capture_ir = Signal(bool(0))
        shift_ir = Signal(bool(0))
        shift_ir_neg = Signal(bool(0))
        exit1_ir = Signal(bool(0))
        pause_ir = Signal(bool(0))
        exit2_ir = Signal(bool(0))
        update_ir = Signal(bool(0))
        extest_select = Signal(bool(0))
        sample_preload_select = Signal(bool(0))
        idcode_select = Signal(bool(0))
        mbist_select = Signal(bool(0))
        debug_select = Signal(bool(0))
        bypass_select = Signal(bool(0))
        # tdo_pad_o = Signal(bool(0))
        # tdo_padoe_o = Signal(bool(0))
        tms_q1 = Signal(bool(0))
        tms_q2 = Signal(bool(0))
        tms_q3 = Signal(bool(0))
        tms_q4 = Signal(bool(0))
        tms_reset = Signal(bool(0))
        print("tap_top: self.tdo_pad_o => ", hex(id(self.tdo_pad_o)))

        @always_comb
        def clogic():
            self.tdo_o.next = self.tdi_pad_i
            self.shift_dr_o.next = shift_dr
            self.pause_dr_o.next = pause_dr
            self.update_dr_o.next = update_dr
            self.capture_dr_o.next = capture_dr

            self.extest_select_o.next = extest_select
            self.sample_preload_select_o.next = sample_preload_select
            self.mbist_select_o.next = mbist_select
            self.debug_select_o.next = debug_select

        @always(self.tck_pad_i.posedge)
        def tms_logic():
          tms_q1.next = self.tms_pad_i
          tms_q2.next = tms_q1
          tms_q3.next = tms_q2
          tms_q4.next = tms_q3

        @always_comb
        def tms_process():
            tms_reset.next = tms_q1 and tms_q2 and tms_q3 and tms_q4 and self.tms_pad_i    # 5 consecutive TMS=1 causes reset

        """ 
        /**********************************************************************************
        *                                                                                 *
        *   TAP State Machine: Fully JTAG compliant                                       *
        *                                                                                 *
        **********************************************************************************/
        """

        # test_logic_reset state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def tlr_logic():
            if self.trst_pad_i:
                test_logic_reset.next = True
            elif tms_reset:
                test_logic_reset.next = True
            else:
                if self.tms_pad_i and (test_logic_reset or select_ir_scan):
                    test_logic_reset.next = True
                else:
                    test_logic_reset.next = False

        # run_test_idle state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def rti_logic():
            if self.trst_pad_i:
                run_test_idle.next = False
            elif tms_reset:
                run_test_idle.next = False
            else:
                if not self.tms_pad_i and (test_logic_reset or run_test_idle or update_dr or update_ir):
                    run_test_idle.next = True
                else:
                    run_test_idle.next = False

        # select_dr_scan state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def sedr_logic():
            if self.trst_pad_i:
                select_dr_scan.next = False
            elif tms_reset:
                select_dr_scan.next = False
            else:
                if self.tms_pad_i and (run_test_idle or update_dr or update_ir):
                    select_dr_scan.next = True
                else:
                    select_dr_scan.next = False

        # capture_dr state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def cdr_logic():
            if self.trst_pad_i:
                capture_dr.next = False
            elif tms_reset:
                capture_dr.next = False
            else:
                if not self.tms_pad_i and select_dr_scan:
                    capture_dr.next = True
                else:
                    capture_dr.next = False

        # shift_dr state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def shdr_logic():
            if self.trst_pad_i:
                shift_dr.next = False
            elif tms_reset:
                shift_dr.next = False
            else:
                if not self.tms_pad_i and (capture_dr or shift_dr or exit2_dr):
                    shift_dr.next = True
                else:
                    shift_dr.next = False

        # exit1_dr state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def e1dr_logic():
            if self.trst_pad_i:
                exit1_dr.next = False
            elif tms_reset:
                exit1_dr.next = False
            else:
                if self.tms_pad_i and (capture_dr or shift_dr):
                    exit1_dr.next = True
                else:
                    exit1_dr.next = False

        # pause_dr state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def pdr_logic():
            if self.trst_pad_i:
                pause_dr.next = False
            elif tms_reset:
                pause_dr.next = False
            else:
                if not self.tms_pad_i and (exit1_dr or pause_dr):
                    pause_dr.next = True
                else:
                    pause_dr.next = False

        # exit2_dr state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def e2dr_logic():
            if self.trst_pad_i:
                exit2_dr.next = False
            elif tms_reset:
                exit2_dr.next = False
            else:
                if self.tms_pad_i and pause_dr:
                    exit2_dr.next = True
                else:
                    exit2_dr.next = False

        # update_dr state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def udr_logic():
            if self.trst_pad_i:
                update_dr.next = False
            elif tms_reset:
                update_dr.next = False
            else:
                if self.tms_pad_i and (exit1_dr or exit2_dr):
                    update_dr.next = True
                else:
                    update_dr.next = False

        # select_ir_scan state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def seir_logic():
            if self.trst_pad_i:
                select_ir_scan.next = False
            elif tms_reset:
                select_ir_scan.next = False
            else:
                if self.tms_pad_i and select_dr_scan:
                    select_ir_scan.next = True
                else:
                    select_ir_scan.next = False

        # capture_ir state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def cir_logic():
            if self.trst_pad_i:
                capture_ir.next = False
            elif tms_reset:
                capture_ir.next = False
            else:
                if not self.tms_pad_i and select_ir_scan:
                    capture_ir.next = True
                else:
                    capture_ir.next = False

        # shift_ir state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def shir_logic():
            if self.trst_pad_i:
                shift_ir.next = False
            elif tms_reset:
                shift_ir.next = False
            else:
                if not self.tms_pad_i and (capture_ir or shift_ir or exit2_ir):
                    shift_ir.next = True
                else:
                    shift_ir.next = False

        # exit1_ir state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def e1ir_logic():
            if self.trst_pad_i:
                exit1_ir.next = False
            elif tms_reset:
                exit1_ir.next = False
            else:
                if self.tms_pad_i and (capture_ir or shift_ir):
                    exit1_ir.next = True
                else:
                    exit1_ir.next = False

        # pause_ir state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def pir_logic():
            if self.trst_pad_i:
                pause_ir.next = False
            elif tms_reset:
                pause_ir.next = False
            else:
                if not self.tms_pad_i and (exit1_ir or pause_ir):
                    pause_ir.next = True
                else:
                    pause_ir.next = False

        # exit2_ir state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def e2ir_logic():
            if self.trst_pad_i:
                exit2_ir.next = False
            elif tms_reset:
                exit2_ir.next = False
            else:
                if self.tms_pad_i and pause_ir:
                    exit2_ir.next = True
                else:
                    exit2_ir.next = False

        # update_ir state
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def uir_logic():
            if self.trst_pad_i:
                update_ir.next = False
            elif tms_reset:
                update_ir.next = False
            else:
                if self.tms_pad_i and (exit1_ir or exit2_ir):
                    update_ir.next = True
                else:
                    update_ir.next = False

        """
        /**********************************************************************************
        *                                                                                 *
        *   End: TAP State Machine                                                        *
        *                                                                                 *
        **********************************************************************************/
        """

        """
        /**********************************************************************************
        *                                                                                 *
        *   jtag_ir:  JTAG Instruction Register                                           *
        *                                                                                 *
        **********************************************************************************/
        """
        jtag_ir = Signal(intbv('1'*IR_LENGTH)[IR_LENGTH:])  # Instruction register
        latched_jtag_ir = Signal(intbv('1'*IR_LENGTH)[IR_LENGTH:])
        latched_jtag_ir_neg = Signal(intbv(0)[IR_LENGTH:])
        instruction_tdo = Signal(bool(0))

        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def jtag_ir_logic():
            if self.trst_pad_i:
                jtag_ir.next = intbv('1'*IR_LENGTH)[IR_LENGTH:]
            elif capture_ir:
                jtag_ir.next = intbv('00000101')  # This value is fixed for easier fault detection
            elif shift_ir:
                jtag_ir.next = concat(self.tdi_pad_i, jtag_ir[IR_LENGTH:1])

        @always(self.tck_pad_i.negedge)
        def ir_tdo_logic():
            instruction_tdo.next = jtag_ir[0]
        """
        /**********************************************************************************
        *                                                                                 *
        *   End: jtag_ir                                                                  *
        *                                                                                 *
        **********************************************************************************/
        """

        """
        /**********************************************************************************
        *                                                                                 *
        *   idcode logic                                                                  *
        *                                                                                 *
        **********************************************************************************/
        """
        idcode_reg = Signal(intbv(0)[32:])
        idcode_tdo = Signal(bool(0))

        @always(self.tck_pad_i.posedge)
        def idcode_reg_logic():
            if idcode_select and shift_dr:
                idcode_reg.next = concat(self.tdi_pad_i, idcode_reg[32:1])
            else:
                idcode_reg.next = IDCODE_VALUE

        @always(self.tck_pad_i.negedge)
        def idcode_tdo_logic():
            idcode_tdo.next = idcode_reg[0]
        """
        /**********************************************************************************
        *                                                                                 *
        *   End: idcode logic                                                             *
        *                                                                                 *
        **********************************************************************************/
        """

        """
        /**********************************************************************************
        *                                                                                 *
        *   Bypass logic                                                                  *
        *                                                                                 *
        **********************************************************************************/
        """
        bypassed_tdo = Signal(bool(0))
        bypass_reg = Signal(bool(0))

        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def byp_logic():
            if self.trst_pad_i:
                bypass_reg.next = False
            elif shift_dr:
                bypass_reg.next = self.tdi_pad_i

        @always(self.tck_pad_i.negedge)
        def byp_tdo_logic():
            bypassed_tdo.next = bypass_reg
        """
        /**********************************************************************************
        *                                                                                 *
        *   End: Bypass logic                                                             *
        *                                                                                 *
        **********************************************************************************/
        """

        """
        /**********************************************************************************
        *                                                                                 *
        *   Activating Instructions                                                       *
        *                                                                                 *
        **********************************************************************************/
        """
        # Updating jtag_ir (Instruction Register)
        @always(self.tck_pad_i.posedge, self.trst_pad_i.posedge)
        def ljtag_ir_logic():
            if self.trst_pad_i:
                latched_jtag_ir.next = IDCODE   # IDCODE selected after reset
            elif tms_reset:
                latched_jtag_ir.next = IDCODE   # IDCODE selected after reset
            elif update_ir:
                latched_jtag_ir.next = jtag_ir

        """
        /**********************************************************************************
        *                                                                                 *
        *   End: Activating Instructions                                                  *
        *                                                                                 *
        **********************************************************************************/
        """

        # Updating jtag_ir (Instruction Register)
        @always_comb
        def latched_ir_logic():
            extest_select.next = False
            sample_preload_select.next = False
            idcode_select.next = False
            mbist_select.next = False
            debug_select.next = False
            bypass_select.next = False

            # synthesis parallel_case
            if latched_jtag_ir == EXTEST:
                extest_select.next = True  # External test
            elif latched_jtag_ir == SAMPLE_PRELOAD:
                sample_preload_select.next = True  # Sample preload
            elif latched_jtag_ir == IDCODE:
                idcode_select.next = True  # ID Code
            elif latched_jtag_ir == MBIST:
                mbist_select.next = True  # Mbist test
            elif latched_jtag_ir == DEBUG:
                debug_select.next = True  # Debug
            elif latched_jtag_ir == BYPASS:
                bypass_select.next = True  # BYPASS
            else:
                bypass_select.next = True  # BYPASS

        """
        /**********************************************************************************
        *                                                                                 *
        *   Multiplexing TDO data                                                         *
        *                                                                                 *
        **********************************************************************************/
        """
        @always_comb
        def tdo_process():
            if shift_ir_neg:
                self.tdo_pad_o.next = instruction_tdo
            else:
                # synthesis parallel_case
                if latched_jtag_ir_neg == IDCODE:
                    self.tdo_pad_o.next = idcode_tdo  # Reading ID code
                elif latched_jtag_ir_neg == DEBUG:
                    self.tdo_pad_o.next = self.debug_tdi_i  # Debug
                elif latched_jtag_ir_neg == SAMPLE_PRELOAD:
                    self.tdo_pad_o.next = self.bs_chain_tdi_i  # Sampling/Preloading
                elif latched_jtag_ir_neg == EXTEST:
                    self.tdo_pad_o.next = self.bs_chain_tdi_i  # External test
                elif latched_jtag_ir_neg == MBIST:
                    self.tdo_pad_o.next = self.mbist_tdi_i  # Mbist test
                else:
                    self.tdo_pad_o.next = bypassed_tdo  # BYPASS instruction

        # Tristate control for tdo_pad_o pin
        @instance
        def tdo_oe_logic():
            while True:
                yield self.tck_pad_i.negedge
                yield delay(1)
                self.tdo_padoe_o.next = shift_ir or shift_dr or (pause_dr and debug_select)
        """
        /**********************************************************************************
        *                                                                                 *
        *   End: Multiplexing TDO data                                                    *
        *                                                                                 *
        **********************************************************************************/
        """

        # @always(tck_pad_i.negedge)
        @instance
        def shift_ir_neg_logic():
            while True:
                yield self.tck_pad_i.negedge
                yield delay(1)
                shift_ir_neg.next = shift_ir
                latched_jtag_ir_neg.next = latched_jtag_ir

        return clogic, tms_logic, tms_process, tlr_logic, rti_logic, sedr_logic, cdr_logic, shdr_logic, \
               e1dr_logic, pdr_logic, e2dr_logic, udr_logic, seir_logic, cir_logic, shir_logic, \
               e1ir_logic, pir_logic, e2ir_logic, uir_logic, jtag_ir_logic, ir_tdo_logic, idcode_reg_logic, \
               idcode_tdo_logic, byp_logic, byp_tdo_logic, ljtag_ir_logic, latched_ir_logic, tdo_process, \
               tdo_oe_logic, shift_ir_neg_logic
