"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
from hdl.standards.s1500.wsp import wsp
import os
import os.path

period = 20  # clk frequency = 50 MHz


@block
def wir(path, name, wsi, wsp, wso, wr_list, user_list, wr_select_list, dr_select_list, monitor=False):
    """
    Wrapper Instruction Register Logic
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param wsi: Wrapper Scan In Port
    :param wsp: Wrapper Scan Port instance
    :param wso: Wrapper Scan Out Port
    :param wr_list: A list of strings defining the Wrapper 1500 instructions as per the standard
    :param user_list: A list of strings defining the instructions for the user defined data registers
    :param wr_select_list: Signal(intbv(0)[len(wr_list):]) to use as 1500 wrapper instruction signals
    :param dr_select_list: Signal(intbv(0)[len(user_list):]) to use as user instruction signals
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    wr_instr_map = {}
    if len(wr_select_list) != len(wr_list):
        raise AssertionError("The len of the wr_select_list does not match the len of the wr_list!")
    if len(dr_select_list) != len(user_list):
        raise AssertionError("The len of the dr_select_list does not match the len of the user_list!")
    if 'WS_BYPASS' not in wr_list:
        raise AssertionError("Required WS_BYPASS instruction was not provided!")
    width = len(bin(intbv(0, min=0, max=(len(wr_list) + len(user_list))).max))
    isr = Signal(intbv(0)[width:])
    dr = Signal(intbv(0)[width:])

    @always(wsp.WRCK.posedge)
    def capture_ff():
        if wsp.SelectWIR == bool(1) and wsp.CaptureWR == bool(1):
            for i in range(width):
                isr.next[i] = dr[i]
        elif wsp.SelectWIR == bool(1) and wsp.ShiftWR == bool(1):
            for i in range(width):
                if i == 0:
                    wso.next = isr[i]
                elif i == width - 1:
                    isr.next[i] = wsi
                    isr.next[i-1] = isr[i]
                else:
                    isr.next[i-1] = isr[i]
        else:
            wso.next = wso

    @always(wsp.WRCK.posedge)
    def update_ff():
        if wsp.WRSTN == bool(0):
            dr.next = intbv(0)[width:]
        elif wsp.SelectWIR == bool(1) and wsp.UpdateWR == bool(1):
            for i in range(width):
                dr.next[i] = isr[i]

    @always_comb
    def decode_instr():
        for i in range(len(wr_select_list)):
            wr_select_list.next[i] = bool(0)
        for i in range(len(dr_select_list)):
            dr_select_list.next[i] = bool(0)

        if dr < (len(wr_list) + len(user_list)):
            if dr < len(wr_list):
                wr_select_list.next[dr] = bool(1)
            else:
                dr_select_list.next[dr - len(wr_list)] = bool(1)
        else:
            raise AssertionError("decode_instr: Invalid instruction detected!", bin(dr))

    if not monitor:
        return capture_ff, update_ff, decode_instr
    else:
        @instance
        def monitor_wsi():
            print("\t\twir({:s}): wsi".format(path + '.' + name), wsi)
            while 1:
                yield wsi
                print("\t\twir({:s}): wsi".format(path + '.' + name), wsi)

        @instance
        def monitor_wso():
            print("\t\twir({:s}): wso".format(path + '.' + name), wso)
            while 1:
                yield wso
                print("\t\twir({:s}): wso".format(path + '.' + name), wso)

        @instance
        def monitor_wr_list():
            print("\t\twir({:s}): wr_list".format(path + '.' + name), wr_list)
            while 1:
                yield wr_list
                print("\t\twir({:s}): wr_list".format(path + '.' + name), wr_list)

        @instance
        def monitor_user_list():
            print("\t\twir({:s}): user_list".format(path + '.' + name), user_list)
            while 1:
                yield user_list
                print("\t\twir({:s}): user_list".format(path + '.' + name), user_list)

        @instance
        def monitor_isr():
            print("\t\twir({:s}): isr".format(path + '.' + name), isr)
            while 1:
                yield isr
                print("\t\twir({:s}): isr".format(path + '.' + name), isr)

        @instance
        def monitor_dr():
            print("\t\twir({:s}): dr".format(path + '.' + name), dr)
            while 1:
                yield dr
                print("\t\twir({:s}): dr".format(path + '.' + name), dr)

        return monitor_wsi, monitor_wso,\
            capture_ff, update_ff, decode_instr,\
            monitor_isr, monitor_dr


@block
def wir_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    H = bool(1)
    L = bool(0)
    wsi = Signal(bool(0))
    wsp_inst = wsp()
    wsp_inst.SelectWIR = Signal(bool(1))
    wso = Signal(bool(0))
    wr_list = ['WS_BYPASS', 'WS_EXTEST', 'WS_INTEST']
    user_list = ['MBIST1', 'MBIST2', 'MBIST3']
    wr_select_list = Signal(intbv(0)[len(wr_list):])
    dr_select_list = Signal(intbv(0)[len(user_list):])
    # ws_bypass = [L, L, L]
    # ws_extest = [H, L, L]
    # ws_intest = [L, H, L]
    # mbist1 = [H, H, L]
    # mbist2 = [L, L, H]
    # mbist3 = [H, L, H]
    ws_bypass = [Signal(bool(0)), Signal(bool(0)), Signal(bool(0))]
    ws_extest = [Signal(bool(1)), Signal(bool(0)), Signal(bool(0))]
    ws_intest = [Signal(bool(0)), Signal(bool(1)), Signal(bool(0))]
    mbist1 = [Signal(bool(1)), Signal(bool(1)), Signal(bool(0))]
    mbist2 = [Signal(bool(0)), Signal(bool(0)), Signal(bool(1))]
    mbist3 = [Signal(bool(1)), Signal(bool(0)), Signal(bool(1))]
    width = len(bin(intbv(0, min=0, max=(len(wr_list) + len(user_list))).max))

    wir_inst = wir('TOP', 'WIR0', wsi, wsp_inst, wso, wr_list, user_list, wr_select_list, dr_select_list,
                   monitor=monitor)

    @instance
    def clkgen():
        while True:
            wsp_inst.WRCK.next = not wsp_inst.WRCK
            yield delay(period // 2)

    # print simulation data to file
    file_data = open("wir_tb.csv", 'w')  # file for saving data
    # print header to file
    print("{0},{1},{2},{3},{4},{5}".format("wsi", "CaptureWR", "ShiftWR", "UpdateWR", "SelectWIR",
                                               "wso"),
          file=file_data)

    # print data on each tap_interface.ClockDR
    @always(wsp_inst.WRCK.posedge)
    def print_data():
        """
        """
        # print in file
        # print.format is not supported in MyHDL 1.0
        print(wsi, ",", wsp_inst.CaptureWR, ",", wsp_inst.ShiftWR, ",",
              wsp_inst.UpdateWR, ",", wsp_inst.SelectWIR, ",", wso,
              file=file_data)

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
        print("width = ", width)
        for i in range(width):
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
        for i in range(width):
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
        for i in range(width):
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
        for i in range(width):
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
        for i in range(width):
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
        for i in range(width):
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

    return wir_inst, clkgen, stimulus, print_data


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
    wr_select_list = Signal(intbv(0)[len(wr_list):])
    dr_select_list = Signal(intbv(0)[len(user_list):])

    wir_inst = wir('TOP', 'WIR0', wsi, wsp_inst, wso, wr_list, user_list, wr_select_list, dr_select_list,
                   monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    wir_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="wir")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    wir_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="wir")
    tb = wir_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="wir_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="wir_tb")


def main():
    tb = wir_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
