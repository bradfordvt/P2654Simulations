"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import os
import os.path

period = 20  # clk frequency = 50 MHz


@block
def WIRmux(path, name, wdr_out, wir_out, select_wir, so, monitor=False):
    """
    MUX to control what WDR is connected to so
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param wdr_out: Signal Out from WDRmux logic
    :param wir_out: Signal Out from WIR register
    :param select_wir: Select Signal for WIR register
    :param so: Signal out from WIRMux
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    @always_comb
    def mux_logic():
        if select_wir == bool(1):
            so.next = wir_out
        else:
            so.next = wdr_out

    if not monitor:
        return mux_logic
    else:
        @instance
        def monitor_wdr_out():
            print("\t\tWIRmux({:s}): wdr_out".format(path + '.' + name), wdr_out)
            while 1:
                yield wdr_out
                print("\t\tWIRmux({:s}): wdr_out".format(path + '.' + name), wdr_out)

        @instance
        def monitor_wir_out():
            print("\t\tWIRmux({:s}): wir_out".format(path + '.' + name), wir_out)
            while 1:
                yield wir_out
                print("\t\tWIRmux({:s}): wir_out".format(path + '.' + name), wir_out)

        @instance
        def monitor_select_wir():
            print("\t\tWIRmux({:s}): select_wir".format(path + '.' + name), select_wir)
            while 1:
                yield select_wir
                print("\t\tWIRmux({:s}): select_wir".format(path + '.' + name), select_wir)

        @instance
        def monitor_so():
            print("\t\tWIRmux({:s}): so".format(path + '.' + name), so)
            while 1:
                yield so
                print("\t\tWIRmux({:s}): so".format(path + '.' + name), so)

        return mux_logic, monitor_wdr_out, monitor_wir_out,\
            monitor_select_wir, monitor_so


@block
def wirmux_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    wdr_out = Signal(bool(0))
    wir_out = Signal(bool(0))
    select_wir = Signal(bool(0))
    so_out = Signal(bool(0))

    wirmux_inst = WIRmux('TOP', 'WIRMUX0', wdr_out, wir_out, select_wir, so_out, monitor=monitor)

    # print simulation data to file
    file_data = open("wirmux_tb.csv", 'w')  # file for saving data
    # print header to file
    print("{0},{1},{2},{3}".format("wdr_out", "wir_out", "select_wir", "so_out"),
          file=file_data)

    # print data on each tap_interface.ClockDR
    @always(so_out)
    def print_data():
        """
        """
        # print in file
        # print.format is not supported in MyHDL 1.0
        print(wdr_out, ",", wir_out, ",", select_wir, ",", so_out,
              file=file_data)

    @instance
    def stimulus():
        """
        Perform instruction decoding for various instructions
        :return:
        """
        select_wir.next = bool(1)
        yield delay(1)
        assert(so_out == bool(0))
        wir_out.next = bool(1)
        yield delay(1)
        assert(so_out == bool(1))
        wir_out.next = bool(0)
        yield delay(1)
        assert(so_out == bool(0))
        select_wir.next = bool(0)
        yield delay(1)
        assert(so_out == bool(0))
        wdr_out.next = bool(1)
        yield delay(1)
        assert(so_out == bool(1))
        wdr_out.next = bool(0)
        yield delay(1)
        assert(so_out == bool(0))

        raise StopSimulation()

    return wirmux_inst, stimulus, print_data


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    wdr_out = Signal(bool(0))
    wir_out = Signal(bool(0))
    select_wir = Signal(bool(0))
    so_out = Signal(bool(0))

    wirmux_inst = WIRmux('TOP', 'WIRMUX0', wdr_out, wir_out, select_wir, so_out, monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    wirmux_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="wirmux")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    wirmux_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="wirmux")
    tb = wirmux_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="wirmux_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="wirmux_tb")


def main():
    tb = wirmux_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
