"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import logging
from p2654.core.InstructionRegister import InstructionRegister

logger = logging.getLogger(__name__)


class TIR:
    def __init__(self, path, name, D, Q, scan_in, tap_interface, local_reset, scan_out, tir_width=9):
        """
        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logging (path instance)
        :param D: tir_width bit wide Signal array of intbv(bool) as the mission input [Signal(bool(0)) for i in range(tir_width)]
        :param Q: tir_width bit wide Signal array of intbv(bool) as the mission output [Signal(bool(0)) for i in range(tir_width)]
        :param scan_in: Input signal for data scanned into TIR
        :param tap_interface: TAPInterface object containing:
            CaptureIR: Signal used to enable the capture of D
            ShiftIR: Signal used to shift the data out ScanOut from the TIR
            UpdateIR: Signal used to latch the TIR to Q
            Reset: Signal used to reset the Q of the TIR
            ClockIR: Test Clock used to synchronize the TIR to the TAP
        :param local_reset: Signal used by the internal hardware to reset the TIR
        :param scan_out: Output signal where data is scanned from the TIR
        """
        logger.info("Constructing s1149dot1.TIR instance ({:s}).".format(path + '.' + name))
        self.path = path
        self.name = name
        self.D = D
        self.Q = Q
        self.scan_in = scan_in
        self.tap_interface = tap_interface
        self.local_reset = local_reset
        self.scan_out = scan_out
        self.tir_width = tir_width
        self.ir_inst = InstructionRegister(
            self.path + '.' + self.name,
            self.name + '(sr)',
            self.scan_in,
            self.tap_interface.CaptureIR,
            self.tap_interface.ShiftIR,
            self.tap_interface.UpdateIR,
            self.tap_interface.Reset,
            self.tap_interface.ClockIR,
            self.scan_out,
            self.D,
            self.Q,
            self.tir_width
        )

    def rtl(self, monitor=False):
        """
        The logic for the TIR
        Delegate logic processing to the associated ScanRegister instance
        :return: The generator methods performing the logic decisions
        """
        logger.debug("TIR({:s}).rtl()".format(self.path + '.' + self.name))
        if monitor == False:
            return self.ir_inst.rtl(monitor=monitor)
        else:
            @instance
            def monitor_scan_in():
                print("\t\tTIR({:s}): scan_in".format(self.path + self.name), self.scan_in)
                while 1:
                    yield self.scan_in
                    print("\t\tTIR({:s}): scan_in".format(self.path + self.name), self.scan_in)

            @instance
            def monitor_scan_out():
                print("\t\tTIR({:s}): scan_out".format(self.path + self.name), self.scan_out)
                while 1:
                    yield self.scan_out
                    print("\t\tTIR({:s}) scan_out:".format(self.path + self.name), self.scan_out)

            return monitor_scan_in, monitor_scan_out, self.ir_inst.rtl(monitor=monitor)
