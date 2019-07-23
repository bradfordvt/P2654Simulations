"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import os
import os.path


class WIRmux:
    def __init__(self, path, name,
                 wdr_out, wir_out,
                 select_wir,
                 so):
        """
        MUX to control what WDR is connected to so
        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logger (path instance)
        :param wdr_out: Signal Out from WDRmux logic
        :param wir_out: Signal Out from WIR register
        :param select_wir: Select Signal for WIR register
        :param so: Signal out from WIRMux
        """
        self.path = path
        self.name = name
        self.wdr_out = wdr_out
        self.wir_out = wir_out
        self.select_wir = select_wir
        self.so = so

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
        return self.wirmux_rtl(monitor=monitor)

    @block
    def wirmux_rtl(self, monitor=False):
        """
        The logic for the Wrapper Data Register MUX
        :return: The generator methods performing the logic decisions
        """
        @always_comb
        def mux_logic():
            if self.select_wir == bool(1):
                self.so.next = self.wir_out
            else:
                self.so.next = self.wdr_out

        if not monitor:
            return mux_logic
        else:
            @instance
            def monitor_wdr_out():
                print("\t\tWIRmux({:s}): wdr_out".format(self.path + '.' + self.name), self.wdr_out)
                while 1:
                    yield self.wdr_out
                    print("\t\tWIRmux({:s}): wdr_out".format(self.path + '.' + self.name), self.wdr_out)

            @instance
            def monitor_wir_out():
                print("\t\tWIRmux({:s}): wir_out".format(self.path + '.' + self.name), self.wir_out)
                while 1:
                    yield self.wir_out
                    print("\t\tWIRmux({:s}): wir_out".format(self.path + '.' + self.name), self.wir_out)

            @instance
            def monitor_select_wir():
                print("\t\tWIRmux({:s}): select_wir".format(self.path + '.' + self.name), self.select_wir)
                while 1:
                    yield self.select_wir
                    print("\t\tWIRmux({:s}): select_wir".format(self.path + '.' + self.name), self.select_wir)

            @instance
            def monitor_so():
                print("\t\tWIRmux({:s}): so".format(self.path + '.' + self.name), self.so)
                while 1:
                    yield self.so
                    print("\t\tWIRmux({:s}): so".format(self.path + '.' + self.name), self.so)

            return mux_logic, monitor_wdr_out, monitor_wir_out,\
                monitor_select_wir, monitor_so

    @staticmethod
    def convert():
        """
        Convert the myHDL design into VHDL and Verilog
        :return:
        """
        wdr_out = Signal(bool(0))
        wir_out = Signal(bool(0))
        select_wir = Signal(bool(0))
        so_out = Signal(bool(0))

        wirmux_inst = WIRmux('TOP', 'WIRMUX0', wdr_out, wir_out, select_wir, so_out)

        wirmux_inst.toVerilog()
        wirmux_inst.toVHDL()

    @staticmethod
    @block
    def testbench(monitor=False):
        """
        Test bench interface for a quick test of the operation of the design
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """
        H = bool(1)
        L = bool(0)
        wdr_out = Signal(bool(0))
        wir_out = Signal(bool(0))
        select_wir = Signal(bool(0))
        so_out = Signal(bool(0))

        wirmux_inst = WIRmux('TOP', 'WIRMUX0', wdr_out, wir_out, select_wir, so_out)

        @instance
        def stimulus():
            """
            Perform instruction decoding for various instructions
            :return:
            """
            select_wir.next = bool(1)
            yield delay(1)
            assert(so_out == bool(0))
            wir_out.next = bool(1)
            yield delay(1)
            assert(so_out == bool(1))
            wir_out.next = bool(0)
            yield delay(1)
            assert(so_out == bool(0))
            select_wir.next = bool(0)
            yield delay(1)
            assert(so_out == bool(0))
            wdr_out.next = bool(1)
            yield delay(1)
            assert(so_out == bool(1))
            wdr_out.next = bool(0)
            yield delay(1)
            assert(so_out == bool(0))

            raise StopSimulation()

        return wirmux_inst.wirmux_rtl(monitor=monitor), stimulus


if __name__ == '__main__':
    tb = WIRmux.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    WIRmux.convert()
