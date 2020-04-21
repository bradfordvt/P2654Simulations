"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import os
import os.path
from hdl.common.ScanRegister import ScanRegister
from hdl.standards.s1687.IJTAGInterface import IJTAGInterface

period = 20  # clk frequency = 50 MHz


@block
def SELWIR(path, name, si, ijtag_interface, so, select_wir, monitor=False):
    """
    Creates a Select WIR register with the following interface:
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logging (path instance)
    :param si: ScanInPort
    :param ijtag_interface: IJTAGInterface defining the control signals for this register
    :param so: ScanOutPort
    :param select_wir: Select WIR signal to be controlled by this register
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    isr = Signal(bool(1))

    @always(ijtag_interface.CLOCK.posedge)
    def capture_ff():
        if ijtag_interface.SELECT == bool(1) and ijtag_interface.CAPTURE == bool(1):
            isr.next = select_wir
        elif ijtag_interface.SELECT == bool(1) and ijtag_interface.SHIFT == bool(1):
            isr.next = si

    @always(ijtag_interface.CLOCK.negedge)
    def update_ff():
        if ijtag_interface.RESET == bool(1):
            select_wir.next = bool(1)
        elif ijtag_interface.SELECT == bool(1) and ijtag_interface.UPDATE == bool(1):
            select_wir.next = isr

    @always(ijtag_interface.CLOCK.negedge)
    def output():
        so.next = isr

    if not monitor:
        return capture_ff, update_ff, output
    else:
        @instance
        def monitor_si():
            print("\t\tselwir({:s}): si".format(path + '.' + name), si)
            while 1:
                yield si
                print("\t\tselwir({:s}): si".format(path + '.' + name), si)

        @instance
        def monitor_ce():
            print("\t\tselwir({:s}): CAPTURE".format(path + '.' + name), ijtag_interface.CAPTURE)
            while 1:
                yield ijtag_interface.CAPTURE
                print("\t\tselwir({:s}): CAPTURE".format(path + '.' + name), ijtag_interface.CAPTURE)

        @instance
        def monitor_se():
            print("\t\tselwir({:s}): SELECT".format(path + '.' + name), ijtag_interface.SELECT)
            while 1:
                yield ijtag_interface.SELECT
                print("\t\tselwir({:s}): SELECT".format(path + '.' + name), ijtag_interface.SELECT)
    
        @instance
        def monitor_ue():
            print("\t\tselwir({:s}): UPDATE".format(path + '.' + name), ijtag_interface.UPDATE)
            while 1:
                yield ijtag_interface.UPDATE
                print("\t\tselwir({:s}): UPDATE".format(path + '.' + name), ijtag_interface.UPDATE)

        @instance
        def monitor_select_wir():
            print("\t\tselwir({:s}): select_wir".format(path + '.' + name), select_wir)
            while 1:
                yield select_wir
                print("\t\tselwir({:s}): select_wir".format(path + '.' + name), select_wir)

        @instance
        def monitor_reset():
            print("\t\tselwir({:s}): RESET".format(path + '.' + name), ijtag_interface.RESET)
            while 1:
                yield ijtag_interface.RESET
                print("\t\tselwir({:s}): RESET".format(path + '.' + name), ijtag_interface.RESET)

        @instance
        def monitor_clock():
            print("\t\tselwir({:s}): CLOCK".format(path + '.' + name), ijtag_interface.CLOCK)
            while 1:
                yield ijtag_interface.CLOCK
                print("\t\tselwir({:s}): CLOCK".format(path + '.' + name), ijtag_interface.CLOCK)

        @instance
        def monitor_so():
            print("\t\tselwir({:s}): so".format(path + '.' + name), so)
            while 1:
                yield so
                print("\t\tselwir({:s}): so".format(path + '.' + name), so)

        @instance
        def monitor_isr():
            print("\t\tselwir({:s}): isr".format(path + '.' + name), isr)
            while 1:
                yield isr
                print("\t\tselwir({:s}): isr".format(path + '.' + name), isr)

        return monitor_si, monitor_ce, monitor_se, monitor_ue, monitor_select_wir, monitor_reset, \
               monitor_clock, monitor_so, capture_ff, update_ff, \
               monitor_isr, output


@block
def SELWIR_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    si = Signal(bool(0))
    so = Signal(bool(0))
    select_wir = Signal(bool(1))
    ijtag_interface = IJTAGInterface()
    ijtag_interface.SELECT = Signal(bool(1))
    si_data = Signal(bool(0))
    so_data = Signal(bool(0))

    selwir_inst = SELWIR('TOP', 'SELWIR0', si, ijtag_interface, so, select_wir, monitor=monitor)

    @instance
    def clkgen():
        while True:
            ijtag_interface.CLOCK.next = not ijtag_interface.CLOCK
            yield delay(period // 2)

    # print simulation data to file
    file_data = open("SELWIR_tb.csv", 'w')  # file for saving data
    # print header to file
    print("{0},{1},{2},{3},{4},{5},{6}".format("si", "ce", "se", "ue", "sel", "so", "select_wir"),
          file=file_data)

    # print data on each tap_interface.ClockDR
    @always(ijtag_interface.CLOCK.posedge)
    def print_data():
        """
        """
        # print in file
        # print.format is not supported in MyHDL 1.0
        print(si, ",", ijtag_interface.CAPTURE, ",", ijtag_interface.SHIFT, ",",
              ijtag_interface.UPDATE, ",", ijtag_interface.SELECT, ",", so, ",", select_wir,
              file=file_data)

    @instance
    def stimulus():
        """
        Not true IJTAG protocol, but used to exercise the state machine with the fewest cycles
        :return:
        """
        H = bool(1)
        L = bool(0)
        # Reset the instrument
        ijtag_interface.RESET.next = bool(1)
        yield delay(10)
        ijtag_interface.RESET.next = bool(0)
        yield delay(10)

        # Start the Capture transition operation
        yield ijtag_interface.CLOCK.posedge
        # Write Capture value
        ijtag_interface.CAPTURE.next = H
        yield ijtag_interface.CLOCK.negedge
        yield ijtag_interface.CLOCK.posedge
        # Write Shift value
        ijtag_interface.CAPTURE.next = L
        ijtag_interface.SHIFT.next = H
        yield ijtag_interface.CLOCK.negedge
        si.next = bool(0)  # First scan
        yield ijtag_interface.CLOCK.posedge
        yield ijtag_interface.CLOCK.negedge
        assert(so == bool(1))

        # Write Update value
        ijtag_interface.SHIFT.next = L
        ijtag_interface.UPDATE.next = H
        yield ijtag_interface.CLOCK.negedge
        yield ijtag_interface.CLOCK.posedge
        assert(select_wir == bool(0))

        # Start the Capture transition operation
        yield ijtag_interface.CLOCK.posedge
        # Write Capture value
        ijtag_interface.CAPTURE.next = H
        yield ijtag_interface.CLOCK.negedge
        yield ijtag_interface.CLOCK.posedge
        # Write Shift value
        ijtag_interface.CAPTURE.next = L
        ijtag_interface.SHIFT.next = H
        yield ijtag_interface.CLOCK.negedge
        si.next = bool(1)  # Second scan
        yield ijtag_interface.CLOCK.posedge
        yield ijtag_interface.CLOCK.negedge
        assert (so == bool(0))

        # Write Update value
        ijtag_interface.SHIFT.next = L
        ijtag_interface.UPDATE.next = H
        yield ijtag_interface.CLOCK.negedge
        yield ijtag_interface.CLOCK.posedge
        assert (select_wir == bool(1))

        # Start the Capture transition operation
        yield ijtag_interface.CLOCK.posedge
        # Write Capture value
        ijtag_interface.CAPTURE.next = H
        yield ijtag_interface.CLOCK.negedge
        yield ijtag_interface.CLOCK.posedge
        # Write Shift value
        ijtag_interface.CAPTURE.next = L
        ijtag_interface.SHIFT.next = H
        yield ijtag_interface.CLOCK.negedge
        si.next = bool(0)  # Third scan
        yield ijtag_interface.CLOCK.posedge
        yield ijtag_interface.CLOCK.negedge
        assert (so == bool(1))

        # Write Update value
        ijtag_interface.SHIFT.next = L
        ijtag_interface.UPDATE.next = H
        yield ijtag_interface.CLOCK.negedge
        yield ijtag_interface.CLOCK.posedge
        assert (select_wir == bool(0))

        raise StopSimulation()

    return selwir_inst, clkgen, stimulus, print_data


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    si = Signal(bool(0))
    so = Signal(bool(0))
    select_wir = Signal(bool(0))
    ijtag_interface = IJTAGInterface()

    selwir_inst = SELWIR('TOP', 'SELWIR0', si, ijtag_interface, so, select_wir)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    selwir_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SELWIR")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    selwir_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SELWIR")
    tb = SELWIR_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SELWIR_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SELWIR_tb")


def main():
    tb = SELWIR_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
