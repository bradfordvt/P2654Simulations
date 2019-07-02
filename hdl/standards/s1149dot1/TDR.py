"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import logging
from p2654.core.ScanRegister import ScanRegister

logger = logging.getLogger(__name__)


class TDR:
    def __init__(self, path, name, D, Q, scan_in, tap_interface, local_reset, scan_out, tdr_width=9):
        """
        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logging (path instance)
        :param D: tdr_width bit wide Signal array of intbv(bool) as the mission input [Signal(bool(0)) for i in range(tdr_width)]
        :param Q: tdr_width bit wide Signal array of intbv(bool) as the mission output [Signal(bool(0)) for i in range(tdr_width)]
        :param scan_in: Input signal for data scanned into TDR
        :param tap_interface: TAPInterface object containing:
            CaptureDR: Signal used to enable the capture of D
            ShiftDR: Signal used to shift the data out ScanOut from the TDR
            UpdateDR: Signal used to latch the TDR to Q
            Select: Signal used to activate the TDR
            Reset: Signal used to reset the Q of the TDR
            ClockDR: Test Clock used to synchronize the TDR to the TAP
        :param local_reset: Signal used by the internal hardware to reset the TDR
        :param scan_out: Output signal where data is scanned from the TDR
        """
        # print(__name__)
        logger.info("Constructing s1149dot1.TDR instance ({:s}).".format(path + '.' + name))
        self.path = path
        self.name = name
        self.D = D
        self.Q = Q
        self.scan_in = scan_in
        self.tap_interface = tap_interface
        self.local_reset = local_reset
        self.scan_out = scan_out
        self.tdr_width = tdr_width
        self.sr_inst = ScanRegister(
            self.path + '.' + self.name,
            self.name + '_SR',
            self.scan_in,
            self.tap_interface.CaptureDR,
            self.tap_interface.ShiftDR,
            self.tap_interface.UpdateDR,
            self.tap_interface.Select,
            self.tap_interface.Reset,
            self.tap_interface.ClockDR,
            self.scan_out,
            self.D,
            self.Q,
            self.tdr_width
        )

    def rtl(self, monitor=False):
        """
        The logic for the TDR
        Delegate logic processing to the associated ScanRegister instance
        :return: The generator methods performing the logic decisions
        """
        logger.debug("TDR({:s}).rtl()".format(self.path + '.' + self.name))
        if monitor == False:
            return self.sr_inst.rtl(monitor=monitor)
        else:
            @instance
            def monitor_scan_in():
                print("\t\tTDR({:s}): scan_in".format(self.path + self.name), self.scan_in)
                while 1:
                    yield self.scan_in
                    print("\t\tTDR({:s}): scan_in".format(self.path + self.name), self.scan_in)

            @instance
            def monitor_scan_out():
                print("\t\tTDR({:s}): scan_out".format(self.path + self.name), self.scan_out)
                while 1:
                    yield self.scan_out
                    print("\t\tTDR({:s}) scan_out:".format(self.path + self.name), self.scan_out)

            return monitor_scan_in, monitor_scan_out, self.sr_inst.rtl(monitor=monitor)


