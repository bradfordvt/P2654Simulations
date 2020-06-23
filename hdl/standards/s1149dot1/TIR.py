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
def TIR(path, name, D, Q, scan_in, tck, tap_interface, local_reset, scan_out, tir_width=9, monitor=False):
    """
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logging (path instance)
    :param D: tir_width bit wide Signal D = Signal(intbv(0)[tir_width:])
    :param Q: tir_width bit wide Signal Q = Signal(intbv(0)[tir_width:])
    :param scan_in: Input signal for data scanned into TIR
    :param tck: TAP TCK
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

    isr = Signal(intbv(val=0, _nrbits=tir_width))

    @always(tck.posedge)
    def capture_ff():
        if tap_interface.Select == bool(1) and tap_interface.CaptureIR == bool(1):
            if tir_width == 1:
                isr.next[0] = D
            else:
                for i in range(tir_width):
                    isr.next[i] = D[i]
        elif tap_interface.Select == bool(1) and tap_interface.ShiftIR == bool(1):
            if tir_width == 1:
                isr.next[0] = scan_in
            else:
                # for i in range(1, tir_width):
                #     isr.next[i - 1] = isr[i]
                # isr.next[tir_width - 1] = scan_in
                isr.next = concat(scan_in, isr[tir_width:1])

    @always(tap_interface.UpdateIR.posedge)
    def update_ff():
        if master_reset == bool(0):
            for i in range(tir_width):
                Q.next[i] = bool(0)
        elif tap_interface.Select == bool(1):
            if tir_width == 1:
                Q.next[0] = isr[0]
            else:
                # for i in range(tir_width):
                #     Q.next[i] = isr[i]
                Q.next = isr

    @always(tck.negedge)
    def output():
        scan_out.next = isr[0]

    @always_comb
    def reset_process():
        master_reset.next = local_reset and tap_interface.Reset

    if not monitor:
        return capture_ff, update_ff, output, reset_process
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

        @instance
        def monitor_isr():
            print("\t\tTIR({:s}): isr".format(path + '.' + name), isr)
            while 1:
                yield isr
                print("\t\tTIR({:s}): isr".format(path + '.' + name), isr)

        @instance
        def monitor_D():
            print("\t\tTIR({:s}): di".format(path + '.' + name), D)
            while 1:
                yield D
                print("\t\tTIR({:s}): di".format(path + '.' + name), D)

        @instance
        def monitor_Q():
            print("\t\tTIR({:s}): do".format(path + '.' + name), Q)
            while 1:
                yield Q
                print("\t\tTIR({:s}): do".format(path + '.' + name), Q)

        @instance
        def monitor_ce():
            print("\t\tTIR({:s}): ce".format(path + '.' + name), tap_interface.CaptureIR)
            while 1:
                yield tap_interface.CaptureIR
                print("\t\tTIR({:s}): ce".format(path + '.' + name), tap_interface.CaptureIR)

        @instance
        def monitor_se():
            print("\t\tTIR({:s}): se".format(path + '.' + name), tap_interface.ShiftIR)
            while 1:
                yield tap_interface.ShiftIR
                print("\t\tTIR({:s}): se".format(path + '.' + name), tap_interface.ShiftIR)

        @instance
        def monitor_ue():
            print("\t\tTIR({:s}): ue".format(path + '.' + name), tap_interface.UpdateIR)
            while 1:
                yield tap_interface.UpdateIR
                print("\t\tTIR({:s}): ue".format(path + '.' + name), tap_interface.UpdateIR)

        @instance
        def monitor_sel():
            print("\t\tTIR({:s}): sel".format(path + '.' + name), tap_interface.Select)
            while 1:
                yield tap_interface.Select
                print("\t\tTIR({:s}): sel".format(path + '.' + name), tap_interface.Select)

        @instance
        def monitor_clock():
            print("\t\tTIR({:s}): clock".format(path + '.' + name), tck)
            while 1:
                yield tck
                print("\t\tTIR({:s}): clock".format(path + '.' + name), tck)

        return monitor_D, monitor_Q, monitor_isr, capture_ff, update_ff, output, reset_process, \
               monitor_scan_in, monitor_scan_out, \
               monitor_ce, monitor_se, monitor_ue, monitor_sel, monitor_clock


@block
def TIR_tb(monitor=False):
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
    si_data[5] = Signal(bool(1))
    si_data[7] = Signal(bool(1))
    so_data = [Signal(bool(0)) for _ in range(width)]
    local_reset = Signal(bool(1))
    t = 0
    tir_inst = TIR('TOP', 'TIR0', D, Q, si, tck, tap_interface, local_reset, so, tir_width=9, monitor=monitor)

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

    @always_comb
    def clkir():
        tap_interface.ClockIR.next = tap_interface.Select and tck

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
        tap_interface.Select.next = True
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
            si.next = si_data[i]
            yield tap_interface.ClockIR.posedge
            so_data[i].next = so
            yield tap_interface.ClockIR.negedge
        # Write Update value
        tap_interface.ShiftIR.next = L
        tap_interface.UpdateIR.next = H
        yield tap_interface.ClockIR.posedge
        tap_interface.UpdateIR.next = L
        yield tap_interface.ClockIR.negedge
        yield tap_interface.ClockIR.posedge
        for j in range(width):
            if j == 5 or j == 7:
                assert (so_data[j] == bool(1))
            else:
                assert (so_data[j] == bool(0))
        for j in range(width):
            if j == 5 or j == 7:
                assert (Q[j] == bool(1))
            else:
                assert (Q[j] == bool(0))

        raise StopSimulation()

    return tir_inst, clkgen, stimulus, reset_signal, print_data, clkir


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
    tck = Signal(bool(0))
    tir_inst = TIR('TOP', 'TIR0', D, Q, si, tck, tap_interface, local_reset, so, tir_width=9, monitor=False)

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
