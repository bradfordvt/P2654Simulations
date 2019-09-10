"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

_______________________________
|  Controller  |    DCBA Hex  |
|     STATE    |      Value   |
+--------------+--------------+
|   EXIT2DR    |       0      |
+--------------+--------------+
|   EXIT1DR    |       1      |
+--------------+--------------+
|   SHIFTDR    |       2      |
+--------------+--------------+
|   PAUSEDR    |       3      |
+--------------+--------------+
|   SELECTIR   |       4      |
+--------------+--------------+
|   UPDATEDR   |       5      |
+--------------+--------------+
|   CAPTUREDR  |       6      |
+--------------+--------------+
|   SELECTDR   |       7      |
+--------------+--------------+
|   EXIT2IR    |       8      |
+--------------+--------------+
|   EXIT1IR    |       9      |
+--------------+--------------+
|   SHIFTIR    |       A      |
+--------------+--------------+
|   PAUSEIR    |       B      |
+--------------+--------------+
| RUNTEST/IDLE |       C      |
+--------------+--------------+
|   UPDATEIR   |       D      |
+--------------+--------------+
|   CAPTUREIR  |       E      |
+--------------+--------------+
|    RESET     |       F      |
+--------------+--------------+
"""

from myhdl import *
from hdl.standards.s1149dot1.JTAGInterface import JTAGInterface
from hdl.standards.s1149dot1.JTAGState import JTAGState
from hdl.standards.s1149dot1.TAPInterface import TAPInterface
import os
import os.path

period = 20  # clk frequency = 50 MHz

@block
def Std1149_1_TAP(path, name, jtag_interface, state, tap_interface, monitor=False):
    """
    TAP Controller logic
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param jtag_interface: JTAGInterface object defining the JTAG signals used by this controller
    :param state: Monitor signal state with this 4 bit encoding
    :param tap_interface: TAPInterface object defining the TAP signals managed by this controller
    :return:
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    NA = Signal(bool(1))
    NB = Signal(bool(1))
    NC = Signal(bool(1))
    ND = Signal(bool(1))
    A = Signal(bool(1))
    B = Signal(bool(1))
    C = Signal(bool(1))
    D = Signal(bool(1))
    update_drstate = Signal(bool(0))
    TAP_POR = jtag_interface.TRST

    @always(jtag_interface.TCK.negedge)
    def reset_gen():
        if not TAP_POR:
            tap_interface.Reset.next = bool(0)
        else:
            tap_interface.Reset.next = bool(not (A and B and C and D))

    @always(jtag_interface.TCK.negedge)
    def enable_gen():
        if not TAP_POR:
            tap_interface.Enable.next = bool(0)
        else:
            tap_interface.Enable.next = bool(
                (not (not (not A and B and not C and D)) and (not (not A and B and not C and not D))))

    @always(jtag_interface.TCK.negedge)
    def shiftir_gen():
        if not TAP_POR:
            tap_interface.ShiftIR.next = bool(1)
        else:
            tap_interface.ShiftIR.next = bool((not A and B and not C and D))

    @always(jtag_interface.TCK.negedge)
    def captureir_gen():
        if not TAP_POR:
            tap_interface.CaptureIR.next = bool(1)
        else:
            tap_interface.CaptureIR.next = bool((not A and B and C and D))

    @always_comb
    def clockir_gen():
        tap_interface.ClockIR.next = bool(not (not jtag_interface.TCK and not A and B and D))

    @always_comb
    def updateir_gen():
        tap_interface.UpdateIR.next = bool((not jtag_interface.TCK and A and not B and C and D))

    @always(jtag_interface.TCK.negedge)
    def shiftdr_gen():
        if not TAP_POR:
            tap_interface.ShiftDR.next = bool(1)
        else:
            tap_interface.ShiftDR.next = bool((not A and B and not C and not D))

    @always(jtag_interface.TCK.negedge)
    def capturedr_gen():
        if not TAP_POR:
            tap_interface.CaptureDR.next = bool(1)
        else:
            tap_interface.CaptureDR.next = bool((not A and B and C and not D))

    @always_comb
    def clockdr_gen():
        tap_interface.ClockDR.next = bool(not (not jtag_interface.TCK and not A and B and not D))

    @always_comb
    def updatedr_gen():
        tap_interface.UpdateDR.next = bool((not jtag_interface.TCK and update_drstate))

    @always_comb
    def updatedr_state_gen():
        tap_interface.UpdateDRState.next = bool((A and not B and C and not D))
        update_drstate.next = bool((A and not B and C and not D))

    @always_comb
    def select_gen():
        tap_interface.Select.next = D

    @always_comb
    def na_gen():
        NA.next = bool((not jtag_interface.TMS and not C and A) or (jtag_interface.TMS and not B) or (
                    jtag_interface.TMS and not A) or (jtag_interface.TMS and D and C))

    @always_comb
    def nb_gen():
        NB.next = bool((not jtag_interface.TMS and B and not A) or (not jtag_interface.TMS and not C) or (
                    not jtag_interface.TMS and not D and B) or (not jtag_interface.TMS and not D and not A) or (
                                   jtag_interface.TMS and C and not B) or (jtag_interface.TMS and D and C and A))

    @always_comb
    def nc_gen():
        NC.next = bool((C and not B) or (C and A) or (jtag_interface.TMS and not B))

    @always_comb
    def nd_gen():
        ND.next = bool(
            (D and not C) or (D and B) or (not jtag_interface.TMS and C and not B) or (not D and C and not B and not A))

    @always(jtag_interface.TCK.posedge)
    def a_gen():
        if not TAP_POR:
            A.next = bool(1)
        else:
            A.next = NA

    @always(jtag_interface.TCK.posedge)
    def b_gen():
        if not TAP_POR:
            B.next = bool(1)
        else:
            B.next = NB

    @always(jtag_interface.TCK.posedge)
    def c_gen():
        if not TAP_POR:
            C.next = bool(1)
        else:
            C.next = NC

    @always(jtag_interface.TCK.posedge)
    def d_gen():
        if not TAP_POR:
            D.next = bool(1)
        else:
            D.next = ND

    @always_comb
    def state_gen():
        state.value.next = concat(D, C, B, A)

    if monitor == False:
        return reset_gen, enable_gen, shiftir_gen, captureir_gen, clockir_gen, updateir_gen, shiftdr_gen, capturedr_gen, \
               clockdr_gen, updatedr_gen, updatedr_state_gen, select_gen, na_gen, nb_gen, nc_gen, nd_gen, \
               a_gen, b_gen, c_gen, d_gen, state_gen
    else:
        @instance
        def Monitor_STATE():
            print("\t\tStd1149_1_TAP.state({:s}):".format(path + '.' + name), state.value, "Binary:",
                  bin(state.value, 4))
            while 1:
                yield state.value
                print("\t\tStd1149_1_TAP.state({:s}):".format(path + '.' + name), state.value, "Binary:",
                      bin(state.value, 4))

        @instance
        def Monitor_Reset():
            print("\t\tStd1149_1_TAP.Reset*({:s}):".format(path + '.' + name), tap_interface.Reset)
            while 1:
                yield tap_interface.Reset
                print("\t\tStd1149_1_TAP.Reset*({:s}):".format(path + '.' + name), tap_interface.Reset)

        @instance
        def Monitor_Enable():
            print("\t\tStd1149_1_TAP.Enable({:s}):".format(path + '.' + name), tap_interface.Enable)
            while 1:
                yield tap_interface.Enable
                print("\t\tStd1149_1_TAP.Enable({:s}):".format(path + '.' + name), tap_interface.Enable)

        @instance
        def Monitor_Select():
            print("\t\tStd1149_1_TAP.Select({:s}):".format(path + '.' + name), tap_interface.Select)
            while 1:
                yield tap_interface.Select
                print("\t\tStd1149_1_TAP.Select({:s}):".format(path + '.' + name), tap_interface.Select)

        @instance
        def Monitor_CaptureDR():
            print("\t\tStd1149_1_TAP.CaptureDR({:s}):".format(path + '.' + name), tap_interface.CaptureDR)
            while 1:
                yield tap_interface.CaptureDR
                print("\t\tStd1149_1_TAP.CaptureDR({:s}):".format(path + '.' + name), tap_interface.CaptureDR)

        @instance
        def Monitor_UpdateDR():
            print("\t\tStd1149_1_TAP.UpdateDR({:s}):".format(path + '.' + name), tap_interface.UpdateDR)
            while 1:
                yield tap_interface.UpdateDR
                print("\t\tStd1149_1_TAP.UpdateDR({:s}):".format(path + '.' + name).format(path + '.' + name),
                      tap_interface.UpdateDR)

        @instance
        def Monitor_ShiftDR():
            print("\t\tStd1149_1_TAP.ShiftDR({:s}):".format(path + '.' + name), tap_interface.ShiftDR)
            while 1:
                yield tap_interface.ShiftDR
                print("\t\tStd1149_1_TAP.ShiftDR({:s}):".format(path + '.' + name), tap_interface.ShiftDR)

        @instance
        def Monitor_CaptureIR():
            print("\t\tStd1149_1_TAP.CaptureIR({:s}):".format(path + '.' + name), tap_interface.CaptureIR)
            while 1:
                yield tap_interface.CaptureIR
                print("\t\tStd1149_1_TAP.CaptureIR({:s}):".format(path + '.' + name), tap_interface.CaptureIR)

        @instance
        def Monitor_UpdateIR():
            print("\t\tStd1149_1_TAP.UpdateIR({:s}):".format(path + '.' + name), tap_interface.UpdateIR)
            while 1:
                yield tap_interface.UpdateIR
                print("\t\tStd1149_1_TAP.UpdateIR({:s}):".format(path + '.' + name), tap_interface.UpdateIR)

        @instance
        def Monitor_ShiftIR():
            print("\t\tStd1149_1_TAP.ShiftIR({:s}):", tap_interface.ShiftIR)
            while 1:
                yield tap_interface.ShiftIR
                print("\t\tStd1149_1_TAP.ShiftIR({:s}):", tap_interface.ShiftIR)

        return reset_gen, enable_gen, shiftir_gen, captureir_gen, clockir_gen, updateir_gen, shiftdr_gen, capturedr_gen, \
               clockdr_gen, updatedr_gen, updatedr_state_gen, select_gen, na_gen, nb_gen, nc_gen, nd_gen, \
               a_gen, b_gen, c_gen, d_gen, state_gen, Monitor_STATE, Monitor_Enable, Monitor_Reset, \
               Monitor_Select, Monitor_CaptureDR, Monitor_ShiftDR, Monitor_UpdateDR, Monitor_CaptureIR, \
               Monitor_ShiftIR, Monitor_UpdateIR


@block
def Std1149_1_TAP_tb(file_data, monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param file_data: File pointer to csv file to write signal information to
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    jtag_interface = JTAGInterface()
    state = JTAGState()
    tap_interface = TAPInterface()
    tck = jtag_interface.TCK
    tms = jtag_interface.TMS
    trst = jtag_interface.TRST
    reset = tap_interface.Reset
    enable = tap_interface.Enable
    shiftir = tap_interface.ShiftIR
    captureir = tap_interface.CaptureIR
    clockir = tap_interface.ClockIR
    updateir = tap_interface.UpdateIR
    shiftdr = tap_interface.ShiftDR
    capturedr = tap_interface.CaptureDR
    clockdr = tap_interface.ClockDR
    updatedr = tap_interface.UpdateDR
    update_drstate = tap_interface.UpdateDRState
    select_out = tap_interface.Select

    tap_inst = Std1149_1_TAP('TOP', 'TAP0', jtag_interface, state, tap_interface, monitor=monitor)

    # print header to console
    print("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15}".format("TCK", "TMS", "TRST",
                                                                                         "state",
                                                                                         "Reset", "Enable", "ShiftIR",
                                                                                         "CaptureIR", "ClockIR",
                                                                                         "UpdateIR",
                                                                                         "ShiftDR", "CaptureDR",
                                                                                         "ClockDR", "UpdateDR",
                                                                                         "UpdateDRState", "Select"))

    # print header to file
    print("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15}".format("TCK", "TMS", "TRST",
                                                                                         "state",
                                                                                         "Reset", "Enable", "ShiftIR",
                                                                                         "CaptureIR", "ClockIR",
                                                                                         "UpdateIR",
                                                                                         "ShiftDR", "CaptureDR",
                                                                                         "ClockDR", "UpdateDR",
                                                                                         "UpdateDRState", "Select"),
          file=file_data)

    # print data on each clock
    @always(tck.posedge)
    def print_data():
        """
        """
        # print on console
        # print.format is not supported in MyHDL 1.0
        print(bool(tck), ",", bool(tms), ",", bool(trst),
              ",", hex(state.value),
              ",", bool(reset), ",", bool(enable), ",",
              bool(shiftir), ",", bool(captureir), ",", bool(clockir), ",",
              bool(updateir),
              ",", bool(shiftdr), ",", bool(capturedr), ",", bool(clockdr), ",",
              bool(updatedr), ",", bool(update_drstate), ",", bool(select_out))

        print(bool(tck), ",", bool(tms), ",", bool(trst),
              ",", hex(state.value),
              ",", bool(reset), ",", bool(enable), ",",
              bool(shiftir), ",", bool(captureir), ",", bool(clockir), ",",
              bool(updateir),
              ",", bool(shiftdr), ",", bool(capturedr), ",", bool(clockdr), ",",
              bool(updatedr), ",", bool(update_drstate), ",", bool(select_out),
              file=file_data)

    @instance
    def stimulus():
        """
        Not true IJTAG protocol, but used to exercise the state machine with the fewest cycles
        :return:
        """
        H = bool(1)
        L = bool(0)
        # Reset the tap
        trst.next = L
        tck.next = H
        yield delay(period)
        assert(select_out == H)
        tck.next = L
        yield delay(period)
        trst.next = H
        yield delay(period)
        tck.next = H
        yield delay(period)
        #######################################################################
        # TLR - IDLE - SelectDR - SelectIR - TLR
        #######################################################################
        # Test for TEST LOGIC RESET state
        assert(state.value == 0xF)
        assert(reset == L)
        assert (select_out == H)
        # ******************************* Move tap to IDLE state
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xC)
        assert (select_out == H)
        # ****************************** Stay in IDLE state
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xC)
        assert(reset == H)
        # ***************************** Move to SelectDR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x7)
        assert(select_out == L)
        # **************************** Move to SelectIR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x4)
        # *************************** Move to Test Logic Reset
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xF)
        assert(reset == H)
        assert(enable == L)
        assert(shiftir == L)
        assert(captureir == L)
        assert(clockir == H)
        assert(updateir == L)
        assert(shiftdr == L)
        assert(capturedr == L)
        assert(clockdr == H)
        assert(updatedr == L)
        assert(update_drstate == L)
        assert(select_out == H)
        #######################################################################
        # TLR - IDLE - SelectDR - SelectIR - CaptureIR - ShiftIR - ShiftIR - Exit1IR - UpdateIR - IDLE
        #######################################################################
        # ********************************** Move tap to IDLE state
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xC)
        # ********************************* Move to SelectDR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x7)
        assert(select_out == L)
        # ******************************** Move to SelectIR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x4)
        assert(reset == H)
        assert(enable == L)
        assert(shiftir == L)
        assert(captureir == L)
        assert(clockir == H)
        assert(updateir == L)
        assert(shiftdr == L)
        assert(capturedr == L)
        assert(clockdr == H)
        assert(updatedr == L)
        assert(update_drstate == L)
        assert(select_out == L)
        # ******************************* Move to CaptureIR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xE)
        assert(select_out == H)
        # ****************************** Move to ShiftIR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        assert(captureir == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xA)
        assert(captureir == H)
        # ***************************** Stay in ShiftIR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        assert(enable == H)
        assert(captureir == L)
        assert(shiftir == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xA)
        # **************************** Move to Exit1IR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert(captureir == L)
        assert(enable == H)
        assert(shiftir == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x9)
        # *************************** Move to UpdateIR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert(enable == L)
        assert(shiftir == L)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xD)
        # *************************** Move to IDLE
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        assert(updateir == H)
        assert(select_out == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xC)
        assert(updateir == L)
        #######################################################################
        # IDLE - SelectDR - CaptureDR - ShiftDR - ShiftDR - Exit1DR - UpdateDR - IDLE
        #######################################################################
        # **************************** Move to SelectDR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x7)
        assert(select_out == L)
        # *************************** Move to CaptureDR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x6)
        # ************************** Move to ShiftDR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        assert(capturedr == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x2)
        assert(capturedr == H)
        # ************************* Stay in ShiftDR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        assert(capturedr == L)
        assert(shiftdr == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x2)
        # ************************* Move to Exit1DR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert(capturedr == L)
        assert(shiftdr == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x1)
        # **************************** Move to UpdateDR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert(shiftdr == L)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x5)
        assert(update_drstate == H)
        # ************************** Move to IDLE
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        assert(updatedr == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xC)
        assert(select_out == H)
        assert(update_drstate == L)
        assert(updatedr == L)
        #######################################################################
        # IDLE - SelectDR - SelectIR - CaptureIR - ShiftIR - Exit1IR - PauseIR - PauseIR - Exit2IR - ShiftIR - UpdateIR - IDLE
        #######################################################################
        # ********************************** Move to SelectDR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x7)
        assert(select_out == L)
        # ******************************* Move to SelectIR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x4)
        # ******************************* Move to CaptureIR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xE)
        assert(select_out == H)
        # ******************************** Move to ShiftIR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        assert(captureir == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xA)
        # ******************************** Move to Exit1IR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert(captureir == L)
        assert(shiftir == H)
        assert(enable == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x9)
        # ********************************* Move to PauseIR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        assert(shiftir == L)
        assert(enable == L)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xB)
        # ******************************** Stay in PauseIR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xB)
        # ********************************* Move to Exit2IR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x8)
        # ********************************* Move to ShiftIR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xA)
        # *********************************** Move to Exit1IR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert(shiftir == H)
        assert(enable == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x9)
        # ********************************* Move to UpdateIR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert(enable == L)
        assert(shiftir == L)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xD)
        # ****************************** Move to IDLE
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        assert(updateir == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xC)
        assert(updateir == L)
        #######################################################################
        # IDLE - SelectDR - CaptureDR - ShiftDR - Exit1DR - PauseDR - PauseDR - Exit2DR - ShiftDR - UpdateDR - IDLE
        #######################################################################
        # ********************************************** Move to SelectDR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x7)
        assert(select_out == L)
        # ***************************************** Move to CaptureDR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x6)
        # ************************************* Move to ShiftDR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        assert(capturedr == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x2)
        # ******************************** Move to Exit1DR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert (capturedr == L)
        assert (shiftdr == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x1)
        # ******************************* Move to PauseDR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        assert(shiftdr == L)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x3)
        # ********************************** Stay in PauseDR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x3)
        # ************************************** Move to Exit2DR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x0)
        # *********************************** Move to ShiftDR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x2)
        # ********************************* Move to Exit1DR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert (shiftdr == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x1)
        # ********************************** Move to UpdateDR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert(shiftdr == L)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x5)
        assert(update_drstate == H)
        # ********************************* Move to IDLE
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        assert(updatedr == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xC)
        assert(update_drstate == L)
        assert(updatedr == L)
        assert(select_out == H)
        #######################################################################
        # IDLE - SelectDR - SelectIR - CaptureIR - Exit1IR - UpdateIR - IDLE
        #######################################################################
        # ********************************** Move to SelectDR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x7)
        assert(select_out == L)
        # ******************************* Move to SelectIR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x4)
        # ********************************** Move to CaptureIR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xE)
        assert(select_out == H)
        # ********************************* Move to Exit1IR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert (captureir == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x9)
        # ********************************* Move to UpdateIR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert(captureir == L)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xD)
        # ************************************* Move to IDLE
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        assert(updateir == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xC)
        assert(updateir == L)
        #######################################################################
        # IDLE - SelectDR - CaptureDR - Exit1DR - UpdateDR - IDLE
        #######################################################################
        # ********************************* Move to SelectDR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x7)
        assert(select_out == L)
        # ********************************* Move to CaptureDR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x6)
        # ******************************** Move to Exit1DR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert (capturedr == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x1)
        # ****************************** Move to UpdateDR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert (capturedr == L)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x5)
        assert(update_drstate == H)
        # ***************************** Move to IDLE
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        assert(updatedr == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xC)
        assert(update_drstate == L)
        assert(updatedr == L)
        assert(select_out == H)
        #######################################################################
        # IDLE - SelectDR - SelectIR - CaptureIR - Exit1IR - UpdateIR - SelectDR - SelectIR - TLR - IDLE
        #######################################################################
        # ********************************* Move to SelectDR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x7)
        assert(select_out == L)
        # ********************************** Move to SelectIR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x4)
        # ********************************** Move to CaptureIR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xE)
        assert(select_out == H)
        # ********************************** Move to Exit1IR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert (captureir == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x9)
        # ********************************* Move to UpdateIR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert(captureir == L)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xD)
        assert(captureir == L)
        # ******************************* Move to SelectDR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert(updateir == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x7)
        assert(select_out == L)
        assert(updateir == L)
        # ********************************* Move to SelectIR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x4)
        # ************************* Move to TLT
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xF)
        assert(select_out == H)
        # ******************************** Move to IDLE
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        assert(reset == L)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xC)
        #######################################################################
        # IDLE - SelectDR - CaptureDR - Exit1DR - UpdateDR - SelectDR - SelectIR - TLR - IDLE
        #######################################################################
        # ********************************* Move to SelectDR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert(reset == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x7)
        assert(select_out == L)
        # ****************************** Move to CaptureDR
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x6)
        # ********************************* Move to Exit1DR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert(capturedr == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x1)
        # ******************************* Move to UpdateDR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert (capturedr == L)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x5)
        assert(update_drstate == H)
        # ********************************** Move to SelectDR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        assert(updatedr == H)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x7)
        assert(update_drstate == L)
        assert(updatedr == L)
        # ********************************* Move to SelectIR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0x4)
        # ************************************** Move to TLR
        tms.next = H
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xF)
        assert(select_out == H)
        # ******************************** Move to IDLE
        tms.next = L
        tck.next = bool(0)
        yield delay(period)
        tck.next = bool(1)
        yield delay(period)
        assert(state.value == 0xC)

        raise StopSimulation()

    return tap_inst, stimulus, print_data


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    jtag_interface = JTAGInterface()
    state = JTAGState()
    tap_interface = TAPInterface()

    tap_inst = Std1149_1_TAP('TOP', 'TAP0', jtag_interface, state, tap_interface, monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    tap_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="Std1149_1_TAP")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    tap_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="Std1149_1_TAP")
    file_data = open("Std1149_1_TAP_tb_conv.csv", 'w')  # file for saving data
    tb = Std1149_1_TAP_tb(file_data, monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="Std1149_1_TAP_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="Std1149_1_TAP_tb")
    file_data.close()


def main():
    file_data = open("Std1149_1_TAP_tb.csv", 'w')  # file for saving data
    tb = Std1149_1_TAP_tb(file_data, monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    file_data.close()
    convert()


if __name__ == '__main__':
    main()
