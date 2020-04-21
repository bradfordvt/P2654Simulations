"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import os
import os.path

period = 20  # clk frequency = 50 MHz


@block
def ScanRegister(path, name, si, ce, se, ue, sel, reset, clock, so, di, do, width=9, monitor=False):
    """
    Generic ScanRegister design following the Capture/Shift/Update protocol
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param si: ScanIn Port
    :param ce: CaptureEnable Port
    :param se: ShiftEnable Port
    :param ue: UpdateEnable Port
    :param sel: Select Port
    :param reset: Reset Port
    :param clock: Clock Port
    :param so: ScanOut Port
    :param di: DataIn Port
    :param do: DataOut Port
    :param width: The number of bits contained in this register
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    isr = Signal(intbv(val=0, _nrbits=width))

    @always(clock.posedge)
    def capture_ff():
        if sel == bool(1) and ce == bool(1):
            if width == 1:
                isr.next[0] = di
            else:
                for i in range(width):
                    isr.next[i] = di[i]
        elif sel == bool(1) and se == bool(1):
            if width == 1:
                isr.next[0] = si
            else:
                for i in range(1, width):
                    isr.next[i - 1] = isr[i]
                isr.next[width - 1] = si

    @always(clock.negedge)
    def update_ff():
        if reset == bool(0):
            for i in range(width):
                do.next[i] = bool(0)
        elif sel == bool(1) and ue == bool(1):
            if width == 1:
                do.next[0] = isr[0]
            else:
                for i in range(width):
                    do.next[i] = isr[i]

    @always(clock.negedge)
    def output():
        so.next = isr[0]

    if not monitor:
        return capture_ff, update_ff, output
    else:
        @instance
        def monitor_si():
            print("\t\tScanRegister({:s}): si".format(path + '.' + name), si)
            while 1:
                yield si
                print("\t\tScanRegister({:s}): si".format(path + '.' + name), si)

        @instance
        def monitor_ce():
            print("\t\tScanRegister({:s}): ce".format(path + '.' + name), ce)
            while 1:
                yield ce
                print("\t\tScanRegister({:s}): ce".format(path + '.' + name), ce)

        @instance
        def monitor_se():
            print("\t\tScanRegister({:s}): se".format(path + '.' + name), se)
            while 1:
                yield se
                print("\t\tScanRegister({:s}): se".format(path + '.' + name), se)

        @instance
        def monitor_ue():
            print("\t\tScanRegister({:s}): ue".format(path + '.' + name), ue)
            while 1:
                yield ue
                print("\t\tScanRegister({:s}): ue".format(path + '.' + name), ue)

        @instance
        def monitor_sel():
            print("\t\tScanRegister({:s}): sel".format(path + '.' + name), sel)
            while 1:
                yield sel
                print("\t\tScanRegister({:s}): sel".format(path + '.' + name), sel)

        @instance
        def monitor_reset():
            print("\t\tScanRegister({:s}): reset".format(path + '.' + name), reset)
            while 1:
                yield reset
                print("\t\tScanRegister({:s}): reset".format(path + '.' + name), reset)

        @instance
        def monitor_clock():
            print("\t\tScanRegister({:s}): clock".format(path + '.' + name), clock)
            while 1:
                yield clock
                print("\t\tScanRegister({:s}): clock".format(path + '.' + name), clock)

        @instance
        def monitor_so():
            print("\t\tScanRegister({:s}): so".format(path + '.' + name), so)
            while 1:
                yield so
                print("\t\tScanRegister({:s}): so".format(path + '.' + name), so)

        @instance
        def monitor_isr():
            print("\t\tScanRegister({:s}): isr".format(path + '.' + name), isr)
            while 1:
                yield isr
                print("\t\tScanRegister({:s}): isr".format(path + '.' + name), isr)

        @instance
        def monitor_di():
            print("\t\tScanRegister({:s}): di".format(path + '.' + name), di)
            while 1:
                yield di
                print("\t\tScanRegister({:s}): di".format(path + '.' + name), di)

        @instance
        def monitor_do():
            print("\t\tScanRegister({:s}): do".format(path + '.' + name), do)
            while 1:
                yield do
                print("\t\tScanRegister({:s}): do".format(path + '.' + name), do)

        return monitor_si, monitor_ce, monitor_se, monitor_ue, monitor_sel, monitor_reset, \
            monitor_clock, monitor_so, monitor_di, monitor_do, capture_ff, update_ff, \
            monitor_isr, output


@block
def ScanRegister_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    width = 9
    si = Signal(bool(0))
    so = Signal(bool(0))
    di = Signal(intbv('010100000'))
    do = Signal(intbv(val=0, _nrbits=width))
    si_data = Signal(intbv('000000101'))
    so_data = Signal(intbv(val=0, _nrbits=width))
    sel = Signal(bool(1))
    ce = Signal(bool(0))
    se = Signal(bool(0))
    ue = Signal(bool(0))
    reset = Signal(bool(0))
    clock = Signal(bool(0))
    t = 0
    sreg_inst = ScanRegister('TOP', 'ScanRegister0', si, ce, se, ue, sel, reset, clock, so, di, do, width=width,
                             monitor=monitor)

    @instance
    def clkgen():
        while True:
            clock.next = not clock
            yield delay(period // 2)

    @instance  # reset signal
    def reset_signal():
        reset.next = 0
        yield delay(period)
        reset.next = 1

    # print simulation data to file
    file_data = open("ScanRegister.csv", 'w')  # file for saving data
    # print header to file
    print("{0},{1},{2},{3},{4},{5},{6},{7}".format("si", "ce", "se", "ue", "sel", "so", "di", "do"),
          file=file_data)

    # print data on each clock
    @always(clock.posedge)
    def print_data():
        """
        """
        # print in file
        # print.format is not supported in MyHDL 1.0
        print(si, ",", ce, ",", se, ",", ue, ",", sel, ",", so, ",", di, ",", do, file=file_data)

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
        # Start the Capture transition operation
        yield clock.posedge
        # Write Capture value
        ce.next = H
        yield clock.negedge
        yield clock.posedge
        # Write Shift value
        ce.next = L
        se.next = H
        yield clock.negedge
        for i in range(width):
            si.next = si_data[i]
            yield clock.posedge
            yield clock.negedge
            so_data.next[i] = so
        # Write Update value
        se.next = L
        ue.next = H
        yield clock.negedge
        yield clock.posedge
        j = width - 1
        while j > -1:
            # print("so_data[", j, "] = ", so_data[j])
            if j == 5 or j == 7:
                assert (so_data[j] == bool(1))
            else:
                assert (so_data[j] == bool(0))
            j = j - 1
        for j in range(width):
            # print("do[", j, "] = ", do[j])
            if j == 0 or j == 2:
                assert (do[j] == bool(1))
            else:
                assert (do[j] == bool(0))
        assert (do == intbv('000000101'))

        raise StopSimulation()

    return sreg_inst, clkgen, stimulus, reset_signal, print_data


@block
def ScanRegister1_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    width = 1
    si = Signal(bool(0))
    so = Signal(bool(0))
    di = Signal(intbv(0)[width:])
    do = Signal(intbv(0)[width:])
    si_data = Signal(intbv('0')[width:])
    so_data = [Signal(bool(0)) for _ in range(width)]
    sel = Signal(bool(1))
    ce = Signal(bool(0))
    se = Signal(bool(0))
    ue = Signal(bool(0))
    reset = Signal(bool(0))
    clock = Signal(bool(0))
    t = 0
    sreg_inst = ScanRegister('TOP', 'ScanRegister1', si, ce, se, ue, sel, reset, clock, so, di, do, width=width,
                             monitor=monitor)

    @instance
    def clkgen():
        while True:
            clock.next = not clock
            yield delay(period // 2)

    @instance  # reset signal
    def reset_signal():
        reset.next = 0
        yield delay(period)
        reset.next = 1

    # print simulation data to file
    file_data = open("ScanRegister1.csv", 'w')  # file for saving data
    # print header to file
    print("{0},{1},{2},{3},{4},{5},{6},{7}".format("si", "ce", "se", "ue", "sel", "so", "di", "do"),
          file=file_data)

    # print data on each clock
    @always(clock.posedge)
    def print_data():
        """
        """
        # print in file
        # print.format is not supported in MyHDL 1.0
        print(si, ",", ce, ",", se, ",", ue, ",", sel, ",", so, ",", di, ",", do, file=file_data)

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
        # Start the Capture transition operation
        yield clock.posedge
        # Write Capture value
        ce.next = H
        yield clock.negedge
        yield clock.posedge
        # Write Shift value
        ce.next = L
        se.next = H
        yield clock.negedge
        si.next = L
        yield clock.posedge
        yield clock.negedge
        so_data[0].next = so
        # Write Update value
        se.next = L
        ue.next = H
        yield clock.negedge
        yield clock.posedge
        assert (so_data[0] == L)
        assert (do[0] == L)
        # Write Capture value
        ue.next = L
        ce.next = H
        yield clock.negedge
        yield clock.posedge
        # Write Shift value
        ce.next = L
        se.next = H
        yield clock.negedge
        si.next = H
        yield clock.posedge
        yield clock.negedge
        so_data[0].next = so
        # Write Update value
        se.next = L
        ue.next = H
        yield clock.negedge
        yield clock.posedge
        assert (so_data[0] == L)
        assert (do[0] == H)
        # Write Capture value
        ue.next = L
        ce.next = H
        yield clock.negedge
        yield clock.posedge
        # Write Shift value
        ce.next = L
        se.next = H
        yield clock.negedge
        si.next = H
        yield clock.posedge
        yield clock.negedge
        so_data[0].next = so
        # Write Shift value
        ce.next = L
        se.next = H
        yield clock.negedge
        si.next = L
        yield clock.posedge
        yield clock.negedge
        so_data[0].next = so
        # Write Update value
        se.next = L
        ue.next = H
        yield clock.negedge
        yield clock.posedge
        ue.next = L
        assert (so_data[0] == H)
        assert (do[0] == L)
        yield clock.negedge
        yield clock.posedge

        raise StopSimulation()

    return sreg_inst, clkgen, stimulus, reset_signal, print_data


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    width = 9
    si = Signal(bool(0))
    so = Signal(bool(0))
    # di = [Signal(bool(0)) for _ in range(width)]
    # do = [Signal(bool(0)) for _ in range(width)]
    di = Signal(intbv(0)[width:])
    do = Signal(intbv(0)[width:])
    sel = Signal(bool(0))
    ce = Signal(bool(0))
    se = Signal(bool(0))
    ue = Signal(bool(0))
    reset = ResetSignal(1, 0, True)
    clock = Signal(bool(0))

    sreg_inst = ScanRegister('TOP', 'ScanRegister0', si, ce, se, ue, sel, reset, clock, so, di, do, width=9,
                             monitor=False)
    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    sreg_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="ScanRegister")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    sreg_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="ScanRegister")
    tb = ScanRegister_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="ScanRegister_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="ScanRegister_tb")


def main():
    tb = ScanRegister_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    tb0 = ScanRegister1_tb(monitor=True)
    tb0.config_sim(trace=True)
    tb0.run_sim()
    convert()


if __name__ == '__main__':
    main()
