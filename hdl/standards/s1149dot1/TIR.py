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
def TIR(path, name, D, Q, scan_in, tap_interface, local_reset, scan_out, tir_width=9, monitor=False):
    """
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logging (path instance)
    :param D: tir_width bit wide Signal D = Signal(intbv(0)[tir_width:])
    :param Q: tir_width bit wide Signal Q = Signal(intbv(0)[tir_width:])
    :param scan_in: Input signal for data scanned into TIR
    :param tap_interface: TAPInterface object containing:
        CaptureIR: Signal used to enable the capture of D
        ShiftIR: Signal used to shift the data out ScanOut from the TIR
        UpdateIR: Signal used to latch the TIR to Q
        Select: Signal used to activate the TIR
        Reset: Signal used to reset the Q of the TIR
        tap_interface.ClockIR: Test tap_interface.ClockIR used to synchronize the TIR to the TAP
    :param local_reset: Active low Signal used by the internal hardware to reset the TIR
    :param scan_out: Output signal where data is scanned from the TIR
    :param tir_width: The number of bits contained in this register
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    master_reset = Signal(bool(1))

    sr_inst = ScanRegister(
        path + '.' + name,
        name + '_SR',
        scan_in,
        tap_interface.CaptureIR,
        tap_interface.ShiftIR,
        tap_interface.UpdateIR,
        tap_interface.Select,
        master_reset,
        tap_interface.ClockIR,
        scan_out,
        D,
        Q,
        width=tir_width,
        monitor=monitor
    )

    @always_comb
    def reset_process():
        master_reset.next = local_reset and tap_interface.Reset

    if monitor == False:
        return sr_inst
    else:
        @instance
        def monitor_scan_in():
            print("\t\tTIR({:s}): scan_in".format(path + name), scan_in)
            while 1:
                yield scan_in
                print("\t\tTIR({:s}): scan_in".format(path + name), scan_in)

        @instance
        def monitor_scan_out():
            print("\t\tTIR({:s}): scan_out".format(path + name), scan_out)
            while 1:
                yield scan_out
                print("\t\tTIR({:s}) scan_out:".format(path + name), scan_out)

        return monitor_scan_in, monitor_scan_out, sr_inst, reset_process


@block
def TIR_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    width = 9
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
    t = 0
    tir_inst = TIR('TOP', 'TIR0', D, Q, si, tap_interface, local_reset, so, tir_width=9, monitor=monitor)

    @instance
    def clkgen():
        while True:
            tap_interface.ClockIR.next = not tap_interface.ClockIR
            yield delay(period // 2)

    @instance  # reset signal
    def reset_signal():
        local_reset.next = 0
        yield delay(period)
        local_reset.next = 1

    # print simulation data to file
    file_data = open("TIR_tb.csv", 'w')  # file for saving data
    # print header to file
    print("{0},{1},{2},{3},{4},{5},{6},{7}".format("si", "CaptureIR", "ShiftIR", "UpdateIR", "Select", "so", "D", "Q"),
          file=file_data)

    # print data on each tap_interface.ClockIR
    @always(tap_interface.ClockIR.posedge)
    def print_data():
        """
        """
        # print in file
        # print.format is not supported in MyHDL 1.0
        print(si, ",", tap_interface.CaptureIR, ",", tap_interface.ShiftIR, ",", tap_interface.UpdateIR, ",",
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
        yield tap_interface.ClockIR.negedge
        # Start the Capture transition operation
        tap_interface.CaptureIR.next = H
        yield tap_interface.ClockIR.posedge
        # Write Capture value
        yield tap_interface.ClockIR.negedge
        tap_interface.CaptureIR.next = L
        tap_interface.ShiftIR.next = H
        # yield tap_interface.ClockIR.posedge
        # Write Shift value
        # yield tap_interface.ClockIR.negedge
        for i in range(width):
            si.next = si_data[width - 1 - i]
            yield tap_interface.ClockIR.posedge
            yield tap_interface.ClockIR.negedge
            so_data[width - 1 - i].next = so
        # Write Update value
        tap_interface.ShiftIR.next = L
        tap_interface.UpdateIR.next = H
        yield tap_interface.ClockIR.posedge
        tap_interface.UpdateIR.next = L
        yield tap_interface.ClockIR.negedge
        yield tap_interface.ClockIR.posedge
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

    return tir_inst, clkgen, stimulus, reset_signal, print_data


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
    tir_inst = TIR('TOP', 'TIR0', D, Q, si, tap_interface, local_reset, so, tir_width=9, monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    tir_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="TIR")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    tir_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="TIR")
    tb = TIR_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="TIR_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="TIR_tb")


def main():
    tb = TIR_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
