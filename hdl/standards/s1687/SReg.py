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
def SReg(path, name, si, ijtag_interface, so, di, do, dr_width=9, monitor=False):
    """
    Creates a Module SReg for IEEE 1687 with the following interface:
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logging (path instance)
    :param si: ScanInPort
    :param ijtag_interface: IJTAGInterface defining the control signals for this register
    :param so: ScanOutPort
    :param di: DataInPort Signal(intbv(0)[dr_width:])
    :param do: DataOutPort Signal(intbv(0)[dr_width:])
    :param dr_width: The width of the DI/DO interfaces and size of the SR
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    reset_n = Signal(bool(1))
    sr_inst = ScanRegister(
                            path + '.' + name,
                            'ScanRegister' + name[-1],
                            si,
                            ijtag_interface.CAPTURE,
                            ijtag_interface.SHIFT,
                            ijtag_interface.UPDATE,
                            ijtag_interface.SELECT,
                            reset_n,
                            ijtag_interface.CLOCK,
                            so,
                            di,
                            do,
                            dr_width
                            )

    @always_comb
    def reset_logic():
        reset_n.next = not ijtag_interface.RESET

    if monitor == False:
        return sr_inst, reset_logic
    else:
        @instance
        def monitor_si():
            print("\t\tSReg({:s}): si".format(path + name), si)
            while 1:
                yield si
                print("\t\tSReg({:s}): si".format(path + name), si)

        @instance
        def monitor_so():
            print("\t\tSReg({:s}): so".format(path + name), so)
            while 1:
                yield so
                print("\t\tSReg({:s}) so:".format(path + name), so)
        @instance
        def monitor_di():
            print("\t\tSReg({:s}): di".format(path + name), di)
            while 1:
                yield di
                print("\t\tSReg({:s}): si".format(path + name), di)

        @instance
        def monitor_do():
            print("\t\tSReg({:s}): do".format(path + name), do)
            while 1:
                yield do
                print("\t\tSReg({:s}) do:".format(path + name), do)

        return monitor_si, monitor_so, monitor_di, monitor_do, sr_inst, reset_logic


@block
def SReg_tb(monitor=False):
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
    si_data = [Signal(bool(0)) for _ in range(dr_width)]
    si_data[dr_width - 5] = Signal(bool(1))
    si_data[dr_width - 7] = Signal(bool(1))
    so_data = [Signal(bool(0)) for _ in range(dr_width)]
    ijtag_interface = IJTAGInterface()

    sreg_inst = SReg('TOP', 'SReg0', si, ijtag_interface, so, di, do, dr_width=9, monitor=monitor)

    @instance
    def clkgen():
        while True:
            ijtag_interface.CLOCK.next = not ijtag_interface.CLOCK
            yield delay(period // 2)

    # print simulation data to file
    file_data = open("SReg_tb.csv", 'w')  # file for saving data
    # print header to file
    print("{0},{1},{2},{3},{4},{5},{6},{7}".format("si", "ce", "se", "ue", "sel", "so", "di", "do"),
          file=file_data)

    # print data on each tap_interface.ClockDR
    @always(ijtag_interface.CLOCK.posedge)
    def print_data():
        """
        """
        # print in file
        # print.format is not supported in MyHDL 1.0
        print(si, ",", ijtag_interface.CAPTURE, ",", ijtag_interface.SHIFT, ",", ijtag_interface.UPDATE, ",",
              ijtag_interface.SELECT, ",", so, ",", di, ",", do, file=file_data)

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
        for i in range(dr_width):
            si.next = si_data[dr_width - 1 - i]
            yield ijtag_interface.CLOCK.posedge
            yield ijtag_interface.CLOCK.negedge
            so_data[dr_width - 1 - i].next = so
        # Write Update value
        ijtag_interface.SHIFT.next = L
        ijtag_interface.UPDATE.next = H
        yield ijtag_interface.CLOCK.negedge
        yield ijtag_interface.CLOCK.posedge
        for j in range(dr_width):
            if j == 1 or j == 3:
                assert(so_data[dr_width - 1 - j] == bool(1))
            else:
                assert(so_data[dr_width - 1 - j] == bool(0))
        for j in range(dr_width):
            if j == 4 or j == 6:
                assert(do[dr_width - 1 - j] == bool(1))
            else:
                assert(do[dr_width - 1 - j] == bool(0))

        raise StopSimulation()

    return sreg_inst, clkgen, stimulus, print_data


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
    ijtag_interface = IJTAGInterface()

    sreg_inst = SReg('TOP', 'SReg0', si, ijtag_interface, so, di, do, dr_width=9, monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    sreg_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SReg")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    sreg_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SReg")
    tb = SReg_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SReg_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SReg_tb")


def main():
    tb = SReg_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
