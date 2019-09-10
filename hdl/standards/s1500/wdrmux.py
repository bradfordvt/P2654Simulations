"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import os
import os.path

period = 20  # clk frequency = 50 MHz


@block
def WDRmux(path, name,
             wby_out, mbist1_out, mbist2_out, mbist3_out,
             wr_select_list, dr_select_list,
             so, monitor=False):
    """
    MUX to control what WDR is connected to so
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param wby_out: Signal Out from WBY register
    :param mbist1_out: Signal Out from MBIST1 register
    :param mbist2_out: Signal Out from MBIST2 register
    :param mbist3_out: Signal Out from MBIST3 register
    :param wr_select_list: [Signal(bool(0) for _ in range(len(wr_list)] to use as 1500 wrapper instruction signals
    :param dr_select_list: [Signal(bool(0) for _ in range(len(user_list)] to use as user instruction signals
    :param so: Signal out from WDRs to WIRMux
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    @always_comb
    def mux_logic():
        if wr_select_list[0] == bool(1):
            so.next = wby_out
        elif dr_select_list[0] == bool(1):
            so.next = mbist1_out
        elif dr_select_list[1] == bool(1):
            so.next = mbist2_out
        elif dr_select_list[2] == bool(1):
            so.next = mbist3_out
        else:
            so.next = bool(0)

    if not monitor:
        return mux_logic
    else:
        @instance
        def monitor_wby_out():
            print("\t\tWDRmux({:s}): wby_out".format(path + '.' + name), wby_out)
            while 1:
                yield wby_out
                print("\t\tWDRmux({:s}): wby_out".format(path + '.' + name), wby_out)

        @instance
        def monitor_mbist1_out():
            print("\t\tWDRmux({:s}): mbist1_out".format(path + '.' + name), mbist1_out)
            while 1:
                yield mbist1_out
                print("\t\tWDRmux({:s}): mbist1_out".format(path + '.' + name), mbist1_out)

        @instance
        def monitor_mbist2_out():
            print("\t\tWDRmux({:s}): mbist2_out".format(path + '.' + name), mbist2_out)
            while 1:
                yield mbist2_out
                print("\t\tWDRmux({:s}): mbist2_out".format(path + '.' + name), mbist2_out)

        @instance
        def monitor_mbist3_out():
            print("\t\tWDRmux({:s}): mbist3_out".format(path + '.' + name), mbist3_out)
            while 1:
                yield mbist3_out
                print("\t\tWDRmux({:s}): mbist3_out".format(path + '.' + name), mbist3_out)

        @instance
        def monitor_so():
            print("\t\tWDRmux({:s}): so".format(path + '.' + name), so)
            while 1:
                yield so
                print("\t\tWDRmux({:s}): so".format(path + '.' + name), so)

        @instance
        def monitor_wr_select_list():
            print("\t\tWDRmux({:s}): wr_select_list".format(path + '.' + name), wr_select_list)
            while 1:
                yield wr_select_list
                print("\t\tWDRmux({:s}): wr_select_list".format(path + '.' + name), wr_select_list)

        @instance
        def monitor_dr_select_list():
            print("\t\tWDRmux({:s}): dr_select_list".format(path + '.' + name), dr_select_list)
            while 1:
                yield dr_select_list
                print("\t\tWDRmux({:s}): dr_select_list".format(path + '.' + name), dr_select_list)

        return mux_logic, monitor_wby_out, monitor_mbist1_out,\
            monitor_mbist2_out, monitor_mbist3_out, monitor_so,\
            monitor_wr_select_list, monitor_dr_select_list


@block
def wdrmux_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    wby_out = Signal(bool(0))
    mbist1_out = Signal(bool(0))
    mbist2_out = Signal(bool(0))
    mbist3_out = Signal(bool(0))
    so_out = Signal(bool(0))
    wr_list = ['WS_BYPASS']
    user_list = ['MBIST1', 'MBIST2', 'MBIST3']
    # wr_select_list = [Signal(bool(0)) for _ in range(len(wr_list))]
    # dr_select_list = [Signal(bool(0)) for _ in range(len(user_list))]
    wr_select_list = Signal(intbv(0)[len(wr_list):])
    dr_select_list = Signal(intbv(0)[len(user_list):])

    wdrmux_inst = WDRmux('TOP', 'WDRMUX0', wby_out, mbist1_out, mbist2_out, mbist3_out,
                         wr_select_list, dr_select_list, so_out, monitor=monitor)

    # print simulation data to file
    file_data = open("wdrmux_tb.csv", 'w')  # file for saving data
    # print header to file
    print("{0},{1},{2},{3},{4}".format("wby_out", "mbist1_out", "mbist2_out", "mbist3_out", "so_out"),
          file=file_data)

    # print data on each tap_interface.ClockDR
    @instance
    def print_data():
        """
        """
        # print in file
        # print.format is not supported in MyHDL 1.0
        while True:
            print(wby_out, ",", mbist1_out, ",", mbist2_out, ",",
                  mbist3_out, ",", so_out,
                  file=file_data)
            yield delay(1)

    @instance
    def stimulus():
        """
        Perform instruction decoding for various instructions
        :return:
        """
        wr_select_list.next[0] = bool(1)
        yield delay(1)
        assert(so_out == bool(0))
        wby_out.next = bool(1)
        yield delay(1)
        assert(so_out == bool(1))
        wby_out.next = bool(0)
        yield delay(1)
        assert(so_out == bool(0))
        wr_select_list.next[0] = bool(0)
        dr_select_list.next[0] = bool(1)
        yield delay(1)
        assert(so_out == bool(0))
        mbist1_out.next = bool(1)
        yield delay(1)
        assert(so_out == bool(1))
        mbist1_out.next = bool(0)
        yield delay(1)
        assert(so_out == bool(0))
        wr_select_list.next[0] = bool(0)
        dr_select_list.next[0] = bool(0)
        dr_select_list.next[1] = bool(1)
        yield delay(1)
        assert(so_out == bool(0))
        mbist2_out.next = bool(1)
        yield delay(1)
        assert(so_out == bool(1))
        mbist2_out.next = bool(0)
        yield delay(1)
        assert(so_out == bool(0))
        wr_select_list.next[0] = bool(0)
        dr_select_list.next[0] = bool(0)
        dr_select_list.next[1] = bool(0)
        dr_select_list.next[2] = bool(1)
        yield delay(1)
        assert(so_out == bool(0))
        mbist3_out.next = bool(1)
        yield delay(1)
        assert(so_out == bool(1))
        mbist3_out.next = bool(0)
        yield delay(1)
        assert(so_out == bool(0))
        wr_select_list.next[0] = bool(0)
        dr_select_list.next[0] = bool(0)
        dr_select_list.next[1] = bool(0)
        dr_select_list.next[2] = bool(0)
        yield delay(1)
        assert(so_out == bool(0))

        raise StopSimulation()

    return wdrmux_inst, stimulus, print_data


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    wby_out = Signal(bool(0))
    mbist1_out = Signal(bool(0))
    mbist2_out = Signal(bool(0))
    mbist3_out = Signal(bool(0))
    so_out = Signal(bool(0))
    wr_list = ['WS_BYPASS']
    user_list = ['MBIST1', 'MBIST2', 'MBIST3']
    # wr_select_list = [Signal(bool(0)) for _ in range(len(wr_list))]
    # dr_select_list = [Signal(bool(0)) for _ in range(len(user_list))]
    wr_select_list = Signal(intbv(0)[len(wr_list):])
    dr_select_list = Signal(intbv(0)[len(user_list):])

    wdrmux_inst = WDRmux('TOP', 'WDRMUX0', wby_out, mbist1_out, mbist2_out, mbist3_out,
                         wr_select_list, dr_select_list, so_out, monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    wdrmux_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="wdrmux")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    wdrmux_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="wdrmux")
    tb = wdrmux_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="wdrmux_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="wdrmux_tb")


def main():
    tb = wdrmux_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
