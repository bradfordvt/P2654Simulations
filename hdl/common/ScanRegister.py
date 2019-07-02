"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import logging
import os
import os.path


logger = logging.getLogger(__name__)


def sa_to_string(tdo_vector):
    dlen = len(tdo_vector)
    response = ""
    for i in range(dlen):
        t = '0'
        if tdo_vector[dlen-i-1] == bool(1):
            t = '1'
        response += t
    return response


class ScanRegister:
    def __init__(self, path, name, si, ce, se, ue, sel, reset, clock, so, di, do, width=9):
        """
        Generic ScanRegister design following the Capture/Shift/Update protocol
        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logger (path instance)
        :param si: ScanIn Port
        :param ce: CaptureEnable Port
        :param se: ShiftEnable Port
        :param ue: UpdateEnable Port
        :param sel: Select Port
        :param reset: Reset Port
        :param clock: Clock Port
        :param so: ScanOut Port
        :param di: DataIn Port
        :param do: DataOut Port
        :param width: The number of bits contained in this register
        """
        # print(__name__)
        logger.info("Constructing ScanRegister instance ({:s}).".format(path + '.' + name))
        self.path = path
        self.name = name
        self.si = si
        self.ce = ce
        self.se = se
        self.ue = ue
        self.sel = sel
        self.reset = reset
        self.clock = clock
        self.so = so
        self.di = di
        self.do = do
        self.width = width
        self.isr = [Signal(bool(0)) for _ in range(width)]

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
        return self.ScanRegister_rtl(monitor=monitor)

    @block
    def ScanRegister_rtl(self, monitor=False):
        """
        The logic for the ScanRegister
        :return: The generator methods performing the logic decisions
        """
        logger.debug("ScanRegister({:s}).rtl()".format(self.path + '.' + self.name))
        @always(self.clock.posedge)
        def capture_ff():
            # print("Entering ScanRegister.rtl.capture_ff()")
            # logger.debug("ScanRegister({:s}): Entering capture_ff".format(self.path + '.' + self.name))
            # logger.debug("\tself.sel = {:s}".format(str(self.sel)))
            # logger.debug("\tself.ce = {:s}".format(str(self.ce)))
            if self.sel == bool(0) and self.ce == bool(1):
                # logger.debug("\tSelect and CaptureEn")
                # logger.debug("\tdi = {:s}".format(sa_to_string(self.di)))
                # logger.debug("\tisr = {:s}".format(sa_to_string(self.isr)))
                for i in range(self.width):
                    self.isr[i].next = self.di[i]
            elif self.sel == bool(0) and self.se == bool(1):
                # logger.debug("\tSelect and ShiftEn")
                # logger.debug("\tsi = {:s}".format(str(self.si)))
                for i in range(self.width):
                    if i == 0:
                        self.isr[i].next = self.si
                        # logger.debug("\t\tsi = {:s}".format(bin(self.si)))
                    elif i == self.width - 1:
                        # logger.debug("\t\tso = {:s}".format(bin(self.isr[i])))
                        self.so.next = self.isr[i]
                        self.isr[i].next = self.isr[i-1]
                    else:
                        self.isr[i].next = self.isr[i-1]
            else:
                self.so.next = self.so

        @always(self.clock.posedge)
        def update_ff():
            # print("Entering ScanRegister.rtl.update_ff()")
            # logger.debug("ScanRegister({:s}): Entering update_ff".format(self.path + '.' + self.name))
            # logger.debug("\tself.clock is: {:s}.".format(str(self.clock)))
            # logger.debug("\tself.reset is: {:s}.".format(str(self.reset)))
            if self.reset == bool(0):
                for i in range(self.width):
                    self.do[i].next = bool(0)
            # elif self.reset == bool(1):
            #     for i in range(self.width):
            #         self.do[i].next = self.do[i]
            elif self.sel == bool(0) and self.ue == bool(1):
                # logger.debug("\tSelect and UpdateEn")
                # logger.debug("\tisr = {:s}".format(sa_to_string(self.isr)))
                # logger.debug("\tdo = {:s}".format(sa_to_string(self.do)))
                for i in range(self.width):
                    self.do[i].next = self.isr[i]

        if monitor == False:
            return capture_ff, update_ff
        else:
            @instance
            def monitor_si():
                print("\t\tScanRegister({:s}): si".format(self.path + '.' + self.name), self.si)
                while 1:
                    yield self.si
                    print("\t\tScanRegister({:s}): si".format(self.path + '.' + self.name), self.si)

            @instance
            def monitor_ce():
                print("\t\tScanRegister({:s}): ce".format(self.path + '.' + self.name), self.ce)
                while 1:
                    yield self.ce
                    print("\t\tScanRegister({:s}): ce".format(self.path + '.' + self.name), self.ce)

            @instance
            def monitor_se():
                print("\t\tScanRegister({:s}): se".format(self.path + '.' + self.name), self.se)
                while 1:
                    yield self.se
                    print("\t\tScanRegister({:s}): se".format(self.path + '.' + self.name), self.se)

            @instance
            def monitor_ue():
                print("\t\tScanRegister({:s}): ue".format(self.path + '.' + self.name), self.ue)
                while 1:
                    yield self.ue
                    print("\t\tScanRegister({:s}): ue".format(self.path + '.' + self.name), self.ue)

            @instance
            def monitor_sel():
                print("\t\tScanRegister({:s}): sel".format(self.path + '.' + self.name), self.sel)
                while 1:
                    yield self.sel
                    print("\t\tScanRegister({:s}): sel".format(self.path + '.' + self.name), self.sel)

            @instance
            def monitor_reset():
                print("\t\tScanRegister({:s}): reset".format(self.path + '.' + self.name), self.reset)
                while 1:
                    yield self.reset
                    print("\t\tScanRegister({:s}): reset".format(self.path + '.' + self.name), self.reset)

            @instance
            def monitor_clock():
                print("\t\tScanRegister({:s}): clock".format(self.path + '.' + self.name), self.clock)
                while 1:
                    yield self.clock
                    print("\t\tScanRegister({:s}): clock".format(self.path + '.' + self.name), self.clock)

            @instance
            def monitor_so():
                print("\t\tScanRegister({:s}): so".format(self.path + '.' + self.name), self.so)
                while 1:
                    yield self.so
                    print("\t\tScanRegister({:s}): so".format(self.path + '.' + self.name), self.so)

            @instance
            def monitor_isr():
                print("\t\tScanRegister({:s}): isr".format(self.path + '.' + self.name), self.isr)
                while 1:
                    yield self.isr
                    print("\t\tScanRegister({:s}): isr".format(self.path + '.' + self.name), self.isr)

            @instance
            def monitor_di():
                print("\t\tScanRegister({:s}): di".format(self.path + '.' + self.name), self.di)
                while 1:
                    yield self.di
                    print("\t\tScanRegister({:s}): di".format(self.path + '.' + self.name), self.di)

            @instance
            def monitor_do():
                print("\t\tScanRegister({:s}): do".format(self.path + '.' + self.name), self.do)
                while 1:
                    yield self.do
                    print("\t\tScanRegister({:s}): do".format(self.path + '.' + self.name), self.do)
            return monitor_si, monitor_ce, monitor_se, monitor_ue, monitor_sel, monitor_reset,\
                monitor_clock, monitor_so, monitor_di, monitor_do, capture_ff, update_ff,\
                monitor_isr

    def get_width(self):
        return self.width

    @staticmethod
    def convert():
        """
        Convert the myHDL design into VHDL and Verilog
        :return:
        """
        width = 9
        si = Signal(bool(0))
        so = Signal(bool(0))
        di = [Signal(bool(0)) for _ in range(width)]
        do = [Signal(bool(0)) for _ in range(width)]
        sel = Signal(bool(0))
        ce = Signal(bool(0))
        se = Signal(bool(0))
        ue = Signal(bool(0))
        reset = ResetSignal(1, active=0, async=True)
        clock = Signal(bool(0))

        sreg_inst = ScanRegister('TOP', 'ScanRegister0', si, ce, se, ue, sel, reset, clock, so, di, do, width=9)

        sreg_inst.toVerilog()
        sreg_inst.toVHDL()

    @staticmethod
    @block
    def testbench(monitor=False):
        """
        Test bench interface for a quick test of the operation of the design
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """
        width = 9
        si = Signal(bool(0))
        so = Signal(bool(0))
        di = [Signal(bool(0)) for _ in range(width)]
        di[width - 1] = Signal(bool(1))
        di[width - 5] = Signal(bool(1))
        do = [Signal(bool(0)) for _ in range(width)]
        si_data = [Signal(bool(0)) for _ in range(width)]
        si_data[width - 5] = Signal(bool(1))
        si_data[width - 7] = Signal(bool(1))
        so_data = [Signal(bool(0)) for _ in range(width)]
        sel = Signal(bool(0))
        ce = Signal(bool(0))
        se = Signal(bool(0))
        ue = Signal(bool(0))
        reset = Signal(bool(0))
        clock = Signal(bool(0))

        sreg_inst = ScanRegister('TOP', 'ScanRegister0', si, ce, se, ue, sel, reset, clock, so, di, do, width=9)

        @always(delay(10))
        def clkgen():
            clock.next = not clock

        @instance
        def stimulus():
            """
            Not true IJTAG protocol, but used to exercise the state machine with the fewest cycles
            :return:
            """
            H = bool(1)
            L = bool(0)
            # Reset the instrument
            reset.next = bool(0)
            yield delay(10)
            reset.next = bool(1)
            yield delay(10)
            # Start the Capture transition operation
            yield clock.posedge
            # Write Capture value
            ce.next = H
            yield clock.negedge
            yield clock.posedge
            # Write Shift value
            ce.next = L
            se.next = H
            yield clock.negedge
            for i in range(width):
                si.next = si_data[width - 1 - i]
                yield clock.posedge
                yield clock.negedge
                so_data[width - 1 - i].next = so
            # Write Update value
            se.next = L
            ue.next = H
            yield clock.negedge
            yield clock.posedge
            for j in range(width):
                if j == 0 or j == 4:
                    assert(so_data[width - 1 - j] == bool(1))
                else:
                    assert(so_data[width - 1 - j] == bool(0))
            for j in range(width):
                if j == 4 or j == 6:
                    assert(do[width - 1 - j] == bool(1))
                else:
                    assert(do[width - 1 - j] == bool(0))

            raise StopSimulation()

        return sreg_inst.ScanRegister_rtl(monitor=monitor), clkgen, stimulus


if __name__ == '__main__':
    tb = ScanRegister.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    ScanRegister.convert()
