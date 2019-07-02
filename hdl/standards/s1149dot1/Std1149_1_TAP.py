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
import logging

logger = logging.getLogger(__name__)


class Std1149_1_TAP:
    def __init__(self, jtag_interface, state, tap_interface):
        """
        TAP Controller logic
        :param jtag_interface: JTAGInterface object defining the JTAG signals used by this controller
        :param state: Monitor signal state with this 4 bit encoding
        :param tap_interface: TAPInterface object defining the TAP signals managed by this controller
        :return:
        """
        self.jtag_interface = jtag_interface
        self.tap_interface = tap_interface
        self.state = state
        self.NA = Signal(bool(1))
        self.NB = Signal(bool(1))
        self.NC = Signal(bool(1))
        self.ND = Signal(bool(1))
        self.A = Signal(bool(1))
        self.B = Signal(bool(1))
        self.C = Signal(bool(1))
        self.D = Signal(bool(1))
        self.TAP_POR = Signal(bool(1))

    def rtl(self, monitor=False):
        @always(self.jtag_interface.TCK.negedge)
        # @always_comb
        def reset_gen():
            if not self.TAP_POR:
                logger.debug("Std1149_1_TAP.reset_gen(): Setting tap_interface.Reset to bool(0).")
                self.tap_interface.Reset.next = bool(0)
            else:
                logger.debug("Std1149_1_TAP.reset_gen(): Setting tap_interface.Reset to {:s}.".format(str(bool(not (self.A and self.B and self.C and self.D)))))
                self.tap_interface.Reset.next = bool(not (self.A and self.B and self.C and self.D))
            # Reset.next = bool(not (A and B and C and D))

        @always(self.jtag_interface.TCK.negedge)
        # @always_comb
        def enable_gen():
            if not self.TAP_POR:
                logger.debug("Std1149_1_TAP.enable_gen(): Setting tap_interface.Enable to bool(0).")
                self.tap_interface.Enable.next = bool(0)
            else:
                logger.debug("Std1149_1_TAP.enable_gen(): Setting tap_interface.Enable to {:s}.".format(str(bool((not (not (not self.A and self.B and not self.C and self.D)) and (not (not self.A and self.B and not self.C and not self.D)))))))
                self.tap_interface.Enable.next = bool((not (not (not self.A and self.B and not self.C and self.D)) and (not (not self.A and self.B and not self.C and not self.D))))
            # Enable.next = bool((not (not (not A and B and not C and D)) and (not (not A and B and not C and not D))))

        @always(self.jtag_interface.TCK.negedge)
        # @always_comb
        def shiftir_gen():
            if not self.TAP_POR:
                self.tap_interface.ShiftIR.next = bool(1)
            else:
                self.tap_interface.ShiftIR.next = bool((not self.A and self.B and not self.C and self.D))
            # ShiftIR.next = bool((not A and B and not C and D))

        @always(self.jtag_interface.TCK.negedge)
        # @always_comb
        def captureir_gen():
            if not self.TAP_POR:
                self.tap_interface.CaptureIR.next = bool(1)
            else:
                self.tap_interface.CaptureIR.next = bool((not self.A and self.B and self.C and self.D))
            # CaptureIR.next = bool((not A and B and C and D))

        @always_comb
        def clockir_gen():
            # print "ClockIR=", ClockIR
            # self.tap_interface.ClockIR.next = bool((not self.jtag_interface.TCK and self.A and not self.B and self.D))
            self.tap_interface.ClockIR.next = bool(not (not self.jtag_interface.TCK and not self.A and self.B and self.D))

        @always_comb
        def updateir_gen():
            self.tap_interface.UpdateIR.next = bool((not self.jtag_interface.TCK and self.A and not self.B and self.C and self.D))

        @always(self.jtag_interface.TCK.negedge)
        # @always_comb
        def shiftdr_gen():
            if not self.TAP_POR:
                logger.debug("Std1149_1_TAP.shiftdr_gen(): Setting tap_interface.ShiftDR to bool(1).")
                self.tap_interface.ShiftDR.next = bool(1)
            else:
                logger.debug("Std1149_1_TAP.enable_gen(): Setting tap_interface.ShiftDR to {:s}.".format(str(bool((not self.A and self.B and not self.C and not self.D)))))
                self.tap_interface.ShiftDR.next = bool((not self.A and self.B and not self.C and not self.D))
            # ShiftDR.next = bool((not A and B and not C and not D))

        @always(self.jtag_interface.TCK.negedge)
        # @always_comb
        def capturedr_gen():
            if not self.TAP_POR:
                logger.debug("Std1149_1_TAP.capturedr_gen(): Setting tap_interface.CaptureDR to bool(1).")
                self.tap_interface.CaptureDR.next = bool(1)
            else:
                # print "In CaptureDRGen: ", bool((not A and B and C and not D))
                # if bool((not A and B and C and not D)) == True:
                #     print "CaptureDR set to ", bool((not A and B and C and not D))
                # else:
                #     print "CaptureDR set to FALSE"
                logger.debug("Std1149_1_TAP.capturedr_gen(): Setting tap_interface.CaptureDR to {:s}.".format(str(bool((not self.A and self.B and self.C and not self.D)))))
                self.tap_interface.CaptureDR.next = bool((not self.A and self.B and self.C and not self.D))
            # CaptureDR.next = bool((not A and B and C and not D))

        @always_comb
        def clockdr_gen():
            # print("ClockDR=", ClockDR)
            # logger.debug("Std1149_1_TAP.clockdr_gen(): Setting tap_interface.ClockDR to {:s}.".format(
            #     str(bool((not self.jtag_interface.TCK and not self.A and self.B and not self.D)))))
            # self.tap_interface.ClockDR.next = bool((not self.jtag_interface.TCK and not self.A and self.B and not self.D))
            logger.debug("Std1149_1_TAP.clockdr_gen(): Setting tap_interface.ClockDR to {:s}.".format(
                str(bool(not (not self.jtag_interface.TCK and not self.A and self.B and not self.D)))))
            self.tap_interface.ClockDR.next = bool(not (not self.jtag_interface.TCK and not self.A and self.B and not self.D))

        @always_comb
        def updatedr_gen():
            logger.debug("Std1149_1_TAP.updatedr_gen(): Setting tap_interface.UpdateDR to {:s}.".format(
                str(bool((not self.jtag_interface.TCK and self.tap_interface.UpdateDRState)))))
            self.tap_interface.UpdateDR.next = bool((not self.jtag_interface.TCK and self.tap_interface.UpdateDRState))

        @always_comb
        def updatedr_state_gen():
            self.tap_interface.UpdateDRState.next = bool((self.A and not self.B and self.C and not self.D))

        @always_comb
        def select_gen():
            logger.debug("Std1149_1_TAP.select_gen(): Setting tap_interface.Select to {:s}.".format(str(self.D)))
            self.tap_interface.Select.next = self.D

        @always_comb
        def na_gen():
            # NA.next = (not (not (not TMS and A and C)) and (not (TMS and not B)) and (not (TMS and not A)) and (not (TMS and C and D)))
            self.NA.next = bool((not self.jtag_interface.TMS and not self.C and self.A) or (self.jtag_interface.TMS and not self.B) or (self.jtag_interface.TMS and not self.A) or (self.jtag_interface.TMS and self.D and self.C))

        @always_comb
        def nb_gen():
            # NB.next = (not ((not (not TMS and not A and B)) and (not (not TMS and not C)) and (not (not TMS and B and not D)) and (not (not TMS and not A and not D)) and (not (TMS and not B and C)) and (not (TMS and A and C and D))))
            self.NB.next = bool((not self.jtag_interface.TMS and self.B and not self.A) or (not self.jtag_interface.TMS and not self.C) or (not self.jtag_interface.TMS and not self.D and self.B) or (not self.jtag_interface.TMS and not self.D and not self.A) or (self.jtag_interface.TMS and self.C and not self.B) or (self.jtag_interface.TMS and self.D and self.C and self.A))

        @always_comb
        def nc_gen():
            # NC.next = (not (not (not B and C)) and (not (A and C)) and (not (TMS and not B)))
            self.NC.next = bool((self.C and not self.B) or (self.C and self.A) or (self.jtag_interface.TMS and not self.B))

        @always_comb
        def nd_gen():
            # ND.next = (not (not (not C and D)) and (not (B and D)) and (not (not TMS and not B and C and not D)))
            self.ND.next = bool((self.D and not self.C) or (self.D and self.B) or (not self.jtag_interface.TMS and self.C and not self.B) or (not self.D and self.C and not self.B and not self.A))

        @always(self.jtag_interface.TCK.posedge)
        def a_gen():
            if not self.TAP_POR:
                self.A.next = bool(1)
            else:
                # print("\tA=", A)
                self.A.next = self.NA

        @always(self.jtag_interface.TCK.posedge)
        def b_gen():
            if not self.TAP_POR:
                self.B.next = bool(1)
            else:
                # print("\tB=", B)
                self.B.next = self.NB

        @always(self.jtag_interface.TCK.posedge)
        def c_gen():
            if not self.TAP_POR:
                self.C.next = bool(1)
            else:
                # print("\tC=", C)
                self.C.next = self.NC

        @always(self.jtag_interface.TCK.posedge)
        def d_gen():
            if not self.TAP_POR:
                self.D.next = bool(1)
            else:
                # print("\tD=", D)
                self.D.next = self.ND

        @always_comb
        def state_gen():
            # print("A=", A)
            # print("B=", B)
            # print("C=", C)
            # print("D=", D)
            #print(concat(D,C,B,A))
            self.state.value.next = concat(self.D, self.C, self.B, self.A)
            logger.debug("Std1149_1_TAP.state_gen(): Setting state to {:s}.".format(str(concat(self.D, self.C, self.B, self.A))))

        if monitor == False:
            return reset_gen, enable_gen, shiftir_gen, captureir_gen, clockir_gen, updateir_gen, shiftdr_gen, capturedr_gen,\
                clockdr_gen, updatedr_gen, updatedr_state_gen, select_gen, na_gen, nb_gen, nc_gen, nd_gen,\
                a_gen, b_gen, c_gen, d_gen, state_gen
        else:
            @instance
            def Monitor_STATE():
                print("\t\tStd1149_1_TAP.state:", self.state.value, "Binary:", bin(self.state.value, 4))
                while 1:
                    yield self.state.value
                    print("\t\tStd1149_1_TAP.state:", self.state.value, "Binary:", bin(self.state.value, 4))

            @instance
            def Monitor_Reset():
                print("\t\tStd1149_1_TAP.Reset*:", self.tap_interface.Reset)
                while 1:
                    yield self.tap_interface.Reset
                    print("\t\tStd1149_1_TAP.Reset*:", self.tap_interface.Reset)

            @instance
            def Monitor_Enable():
                print("\t\tStd1149_1_TAP.Enable:", self.tap_interface.Enable)
                while 1:
                    yield self.tap_interface.Enable
                    print("\t\tStd1149_1_TAP.Enable:", self.tap_interface.Enable)

            @instance
            def Monitor_Select():
                print("\t\tStd1149_1_TAP.Select:", self.tap_interface.Select)
                while 1:
                    yield self.tap_interface.Select
                    print("\t\tStd1149_1_TAP.Select:", self.tap_interface.Select)

            @instance
            def Monitor_CaptureDR():
                print("\t\tStd1149_1_TAP.CaptureDR:", self.tap_interface.CaptureDR)
                while 1:
                    yield self.tap_interface.CaptureDR
                    print("\t\tStd1149_1_TAP.CaptureDR:", self.tap_interface.CaptureDR)

            @instance
            def Monitor_UpdateDR():
                print("\t\tStd1149_1_TAP.UpdateDR:", self.tap_interface.UpdateDR)
                while 1:
                    yield self.tap_interface.UpdateDR
                    print("\t\tStd1149_1_TAP.UpdateDR:", self.tap_interface.UpdateDR)

            @instance
            def Monitor_ShiftDR():
                print("\t\tStd1149_1_TAP.ShiftDR:", self.tap_interface.ShiftDR)
                while 1:
                    yield self.tap_interface.ShiftDR
                    print("\t\tStd1149_1_TAP.ShiftDR:", self.tap_interface.ShiftDR)

            @instance
            def Monitor_CaptureIR():
                print("\t\tStd1149_1_TAP.CaptureIR:", self.tap_interface.CaptureIR)
                while 1:
                    yield self.tap_interface.CaptureIR
                    print("\t\tStd1149_1_TAP.CaptureIR:", self.tap_interface.CaptureIR)

            @instance
            def Monitor_UpdateIR():
                print("\t\tStd1149_1_TAP.UpdateIR:", self.tap_interface.UpdateIR)
                while 1:
                    yield self.tap_interface.UpdateIR
                    print("\t\tStd1149_1_TAP.UpdateIR:", self.tap_interface.UpdateIR)

            @instance
            def Monitor_ShiftIR():
                print("\t\tStd1149_1_TAP.ShiftIR:", self.tap_interface.ShiftIR)
                while 1:
                    yield self.tap_interface.ShiftIR
                    print("\t\tStd1149_1_TAP.ShiftIR:", self.tap_interface.ShiftIR)

            return reset_gen, enable_gen, shiftir_gen, captureir_gen, clockir_gen, updateir_gen, shiftdr_gen, capturedr_gen,\
                clockdr_gen, updatedr_gen, updatedr_state_gen, select_gen, na_gen, nb_gen, nc_gen, nd_gen,\
                a_gen, b_gen, c_gen, d_gen, state_gen, Monitor_STATE, Monitor_Enable, Monitor_Reset,\
                Monitor_Select, Monitor_CaptureDR, Monitor_ShiftDR, Monitor_UpdateDR, Monitor_CaptureIR,\
                Monitor_ShiftIR, Monitor_UpdateIR

