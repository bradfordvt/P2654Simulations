"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import os
import os.path


class WDRmux:
    def __init__(self, path, name,
                 wby_out, mbist1_out, mbist2_out, mbist3_out,
                 wr_select_list, dr_select_list,
                 so):
        """
        MUX to control what WDR is connected to so
        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logger (path instance)
        :param wby_out: Signal Out from WBY register
        :param mbist1_out: Signal Out from MBIST1 register
        :param mbist2_out: Signal Out from MBIST2 register
        :param mbist3_out: Signal Out from MBIST3 register
        :param wr_select_list: [Signal(bool(0) for _ in range(len(wr_list)] to use as 1500 wrapper instruction signals
        :param dr_select_list: [Signal(bool(0) for _ in range(len(user_list)] to use as user instruction signals
        :param so: Signal out from WDRs to WIRMux
        """
        self.path = path
        self.name = name
        self.wby_out = wby_out
        self.mbist1_out = mbist1_out
        self.mbist2_out = mbist2_out
        self.mbist3_out = mbist3_out
        self.wr_select_list = wr_select_list
        self.dr_select_list = dr_select_list
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
        return self.wdrmux_rtl(monitor=monitor)

    @block
    def wdrmux_rtl(self, monitor=False):
        """
        The logic for the Wrapper Data Register MUX
        :return: The generator methods performing the logic decisions
        """
        @always_comb
        def mux_logic():
            if self.wr_select_list[0] == bool(1):
                self.so.next = self.wby_out
            elif self.dr_select_list[0] == bool(1):
                self.so.next = self.mbist1_out
            elif self.dr_select_list[1] == bool(1):
                self.so.next = self.mbist2_out
            elif self.dr_select_list[2] == bool(1):
                self.so.next = self.mbist3_out
            else:
                self.so.next = bool(0)

        if not monitor:
            return mux_logic
        else:
            @instance
            def monitor_wby_out():
                print("\t\tWDRmux({:s}): wby_out".format(self.path + '.' + self.name), self.wby_out)
                while 1:
                    yield self.wby_out
                    print("\t\tWDRmux({:s}): wby_out".format(self.path + '.' + self.name), self.wby_out)

            @instance
            def monitor_mbist1_out():
                print("\t\tWDRmux({:s}): mbist1_out".format(self.path + '.' + self.name), self.mbist1_out)
                while 1:
                    yield self.mbist1_out
                    print("\t\tWDRmux({:s}): mbist1_out".format(self.path + '.' + self.name), self.mbist1_out)

            @instance
            def monitor_mbist2_out():
                print("\t\tWDRmux({:s}): mbist2_out".format(self.path + '.' + self.name), self.mbist2_out)
                while 1:
                    yield self.mbist2_out
                    print("\t\tWDRmux({:s}): mbist2_out".format(self.path + '.' + self.name), self.mbist2_out)

            @instance
            def monitor_mbist3_out():
                print("\t\tWDRmux({:s}): mbist3_out".format(self.path + '.' + self.name), self.mbist3_out)
                while 1:
                    yield self.mbist3_out
                    print("\t\tWDRmux({:s}): mbist3_out".format(self.path + '.' + self.name), self.mbist3_out)

            @instance
            def monitor_so():
                print("\t\tWDRmux({:s}): so".format(self.path + '.' + self.name), self.so)
                while 1:
                    yield self.so
                    print("\t\tWDRmux({:s}): so".format(self.path + '.' + self.name), self.so)

            @instance
            def monitor_wr_select_list():
                print("\t\tWDRmux({:s}): wr_select_list".format(self.path + '.' + self.name), self.wr_select_list)
                while 1:
                    yield self.wr_select_list
                    print("\t\tWDRmux({:s}): wr_select_list".format(self.path + '.' + self.name), self.wr_select_list)

            @instance
            def monitor_dr_select_list():
                print("\t\tWDRmux({:s}): dr_select_list".format(self.path + '.' + self.name), self.dr_select_list)
                while 1:
                    yield self.dr_select_list
                    print("\t\tWDRmux({:s}): dr_select_list".format(self.path + '.' + self.name), self.dr_select_list)

            return mux_logic, monitor_wby_out, monitor_mbist1_out,\
                monitor_mbist2_out, monitor_mbist3_out, monitor_so,\
                monitor_wr_select_list, monitor_dr_select_list

    @staticmethod
    def convert():
        """
        Convert the myHDL design into VHDL and Verilog
        :return:
        """
        wby_out = Signal(bool(0))
        mbist1_out = Signal(bool(0))
        mbist2_out = Signal(bool(0))
        mbist3_out = Signal(bool(0))
        so_out = Signal(bool(0))
        wr_list = ['WS_BYPASS']
        user_list = ['MBIST1', 'MBIST2', 'MBIST3']
        wr_select_list = [Signal(bool(0)) for _ in range(len(wr_list))]
        dr_select_list = [Signal(bool(0)) for _ in range(len(user_list))]

        wdrmux_inst = WDRmux('TOP', 'WDRMUX0', wby_out, mbist1_out, mbist2_out, mbist3_out,
                             wr_select_list, dr_select_list, so_out)

        wdrmux_inst.toVerilog()
        wdrmux_inst.toVHDL()

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
        wby_out = Signal(bool(0))
        mbist1_out = Signal(bool(0))
        mbist2_out = Signal(bool(0))
        mbist3_out = Signal(bool(0))
        so_out = Signal(bool(0))
        wr_list = ['WS_BYPASS']
        user_list = ['MBIST1', 'MBIST2', 'MBIST3']
        wr_select_list = [Signal(bool(0)) for _ in range(len(wr_list))]
        dr_select_list = [Signal(bool(0)) for _ in range(len(user_list))]

        wdrmux_inst = WDRmux('TOP', 'WDRMUX0', wby_out, mbist1_out, mbist2_out, mbist3_out,
                             wr_select_list, dr_select_list, so_out)

        @instance
        def stimulus():
            """
            Perform instruction decoding for various instructions
            :return:
            """
            wr_select_list[0].next = bool(1)
            yield delay(1)
            assert(so_out == bool(0))
            wby_out.next = bool(1)
            yield delay(1)
            assert(so_out == bool(1))
            wby_out.next = bool(0)
            yield delay(1)
            assert(so_out == bool(0))
            wr_select_list[0].next = bool(0)
            dr_select_list[0].next = bool(1)
            yield delay(1)
            assert(so_out == bool(0))
            mbist1_out.next = bool(1)
            yield delay(1)
            assert(so_out == bool(1))
            mbist1_out.next = bool(0)
            yield delay(1)
            assert(so_out == bool(0))
            wr_select_list[0].next = bool(0)
            dr_select_list[0].next = bool(0)
            dr_select_list[1].next = bool(1)
            yield delay(1)
            assert(so_out == bool(0))
            mbist2_out.next = bool(1)
            yield delay(1)
            assert(so_out == bool(1))
            mbist2_out.next = bool(0)
            yield delay(1)
            assert(so_out == bool(0))
            wr_select_list[0].next = bool(0)
            dr_select_list[0].next = bool(0)
            dr_select_list[1].next = bool(0)
            dr_select_list[2].next = bool(1)
            yield delay(1)
            assert(so_out == bool(0))
            mbist3_out.next = bool(1)
            yield delay(1)
            assert(so_out == bool(1))
            mbist3_out.next = bool(0)
            yield delay(1)
            assert(so_out == bool(0))
            wr_select_list[0].next = bool(0)
            dr_select_list[0].next = bool(0)
            dr_select_list[1].next = bool(0)
            dr_select_list[2].next = bool(0)
            yield delay(1)
            assert(so_out == bool(0))

            raise StopSimulation()

        return wdrmux_inst.wdrmux_rtl(monitor=monitor), stimulus


if __name__ == '__main__':
    tb = WDRmux.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    WDRmux.convert()
