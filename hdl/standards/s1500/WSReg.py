"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import os
import os.path
from hdl.common.ScanRegister import ScanRegister
from hdl.standards.s1500.wsp import wsp

period = 20  # clk frequency = 50 MHz


@block
def WSReg(path, name, si, wsp_interface, select, so, di, do, dr_width=9, monitor=False):
    """
    Creates a Module SReg for IEEE 1687 with the following interface:
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logging (path instance)
    :param si: ScanInPort
    :param wsp_interface: Wrapper Serial Port (WSP) interface defining the control signals for this register
    :param select: DR_Select signal from WIR for this register
    :param so: ScanOutPort
    :param di: DataInPort Signal(intbv(0)[dr_width:])
    :param do: DataOutPort Signal(intbv(0)[dr_width:])
    :param dr_width: The width of the DI/DO interfaces and size of the SR
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    myselect = Signal(bool(0))
    sr_inst = ScanRegister(
                            path + '.' + name,
                            'ScanRegister' + name[-1],
                            si,
                            wsp_interface.CaptureWR,
                            wsp_interface.ShiftWR,
                            wsp_interface.UpdateWR,
                            myselect,
                            wsp_interface.WRSTN,
                            wsp_interface.WRCK,
                            so,
                            di,
                            do,
                            width=dr_width,
                            monitor=monitor
                            )

    @always_comb
    def select_logic():
        myselect.next = not wsp_interface.SelectWIR and select

    if monitor == False:
        return sr_inst, select_logic
    else:
        @instance
        def monitor_si():
            print("\t\tSReg({:s}): si".format(path + "." + name), si)
            while 1:
                yield si
                print("\t\tSReg({:s}): si".format(path + "." + name), si)

        @instance
        def monitor_so():
            print("\t\tSReg({:s}): so".format(path + "." + name), so)
            while 1:
                yield so
                print("\t\tSReg({:s}) so:".format(path + "." + name), so)
        @instance
        def monitor_di():
            print("\t\tSReg({:s}): di".format(path + "." + name), di)
            while 1:
                yield di
                print("\t\tSReg({:s}): si".format(path + "." + name), di)

        @instance
        def monitor_do():
            print("\t\tSReg({:s}): do".format(path + "." + name), do)
            while 1:
                yield do
                print("\t\tSReg({:s}) do:".format(path + "." + name), do)

        return monitor_si, monitor_so, monitor_di, monitor_do, sr_inst, select_logic


@block
def WSReg_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    dr_width = 9
    si = Signal(bool(0))
    so = Signal(bool(0))
    di = Signal(intbv('010100000')[dr_width:])
    do = Signal(intbv(0)[dr_width:])
    si_data = Signal(intbv('000000101')[dr_width:])
    so_data = [Signal(bool(0)) for _ in range(dr_width)]
    wsp_interface = wsp()
    dr_select = Signal(bool(1))

    wsreg_inst = WSReg('TOP', 'WSReg0', si, wsp_interface, dr_select, so, di, do, dr_width=dr_width, monitor=monitor)

    @instance
    def clkgen():
        while True:
            wsp_interface.WRCK.next = not wsp_interface.WRCK
            yield delay(period // 2)

    # print simulation data to file
    file_data = open("WSReg_tb.csv", 'w')  # file for saving data
    # print header to file
    print("{0},{1},{2},{3},{4},{5},{6},{7}".format("si", "ce", "se", "ue", "sel", "so", "di", "do"),
          file=file_data)

    # print data on each tap_interface.ClockDR
    @always(wsp_interface.WRCK.posedge)
    def print_data():
        """
        """
        # print in file
        # print.format is not supported in MyHDL 1.0
        print(si, ",", wsp_interface.CaptureWR, ",", wsp_interface.ShiftWR, ",", wsp_interface.UpdateWR, ",",
              wsp_interface.SelectWIR, ",", so, ",", di, ",", do, file=file_data)

    @instance
    def stimulus():
        """
        Not true IJTAG protocol, but used to exercise the state machine with the fewest cycles
        :return:
        """
        H = bool(1)
        L = bool(0)
        # Reset the instrument
        wsp_interface.WRSTN.next = bool(0)
        yield delay(10)
        wsp_interface.WRSTN.next = bool(1)
        yield delay(10)
        # Start the Capture transition operation
        yield wsp_interface.WRCK.posedge
        # Write Capture value
        wsp_interface.CaptureWR.next = H
        yield wsp_interface.WRCK.negedge
        yield wsp_interface.WRCK.posedge
        # Write Shift value
        wsp_interface.CaptureWR.next = L
        wsp_interface.ShiftWR.next = H
        yield wsp_interface.WRCK.negedge
        for i in range(dr_width):
            si.next = si_data[i]
            yield wsp_interface.WRCK.posedge
            yield wsp_interface.WRCK.negedge
            print("so = ", so)
            so_data[i].next = so
        # Write Update value
        wsp_interface.ShiftWR.next = L
        wsp_interface.UpdateWR.next = H
        yield wsp_interface.WRCK.negedge
        yield wsp_interface.WRCK.posedge
        j = dr_width - 1
        print("so_data = ", so_data)
        while j > -1:
            print("so_data[", j, "] = ", so_data[j])
            if j == 5 or j == 7:
                assert (so_data[j] == bool(1))
            else:
                assert (so_data[j] == bool(0))
            j = j - 1
        print("do = ", do)
        for j in range(dr_width):
            print("do[", j, "] = ", do[j])
            if j == 0 or j == 2:
                assert (do[j] == bool(1))
            else:
                assert (do[j] == bool(0))
        assert (do == intbv('000000101'))

        raise StopSimulation()

    return wsreg_inst, clkgen, stimulus, print_data


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    dr_width = 9
    si = Signal(bool(0))
    so = Signal(bool(0))
    di = Signal(intbv('000000000')[dr_width:])
    do = Signal(intbv(0)[dr_width:])
    wsp_interface = wsp()
    dr_select = Signal(bool(1))

    wsreg_inst = WSReg('TOP', 'SReg0', si, wsp_interface, dr_select, so, di, do, dr_width=9, monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    wsreg_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SReg")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    wsreg_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SReg")
    tb = WSReg_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SReg_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SReg_tb")


def main():
    tb = WSReg_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
