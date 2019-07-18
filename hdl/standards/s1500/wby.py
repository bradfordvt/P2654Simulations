"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import os
import os.path
from hdl.standards.s1500.wsp import wsp


class wby:
    """
    This class implements the logic for the WBY (Wrapper BYPASS Register) of IEEE Std 1500 standard.
    """
    def __init__(self, path, name, wsi, wsp, select, wby_wso, width=1):
        """
        IEEE Std 1500 Wrapper BYPASS Register (WBY) Logic adhering to Figure 15 of the standard
        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logging (path instance)
        :param wsi: Wrapper Scan In Signal
        :param wsp: Wrapper Scan Port instance
        :param select: Select Signal for WBY from WIR (select and wsp.ShiftWB are used to create the ShiftWBY signal)
        :param wby_wso: Wrapper BYPASS Scan Out Signal
        :param width: The number of scan bits implemented by this WBY
        """
        self.path = path
        self.name = name
        self.wsi = wsi
        self.wsp = wsp
        self.select = select
        self.wby_wso = wby_wso
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
        return self.wby_rtl(monitor=monitor)

    @block
    def wby_rtl(self, monitor=False):
        """
        The logic for the WBY
        :return: The generator methods performing the logic decisions
        """

        @always(self.wsp.WRCK.posedge)
        def shiftFF():
            if self.wsp.WRSTN == bool(0):
                for i in range(self.width):
                    self.isr[i].next = bool(0)
                self.wby_wso.next = bool(0)
            elif self.select == bool(1) and self.wsp.ShiftWR == bool(1):
                for i in range(self.width):
                    if i == 0:
                        self.isr[i].next = self.wsi
                        if self.width == 1:
                            self.wby_wso.next = self.isr[i]
                    elif i == self.width - 1:
                        self.wby_wso.next = self.isr[i]
                        self.isr[i].next = self.isr[i - 1]
                    else:
                        self.isr[i].next = self.isr[i - 1]
            else:
                self.wby_wso.next = self.wby_wso

        if not monitor:
            return shiftFF
        else:
            @instance
            def monitor_wsi():
                print("\t\twby({:s}): wsi".format(self.path + '.' + self.name), self.wsi)
                while 1:
                    yield self.wsi
                    print("\t\twby({:s}): wsi".format(self.path + '.' + self.name), self.wsi)

            @instance
            def monitor_wby_wso():
                print("\t\twby({:s}): wby_wso".format(self.path + '.' + self.name), self.wby_wso)
                while 1:
                    yield self.wby_wso
                    print("\t\twby({:s}): wby_wso".format(self.path + '.' + self.name), self.wby_wso)

            @instance
            def monitor_select():
                print("\t\twby({:s}): select".format(self.path + '.' + self.name), self.select)
                while 1:
                    yield self.select
                    print("\t\twby({:s}): select".format(self.path + '.' + self.name), self.select)

            @instance
            def monitor_wsp_shiftwr():
                print("\t\twby({:s}): wsp.ShiftWR".format(self.path + '.' + self.name), self.wsp.ShiftWR)
                while 1:
                    yield self.wsp.ShiftWR
                    print("\t\twby({:s}): wsp.ShiftWR".format(self.path + '.' + self.name), self.wsp.ShiftWR)

            @instance
            def monitor_isr():
                print("\t\twby({:s}): isr".format(self.path + '.' + self.name), self.isr)
                while 1:
                    yield self.isr
                    print("\t\twby({:s}): isr".format(self.path + '.' + self.name), self.isr)

            return shiftFF, \
                monitor_wsi, monitor_wby_wso, monitor_wsp_shiftwr, monitor_select, \
                monitor_isr

    @staticmethod
    def convert():
        """
        Convert the myHDL design into VHDL and Verilog
        :return:
        """
        width = 1
        wsi = Signal(bool(0))
        wby_wso = Signal(bool(0))
        select = Signal(bool(0))
        wsp_inst = wsp()
        wsp_inst.WRSTN.next = bool(1)
        yield delay(1)

        wby_inst = wby("DEMO", "WBY0", wsi, wsp_inst, select, wby_wso, width=width)

        wby_inst.toVerilog()
        wby_inst.toVHDL()

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
        width = 1
        data = [H, L, H, H, L]
        expect = [L, H, L, H, H, L]
        wsi = Signal(bool(0))
        wby_wso = Signal(bool(0))
        select = Signal(bool(0))
        wsp_inst = wsp()

        wby_inst = wby("DEMO", "WBY0", wsi, wsp_inst, select, wby_wso, width=width)

        @always(delay(10))
        def clkgen():
            wsp_inst.WRCK.next = not wsp_inst.WRCK

        @instance
        def stimulus():
            """
            Test the WBY shift operations
            :return:
            """
            # Reset the instrument
            wsp_inst.WRSTN.next = L
            yield delay(10)
            wsp_inst.WRSTN.next = H
            yield delay(10)
            # Write Shift value
            wsp_inst.ShiftWR.next = H
            select.next = H
            yield wsp_inst.WRCK.negedge
            for i in range(len(data)):
                wsi.next = data[i]
                yield wsp_inst.WRCK.posedge
                yield wsp_inst.WRCK.negedge
                assert(wby_wso == expect[i])
            wsi.next = L
            yield wsp_inst.WRCK.posedge
            yield wsp_inst.WRCK.negedge
            assert (wby_wso == expect[len(data)])

            raise StopSimulation()

        return wby_inst.wby_rtl(monitor=monitor), clkgen, stimulus


if __name__ == '__main__':
    tb = wby.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    wby.convert()
