"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import os
import os.path
from hdl.standards.s1500.wsp import wsp
from hdl.common.ScanRegister import ScanRegister

period = 20  # clk frequency = 50 MHz


@block
def wby(path, name, wsi, wsp_interface, select, wby_wso, width=1, monitor=False):
    """
    This class implements the logic for the WBY (Wrapper BYPASS Register) of IEEE Std 1500 standard.
    IEEE Std 1500 Wrapper BYPASS Register (WBY) Logic adhering to Figure 15 of the standard
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logging (path instance)
    :param wsi: Wrapper Scan In Signal
    :param wsp_interface: Wrapper Scan Port instance
    :param select: Select Signal for WBY from WIR (select and wsp_interface.ShiftWB are used to create
            the ShiftWBY signal)
    :param wby_wso: Wrapper BYPASS Scan Out Signal
    :param width: The number of scan bits implemented by this WBY
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    master_select = Signal(bool(0))
    D = Signal(intbv(val=0, _nrbits=width))
    Q = Signal(intbv(val=0, _nrbits=width))

    sr_inst = ScanRegister(
        path + '.' + name,
        name + '_SR',
        wsi,
        wsp_interface.CaptureWR,
        wsp_interface.ShiftWR,
        wsp_interface.UpdateWR,
        master_select,
        wsp_interface.WRSTN,
        wsp_interface.WRCK,
        wby_wso,
        D,
        Q,
        width=width,
        monitor=monitor
    )

    @always_comb
    def select_process():
        master_select.next = select and not wsp_interface.SelectWIR

    if not monitor:
        return sr_inst, select_process
    else:
        @instance
        def monitor_wsi():
            print("\t\twby({:s}): wsi".format(path + '.' + name), wsi)
            while 1:
                yield wsi
                print("\t\twby({:s}): wsi".format(path + '.' + name), wsi)

        @instance
        def monitor_wby_wso():
            print("\t\twby({:s}): wby_wso".format(path + '.' + name), wby_wso)
            while 1:
                yield wby_wso
                print("\t\twby({:s}): wby_wso".format(path + '.' + name), wby_wso)

        @instance
        def monitor_select():
            print("\t\twby({:s}): select".format(path + '.' + name), select)
            while 1:
                yield select
                print("\t\twby({:s}): select".format(path + '.' + name), select)

        @instance
        def monitor_wsp_interface_shiftwr():
            print("\t\twby({:s}): wsp_interface.ShiftWR".format(path + '.' + name), wsp_interface.ShiftWR)
            while 1:
                yield wsp_interface.ShiftWR
                print("\t\twby({:s}): wsp_interface.ShiftWR".format(path + '.' + name), wsp_interface.ShiftWR)

        return sr_inst, select_process, \
            monitor_wsi, monitor_wby_wso, monitor_wsp_interface_shiftwr, monitor_select


@block
def wby_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    hi = bool(1)
    lo = bool(0)
    width = 1
    # data = [hi, lo, hi, hi, lo]
    data = Signal(intbv('01101'))
    ldata = 5
    # expect = [lo, hi, lo, hi, hi, lo]
    expect = Signal(intbv('011010'))
    wsi = Signal(bool(0))
    wby_wso = Signal(bool(0))
    select = Signal(bool(0))
    wsp_interface_inst = wsp()

    wby_inst = wby("DEMO", "WBY0", wsi, wsp_interface_inst, select, wby_wso, width=width, monitor=monitor)

    @instance
    def clkgen():
        while True:
            wsp_interface_inst.WRCK.next = not wsp_interface_inst.WRCK
            yield delay(period // 2)

    # print simulation data to file
    file_data = open("wby_tb.csv", 'w')  # file for saving data
    # print header to file
    print("{0},{1},{2},{3},{4},{5},{6}".format("wsi", "CaptureWR", "ShiftWR", "UpdateWR", "SelectWIR", "select",
                                               "wby_wso"),
          file=file_data)

    # print data on each tap_interface.ClockDR
    @always(wsp_interface_inst.WRCK.posedge)
    def print_data():
        """
        """
        # print in file
        # print.format is not supported in MyHDL 1.0
        print(wsi, ",", wsp_interface_inst.CaptureWR, ",", wsp_interface_inst.ShiftWR, ",",
              wsp_interface_inst.UpdateWR, ",", wsp_interface_inst.SelectWIR, ",", select, ",", wby_wso,
              file=file_data)

    @instance
    def stimulus():
        """
        Not true IJTAG protocol, but used to exercise the state machine with the fewest cycles
        :return:
        """
        # Reset the instrument
        wsp_interface_inst.WRSTN.next = lo
        yield delay(10)
        wsp_interface_inst.WRSTN.next = hi
        yield delay(10)
        # Capture Value of bool(0)
        select.next = hi
        wsp_interface_inst.CaptureWR.next = hi
        yield wsp_interface_inst.WRCK.negedge
        yield wsp_interface_inst.WRCK.posedge
        # Write Shift value
        wsp_interface_inst.CaptureWR.next = lo
        wsp_interface_inst.ShiftWR.next = hi
        yield wsp_interface_inst.WRCK.negedge
        for i in range(ldata):
            wsi.next = data[i]
            yield wsp_interface_inst.WRCK.posedge
            yield wsp_interface_inst.WRCK.negedge
            assert(wby_wso == expect[i])
        wsi.next = lo
        yield wsp_interface_inst.WRCK.posedge
        yield wsp_interface_inst.WRCK.negedge
        assert (wby_wso == expect[len(data)])

        yield delay(100)

        raise StopSimulation()

    return wby_inst, clkgen, stimulus, print_data


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    width = 1
    wsi = Signal(bool(0))
    wby_wso = Signal(bool(0))
    select = Signal(bool(1))
    wsp_interface_inst = wsp()
    wsp_interface_inst.SelectWIR = Signal(bool(0))

    wby_inst = wby("DEMO", "WBY0", wsi, wsp_interface_inst, select, wby_wso, width=width, monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    wby_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="wby")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    wby_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="wby")
    tb = wby_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="wby_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="wby_tb")


def main():
    tb = wby_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
