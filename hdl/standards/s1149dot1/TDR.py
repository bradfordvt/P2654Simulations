"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
from hdl.common.ScanRegister import ScanRegister
from hdl.standards.s1149dot1.TAPInterface import TAPInterface
import os
import os.path

period = 20  # clk frequency = 50 MHz


@block
def TDR(path, name, D, Q, scan_in, tck, tap_interface, local_reset, scan_out, select, tdr_width=9, monitor=False):
    """
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logging (path instance)
    :param D: tdr_width bit wide Signal D = Signal(intbv(0)[tdr_width:])
    :param Q: tdr_width bit wide Signal Q = Signal(intbv(0)[tdr_width:])
    :param scan_in: Input signal for data scanned into TDR
    :param tck: TAP TCK
    :param tap_interface: TAPInterface object containing:
        CaptureDR: Signal used to enable the capture of D
        ShiftDR: Signal used to shift the data out ScanOut from the TDR
        UpdateDR: Signal used to latch the TDR to Q
        Select: Signal used to activate the TDR
        Reset: Signal used to reset the Q of the TDR
        tap_interface.ClockDR: Test tap_interface.ClockDR used to synchronize the TDR to the TAP
    :param local_reset: Active low Signal used by the internal hardware to reset the TDR
    :param scan_out: Output signal where data is scanned from the TDR
    :param select: Select from TIR decoder for this register
    :param tdr_width: The number of bits contained in this register
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    master_reset = Signal(bool(1))
    master_select = Signal(bool(0))
    
    sr_inst = ScanRegister(
        path + '.' + name,
        name + '_SR',
        scan_in,
        tap_interface.CaptureDR,
        tap_interface.ShiftDR,
        tap_interface.UpdateDR,
        tap_interface.Select,
        master_reset,
        tck,
        scan_out,
        D,
        Q,
        width=tdr_width,
        monitor=monitor
    )
    
    @always_comb
    def reset_process():
        master_reset.next = local_reset and tap_interface.Reset

    @always_comb
    def select_process():
        master_select.next = tap_interface.Select and select

    if monitor == False:
        return sr_inst, reset_process, select_process
    else:
        @instance
        def monitor_scan_in():
            print("\t\tTDR({:s}): scan_in".format(path + name), scan_in)
            while 1:
                yield scan_in
                print("\t\tTDR({:s}): scan_in".format(path + name), scan_in)

        @instance
        def monitor_scan_out():
            print("\t\tTDR({:s}): scan_out".format(path + name), scan_out)
            while 1:
                yield scan_out
                print("\t\tTDR({:s}) scan_out:".format(path + name), scan_out)

        return monitor_scan_in, monitor_scan_out, sr_inst, reset_process, select_process


@block
def TDR_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    width = 9
    tck = Signal(bool(0))
    tap_interface = TAPInterface()
    si = Signal(bool(0))
    so = Signal(bool(0))
    D = Signal(intbv('010100000')[width:])
    Q = Signal(intbv(0)[width:])
    si_data = [Signal(bool(0)) for _ in range(width)]
    si_data[width - 5] = Signal(bool(1))
    si_data[width - 7] = Signal(bool(1))
    so_data = [Signal(bool(0)) for _ in range(width)]
    local_reset = Signal(bool(1))
    select = Signal(bool(1))
    t = 0
    tdr_inst = TDR('TOP', 'TDR0', D, Q, si, tck, tap_interface, local_reset, so, select, tdr_width=9, monitor=monitor)

    @instance
    def clkgen():
        while True:
            tck.next = not tck
            yield delay(period // 2)

    @instance  # reset signal
    def reset_signal():
        local_reset.next = 0
        yield delay(period)
        local_reset.next = 1

    # print simulation data to file
    file_data = open("TDR_tb.csv", 'w')  # file for saving data
    # print header to file
    print("{0},{1},{2},{3},{4},{5},{6},{7}".format("si", "CaptureDR", "ShiftDR", "UpdateDR", "Select", "so", "D", "Q"),
          file=file_data)

    # print data on each tap_interface.ClockDR
    @always(tap_interface.ClockDR.posedge)
    def print_data():
        """
        """
        # print in file
        # print.format is not supported in MyHDL 1.0
        print(si, ",", tap_interface.CaptureDR, ",", tap_interface.ShiftDR, ",", tap_interface.UpdateDR, ",",
              tap_interface.Select, ",", so, ",", D, ",", Q, file=file_data)

    @instance
    def stimulus():
        """
        Not true IJTAG protocol, but used to exercise the state machine with the fewest cycles
        :return:
        """
        H = bool(1)
        L = bool(0)
        # # Reset the instrument
        # reset.next = bool(0)
        # yield delay(period)
        # reset.next = bool(1)
        yield delay(period)
        yield tap_interface.ClockDR.negedge
        # Start the Capture transition operation
        tap_interface.CaptureDR.next = H
        yield tap_interface.ClockDR.posedge
        # Write Capture value
        yield tap_interface.ClockDR.negedge
        tap_interface.CaptureDR.next = L
        tap_interface.ShiftDR.next = H
        # yield tap_interface.ClockDR.posedge
        # Write Shift value
        # yield tap_interface.ClockDR.negedge
        for i in range(width):
            si.next = si_data[width - 1 - i]
            yield tap_interface.ClockDR.posedge
            yield tap_interface.ClockDR.negedge
            so_data[width - 1 - i].next = so
        # Write Update value
        tap_interface.ShiftDR.next = L
        tap_interface.UpdateDR.next = H
        yield tap_interface.ClockDR.posedge
        tap_interface.UpdateDR.next = L
        yield tap_interface.ClockDR.negedge
        yield tap_interface.ClockDR.posedge
        for j in range(width):
            if j == 3 or j == 1:
                assert (so_data[width - 1 - j] == bool(1))
            else:
                assert (so_data[width - 1 - j] == bool(0))
        for j in range(width):
            if j == 4 or j == 6:
                assert (Q[width - 1 - j] == bool(1))
            else:
                assert (Q[width - 1 - j] == bool(0))

        raise StopSimulation()

    return tdr_inst, clkgen, stimulus, reset_signal, print_data


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    width = 9
    tap_interface = TAPInterface()
    si = Signal(bool(0))
    so = Signal(bool(0))
    D = Signal(intbv('000000000')[width:])
    Q = Signal(intbv(0)[width:])
    local_reset = Signal(bool(1))
    tdr_inst = TDR('TOP', 'TDR0', D, Q, si, tap_interface, local_reset, so, tdr_width=9, monitor=False)
    
    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    tdr_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="TDR")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    tdr_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="TDR")
    tb = TDR_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="TDR_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="TDR_tb")


def main():
    tb = TDR_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
