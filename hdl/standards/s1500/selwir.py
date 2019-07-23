"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import os
import os.path
from hdl.common.ScanRegister import ScanRegister
from hdl.standards.s1687.IJTAGInterface import IJTAGInterface


class SELWIR:
    def __init__(self, path, name, si, ijtag_interface, so, select_wir):
        """
        Creates a Select WIR register with the following interface:
        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logging (path instance)
        :param si: ScanInPort
        :param ijtag_interface: IJTAGInterface defining the control signals for this register
        :param so: ScanOutPort
        :param select_wir: Select WIR signal to be controlled by this register
        """
        self.path = path
        self.name = name
        self.si = si
        self.ijtag_interface = ijtag_interface
        self.so = so
        self.select_wir = select_wir
        self.isr = Signal(bool(0))

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
        return self.selwir_rtl(monitor=monitor)

    @block
    def selwir_rtl(self, monitor=False):
        """
        The logic for the selwir
        :return: The generator methods performing the logic decisions
        """
        @always(self.ijtag_interface.CLOCK.posedge)
        def capture_ff():
            if self.ijtag_interface.SELECT == bool(0) and self.ijtag_interface.CAPTURE == bool(1):
                self.isr.next = self.select_wir
            elif self.ijtag_interface.SELECT == bool(0) and self.ijtag_interface.SHIFT == bool(1):
                self.isr.next = self.si
                self.so.next = self.isr
            else:
                self.so.next = self.so

        @always(self.ijtag_interface.CLOCK.posedge)
        def update_ff():
            if self.ijtag_interface.RESET == bool(0):
                self.select_wir.next = bool(0)
            elif self.ijtag_interface.SELECT == bool(0) and self.ijtag_interface.UPDATE == bool(1):
                self.select_wir.next = self.isr

        if not monitor:
            return capture_ff, update_ff
        else:
            @instance
            def monitor_si():
                print("\t\tselwir({:s}): si".format(self.path + '.' + self.name), self.si)
                while 1:
                    yield self.si
                    print("\t\tselwir({:s}): si".format(self.path + '.' + self.name), self.si)

            @instance
            def monitor_ce():
                print("\t\tselwir({:s}): CAPTURE".format(self.path + '.' + self.name), self.ijtag_interface.CAPTURE)
                while 1:
                    yield self.ijtag_interface.CAPTURE
                    print("\t\tselwir({:s}): CAPTURE".format(self.path + '.' + self.name), self.ijtag_interface.CAPTURE)

            @instance
            def monitor_se():
                print("\t\tselwir({:s}): SELECT".format(self.path + '.' + self.name), self.ijtag_interface.SELECT)
                while 1:
                    yield self.ijtag_interface.SELECT
                    print("\t\tselwir({:s}): SELECT".format(self.path + '.' + self.name), self.ijtag_interface.SELECT)

            @instance
            def monitor_ue():
                print("\t\tselwir({:s}): UPDATE".format(self.path + '.' + self.name), self.ijtag_interface.UPDATE)
                while 1:
                    yield self.ijtag_interface.UPDATE
                    print("\t\tselwir({:s}): UPDATE".format(self.path + '.' + self.name), self.ijtag_interface.UPDATE)

            @instance
            def monitor_select_wir():
                print("\t\tselwir({:s}): select_wir".format(self.path + '.' + self.name), self.select_wir)
                while 1:
                    yield self.select_wir
                    print("\t\tselwir({:s}): select_wir".format(self.path + '.' + self.name), self.select_wir)

            @instance
            def monitor_reset():
                print("\t\tselwir({:s}): RESET".format(self.path + '.' + self.name), self.ijtag_interface.RESET)
                while 1:
                    yield self.ijtag_interface.RESET
                    print("\t\tselwir({:s}): RESET".format(self.path + '.' + self.name), self.ijtag_interface.RESET)

            @instance
            def monitor_clock():
                print("\t\tselwir({:s}): CLOCK".format(self.path + '.' + self.name), self.ijtag_interface.CLOCK)
                while 1:
                    yield self.ijtag_interface.CLOCK
                    print("\t\tselwir({:s}): CLOCK".format(self.path + '.' + self.name), self.ijtag_interface.CLOCK)

            @instance
            def monitor_so():
                print("\t\tselwir({:s}): so".format(self.path + '.' + self.name), self.so)
                while 1:
                    yield self.so
                    print("\t\tselwir({:s}): so".format(self.path + '.' + self.name), self.so)

            @instance
            def monitor_isr():
                print("\t\tselwir({:s}): isr".format(self.path + '.' + self.name), self.isr)
                while 1:
                    yield self.isr
                    print("\t\tselwir({:s}): isr".format(self.path + '.' + self.name), self.isr)

            return monitor_si, monitor_ce, monitor_se, monitor_ue, monitor_select_wir, monitor_reset, \
                   monitor_clock, monitor_so, capture_ff, update_ff, \
                   monitor_isr

    @staticmethod
    def convert():
        """
        Convert the myHDL design into VHDL and Verilog
        :return:
        """
        si = Signal(bool(0))
        so = Signal(bool(0))
        select_wir = Signal(bool(0))
        ijtag_interface = IJTAGInterface()

        selwir_inst = SELWIR('TOP', 'SELWIR0', si, ijtag_interface, so, select_wir)

        selwir_inst.toVerilog()
        selwir_inst.toVHDL()

    @staticmethod
    @block
    def testbench(monitor=False):
        """
        Test bench interface for a quick test of the operation of the design
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """
        si = Signal(bool(0))
        so = Signal(bool(0))
        select_wir = Signal(bool(0))
        ijtag_interface = IJTAGInterface()
        si_data = Signal(bool(0))
        so_data = Signal(bool(0))

        selwir_inst = SELWIR('TOP', 'SELWIR0', si, ijtag_interface, so, select_wir)

        @always(delay(10))
        def clkgen():
            ijtag_interface.CLOCK.next = not ijtag_interface.CLOCK

        @instance
        def stimulus():
            """
            Not true IJTAG protocol, but used to exercise the state machine with the fewest cycles
            :return:
            """
            H = bool(1)
            L = bool(0)
            # Reset the instrument
            ijtag_interface.RESET.next = bool(0)
            yield delay(10)
            ijtag_interface.RESET.next = bool(1)
            yield delay(10)

            # Start the Capture transition operation
            yield ijtag_interface.CLOCK.posedge
            # Write Capture value
            ijtag_interface.CAPTURE.next = H
            yield ijtag_interface.CLOCK.negedge
            yield ijtag_interface.CLOCK.posedge
            # Write Shift value
            ijtag_interface.CAPTURE.next = L
            ijtag_interface.SHIFT.next = H
            yield ijtag_interface.CLOCK.negedge
            si.next = bool(0)  # First scan
            yield ijtag_interface.CLOCK.posedge
            yield ijtag_interface.CLOCK.negedge

            # Write Update value
            ijtag_interface.SHIFT.next = L
            ijtag_interface.UPDATE.next = H
            yield ijtag_interface.CLOCK.negedge
            yield ijtag_interface.CLOCK.posedge
            assert(so == bool(0))
            assert(select_wir == bool(0))

            # Start the Capture transition operation
            yield ijtag_interface.CLOCK.posedge
            # Write Capture value
            ijtag_interface.CAPTURE.next = H
            yield ijtag_interface.CLOCK.negedge
            yield ijtag_interface.CLOCK.posedge
            # Write Shift value
            ijtag_interface.CAPTURE.next = L
            ijtag_interface.SHIFT.next = H
            yield ijtag_interface.CLOCK.negedge
            si.next = bool(1)  # Second scan
            yield ijtag_interface.CLOCK.posedge
            yield ijtag_interface.CLOCK.negedge

            # Write Update value
            ijtag_interface.SHIFT.next = L
            ijtag_interface.UPDATE.next = H
            yield ijtag_interface.CLOCK.negedge
            yield ijtag_interface.CLOCK.posedge
            assert (so == bool(0))
            assert (select_wir == bool(1))

            # Start the Capture transition operation
            yield ijtag_interface.CLOCK.posedge
            # Write Capture value
            ijtag_interface.CAPTURE.next = H
            yield ijtag_interface.CLOCK.negedge
            yield ijtag_interface.CLOCK.posedge
            # Write Shift value
            ijtag_interface.CAPTURE.next = L
            ijtag_interface.SHIFT.next = H
            yield ijtag_interface.CLOCK.negedge
            si.next = bool(0) # Third scan
            yield ijtag_interface.CLOCK.posedge
            yield ijtag_interface.CLOCK.negedge

            # Write Update value
            ijtag_interface.SHIFT.next = L
            ijtag_interface.UPDATE.next = H
            yield ijtag_interface.CLOCK.negedge
            yield ijtag_interface.CLOCK.posedge
            assert (so == bool(1))
            assert (select_wir == bool(0))

            raise StopSimulation()

        return selwir_inst.selwir_rtl(monitor=monitor), clkgen, stimulus


if __name__ == '__main__':
    tb = SELWIR.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    SELWIR.convert()
