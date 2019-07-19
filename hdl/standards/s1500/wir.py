"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
from hdl.standards.s1500.wsp import wsp
import os
import os.path


class wir:
    def __init__(self, path, name, wsi, wsp, select_wir, wso, wr_list, user_list, wr_select_list, dr_select_list):
        """
        Wrapper Instruction Register Logic
        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logger (path instance)
        :param wsi: Wrapper Scan In Port
        :param wsp: Wrapper Scan Port instance
        :param select_wir: SelectWIR signal to activate access to WIR
        :param wso: Wrapper Scan Out Port
        :param wr_list: A list of strings defining the Wrapper 1500 instructions as per the standard
        :param user_list: A list of strings defining the instructions for the user defined data registers
        :param wr_select_list: [Signal(bool(0) for _ in range(len(wr_list)] to use as 1500 wrapper instruction signals
        :param dr_select_list: [Signal(bool(0) for _ in range(len(user_list)] to use as user instruction signals
        """
        self.path = path
        self.name = name
        self.wsi = wsi
        self.wsp = wsp
        self.select_wir = select_wir
        self.wso = wso
        self.wr_list = wr_list
        self.user_list = user_list
        self.wr_instr_map = {}
        self.wr_select_list = wr_select_list
        if len(wr_select_list) != len(wr_list):
            raise AssertionError("The len of the wr_select_list does not match the len of the wr_list!")
        for i in range(len(wr_select_list)):
            if not isinstance(wr_select_list[i], SignalType):
                raise AssertionError("wr_select_list[{:d}] is not a Signal(bool(0)) type!".format(i))
        self.dr_select_list = dr_select_list
        if len(dr_select_list) != len(user_list):
            raise AssertionError("The len of the dr_select_list does not match the len of the user_list!")
        for i in range(len(dr_select_list)):
            if not isinstance(dr_select_list[i], SignalType):
                raise AssertionError("dr_select_list[{:d}] is not a Signal(bool(0)) type!".format(i))
        if 'WS_BYPASS' not in wr_list:
            raise AssertionError("Required WS_BYPASS instruction was not provided!")
        self.width = len(bin(intbv(0, min=0, max=(len(self.wr_list) + len(self.user_list))).max))
        self.isr = Signal(intbv(0)[self.width:])
        self.dr = Signal(intbv(0)[self.width:])

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
        return self.wir_rtl(monitor=monitor)

    @block
    def wir_rtl(self, monitor=False):
        """
        The logic for the Wrapper Instruction Register
        :return: The generator methods performing the logic decisions
        """
        @always(self.wsp.WRCK.posedge)
        def capture_ff():
            if self.select_wir == bool(1) and self.wsp.CaptureWR == bool(1):
                for i in range(self.width):
                    self.isr.next[i] = self.dr[i]
            elif self.select_wir == bool(1) and self.wsp.ShiftWR == bool(1):
                for i in range(self.width):
                    if i == 0:
                        self.wso.next = self.isr[i]
                    elif i == self.width - 1:
                        self.isr.next[i] = self.wsi
                        self.isr.next[i-1] = self.isr[i]
                    else:
                        self.isr.next[i-1] = self.isr[i]
            else:
                self.wso.next = self.wso

        @always(self.wsp.WRCK.posedge)
        def update_ff():
            if self.wsp.WRSTN == bool(0):
                self.dr.next = intbv(0)[self.width:]
            elif self.select_wir == bool(1) and self.wsp.UpdateWR == bool(1):
                for i in range(self.width):
                    self.dr.next[i] = self.isr[i]

        @always_comb
        def decode_instr():
            for i in range(len(self.wr_select_list)):
                self.wr_select_list[i].next = bool(0)
            for i in range(len(self.dr_select_list)):
                self.dr_select_list[i].next = bool(0)

            if self.dr < (len(self.wr_list) + len(self.user_list)):
                if self.dr < len(self.wr_list):
                    self.wr_select_list[self.dr].next = bool(1)
                else:
                    self.dr_select_list[self.dr - len(self.wr_list)].next = bool(1)
            else:
                raise AssertionError("decode_instr: Invalid instruction detected!", bin(self.dr))

        if not monitor:
            return capture_ff, update_ff, decode_instr
        else:
            @instance
            def monitor_wsi():
                print("\t\twir({:s}): wsi".format(self.path + '.' + self.name), self.wsi)
                while 1:
                    yield self.wsi
                    print("\t\twir({:s}): wsi".format(self.path + '.' + self.name), self.wsi)

            @instance
            def monitor_wso():
                print("\t\twir({:s}): wso".format(self.path + '.' + self.name), self.wso)
                while 1:
                    yield self.wso
                    print("\t\twir({:s}): wso".format(self.path + '.' + self.name), self.wso)

            @instance
            def monitor_select_wir():
                print("\t\twir({:s}): select_wir".format(self.path + '.' + self.name), self.select_wir)
                while 1:
                    yield self.select_wir
                    print("\t\twir({:s}): select_wir".format(self.path + '.' + self.name), self.select_wir)

            @instance
            def monitor_wr_list():
                print("\t\twir({:s}): wr_list".format(self.path + '.' + self.name), self.wr_list)
                while 1:
                    yield self.wr_list
                    print("\t\twir({:s}): wr_list".format(self.path + '.' + self.name), self.wr_list)

            @instance
            def monitor_user_list():
                print("\t\twir({:s}): user_list".format(self.path + '.' + self.name), self.user_list)
                while 1:
                    yield self.user_list
                    print("\t\twir({:s}): user_list".format(self.path + '.' + self.name), self.user_list)

            @instance
            def monitor_isr():
                print("\t\twir({:s}): isr".format(self.path + '.' + self.name), self.isr)
                while 1:
                    yield self.isr
                    print("\t\twir({:s}): isr".format(self.path + '.' + self.name), self.isr)

            @instance
            def monitor_dr():
                print("\t\twir({:s}): dr".format(self.path + '.' + self.name), self.dr)
                while 1:
                    yield self.dr
                    print("\t\twir({:s}): dr".format(self.path + '.' + self.name), self.dr)

            return monitor_wsi, monitor_wso, monitor_select_wir,\
                capture_ff, update_ff, decode_instr,\
                monitor_isr, monitor_dr

    def get_width(self):
        return self.width

    @staticmethod
    def convert():
        """
        Convert the myHDL design into VHDL and Verilog
        :return:
        """
        wsi = Signal(bool(0))
        wsp_inst = wsp()
        select_wir = Signal(bool(1))
        wso = Signal(bool(0))
        wr_list = ['WS_BYPASS', 'WS_EXTEST', 'WS_INTEST']
        user_list = ['MBIST1', 'MBIST2', 'MBIST3']
        wr_select_list = [Signal(bool(0)) for _ in range(len(wr_list))]
        dr_select_list = [Signal(bool(0)) for _ in range(len(user_list))]

        wir_inst = wir('TOP', 'WIR0', wsi, wsp_inst, select_wir, wso, wr_list, user_list, wr_select_list, dr_select_list)

        wir_inst.toVerilog()
        wir_inst.toVHDL()

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
        wsi = Signal(bool(0))
        wsp_inst = wsp()
        select_wir = Signal(bool(1))
        wso = Signal(bool(0))
        wr_list = ['WS_BYPASS', 'WS_EXTEST', 'WS_INTEST']
        user_list = ['MBIST1', 'MBIST2', 'MBIST3']
        wr_select_list = [Signal(bool(0)) for _ in range(len(wr_list))]
        dr_select_list = [Signal(bool(0)) for _ in range(len(user_list))]
        ws_bypass = [L, L, L]
        ws_extest = [H, L, L]
        ws_intest = [L, H, L]
        mbist1 = [H, H, L]
        mbist2 = [L, L, H]
        mbist3 = [H, L, H]

        wir_inst = wir('TOP', 'WIR0', wsi, wsp_inst, select_wir, wso, wr_list, user_list, wr_select_list, dr_select_list)

        @always(delay(10))
        def clkgen():
            wsp_inst.WRCK.next = not wsp_inst.WRCK

        @instance
        def stimulus():
            """
            Perform instruction decoding for various instructions
            :return:
            """
            # Reset the WIR
            wsp_inst.WRSTN.next = bool(0)
            yield delay(10)
            wsp_inst.WRSTN.next = bool(1)
            yield delay(10)
            # Start with WS_BYPASS instruction
            # Start the Capture transition operation
            yield wsp_inst.WRCK.posedge
            # Write Capture value
            wsp_inst.CaptureWR.next = H
            yield wsp_inst.WRCK.negedge
            yield wsp_inst.WRCK.posedge
            # Write Shift value
            wsp_inst.CaptureWR.next = L
            wsp_inst.ShiftWR.next = H
            yield wsp_inst.WRCK.negedge
            print("wir_inst.get_width() = ", wir_inst.get_width())
            for i in range(wir_inst.get_width()):
                wsi.next = ws_bypass[i]
                yield wsp_inst.WRCK.posedge
                yield wsp_inst.WRCK.negedge
                assert(wso == ws_bypass[i])
            # Write Update value
            wsp_inst.ShiftWR.next = L
            wsp_inst.UpdateWR.next = H
            yield wsp_inst.WRCK.negedge
            yield wsp_inst.WRCK.posedge
            assert(wr_select_list[0] == H)  # WS_BYPASS selected
            assert(wr_select_list[1] == L)  # WS_EXTEST deselected
            assert(wr_select_list[2] == L)  # WS_INTEST deselected
            for i in range(1, len(dr_select_list)):
                assert(dr_select_list[i] == L)

            # Start with WS_EXTEST instruction
            # Start the Capture transition operation
            yield wsp_inst.WRCK.posedge
            # Write Capture value
            wsp_inst.CaptureWR.next = H
            wsp_inst.UpdateWR.next = L
            yield wsp_inst.WRCK.negedge
            yield wsp_inst.WRCK.posedge
            # Write Shift value
            wsp_inst.CaptureWR.next = L
            wsp_inst.ShiftWR.next = H
            yield wsp_inst.WRCK.negedge
            for i in range(wir_inst.get_width()):
                wsi.next = ws_extest[i]
                yield wsp_inst.WRCK.posedge
                yield wsp_inst.WRCK.negedge
                assert(wso == ws_bypass[i])
            # Write Update value
            wsp_inst.ShiftWR.next = L
            wsp_inst.UpdateWR.next = H
            yield wsp_inst.WRCK.negedge
            yield wsp_inst.WRCK.posedge
            assert(wr_select_list[0] == L)  # WS_BYPASS deselected
            assert(wr_select_list[1] == H)  # WS_EXTEST selected
            assert(wr_select_list[2] == L)  # WS_INTEST deselected
            for i in range(1, len(dr_select_list)):
                assert(dr_select_list[i] == L)

            # Start with WS_INTEST instruction
            # Start the Capture transition operation
            yield wsp_inst.WRCK.posedge
            # Write Capture value
            wsp_inst.CaptureWR.next = H
            wsp_inst.UpdateWR.next = L
            yield wsp_inst.WRCK.negedge
            yield wsp_inst.WRCK.posedge
            # Write Shift value
            wsp_inst.CaptureWR.next = L
            wsp_inst.ShiftWR.next = H
            yield wsp_inst.WRCK.negedge
            for i in range(wir_inst.get_width()):
                wsi.next = ws_intest[i]
                yield wsp_inst.WRCK.posedge
                yield wsp_inst.WRCK.negedge
                assert(wso == ws_extest[i])
            # Write Update value
            wsp_inst.ShiftWR.next = L
            wsp_inst.UpdateWR.next = H
            yield wsp_inst.WRCK.negedge
            yield wsp_inst.WRCK.posedge
            assert(wr_select_list[0] == L)  # WS_BYPASS deselected
            assert(wr_select_list[1] == L)  # WS_EXTEST deselected
            assert(wr_select_list[2] == H)  # WS_INTEST selected
            for i in range(1, len(dr_select_list)):
                assert(dr_select_list[i] == L)

            # Start with MBIST1 instruction
            # Start the Capture transition operation
            yield wsp_inst.WRCK.posedge
            # Write Capture value
            wsp_inst.CaptureWR.next = H
            wsp_inst.UpdateWR.next = L
            yield wsp_inst.WRCK.negedge
            yield wsp_inst.WRCK.posedge
            # Write Shift value
            wsp_inst.CaptureWR.next = L
            wsp_inst.ShiftWR.next = H
            yield wsp_inst.WRCK.negedge
            for i in range(wir_inst.get_width()):
                wsi.next = mbist1[i]
                yield wsp_inst.WRCK.posedge
                yield wsp_inst.WRCK.negedge
                assert(wso == ws_intest[i])
            # Write Update value
            wsp_inst.ShiftWR.next = L
            wsp_inst.UpdateWR.next = H
            yield wsp_inst.WRCK.negedge
            yield wsp_inst.WRCK.posedge
            assert(wr_select_list[0] == L)  # WS_BYPASS deselected
            assert(wr_select_list[1] == L)  # WS_EXTEST deselected
            assert(wr_select_list[2] == L)  # WS_INTEST deselected
            assert(dr_select_list[0] == H)  # MBIST1 selected
            assert(dr_select_list[1] == L)  # MBIST2 deselected
            assert(dr_select_list[2] == L)  # MBIST3 deselected

            # Start with MBIST2 instruction
            # Start the Capture transition operation
            yield wsp_inst.WRCK.posedge
            # Write Capture value
            wsp_inst.CaptureWR.next = H
            wsp_inst.UpdateWR.next = L
            yield wsp_inst.WRCK.negedge
            yield wsp_inst.WRCK.posedge
            # Write Shift value
            wsp_inst.CaptureWR.next = L
            wsp_inst.ShiftWR.next = H
            yield wsp_inst.WRCK.negedge
            for i in range(wir_inst.get_width()):
                wsi.next = mbist2[i]
                yield wsp_inst.WRCK.posedge
                yield wsp_inst.WRCK.negedge
                assert(wso == mbist1[i])
            # Write Update value
            wsp_inst.ShiftWR.next = L
            wsp_inst.UpdateWR.next = H
            yield wsp_inst.WRCK.negedge
            yield wsp_inst.WRCK.posedge
            assert(wr_select_list[0] == L)  # WS_BYPASS deselected
            assert(wr_select_list[1] == L)  # WS_EXTEST deselected
            assert(wr_select_list[2] == L)  # WS_INTEST deselected
            assert(dr_select_list[0] == L)  # MBIST1 deselected
            assert(dr_select_list[1] == H)  # MBIST2 selected
            assert(dr_select_list[2] == L)  # MBIST3 deselected

            # Start with MBIST3 instruction
            # Start the Capture transition operation
            yield wsp_inst.WRCK.posedge
            # Write Capture value
            wsp_inst.CaptureWR.next = H
            wsp_inst.UpdateWR.next = L
            yield wsp_inst.WRCK.negedge
            yield wsp_inst.WRCK.posedge
            # Write Shift value
            wsp_inst.CaptureWR.next = L
            wsp_inst.ShiftWR.next = H
            yield wsp_inst.WRCK.negedge
            for i in range(wir_inst.get_width()):
                wsi.next = mbist3[i]
                yield wsp_inst.WRCK.posedge
                yield wsp_inst.WRCK.negedge
                assert(wso == mbist2[i])
            # Write Update value
            wsp_inst.ShiftWR.next = L
            wsp_inst.UpdateWR.next = H
            yield wsp_inst.WRCK.negedge
            yield wsp_inst.WRCK.posedge
            wsp_inst.UpdateWR.next = L
            yield wsp_inst.WRCK.negedge
            yield wsp_inst.WRCK.posedge
            assert(wr_select_list[0] == L)  # WS_BwspYPASS deselected
            assert(wr_select_list[1] == L)  # WS_EXTEST deselected
            assert(wr_select_list[2] == L)  # WS_INTEST deselected
            assert(dr_select_list[0] == L)  # MBIST1 deselected
            assert(dr_select_list[1] == L)  # MBIST2 deselected
            assert(dr_select_list[2] == H)  # MBIST3 selected

            raise StopSimulation()

        return wir_inst.wir_rtl(monitor=monitor), clkgen, stimulus


if __name__ == '__main__':
    tb = wir.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    wir.convert()
