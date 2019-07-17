"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

This file is inspired by the JTAG_Ctrl_Master design as jtag_master
on opencores.org.  The myHDL has been translated from VHDL to myHDL
by Bradford G. van Treuren with additional logic and methods added
to enhance features and fix multiple driver bugs detected during
conversion to Verilog and VHDL from myHDL during the audit phase
of the conversion process.

The following header is from the original JTAG_Cntrl_Master.vhd file on
opencores.org.

--    This file is part of JTAG_Master.
--
--    JTAG_Master is free software: you can redistribute it and/or modify
--    it under the terms of the GNU General Public License as published by
--    the Free Software Foundation, either version 3 of the License, or
--    (at your option) any later version.
--
--    JTAG_Master is distributed in the hope that it will be useful,
--    but WITHOUT ANY WARRANTY; without even the implied warranty of
--    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
--    GNU General Public License for more details.
--
--    You should have received a copy of the GNU General Public License
--    along with JTAG_Master.  If not, see <http://www.gnu.org/licenses/>.


----------------------------------------------------------------------------------
-- Company:
-- Engineer:       Andreas Weschenfelder
--
-- Create Date:    07:53:01 04/29/2010
-- Design Name:
-- Module Name:    JTAG_Ctrl_Master - Behavioral
-- Project Name:
-- Target Devices:
-- Tool versions:
-- Description:
--
-- Dependencies:
--
-- Revision:
-- Revision 0.01 - File Created
-- Additional Comments:
--
----------------------------------------------------------------------------------
"""
import os
from myhdl import *
from hdl.hosts.jtaghost.bram import RAM


class JTAGCtrlMaster:
    """
    Logic to control an IEEE 1149.1 interface as the host controller to a system, board, or device.
    """
    TEST_LOGIC_RESET, RUN_TEST_IDLE, SELECT_DR, CAPTURE_DR, SHIFT_DR, EXIT1_DR, PAUSE_DR, \
    EXIT2_DR, UPDATE_DR, SELECT_IR, CAPTURE_IR, SHIFT_IR, EXIT1_IR, PAUSE_IR, EXIT2_IR, UPDATE_IR = range(16)

    # Signals for main thread
    TypeStateJTAGMaster = enum(
        'State_IDLE',
        'State_TapToStart',
        'State_Shift',
        'State_TapToEnd',
        'State_TapToEnd2',
    )

    # Signals for TMS
    TypeTMSStates = enum(
        'idle',
        'prepare_for_working',
        'working_normal1',
        'working_normal2',
        'working_normal3',
        'working_softreset1',
        'working_softreset2',
        'working_softreset3',
    )

    # Signals for TDI/TDO
    TypeShiftStates = enum(
        'idle',
        'prepare_for_working',
        'shifting1',
        'shifting2',
        'shifting3',
        'shifting4',
        'shifting5',
        # encoding="one_hot"
    )

    def __init__(self, parent, name,
                 clk,
                 reset_n,
                 # JTAG Part
                 bit_count, shift_strobe,
                 tdo, tck, tms, tdi, trst,
                 busy,
                 state_start, state_end, state_current,
                 # Ram Part
                 addr, wr, din, dout,
                 addr_width=10,  # Range 2**addr_width
                 data_width=8
                 ):
        self.parent = parent
        self.name = name
        self.clk = clk
        self.reset_n = reset_n
        self.bit_count = bit_count
        self.shift_strobe = shift_strobe
        self.tdo = tdo
        self.tck = tck
        self.tms = tms
        self.tdi = tdi
        self.trst = trst
        self.busy = busy
        self.addr = addr
        self.wr = wr
        self.din = din
        self.dout = dout
        self.addr_width = addr_width
        self.data_width = data_width
        self.read_data = Signal(intbv(0)[self.data_width:])
        self.state_start = state_start
        self.state_end = state_end
        self.state_current = state_current

        # Signals for main thread
        self.StateJTAGMaster = Signal(JTAGCtrlMaster.TypeStateJTAGMaster.State_IDLE)

        # Signals for TMS
        self.int_TMS_CurrState = Signal(intbv(JTAGCtrlMaster.TEST_LOGIC_RESET)[4:])
        self.int_TMS_StateIn = Signal(intbv(JTAGCtrlMaster.TEST_LOGIC_RESET)[4:])
        self.int_TMS_SoftResetCnt = Signal(intbv('0000'))
        self.TMSState = Signal(JTAGCtrlMaster.TypeTMSStates.idle)
        self.tms_tck = Signal(bool(1))

        # Signals for TDI/TDO
        self.shift_state = Signal(JTAGCtrlMaster.TypeShiftStates.idle)
        self.int_bit_count = Signal(intbv(0)[self.addr_width:])
        self.shift_tck = Signal(bool(1))

        # Signals for Ram
        self.BRAM_adr = Signal(intbv(0)[addr_width:])
        self.BRAM_Din = Signal(intbv(0)[data_width:])
        self.BRAM_Dout = Signal(intbv(0)[data_width:])
        self.BRAM_WR = Signal(bool(0))

        # instances of components
        self.state_current.next = self.int_TMS_CurrState

        self.JTAG_BRAM = RAM(self.clk,
                             self.reset_n,
                             self.BRAM_WR,  # Write
                             self.BRAM_adr,  # Awr
                             self.BRAM_adr,  # Ard
                             self.BRAM_Din,  # Din
                             self.BRAM_Dout,  # Dout
                             addr_width=self.addr_width,
                             data_width=self.data_width
                             )

        self.BRAM_RD = Signal(bool(0))
        self.cur_bit_count = Signal(intbv(0)[self.addr_width:])

    def toVHDL(self):
        """
        Converts the myHDL logic into VHDL
        :return:
        """
        vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
        if not os.path.exists(vhdl_dir):
            os.mkdir(vhdl_dir, mode=0o777)
        self.rtl(monitor=False).convert(hdl="VHDL", initial_values=True, directory=vhdl_dir)

    def toVerilog(self):
        """
        Converts the myHDL logic into Verilog
        :return:
        """
        verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
        if not os.path.exists(verilog_dir):
            os.mkdir(verilog_dir, mode=0o777)
        self.rtl(monitor=False).convert(hdl="Verilog", initial_values=True, directory=verilog_dir)

    def rtl(self, monitor=False):
        """
        Wrapper around the RTL logic to get a meaningful name during conversion
        :param monitor:
        :return:
        """
        return self.JTAGCtrlMaster_rtl(monitor=monitor)

    @block
    def JTAGCtrlMaster_rtl(self, monitor=False):
        """
        Logic to implement the JTAGHost Controller's JTAGTMSBlock
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """
        @always_comb
        def comb_process():
            self.state_current.next = self.int_TMS_CurrState

        @always_seq(self.clk.posedge, reset=self.reset_n)
        def trst_process():
            if self.reset_n == bool(0):
                self.trst.next = bool(0)
            else:
                self.trst.next = bool(1)

        @always_comb
        def tck_process():
            if not self.tms_tck or not self.shift_tck:
                self.tck.next = bool(0)
            else:
                self.tck.next = bool(1)

        # @always_seq(self.clk.posedge, reset=self.reset_n)
        @always_comb
        def ram_process():
            """
            BlockRAM Control
            """
            self.dout.next = self.BRAM_Dout
            if self.shift_state == JTAGCtrlMaster.TypeShiftStates.idle:
                self.BRAM_adr.next = self.addr
            else:
                self.BRAM_adr.next = self.int_bit_count[13:3]

        @always_seq(self.clk.posedge, reset=self.reset_n)
        def master_logic():
            if self.reset_n == 0:
                self.StateJTAGMaster.next = JTAGCtrlMaster.TypeStateJTAGMaster.State_IDLE
            else:
                # Main Thread
                if self.StateJTAGMaster == JTAGCtrlMaster.TypeStateJTAGMaster.State_IDLE:
                    self.busy.next = 0
                    if self.shift_strobe == 1:
                        self.busy.next = 1
                        self.int_TMS_StateIn.next = self.state_start
                        # Fix "Signal has multiple drivers: self_TMSState" error in toVerilog conversion
                        # self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.prepare_for_working
                        # Done Fix
                        self.StateJTAGMaster.next = JTAGCtrlMaster.TypeStateJTAGMaster.State_TapToStart
                    # Fix "Signal has multiple drivers: self_BRAM_Din" error in toVerilog conversion
                    # self.BRAM_WR.next = self.wr
                    # self.BRAM_Din.next = self.din
                    # Done Fix
                elif self.StateJTAGMaster == JTAGCtrlMaster.TypeStateJTAGMaster.State_TapToStart:
                    if self.TMSState == JTAGCtrlMaster.TypeTMSStates.idle:
                        self.StateJTAGMaster.next = JTAGCtrlMaster.TypeStateJTAGMaster.State_Shift
                        # Fix "Signal has multiple drivers: self_shift_state" error in toVerilog conversion
                        # self.shift_state.next = JTAGCtrlMaster.TypeShiftStates.prepare_for_working
                        # Done Fix
                elif self.StateJTAGMaster == JTAGCtrlMaster.TypeStateJTAGMaster.State_Shift:
                    if self.shift_state == JTAGCtrlMaster.TypeShiftStates.idle:
                        self.int_TMS_StateIn.next = self.state_end
                        # Fix "Signal has multiple drivers: self_TMSState" error in toVerilog conversion
                        # self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.prepare_for_working
                        # Done Fix
                        self.StateJTAGMaster.next = JTAGCtrlMaster.TypeStateJTAGMaster.State_TapToEnd
                elif self.StateJTAGMaster == JTAGCtrlMaster.TypeStateJTAGMaster.State_TapToEnd:
                    if self.TMSState == JTAGCtrlMaster.TypeTMSStates.idle:
                        self.busy.next = 0
                        self.StateJTAGMaster.next = JTAGCtrlMaster.TypeStateJTAGMaster.State_TapToEnd2
                elif self.StateJTAGMaster == JTAGCtrlMaster.TypeStateJTAGMaster.State_TapToEnd2:
                    if self.shift_strobe == 0:
                        self.StateJTAGMaster.next = JTAGCtrlMaster.TypeStateJTAGMaster.State_IDLE
                else:
                    self.StateJTAGMaster.next = JTAGCtrlMaster.TypeStateJTAGMaster.State_IDLE

        @always_seq(self.clk.posedge, reset=self.reset_n)
        def shift_logic():
            """
            Control data shifting to/from of device
            """
            if self.reset_n == 0:
                self.shift_state.next = JTAGCtrlMaster.TypeShiftStates.idle
            else:
                if self.shift_state == JTAGCtrlMaster.TypeShiftStates.idle:
                    # pass
                    # Fix "Signal has multiple drivers: self_BRAM_Din" error in toVerilog conversion
                    self.BRAM_WR.next = self.wr
                    self.BRAM_Din.next = self.din
                    # Done Fix
                    # Fix "Signal has multiple drivers: self_shift_state" error in toVerilog conversion
                    if self.StateJTAGMaster == JTAGCtrlMaster.TypeStateJTAGMaster.State_TapToStart:
                        if self.TMSState == JTAGCtrlMaster.TypeTMSStates.idle:
                            self.shift_state.next = JTAGCtrlMaster.TypeShiftStates.prepare_for_working
                    # Done Fix
                elif self.shift_state == JTAGCtrlMaster.TypeShiftStates.prepare_for_working:
                    if self.bit_count == intbv("0000000000000000"):
                        self.shift_state.next = JTAGCtrlMaster.TypeShiftStates.idle
                    else:
                        self.shift_state.next = JTAGCtrlMaster.TypeShiftStates.shifting1
                        self.int_bit_count.next = intbv("0000000000000000")
                elif self.shift_state == JTAGCtrlMaster.TypeShiftStates.shifting1:
                    # Fix "Signal has multiple drivers: self_int_TMS_CurrState" error in toVerilog conversion
                    # TMS: Last bit, set at TMS state change
                    # if self.bit_count == (self.int_bit_count + 1):
                    #     if self.int_TMS_CurrState != self.state_end:
                    #         self.tms.next = 1
                    #         self.int_TMS_CurrState.next = self.int_TMS_CurrState + 1
                    # Done Fix
                    # Push TDI
                    self.tdi.next = self.BRAM_Dout[self.int_bit_count % self.data_width]
                    self.shift_state.next = JTAGCtrlMaster.TypeShiftStates.shifting2
                elif self.shift_state == JTAGCtrlMaster.TypeShiftStates.shifting2:
                    self.shift_tck.next = 0
                    self.shift_state.next = JTAGCtrlMaster.TypeShiftStates.shifting3
                elif self.shift_state == JTAGCtrlMaster.TypeShiftStates.shifting3:
                    # Push TDO
                    self.shift_state.next = JTAGCtrlMaster.TypeShiftStates.shifting4
                    self.BRAM_Din.next = self.BRAM_Dout
                    self.BRAM_Din.next[self.int_bit_count % self.data_width] = self.tdo
                    self.BRAM_WR.next = 1
                elif self.shift_state == JTAGCtrlMaster.TypeShiftStates.shifting4:
                    self.BRAM_WR.next = 0
                    self.shift_tck.next = 1
                    if self.bit_count == (self.int_bit_count + 1):
                        self.shift_state.next = JTAGCtrlMaster.TypeShiftStates.idle
                    else:
                        self.shift_state.next = JTAGCtrlMaster.TypeShiftStates.shifting1
                        self.int_bit_count.next = self.int_bit_count + 1
                else:
                    self.shift_state.next = JTAGCtrlMaster.TypeShiftStates.idle

        @always_seq(self.clk.posedge, reset=self.reset_n)
        def tms_logic():
            """
            Control TAP state of device
            """
            if self.reset_n == bool(0):
                self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.idle
                self.int_TMS_CurrState.next = JTAGCtrlMaster.TEST_LOGIC_RESET
            else:
                if self.TMSState == JTAGCtrlMaster.TypeTMSStates.idle:
                    # pass
                    # Fix "Signal has multiple drivers: self_TMSState" error in toVerilog conversion
                    if self.shift_strobe == 1:
                        self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.prepare_for_working
                    elif self.shift_state == JTAGCtrlMaster.TypeShiftStates.idle:
                        self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.prepare_for_working
                    # Done Fix
                elif self.TMSState == JTAGCtrlMaster.TypeTMSStates.prepare_for_working:
                    if self.int_TMS_CurrState != self.int_TMS_StateIn:
                        self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.working_normal1
                    else:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.TEST_LOGIC_RESET:
                            self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.working_softreset1
                        else:
                            # already in state -> do nothing
                            self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.idle
                elif self.TMSState == JTAGCtrlMaster.TypeTMSStates.working_normal1:
                    if self.int_TMS_CurrState == JTAGCtrlMaster.TEST_LOGIC_RESET:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.TEST_LOGIC_RESET:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.TEST_LOGIC_RESET
                        else:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.RUN_TEST_IDLE
                    elif self.int_TMS_CurrState == JTAGCtrlMaster.RUN_TEST_IDLE:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.RUN_TEST_IDLE:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.RUN_TEST_IDLE
                        else:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.SELECT_DR
                    elif self.int_TMS_CurrState == JTAGCtrlMaster.SELECT_DR:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.TEST_LOGIC_RESET or \
                                self.int_TMS_StateIn == JTAGCtrlMaster.RUN_TEST_IDLE or \
                                self.int_TMS_StateIn == JTAGCtrlMaster.SELECT_IR or \
                                self.int_TMS_StateIn == JTAGCtrlMaster.CAPTURE_IR or \
                                self.int_TMS_StateIn == JTAGCtrlMaster.SHIFT_IR or \
                                self.int_TMS_StateIn == JTAGCtrlMaster.EXIT1_IR or \
                                self.int_TMS_StateIn == JTAGCtrlMaster.PAUSE_IR or \
                                self.int_TMS_StateIn == JTAGCtrlMaster.EXIT2_IR or \
                                self.int_TMS_StateIn == JTAGCtrlMaster.UPDATE_IR:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.SELECT_IR
                        else:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.CAPTURE_DR
                    elif self.int_TMS_CurrState == JTAGCtrlMaster.CAPTURE_DR:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.EXIT1_DR:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.EXIT1_DR
                        else:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.SHIFT_DR
                    elif self.int_TMS_CurrState == JTAGCtrlMaster.SHIFT_DR:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.SHIFT_DR:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.SHIFT_DR
                        # Fix "Signal has multiple drivers: self_int_TMS_CurrState" error in toVerilog conversion
                        # TMS: Last bit, set at TMS state change
                        elif (self.bit_count == (self.int_bit_count + 1)) and (
                                self.int_TMS_CurrState != self.state_end):
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.EXIT1_DR
                        # Done Fix
                        else:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.EXIT1_DR
                    elif self.int_TMS_CurrState == JTAGCtrlMaster.EXIT1_DR:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.UPDATE_DR:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.UPDATE_DR
                        else:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.PAUSE_DR
                    elif self.int_TMS_CurrState == JTAGCtrlMaster.PAUSE_DR:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.PAUSE_DR:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.PAUSE_DR
                        else:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.EXIT2_DR
                    elif self.int_TMS_CurrState == JTAGCtrlMaster.EXIT2_DR:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.SHIFT_DR:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.SHIFT_DR
                        else:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.UPDATE_DR
                    elif self.int_TMS_CurrState == JTAGCtrlMaster.UPDATE_DR:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.RUN_TEST_IDLE:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.RUN_TEST_IDLE
                        else:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.SELECT_DR
                    elif self.int_TMS_CurrState == JTAGCtrlMaster.SELECT_IR:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.TEST_LOGIC_RESET:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.TEST_LOGIC_RESET
                        else:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.CAPTURE_IR
                    elif self.int_TMS_CurrState == JTAGCtrlMaster.CAPTURE_IR:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.EXIT1_IR:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.EXIT1_IR
                        else:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.SHIFT_IR
                    elif self.int_TMS_CurrState == JTAGCtrlMaster.SHIFT_IR:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.SHIFT_IR:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.SHIFT_IR
                        # Fix "Signal has multiple drivers: self_int_TMS_CurrState" error in toVerilog conversion
                        # TMS: Last bit, set at TMS state change
                        elif (self.bit_count == (self.int_bit_count + 1)) and (
                                    self.int_TMS_CurrState != self.state_end):
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.EXIT1_IR
                        # Done Fix
                        else:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.EXIT1_IR
                    elif self.int_TMS_CurrState == JTAGCtrlMaster.EXIT1_IR:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.UPDATE_IR:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.UPDATE_IR
                        else:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.PAUSE_IR
                    elif self.int_TMS_CurrState == JTAGCtrlMaster.PAUSE_IR:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.PAUSE_IR:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.PAUSE_IR
                        else:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.EXIT2_IR
                    elif self.int_TMS_CurrState == JTAGCtrlMaster.EXIT2_IR:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.SHIFT_IR:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.SHIFT_IR
                        else:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.UPDATE_IR
                    elif self.int_TMS_CurrState == JTAGCtrlMaster.UPDATE_IR:
                        if self.int_TMS_StateIn == JTAGCtrlMaster.RUN_TEST_IDLE:
                            self.tms.next = 0
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.RUN_TEST_IDLE
                        else:
                            self.tms.next = 1
                            self.int_TMS_CurrState.next = JTAGCtrlMaster.SELECT_DR
                    else:
                        self.int_TMS_CurrState.next = JTAGCtrlMaster.TEST_LOGIC_RESET
                    self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.working_normal2
                elif self.TMSState == JTAGCtrlMaster.TypeTMSStates.working_normal2:
                    self.tms_tck.next = 0
                    self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.working_normal3
                elif self.TMSState == JTAGCtrlMaster.TypeTMSStates.working_normal3:
                    self.tms_tck.next = 1
                    if self.int_TMS_CurrState == self.int_TMS_StateIn:
                        self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.idle
                    else:
                        self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.working_normal1
                elif self.TMSState == JTAGCtrlMaster.TypeTMSStates.working_softreset1:
                    self.tms.next = 1
                    self.int_TMS_SoftResetCnt.next = intbv('0101')
                    self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.working_softreset2
                elif self.TMSState == JTAGCtrlMaster.TypeTMSStates.working_softreset2:
                    self.tms_tck.next = 0
                    self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.working_softreset3
                elif self.TMSState == JTAGCtrlMaster.TypeTMSStates.working_softreset3:
                    self.tms_tck.next = 1
                    self.int_TMS_SoftResetCnt.next = self.int_TMS_SoftResetCnt - 1
                    if self.int_TMS_SoftResetCnt > intbv('0000'):
                        self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.working_softreset2
                    else:
                        self.int_TMS_CurrState.next = JTAGCtrlMaster.TEST_LOGIC_RESET
                        self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.idle
                else:
                    self.TMSState.next = JTAGCtrlMaster.TypeTMSStates.idle

        if not monitor:
            return comb_process, trst_process, master_logic, shift_logic, tms_logic, tck_process, ram_process, \
                   self.JTAG_BRAM.RAM_rtl()
        else:
            @instance
            def Monitor_TMSState():
                print("\t\tJTAGCtrlMaster.TMSState:", self.TMSState, "Binary:", bin(self.TMSState, 4))
                while 1:
                    yield self.TMSState
                    print("\t\tJTAGCtrlMaster.TMSState:", self.TMSState, "Binary:", bin(self.TMSState, 4))

            @instance
            def Monitor_int_TMS_CurrState():
                print("\t\tJTAGCtrlMaster.int_TMS_CurrState:", self.int_TMS_CurrState, "Binary:", bin(self.int_TMS_CurrState, 4))
                while 1:
                    yield self.int_TMS_CurrState
                    print("\t\tJTAGCtrlMaster.int_TMS_CurrState:", self.int_TMS_CurrState, "Binary:", bin(self.int_TMS_CurrState, 4))

            @instance
            def Monitor_int_TMS_StateIn():
                print("\t\tJTAGCtrlMaster.int_TMS_StateIn:", self.int_TMS_StateIn, "Binary:", bin(self.int_TMS_StateIn, 4))
                while 1:
                    yield self.int_TMS_StateIn
                    print("\t\tJTAGCtrlMaster.TMSState:", self.int_TMS_StateIn, "Binary:", bin(self.int_TMS_StateIn, 4))

            @instance
            def Monitor_StateJTAGMaster():
                print("\t\tJTAGCtrlMaster.StateJTAGMaster:", self.StateJTAGMaster, "Binary:", bin(self.StateJTAGMaster, 4))
                while 1:
                    yield self.StateJTAGMaster
                    print("\t\tJTAGCtrlMaster.TMSState:", self.StateJTAGMaster, "Binary:", bin(self.StateJTAGMaster, 4))

            @instance
            def Monitor_shift_state():
                print("\t\tJTAGCtrlMaster.shift_state:", self.shift_state, "Binary:", bin(self.shift_state, 3))
                while 1:
                    yield self.shift_state
                    print("\t\tJTAGCtrlMaster.shift_state:", self.shift_state, "Binary:", bin(self.shift_state, 3))

            @instance
            def Monitor_state_current():
                print("\t\tJTAGCtrlMaster.state_current:", self.state_current, "Binary:", bin(self.state_current, 4))
                while 1:
                    yield self.state_current
                    print("\t\tJTAGCtrlMaster.state_current:", self.state_current, "Binary:", bin(self.state_current, 4))

            @instance
            def Monitor_int_bit_count():
                print("\t\tJTAGCtrlMaster.int_bit_count:", self.int_bit_count)
                while 1:
                    yield self.int_bit_count
                    print("\t\tJTAGCtrlMaster.int_bit_count:", self.int_bit_count)

            return comb_process, \
                   trst_process, master_logic, shift_logic, tms_logic, ram_process, self.JTAG_BRAM.RAM_rtl(), \
                   Monitor_TMSState, Monitor_int_bit_count, Monitor_int_TMS_CurrState, Monitor_int_TMS_StateIn, \
                   Monitor_shift_state, Monitor_state_current, Monitor_StateJTAGMaster, tck_process

    def write_vector(self, addr, data):
        """
        Non-convertable code
        This code is used to simplify writing of test benches
        :param addr: Address of memory buffer to store the next segment of the vector into (size of data_width)
        :param data: The contents to be written into the memory buffer of the master (size of data_width)
        :return:
        """
        yield self.clk.negedge
        self.addr.next = addr
        self.din.next = data
        self.wr.next = bool(1)
        yield self.clk.posedge
        yield self.clk.negedge
        self.wr.next = bool(0)
        yield self.clk.posedge
        self.addr.next = 0

    def read_vector(self, addr):
        """
        Non-convertable code
        This code is used to simplify writing of test benches
        :param addr: Address of memory buffer to fetch the next segment of the vector from (size of data_width)
        :return:
        """
        yield self.clk.negedge
        self.addr.next = addr
        self.wr.next = bool(0)
        yield self.clk.posedge
        self.read_data.next = self.dout
        yield self.clk.negedge
        yield self.clk.posedge
        self.addr.next = 0

    def get_read_data(self):
        """
        Returns the value fetched by the read_vector call
        :return:
        """
        return self.read_data

    def scan_vector(self, tdi_vector, count, tdo_vector, start, end):
        """
        Scan the vector to the TAP with the IR data and capture the response in tdo_vector
        :param tdi_vector: Array of integers for the data to be shifted out (tdi_vector[0] is first integer sent)
        :param count: number of bits to shift
        :param tdo_vector: Array of integers for the data to be captured into (tdo_vector[0] is first integer captured)
        :param start: JTAGCtrlMaster.SHIFTIR or SHIFTDR
        :param end: JTAGCtrlMaster.RUN_TEST_IDLE
        :return:
        """
        # Fill the JTAGCtrlMaster data buffer memory with tdi data
        num_full_words = int(count // self.data_width)
        remainder = count % self.data_width
        addr = intbv(0)[self.addr_width:]
        for i in range(num_full_words):
            data = intbv(tdi_vector[i])[self.data_width:]
            yield self.write_vector(addr, data)
            addr = addr + 1
        # Now write out the remaining bits that may be a partial word in size, but a full word needs to be written
        if remainder > 0:
            data = intbv(tdi_vector[num_full_words])[self.data_width:]
            yield self.write_vector(addr, data)
        # Now start the scan operation
        self.bit_count.next = intbv(count)[self.addr_width:]
        self.shift_strobe.next = bool(1)
        self.state_start.next = start
        self.state_end.next = end
        yield self.busy.posedge
        self.shift_strobe.next = bool(0)
        yield self.busy.negedge
        # Scan completed, now fetch the captured data
        addr = intbv(0)[self.addr_width:]
        for i in range(num_full_words):
            yield self.read_vector(addr)
            data = self.get_read_data()
            tdo_vector[i] = int(data)
            addr = addr + 1
        # Now read out the remaining bits that may be a partial word in size, but a full word needs to be read
        if remainder > 0:
            yield self.read_vector(addr)
            data = self.get_read_data()
            tdo_vector[num_full_words] = int(data)

    def scan_ir(self, tdi_vector, count, tdo_vector):
        """
        Scan the vector to the TAP with the IR data and capture the response in tdo_vector
        :param tdi_vector: Signal(intbv(0)[count:]) Data to be shifted out
        :param count: number of bits to shift
        :param tdo_vector: Signal(intbv(0)[count]) Data to be captured
        :return:
        """
        start = JTAGCtrlMaster.SHIFT_IR
        end = JTAGCtrlMaster.RUN_TEST_IDLE
        yield self.scan_vector(tdi_vector, count, tdo_vector, start, end)

    def scan_dr(self, tdi_vector, count, tdo_vector):
        """
        Scan the vector to the TAP with the DR data and capture the response in tdo_vector
        :param tdi_vector: Signal(intbv(0)[count:]) Data to be shifted out
        :param count: number of bits to shift
        :param tdo_vector: Signal(intbv(0)[count]) Data to be captured
        :return:
        """
        start = JTAGCtrlMaster.SHIFT_DR
        end = JTAGCtrlMaster.RUN_TEST_IDLE
        yield self.scan_vector(tdi_vector, count, tdo_vector, start, end)

    @staticmethod
    def convert():
        """
        Convert the myHDL design into VHDL and Verilog
        :return:
        """
        addr_width = 10
        data_width = 8
        clk = Signal(bool(0))
        reset_n = ResetSignal(1, active=0, async=True)
        # JTAG Part
        bit_count = Signal(intbv(0)[addr_width:])
        shift_strobe = Signal(bool(0))
        tdo = Signal(bool(0))
        tck = Signal(bool(0))
        tms = Signal(bool(0))
        tdi = Signal(bool(0))
        trst = Signal(bool(1))
        busy = Signal(bool(0))
        state_start = Signal(intbv(JTAGCtrlMaster.TEST_LOGIC_RESET)[4:])
        state_end = Signal(intbv(JTAGCtrlMaster.TEST_LOGIC_RESET)[4:])
        state_current = Signal(intbv(JTAGCtrlMaster.TEST_LOGIC_RESET)[4:])
        # Ram Part
        addr = Signal(intbv(0)[addr_width:])
        wr = Signal(bool(0))
        din = Signal(intbv(0)[data_width:])
        dout = Signal(intbv(0)[data_width:])

        jcm_inst = JTAGCtrlMaster('DEMO', 'JCM0',
                                  clk,
                                  reset_n,
                                  bit_count, shift_strobe,
                                  tdo, tck, tms, tdi, trst,
                                  busy,
                                  state_start, state_end, state_current,
                                  addr, wr, din, dout,
                                  addr_width=addr_width,
                                  data_width=data_width)

        jcm_inst.toVerilog()
        jcm_inst.toVHDL()

    @staticmethod
    @block
    def testbench(monitor=False):
        """
        Test bench interface for a quick test of the operation of the design
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """
        addr_width = 10
        data_width = 8
        clk = Signal(bool(0))
        reset_n = ResetSignal(1, active=0, async=True)
        # JTAG Part
        bit_count = Signal(intbv(0)[16:])
        shift_strobe = Signal(bool(0))
        tdo = Signal(bool(0))
        tck = Signal(bool(0))
        tms = Signal(bool(0))
        tdi = Signal(bool(0))
        trst = Signal(bool(1))
        busy = Signal(bool(0))
        state_start = Signal(intbv(JTAGCtrlMaster.TEST_LOGIC_RESET)[4:])
        state_end = Signal(intbv(JTAGCtrlMaster.TEST_LOGIC_RESET)[4:])
        state_current = Signal(intbv(JTAGCtrlMaster.TEST_LOGIC_RESET)[4:])
        # Ram Part
        addr = Signal(intbv(0)[addr_width:])
        wr = Signal(bool(0))
        din = Signal(intbv(0)[data_width:])
        dout = Signal(intbv(0)[data_width:])
        ir_tdi_vector = [0x55, 0x19]
        ir_tdo_vector = [0, 0]
        dr_tdi_vector = [0xA5, 0x66]
        dr_tdo_vector = [0, 0]
        count = 15

        jcm_inst = JTAGCtrlMaster('DEMO', 'JCM0',
                                  clk,
                                  reset_n,
                                  bit_count, shift_strobe,
                                  tdo, tck, tms, tdi, trst,
                                  busy,
                                  state_start, state_end, state_current,
                                  addr, wr, din, dout,
                                  addr_width=addr_width,
                                  data_width=data_width)

        @always(delay(10))
        def clkgen():
            clk.next = not clk

        @always_seq(clk.posedge, reset=reset_n)
        def loopback():
            tdo.next = tdi

        @instance
        def stimulus():
            """
            Scan an IR followed by a scan of a DR
            :return:
            """
            H = bool(1)
            L = bool(0)
            # Reset the instrument
            reset_n.next = bool(0)
            yield delay(2)
            reset_n.next = bool(1)
            yield delay(50)
            # Scan the IR
            yield jcm_inst.scan_ir(ir_tdi_vector, count, ir_tdo_vector)
            print("ir_tdo_vector = ", ir_tdo_vector)
            assert(ir_tdo_vector == [0x55, 0x19])  # Captured TDO value returned to ir_tdo_vector
            yield jcm_inst.scan_dr(dr_tdi_vector, count, dr_tdo_vector)
            print("dr_tdo_vector = ", dr_tdo_vector)
            assert(dr_tdo_vector == [0xA5, 0x66])  # Captured TDO value returned to dr_tdo_vector
            raise StopSimulation()

        return jcm_inst.JTAGCtrlMaster_rtl(monitor=monitor), clkgen, stimulus, loopback


if __name__ == '__main__':
    tb = JTAGCtrlMaster.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    JTAGCtrlMaster.convert()
