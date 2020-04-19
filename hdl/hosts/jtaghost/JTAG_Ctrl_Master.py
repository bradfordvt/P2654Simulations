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
from hdl.hosts.jtaghost.bram import RAM, RAMInterface
from hdl.standards.s1149dot1.JTAGInterface import JTAGInterface

period = 20  # clk frequency = 50 MHz


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


class JTAGCtrlMasterInterface:
    def __init__(self, clk, reset_n, addr_width=10, data_width=8):
        # self.clk = Signal(bool(0))
        # self.reset_n = ResetSignal(1, 0, True)
        self.clk = clk
        self.reset_n = reset_n
        # JTAG Part
        self.bit_count = Signal(intbv(0)[16:])
        self.shift_strobe = Signal(bool(0))
        self.tdo = Signal(bool(0))
        self.tdi = Signal(bool(0))
        self.jtag_interface = JTAGInterface()
        self.busy = Signal(bool(0))
        self.state_start = Signal(intbv(TEST_LOGIC_RESET)[4:])
        self.state_end = Signal(intbv(TEST_LOGIC_RESET)[4:])
        self.state_current = Signal(intbv(TEST_LOGIC_RESET)[4:])
        # Ram Part
        self.addr = Signal(intbv(0)[addr_width:])
        self.wr = Signal(bool(0))
        self.din = Signal(intbv(0)[data_width:])
        self.dout = Signal(intbv(0)[data_width:])
        self.read_data = Signal(intbv(0)[data_width:])
        self.addr_width = addr_width
        self.data_width = data_width


@block
def JTAGCtrlMaster(parent, name,
                   control_interface,
                   # clk,
                   # reset_n,
                   # JTAG Part
                   # bit_count, shift_strobe,
                   # tdo, tck, tms, tdi, trst,
                   # busy,
                   # state_start, state_end, state_current,
                   # Ram Part
                   # addr, wr, din, dout,
                   # addr_width=10,  # Range 2**addr_width
                   # data_width=8,
                   monitor=False
                   ):
    """

    :param parent:
    :param name:
    :param clk:
    :param reset_n:
    :param bit_count:
    :param shift_strobe:
    :param tdo:
    :param tck:
    :param tms:
    :param tdi:
    :param trst:
    :param busy:
    :param state_start:
    :param state_end:
    :param state_current:
    :param mem_interface:
    :param monitor:
    :return:
    """
    # read_data = Signal(intbv(0)[mem_interface.data_width:])

    # Signals for main thread
    StateJTAGMaster = Signal(TypeStateJTAGMaster.State_IDLE)

    # Signals for TMS
    int_TMS_CurrState = Signal(intbv(TEST_LOGIC_RESET)[4:])
    int_TMS_StateIn = Signal(intbv(TEST_LOGIC_RESET)[4:])
    int_TMS_SoftResetCnt = Signal(intbv('0000'))
    TMSState = Signal(TypeTMSStates.idle)
    tms_tck = Signal(bool(1))

    # Signals for TDI/TDO
    shift_state = Signal(TypeShiftStates.idle)
    int_bit_count = Signal(intbv(0)[control_interface.addr_width:])
    shift_tck = Signal(bool(1))

    # Signals for Ram
    ram_interface = RAMInterface(addr_width=control_interface.addr_width, data_width=control_interface.data_width)
    BRAM_adr = Signal(intbv(0)[control_interface.addr_width:])
    # BRAM_Din = Signal(intbv(0)[data_width:])
    # BRAM_Dout = Signal(intbv(0)[data_width:])
    # BRAM_WR = Signal(bool(0))

    # instances of components
    control_interface.state_current.next = int_TMS_CurrState

    # JTAG_BRAM = RAM(clk,
    #                 reset_n,
    #                 BRAM_WR,  # Write
    #                 BRAM_adr,  # Awr
    #                 BRAM_adr,  # Ard
    #                 BRAM_Din,  # Din
    #                 BRAM_Dout,  # Dout
    #                 addr_width=addr_width,
    #                 data_width=data_width
    #                 )
    JTAG_BRAM = RAM(ram_interface)

    BRAM_RD = Signal(bool(0))
    cur_bit_count = Signal(intbv(0)[control_interface.addr_width:])

    @always_comb
    def ram_addr():
        ram_interface.Ard.next = BRAM_adr
        ram_interface.Awr.next = BRAM_adr
        ram_interface.clk.next = control_interface.clk
        ram_interface.reset_n.next = control_interface.reset_n

    @always_comb
    def comb_process():
        control_interface.state_current.next = int_TMS_CurrState

    @always_seq(control_interface.clk.posedge, reset=control_interface.reset_n)
    def trst_process():
        if control_interface.reset_n == bool(0):
            control_interface.jtag_interface.TRST.next = False
        else:
            control_interface.jtag_interface.TRST.next = True

    @always_comb
    def tck_process():
        if not tms_tck or not shift_tck:
            control_interface.jtag_interface.TCK.next = False
        else:
            control_interface.jtag_interface.TCK.next = True

    @always_comb
    def ram_process():
        """
        BlockRAM Control
        """
        control_interface.dout.next = ram_interface.Dout
        if shift_state == TypeShiftStates.idle:
            BRAM_adr.next = control_interface.addr
        else:
            BRAM_adr.next = int_bit_count[13:3]

    @always_seq(control_interface.clk.posedge, reset=control_interface.reset_n)
    def master_logic():
        if control_interface.reset_n == 0:
            StateJTAGMaster.next = TypeStateJTAGMaster.State_IDLE
        else:
            # Main Thread
            if StateJTAGMaster == TypeStateJTAGMaster.State_IDLE:
                control_interface.busy.next = False
                if control_interface.shift_strobe:
                    control_interface.busy.next = True
                    int_TMS_StateIn.next = control_interface.state_start
                    # Fix "Signal has multiple drivers: self_TMSState" error in toVerilog conversion
                    # TMSState.next = TypeTMSStates.prepare_for_working
                    # Done Fix
                    StateJTAGMaster.next = TypeStateJTAGMaster.State_TapToStart
                # Fix "Signal has multiple drivers: self_BRAM_Din" error in toVerilog conversion
                # BRAM_WR.next = wr
                # BRAM_Din.next = din
                # Done Fix
            elif StateJTAGMaster == TypeStateJTAGMaster.State_TapToStart:
                if TMSState == TypeTMSStates.idle:
                    StateJTAGMaster.next = TypeStateJTAGMaster.State_Shift
                    # Fix "Signal has multiple drivers: self_shift_state" error in toVerilog conversion
                    # shift_state.next = TypeShiftStates.prepare_for_working
                    # Done Fix
            elif StateJTAGMaster == TypeStateJTAGMaster.State_Shift:
                if shift_state == TypeShiftStates.idle:
                    int_TMS_StateIn.next = control_interface.state_end
                    # Fix "Signal has multiple drivers: self_TMSState" error in toVerilog conversion
                    # TMSState.next = TypeTMSStates.prepare_for_working
                    # Done Fix
                    StateJTAGMaster.next = TypeStateJTAGMaster.State_TapToEnd
            elif StateJTAGMaster == TypeStateJTAGMaster.State_TapToEnd:
                if TMSState == TypeTMSStates.idle:
                    control_interface.busy.next = False
                    StateJTAGMaster.next = TypeStateJTAGMaster.State_TapToEnd2
            elif StateJTAGMaster == TypeStateJTAGMaster.State_TapToEnd2:
                if not control_interface.shift_strobe:
                    StateJTAGMaster.next = TypeStateJTAGMaster.State_IDLE
            else:
                StateJTAGMaster.next = TypeStateJTAGMaster.State_IDLE

    @always_seq(control_interface.clk.posedge, reset=control_interface.reset_n)
    def shift_logic():
        """
        Control data shifting to/from of device
        """
        if not control_interface.reset_n:
            shift_state.next = TypeShiftStates.idle
        else:
            if shift_state == TypeShiftStates.idle:
                # pass
                # Fix "Signal has multiple drivers: self_BRAM_Din" error in toVerilog conversion
                ram_interface.Write.next = control_interface.wr
                ram_interface.Din.next = control_interface.din
                # Done Fix
                # Fix "Signal has multiple drivers: self_shift_state" error in toVerilog conversion
                if StateJTAGMaster == TypeStateJTAGMaster.State_TapToStart:
                    if TMSState == TypeTMSStates.idle:
                        shift_state.next = TypeShiftStates.prepare_for_working
                # Done Fix
            elif shift_state == TypeShiftStates.prepare_for_working:
                if control_interface.bit_count == intbv("0000000000000000"):
                    shift_state.next = TypeShiftStates.idle
                else:
                    shift_state.next = TypeShiftStates.shifting1
                    int_bit_count.next = intbv("0000000000000000")
            elif shift_state == TypeShiftStates.shifting1:
                # Fix "Signal has multiple drivers: self_int_TMS_CurrState" error in toVerilog conversion
                # TMS: Last bit, set at TMS state change
                # if bit_count == (int_bit_count + 1):
                #     if int_TMS_CurrState != state_end:
                #         tms.next = 1
                #         int_TMS_CurrState.next = int_TMS_CurrState + 1
                # Done Fix
                # Push TDI
                control_interface.tdi.next = ram_interface.Dout[int_bit_count % control_interface.data_width]
                shift_state.next = TypeShiftStates.shifting2
            elif shift_state == TypeShiftStates.shifting2:
                shift_tck.next = False
                shift_state.next = TypeShiftStates.shifting3
            elif shift_state == TypeShiftStates.shifting3:
                # Push TDO
                shift_state.next = TypeShiftStates.shifting4
                ram_interface.Din.next = ram_interface.Dout
                ram_interface.Din.next[int_bit_count % control_interface.data_width] = control_interface.tdo
                ram_interface.Write.next = True
            elif shift_state == TypeShiftStates.shifting4:
                ram_interface.Write.next = False
                shift_tck.next = True
                if control_interface.bit_count == (int_bit_count + 1):
                    shift_state.next = TypeShiftStates.idle
                else:
                    shift_state.next = TypeShiftStates.shifting1
                    int_bit_count.next = int_bit_count + 1
            else:
                shift_state.next = TypeShiftStates.idle

    @always_seq(control_interface.clk.posedge, reset=control_interface.reset_n)
    def tms_logic():
        """
        Control TAP state of device
        """
        if not control_interface.reset_n:
            TMSState.next = TypeTMSStates.idle
            int_TMS_CurrState.next = TEST_LOGIC_RESET
        else:
            if TMSState == TypeTMSStates.idle:
                # pass
                # Fix "Signal has multiple drivers: self_TMSState" error in toVerilog conversion
                if control_interface.shift_strobe:
                    TMSState.next = TypeTMSStates.prepare_for_working
                elif shift_state == TypeShiftStates.idle:
                    TMSState.next = TypeTMSStates.prepare_for_working
                # Done Fix
            elif TMSState == TypeTMSStates.prepare_for_working:
                if int_TMS_CurrState != int_TMS_StateIn:
                    TMSState.next = TypeTMSStates.working_normal1
                else:
                    if int_TMS_StateIn == TEST_LOGIC_RESET:
                        TMSState.next = TypeTMSStates.working_softreset1
                    else:
                        # already in state -> do nothing
                        TMSState.next = TypeTMSStates.idle
            elif TMSState == TypeTMSStates.working_normal1:
                if int_TMS_CurrState == TEST_LOGIC_RESET:
                    if int_TMS_StateIn == TEST_LOGIC_RESET:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = TEST_LOGIC_RESET
                    else:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = RUN_TEST_IDLE
                elif int_TMS_CurrState == RUN_TEST_IDLE:
                    if int_TMS_StateIn == RUN_TEST_IDLE:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = RUN_TEST_IDLE
                    else:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = SELECT_DR
                elif int_TMS_CurrState == SELECT_DR:
                    if int_TMS_StateIn == TEST_LOGIC_RESET or \
                            int_TMS_StateIn == RUN_TEST_IDLE or \
                            int_TMS_StateIn == SELECT_IR or \
                            int_TMS_StateIn == CAPTURE_IR or \
                            int_TMS_StateIn == SHIFT_IR or \
                            int_TMS_StateIn == EXIT1_IR or \
                            int_TMS_StateIn == PAUSE_IR or \
                            int_TMS_StateIn == EXIT2_IR or \
                            int_TMS_StateIn == UPDATE_IR:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = SELECT_IR
                    else:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = CAPTURE_DR
                elif int_TMS_CurrState == CAPTURE_DR:
                    if int_TMS_StateIn == EXIT1_DR:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = EXIT1_DR
                    else:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = SHIFT_DR
                elif int_TMS_CurrState == SHIFT_DR:
                    if int_TMS_StateIn == SHIFT_DR:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = SHIFT_DR
                    # Fix "Signal has multiple drivers: self_int_TMS_CurrState" error in toVerilog conversion
                    # TMS: Last bit, set at TMS state change
                    elif (control_interface.bit_count == (int_bit_count + 1)) and (
                            int_TMS_CurrState != control_interface.state_end):
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = EXIT1_DR
                    # Done Fix
                    else:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = EXIT1_DR
                elif int_TMS_CurrState == EXIT1_DR:
                    if int_TMS_StateIn == UPDATE_DR:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = UPDATE_DR
                    else:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = PAUSE_DR
                elif int_TMS_CurrState == PAUSE_DR:
                    if int_TMS_StateIn == PAUSE_DR:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = PAUSE_DR
                    else:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = EXIT2_DR
                elif int_TMS_CurrState == EXIT2_DR:
                    if int_TMS_StateIn == SHIFT_DR:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = SHIFT_DR
                    else:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = UPDATE_DR
                elif int_TMS_CurrState == UPDATE_DR:
                    if int_TMS_StateIn == RUN_TEST_IDLE:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = RUN_TEST_IDLE
                    else:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = SELECT_DR
                elif int_TMS_CurrState == SELECT_IR:
                    if int_TMS_StateIn == TEST_LOGIC_RESET:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = TEST_LOGIC_RESET
                    else:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = CAPTURE_IR
                elif int_TMS_CurrState == CAPTURE_IR:
                    if int_TMS_StateIn == EXIT1_IR:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = EXIT1_IR
                    else:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = SHIFT_IR
                elif int_TMS_CurrState == SHIFT_IR:
                    if int_TMS_StateIn == SHIFT_IR:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = SHIFT_IR
                    # Fix "Signal has multiple drivers: self_int_TMS_CurrState" error in toVerilog conversion
                    # TMS: Last bit, set at TMS state change
                    elif (control_interface.bit_count == (int_bit_count + 1)) and (
                                int_TMS_CurrState != control_interface.state_end):
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = EXIT1_IR
                    # Done Fix
                    else:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = EXIT1_IR
                elif int_TMS_CurrState == EXIT1_IR:
                    if int_TMS_StateIn == UPDATE_IR:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = UPDATE_IR
                    else:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = PAUSE_IR
                elif int_TMS_CurrState == PAUSE_IR:
                    if int_TMS_StateIn == PAUSE_IR:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = PAUSE_IR
                    else:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = EXIT2_IR
                elif int_TMS_CurrState == EXIT2_IR:
                    if int_TMS_StateIn == SHIFT_IR:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = SHIFT_IR
                    else:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = UPDATE_IR
                elif int_TMS_CurrState == UPDATE_IR:
                    if int_TMS_StateIn == RUN_TEST_IDLE:
                        control_interface.jtag_interface.TMS.next = False
                        int_TMS_CurrState.next = RUN_TEST_IDLE
                    else:
                        control_interface.jtag_interface.TMS.next = True
                        int_TMS_CurrState.next = SELECT_DR
                else:
                    int_TMS_CurrState.next = TEST_LOGIC_RESET
                TMSState.next = TypeTMSStates.working_normal2
            elif TMSState == TypeTMSStates.working_normal2:
                tms_tck.next = False
                TMSState.next = TypeTMSStates.working_normal3
            elif TMSState == TypeTMSStates.working_normal3:
                tms_tck.next = True
                if int_TMS_CurrState == int_TMS_StateIn:
                    TMSState.next = TypeTMSStates.idle
                else:
                    TMSState.next = TypeTMSStates.working_normal1
            elif TMSState == TypeTMSStates.working_softreset1:
                control_interface.jtag_interface.TMS.next = True
                int_TMS_SoftResetCnt.next = intbv('0101')
                TMSState.next = TypeTMSStates.working_softreset2
            elif TMSState == TypeTMSStates.working_softreset2:
                tms_tck.next = False
                TMSState.next = TypeTMSStates.working_softreset3
            elif TMSState == TypeTMSStates.working_softreset3:
                tms_tck.next = True
                int_TMS_SoftResetCnt.next = int_TMS_SoftResetCnt - 1
                if int_TMS_SoftResetCnt > intbv('0000'):
                    TMSState.next = TypeTMSStates.working_softreset2
                else:
                    int_TMS_CurrState.next = TEST_LOGIC_RESET
                    TMSState.next = TypeTMSStates.idle
            else:
                TMSState.next = TypeTMSStates.idle

    if not monitor:
        return comb_process, trst_process, master_logic, shift_logic, tms_logic, tck_process, ram_process, ram_addr, \
               JTAG_BRAM
    else:
        @instance
        def Monitor_TMSState():
            print("\t\tTMSState:", TMSState, "Binary:", bin(TMSState, 4))
            while 1:
                yield TMSState
                print("\t\tTMSState:", TMSState, "Binary:", bin(TMSState, 4))

        @instance
        def Monitor_int_TMS_CurrState():
            print("\t\tint_TMS_CurrState:", int_TMS_CurrState, "Binary:", bin(int_TMS_CurrState, 4))
            while 1:
                yield int_TMS_CurrState
                print("\t\tint_TMS_CurrState:", int_TMS_CurrState, "Binary:", bin(int_TMS_CurrState, 4))

        @instance
        def Monitor_int_TMS_StateIn():
            print("\t\tint_TMS_StateIn:", int_TMS_StateIn, "Binary:", bin(int_TMS_StateIn, 4))
            while 1:
                yield int_TMS_StateIn
                print("\t\tTMSState:", int_TMS_StateIn, "Binary:", bin(int_TMS_StateIn, 4))

        @instance
        def Monitor_StateJTAGMaster():
            print("\t\tStateJTAGMaster:", StateJTAGMaster, "Binary:", bin(StateJTAGMaster, 4))
            while 1:
                yield StateJTAGMaster
                print("\t\tTMSState:", StateJTAGMaster, "Binary:", bin(StateJTAGMaster, 4))

        @instance
        def Monitor_shift_state():
            print("\t\tshift_state:", shift_state, "Binary:", bin(shift_state, 3))
            while 1:
                yield shift_state
                print("\t\tshift_state:", shift_state, "Binary:", bin(shift_state, 3))

        @instance
        def Monitor_state_current():
            print("\t\tstate_current:", control_interface.state_current, "Binary:", bin(control_interface.state_current, 4))
            while 1:
                yield control_interface.state_current
                print("\t\tstate_current:", control_interface.state_current, "Binary:", bin(control_interface.state_current, 4))

        @instance
        def Monitor_int_bit_count():
            print("\t\tint_bit_count:", int_bit_count)
            while 1:
                yield int_bit_count
                print("\t\tint_bit_count:", int_bit_count)

        return comb_process, \
            trst_process, master_logic, shift_logic, tms_logic, ram_process, ram_addr, JTAG_BRAM, \
            Monitor_TMSState, Monitor_int_bit_count, Monitor_int_TMS_CurrState, Monitor_int_TMS_StateIn, \
            Monitor_shift_state, Monitor_state_current, Monitor_StateJTAGMaster, tck_process


def write_vector(clk, waddr, din, wr, addr, data):
    """
    Non-convertable code
    This code is used to simplify writing of test benches
    :param control_interface: Interface to this device
    :param addr: Address of memory buffer to store the next segment of the vector into (size of data_width)
    :param data: The contents to be written into the memory buffer of the master (size of data_width)
    :return:
    """
    yield clk.negedge
    waddr.next = addr
    din.next = data
    wr.next = bool(1)
    yield clk.posedge
    yield clk.negedge
    wr.next = bool(0)
    yield clk.posedge
    waddr.next = 0


def read_vector(clk, raddr, wr, read_data, dout, addr):
    """
    Non-convertable code
    This code is used to simplify writing of test benches
    :param addr: Address of memory buffer to fetch the next segment of the vector from (size of data_width)
    :return:
    """
    yield clk.negedge
    raddr.next = addr
    wr.next = bool(0)
    yield clk.posedge
    read_data.next = dout
    yield clk.negedge
    yield clk.posedge
    raddr.next = 0


def get_read_data(read_data):
    """
    Returns the value fetched by the read_vector call
    :return:
    """
    return read_data


def scan_vector(clk, waddr, raddr, wr, din, dout, read_data, bit_count, shift_strobe, state_start, state_end, busy,
                tdi_vector, count, tdo_vector, start, end, addr_width=10, data_width=8):
    """
    Scan the vector to the TAP with the IR data and capture the response in tdo_vector
    :param tdi_vector: Array of integers for the data to be shifted out (tdi_vector[0] is first integer sent)
    :param count: number of bits to shift
    :param tdo_vector: Array of integers for the data to be captured into (tdo_vector[0] is first integer captured)
    :param start: SHIFTIR or SHIFTDR
    :param end: RUN_TEST_IDLE
    :return:
    """
    # Fill the JTAGCtrlMaster data buffer memory with tdi data
    num_full_words = int(count // data_width)
    remainder = count % data_width
    addr = intbv(0)[addr_width:]
    for i in range(num_full_words):
        data = intbv(tdi_vector[i])[data_width:]
        yield write_vector(clk, waddr, din, wr, addr, data)
        addr = addr + 1
    # Now write out the remaining bits that may be a partial word in size, but a full word needs to be written
    if remainder > 0:
        data = intbv(tdi_vector[num_full_words])[data_width:]
        yield write_vector(clk, waddr, din, wr, addr, data)
    # Now start the scan operation
    bit_count.next = intbv(count)[addr_width:]
    shift_strobe.next = bool(1)
    state_start.next = start
    state_end.next = end
    yield busy.posedge
    shift_strobe.next = bool(0)
    yield busy.negedge
    # Scan completed, now fetch the captured data
    addr = intbv(0)[addr_width:]
    for i in range(num_full_words):
        yield read_vector(clk, raddr, wr, read_data, dout, addr)
        data = get_read_data(read_data)
        tdo_vector[i] = int(data)
        addr = addr + 1
    # Now read out the remaining bits that may be a partial word in size, but a full word needs to be read
    if remainder > 0:
        yield read_vector(clk, raddr, wr, read_data, dout, addr)
        data = get_read_data(read_data)
        tdo_vector[num_full_words] = int(data)


def scan_ir(clk, waddr, raddr, wr, din, dout, read_data, bit_count, shift_strobe, state_start, state_end, busy,
            tdi_vector, count, tdo_vector, addr_width=10, data_width=8):
    """
    Scan the vector to the TAP with the IR data and capture the response in tdo_vector
    :param tdi_vector: Signal(intbv(0)[count:]) Data to be shifted out
    :param count: number of bits to shift
    :param tdo_vector: Signal(intbv(0)[count]) Data to be captured
    :return:
    """
    start = SHIFT_IR
    end = RUN_TEST_IDLE
    yield scan_vector(clk, waddr, raddr, wr, din, dout, read_data, bit_count, shift_strobe, state_start,
                      state_end, busy,
                      tdi_vector, count, tdo_vector, start, end,
                      addr_width=addr_width, data_width=data_width)


def scan_dr(clk, waddr, raddr, wr, din, dout, read_data, bit_count, shift_strobe, state_start, state_end, busy,
            tdi_vector, count, tdo_vector, addr_width=10, data_width=8):
    """
    Scan the vector to the TAP with the DR data and capture the response in tdo_vector
    :param tdi_vector: Signal(intbv(0)[count:]) Data to be shifted out
    :param count: number of bits to shift
    :param tdo_vector: Signal(intbv(0)[count]) Data to be captured
    :return:
    """
    start = SHIFT_DR
    end = RUN_TEST_IDLE
    yield scan_vector(clk, waddr, raddr, wr, din, dout, read_data, bit_count, shift_strobe, state_start,
                      state_end, busy,
                      tdi_vector, count, tdo_vector, start, end,
                      addr_width=addr_width, data_width=data_width)


@block
def JTAGCtrlMaster_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    addr_width = 10
    data_width = 8
    clk = Signal(bool(0))
    reset_n = ResetSignal(1, 0, True)

    control_interface = JTAGCtrlMasterInterface(clk, reset_n, addr_width=addr_width, data_width=data_width)
    ir_tdi_vector = [Signal(intbv(0x55)[data_width:]), Signal(intbv(0x19)[data_width:])]
    ir_tdo_vector = [Signal(intbv(0)[data_width:]), Signal(intbv(0)[data_width:])]
    dr_tdi_vector = [Signal(intbv(0xA5)[data_width:]), Signal(intbv(0x66)[data_width:])]
    dr_tdo_vector = [Signal(intbv(0)[data_width:]), Signal(intbv(0)[data_width:])]
    count = 15

    jcm_inst = JTAGCtrlMaster('DEMO', 'JCM0',
                              control_interface,
                              monitor=monitor)

    @instance
    def clkgen():
        while True:
            control_interface.clk.next = not control_interface.clk
            yield delay(period // 2)

    @always_seq(control_interface.clk.posedge, reset=control_interface.reset_n)
    def loopback():
        control_interface.tdo.next = control_interface.tdi

    @instance
    def stimulus():
        """
        Scan an IR followed by a scan of a DR
        :return:
        """
        H = bool(1)
        L = bool(0)
        # Reset the instrument
        control_interface.reset_n.next = bool(0)
        yield delay(2)
        control_interface.reset_n.next = bool(1)
        yield delay(50)
        # Scan the IR
        # yield scan_ir(control_interface.clk, control_interface.addr, control_interface.addr, control_interface.wr,
        #               control_interface.din, control_interface.dout, control_interface.read_data,
        #               control_interface.bit_count, control_interface.shift_strobe,
        #               control_interface.state_start, control_interface.state_end, control_interface.busy,
        #               ir_tdi_vector, count, ir_tdo_vector,
        #               addr_width=addr_width, data_width=data_width)

        start = SHIFT_IR
        end = RUN_TEST_IDLE
        # Fill the JTAGCtrlMaster data buffer memory with tdi data
        num_full_words = int(count // data_width)
        remainder = count % data_width
        addr = intbv(0)[addr_width:]
        for i in range(num_full_words):
            data = ir_tdi_vector[i]
            # yield write_vector(clk, waddr, din, wr, addr, data)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.din.next = data
            control_interface.wr.next = bool(1)
            yield control_interface.clk.posedge
            yield control_interface.clk.negedge
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

            addr += 1
        # Now write out the remaining bits that may be a partial word in size, but a full word needs to be written
        if remainder > 0:
            data = ir_tdi_vector[num_full_words]
            # yield write_vector(clk, waddr, din, wr, addr, data)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.din.next = data
            control_interface.wr.next = bool(1)
            yield control_interface.clk.posedge
            yield control_interface.clk.negedge
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

        # Now start the scan operation
        control_interface.bit_count.next = intbv(count)[addr_width:]
        control_interface.shift_strobe.next = bool(1)
        control_interface.state_start.next = start
        control_interface.state_end.next = end
        yield control_interface.busy.posedge
        control_interface.shift_strobe.next = bool(0)
        yield control_interface.busy.negedge
        # Scan completed, now fetch the captured data
        addr = intbv(0)[addr_width:]
        for i in range(num_full_words):
            # yield read_vector(clk, raddr, wr, read_data, dout, addr)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            # control_interface.read_data.next = control_interface.dout
            rdata = int(control_interface.dout)
            yield control_interface.clk.negedge
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

            # data = get_read_data(read_data)
            # data = control_interface.read_data
            # ir_tdo_vector[i] = int(data)
            ir_tdo_vector[i] = rdata
            addr += 1
        # Now read out the remaining bits that may be a partial word in size, but a full word needs to be read
        if remainder > 0:
            # yield read_vector(clk, raddr, wr, read_data, dout, addr)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            # control_interface.read_data.next = control_interface.dout
            rdata = int(control_interface.dout)
            yield control_interface.clk.negedge
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

            # data = get_read_data(read_data)
            # data = control_interface.read_data
            ir_tdo_vector[num_full_words] = rdata

        print("ir_tdo_vector = ", ir_tdo_vector)
        assert(ir_tdo_vector[0] == 0x55)  # Captured TDO value returned to ir_tdo_vector
        assert(ir_tdo_vector[1] == 0x19)  # Captured TDO value returned to ir_tdo_vector
        # yield scan_dr(control_interface.clk, control_interface.addr, control_interface.addr, control_interface.wr,
        #               control_interface.din, control_interface.dout, control_interface.read_data,
        #               control_interface.bit_count, control_interface.shift_strobe,
        #               control_interface.state_start, control_interface.state_end, control_interface.busy,
        #               dr_tdi_vector, count, dr_tdo_vector,
        #               addr_width=addr_width, data_width=data_width)
        start = SHIFT_DR
        end = RUN_TEST_IDLE
        # Fill the JTAGCtrlMaster data buffer memory with tdi data
        num_full_words = int(count // data_width)
        remainder = count % data_width
        addr = intbv(0)[addr_width:]
        for i in range(num_full_words):
            data = dr_tdi_vector[i]
            # yield write_vector(clk, waddr, din, wr, addr, data)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.din.next = data
            control_interface.wr.next = bool(1)
            yield control_interface.clk.posedge
            yield control_interface.clk.negedge
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

            addr += 1
        # Now write out the remaining bits that may be a partial word in size, but a full word needs to be written
        if remainder > 0:
            data = dr_tdi_vector[num_full_words]
            # yield write_vector(clk, waddr, din, wr, addr, data)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.din.next = data
            control_interface.wr.next = bool(1)
            yield control_interface.clk.posedge
            yield control_interface.clk.negedge
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

        # Now start the scan operation
        control_interface.bit_count.next = intbv(count)[addr_width:]
        control_interface.shift_strobe.next = bool(1)
        control_interface.state_start.next = start
        control_interface.state_end.next = end
        yield control_interface.busy.posedge
        control_interface.shift_strobe.next = bool(0)
        yield control_interface.busy.negedge
        # Scan completed, now fetch the captured data
        addr = intbv(0)[addr_width:]
        for i in range(num_full_words):
            # yield read_vector(clk, raddr, wr, read_data, dout, addr)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            # control_interface.read_data.next = control_interface.dout
            rdata = int(control_interface.dout)
            yield control_interface.clk.negedge
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

            # data = get_read_data(read_data)
            #data = control_interface.read_data
            # print("control_interface.read_data = ", control_interface.read_data)
            print("rdata0 = ", rdata)
            dr_tdo_vector[i] = rdata
            addr += 1
        # Now read out the remaining bits that may be a partial word in size, but a full word needs to be read
        if remainder > 0:
            # yield read_vector(clk, raddr, wr, read_data, dout, addr)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            # control_interface.read_data.next = control_interface.dout
            # print("control_interface.read_data = ", control_interface.read_data)
            rdata = int(control_interface.dout)
            print("data1 = ", rdata)
            yield control_interface.clk.negedge
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

            # data = get_read_data(read_data)
            # data = control_interface.read_data
            dr_tdo_vector[num_full_words] = rdata
        print("dr_tdo_vector = ", dr_tdo_vector)
        assert(dr_tdo_vector[0] == 0xA5)  # Captured TDO value returned to dr_tdo_vector
        assert(dr_tdo_vector[1] == 0x66)  # Captured TDO value returned to dr_tdo_vector
        raise StopSimulation()

    return jcm_inst, clkgen, stimulus, loopback


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    clk = Signal(bool(0))
    reset_n = ResetSignal(1, 0, True)

    control_instance = JTAGCtrlMasterInterface(clk, reset_n, addr_width=10, data_width=8)

    jcm_inst = JTAGCtrlMaster('DEMO', 'JCM0',
                              control_instance,
                              monitor=False
                              )

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    jcm_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="JTAGCtrlMaster")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    jcm_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="JTAGCtrlMaster")
    tb = JTAGCtrlMaster_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="JTAGCtrlMaster_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="JTAGCtrlMaster_tb")


def main():
    tb = JTAGCtrlMaster_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()