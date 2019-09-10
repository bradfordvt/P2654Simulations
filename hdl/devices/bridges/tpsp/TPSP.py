"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

TPSP Interface
Used to simulate the 2-pin Serial Port for the purposes of testing the IEEE 1687 or IEEE 1149.1-2013 networks.
Design concept provided by: Martin Keim (Mentor Graphics).
myHDL implementation created by: Bradford G, Van Treuren
Date Created: June 25, 2019

"""

from myhdl import *
from hdl.standards.s1149dot1.JTAGInterface import JTAGInterface
import os
import os.path

period = 20  # clk frequency = 50 MHz

t_State = enum('START', 'TMS', 'TDI', 'TDO')
ACTIVE_LOW = 0
START_POWER = Signal(intbv(10, min=0, max=101))
TMS_POWER = Signal(intbv(30, min=0, max=101))
TDI_POWER = Signal(intbv(100, min=0, max=101))
TDO_POWER = Signal(intbv(70, min=0, max=101))

START_TEMP = Signal(intbv(10, min=0, max=101))
TMS_TEMP = Signal(intbv(20, min=0, max=101))
TDI_TEMP = Signal(intbv(100, min=0, max=101))
TDO_TEMP = Signal(intbv(70, min=0, max=101))


def int_to_list(ival):
    """
    Convert an intbv into a list of boolean values
    :param ival: intbv value
    :return: A list of boolean values of the size of the intbv
    """
    blist = []
    binary = bin(ival)[2:]
    blen = len(binary)
    for i in range(blen):
        if binary[i] == 0:
            blist.append(bool(0))
        else:
            blist.append(bool(1))
    return blist


@block
def TPSP(path, name, spclk, reset_n, spio_in, spio_en, spio_out,
             jtag_interface, tdi, tdo, tdo_en,
             power_usage_register, thermal_register, monitor=False):
    """
    Logic to create an instance of the 2-Pin Serial Port
    :param path: Dot path of the parent of this instance
    :param name: String containing the instance name to be printed in diagnostic messages
    :param spclk: Clock signal used to change state and tick the delay times for delay states
    :param reset_n: Reset signal for state machine. 0=Reset, 1=No reset
    :param spio_in: Data Input Signal
    :param spio_en: Control Signal to enable the SPIO_OUT to the SPIO bus
    :param spio_out: Data Output Signal
    :param jtag_interface: JTAGInterface object defining the JTAG signals used by this controller
    :param tdi: Test Data Input signal of the jtag_interface for this device
    :param tdo: Test Data Output signal of the jtag_interface for this device
    :param tdo_en: Test Data Output Enable input signal for the jtag_interface for this device
    :param power_usage_register: Signal(intbv(0, min=0, max=101)) signal representing 0 - 100% power usage
            that changes over time depending on the operation being performed.  The power monitor would
            monitor this value and report how much total power in the system is being used.
    :param thermal_register: Signal(intbv(0, min=0, max=101)) signal representing 0 - 100% themal usage
            that changes over time depending on the operation being performed.  The temperature monitor
            would monitor this value and report the temperature the system is producing.
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    state = Signal(t_State.START)
    spio_tms = Signal(bool(1))
    power_usage_register.next = START_POWER
    thermal_register.next = START_TEMP

    @always(spclk.posedge)
    def state_machine():
        if reset_n == ACTIVE_LOW:
            jtag_interface.TCK.next = bool(1)
            jtag_interface.TMS.next = bool(1)
            jtag_interface.TRST.next = bool(1)
            tdi.next = bool(0)
            spio_en.next = bool(0)
            spio_out.next = bool(0)
            state.next = t_State.START
            power_usage_register.next = START_POWER
            thermal_register.next = START_TEMP

        else:
            if state == t_State.START:
                jtag_interface.TCK.next = bool(1)
                jtag_interface.TMS.next = bool(1)
                tdi.next = bool(0)
                state.next = t_State.TMS

            elif state == t_State.TMS:
                spio_tms.next = spio_in
                jtag_interface.TCK.next = bool(0)
                state.next = t_State.TDI
                power_usage_register.next = TMS_POWER
                thermal_register.next = TMS_TEMP

            elif state == t_State.TDI:
                jtag_interface.TMS.next = spio_tms
                tdi.next = spio_in
                if tdo_en:
                    spio_en.next = bool(1)
                    spio_out.next = tdo
                else:
                    spio_en.next = bool(0)
                    spio_out.next = bool(0)
                state.next = t_State.TDO
                power_usage_register.next = TDI_POWER
                thermal_register.next = TDI_TEMP

            elif state == t_State.TDO:
                spio_en.next = bool(0)  # Disable the spio_out output
                jtag_interface.TCK.next = bool(1)
                state.next = t_State.TMS
                power_usage_register.next = TDO_POWER
                thermal_register.next = TDO_TEMP

            else:
                raise ValueError("Undefined state")

    if not monitor:
        return state_machine
    else:
        @instance
        def monitor_power_usage():
            print("\t\tTPSP({:s}).power_usage_register:".format(name),
                  power_usage_register)
            while 1:
                yield power_usage_register
                print("\t\tTPSP({:s}).power_usage_register:".format(name),
                      power_usage_register)

        @instance
        def monitor_tempurature():
            print("\t\tTPSP({:s}).thermal_register:".format(name), thermal_register)
            while 1:
                yield thermal_register
                print("\t\tTPSP({:s}).thermal_register:".format(name),
                      thermal_register)

        @instance
        def monitor_state():
            print("\t\tTPSP({:s}).state:".format(name), state)
            while 1:
                yield state
                print("\t\tTPSP({:s}).state:".format(name), state)

        @instance
        def monitor_reset_n():
            print("\t\tTPSP({:s}).reset_n:".format(name), reset_n)
            while 1:
                yield reset_n
                print("\t\tTPSP({:s}).reset_n:".format(name), reset_n)

        @instance
        def monitor_spclk():
            print("\t\tTPSP({:s}).spclk:".format(name), spclk)
            while 1:
                yield spclk
                print("\t\tTPSP({:s}).spclk:".format(name), spclk)

        @instance
        def monitor_spio_in():
            print("\t\tTPSP({:s}).spio_in:".format(name), spio_in)
            while 1:
                yield spio_in
                print("\t\tTPSP({:s}).spio_in:".format(name),
                      spio_in)

        @instance
        def monitor_spio_en():
            print("\t\tTPSP({:s}).spio_en:".format(name), spio_en)
            while 1:
                yield spio_en
                print("\t\tTPSP({:s}).spio_en:".format(name),
                      spio_en)

        @instance
        def monitor_spio_out():
            print("\t\tTPSP({:s}).spio_out:".format(name), spio_out)
            while 1:
                yield spio_out
                print("\t\tTPSP({:s}).spio_out:".format(name),
                      spio_out)

        @instance
        def monitor_tdi():
            print("\t\tTPSP({:s}).tdi:".format(name), tdi)
            while 1:
                yield tdi
                print("\t\tTPSP({:s}).tdi:".format(name),
                      tdi)

        @instance
        def monitor_tms():
            print("\t\tTPSP({:s}).tms:".format(name), jtag_interface.TMS)
            while 1:
                yield jtag_interface.TMS
                print("\t\tTPSP({:s}).tms:".format(name),
                      jtag_interface.TMS)

        @instance
        def monitor_tdo():
            print("\t\tTPSP({:s}).tdo:".format(name), tdo)
            while 1:
                yield tdo
                print("\t\tTPSP({:s}).tdo:".format(name),
                      tdo)

        @instance
        def monitor_tdo_en():
            print("\t\tTPSP({:s}).tdo_en:".format(name), tdo_en)
            while 1:
                yield tdo_en
                print("\t\tTPSP({:s}).tdo_en:".format(name),
                      tdo_en)

        @instance
        def monitor_tck():
            print("\t\tTPSP({:s}).tck:".format(name), jtag_interface.TCK)
            while 1:
                yield jtag_interface.TCK
                print("\t\tTPSP({:s}).tck:".format(name),
                      jtag_interface.TCK)

        @instance
        def monitor_spio_tms():
            print("\t\tTPSP({:s}).spio_tms:".format(name), spio_tms)
            while 1:
                yield spio_tms
                print("\t\tTPSP({:s}).spio_tms:".format(name),
                      spio_tms)

        return state_machine, monitor_reset_n, monitor_spclk, monitor_spio_in, monitor_spio_en, \
            monitor_spio_out, monitor_tdi, monitor_tdo, monitor_tdo_en, monitor_tms, monitor_tck, \
            monitor_state, monitor_power_usage, monitor_tempurature, monitor_spio_tms


@block
def TPSP_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """

    spclk = Signal(bool(0))
    spio_in = Signal(bool(0))
    spio_en = Signal(bool(0))
    spio_out = Signal(bool(0))
    tdo = Signal(bool(0))
    tdi = Signal(bool(0))
    tdo_en = Signal(bool(0))
    jtag_interface = JTAGInterface()
    reset_n = ResetSignal(1, 0, True)
    power_usage = Signal(intbv(0, min=0, max=101))
    thermal = Signal(intbv(0, min=0, max=101))

    tpsp_inst = TPSP('TOP', 'TPSP0', spclk, reset_n, spio_in, spio_en, spio_out,
                     jtag_interface, tdi, tdo, tdo_en, power_usage, thermal, monitor=monitor)

    @instance
    def clkgen():
        while True:
            spclk.next = not spclk
            yield delay(period // 2)

    # print simulation data to file
    file_data = open("TPSP_tb.csv", 'w')  # file for saving data
    # print header to file
    print("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}".format("spio_in", "spio_en", "spio_out", "tdo", "tdi", "tdo_en",
                                                           "jtag_interface.TCK", "jtag_interface.TMS", "power_usage",
                                                           "thermal"),
          file=file_data)

    # print data on each clock
    @always(spclk.posedge)
    def print_data():
        """
        """
        # print in file
        # print.format is not supported in MyHDL 1.0
        print(spio_in, ",", spio_en, ",", spio_out, ",", tdo, ",", tdi, ",", tdo_en, ",", jtag_interface.TCK, ",",
              jtag_interface.TMS, power_usage, thermal, file=file_data)

    @instance
    def stimulus():
        """
        Not true JTAG protocol, but used to exercise the state machine with the fewest cycles
        :return:
        """
        H = bool(1)
        L = bool(0)
        # Reset the instrument
        reset_n.next = bool(0)
        yield delay(10)
        reset_n.next = bool(1)
        yield delay(10)
        # Start the TAP transition operation
        yield spclk.negedge
        # Write TMS value
        spio_in.next = H
        tdo.next = H
        tdo_en.next = H
        yield spclk.posedge
        yield spclk.negedge
        # Write TDI value
        spio_in.next = H  # Value of TDI to be driven
        assert(spio_en == L)  # spio_in active for input
        yield spclk.posedge
        yield spclk.negedge
        # Capture TDO value
        # spio_in.next = H  # Don't care since it is not used here while spio_out is enabled
        # Next JTAG Cycle
        assert (tdi == H)
        # yield spclk.posedge
        tdo.next = H
        tdo_en.next = L
        assert(spio_en == H)  # spio_out enabled for output during TDO cycle
        assert(spio_out == H)  # Captured TDO value returned to spio_out
        yield spclk.negedge
        # Write TMS value
        spio_in.next = L
        tdo.next = L
        tdo_en.next = H
        yield spclk.posedge
        assert(spio_en == L)
        assert(tdi == H)
        yield spclk.negedge
        # Write TDI value
        spio_in.next = L  # Value of TDI to be driven
        assert(spio_en == L)  # spio_in active for input
        yield spclk.posedge
        yield spclk.negedge
        # Capture TDO value
        # spio_in.next = H  # Don't care since it is not used here while spio_out is enabled
        assert (tdi == L)
        tdo.next = L
        tdo_en.next = L
        yield spclk.posedge
        assert(spio_en == H)  # spio_out enabled for output during TDO cycle
        assert(spio_out == L)  # Captured TDO value returned to spio_out
        yield spclk.negedge
        yield spclk.posedge
        raise StopSimulation()

    return tpsp_inst, clkgen, stimulus, print_data

def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    spclk = Signal(bool(0))
    spio_in = Signal(bool(0))
    spio_en = Signal(bool(0))
    spio_out = Signal(bool(0))
    tdo = Signal(bool(0))
    tdi = Signal(bool(0))
    tdo_en = Signal(bool(0))
    jtag_interface = JTAGInterface()
    reset_n = ResetSignal(1, 0, True)
    power_usage = Signal(intbv(0, min=0, max=101))
    thermal = Signal(intbv(0, min=0, max=101))

    tpsp_inst = TPSP('TOP', 'TPSP0', spclk, reset_n, spio_in, spio_en, spio_out,
                     jtag_interface, tdi, tdo, tdo_en, power_usage, thermal, monitor=False)
    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    tpsp_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="TPSP")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    tpsp_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="TPSP")
    tb = TPSP_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="TPSP_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="TPSP_tb")


def main():
    tb = TPSP_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
