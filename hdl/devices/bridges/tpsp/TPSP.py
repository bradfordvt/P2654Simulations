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


class TPSP:
    """
    Class structure implementing the RTL for the interface logic.
    """

    def __init__(self, name, spclk, reset_n, spio_in, spio_en, spio_out,
                 jtag_interface, tdi, tdo, tdo_en,
                 power_usage_register, thermal_register):
        """
        Constructor to create an instance of the MBIST Simulated Instrument
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
                that changes over time depending on the operation being performed.  The tempurature monitor
                would monitor this value and report the temperature the system is producing.
        """
        self.name = name
        self.state = Signal(t_State.START)
        self.reset_n = reset_n
        self.spclk = spclk
        self.spio_in = spio_in
        self.spio_en = spio_en
        self.spio_out = spio_out
        self.jtag_interface = jtag_interface
        self.spio_tms = Signal(bool(1))
        self.tdi = tdi
        self.tdo = tdo
        self.tdo_en = tdo_en
        self.power_usage_register = power_usage_register
        self.thermal_register = thermal_register
        self.power_usage_register.next = START_POWER
        self.thermal_register.next = START_TEMP

    def toVHDL(self):
        """
        Converts the myHDL logic into VHDL
        :return:
        """
        vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
        if not os.path.exists(vhdl_dir):
            os.mkdir(vhdl_dir, mode=0o777)
        self.rtl(monitor=False).convert(hdl="VHDL", initial_values=True, directory=vhdl_dir)

    def toVerilog(self):
        """
        Converts the myHDL logic into Verilog
        :return:
        """
        verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
        if not os.path.exists(verilog_dir):
            os.mkdir(verilog_dir, mode=0o777)
        self.rtl(monitor=False).convert(hdl="Verilog", initial_values=True, directory=verilog_dir)

    def rtl(self, monitor=False):
        """
        Wrapper around the RTL logic to get a meaningful name during conversion
        :param monitor:
        :return:
        """
        return self.TPSP_rtl(monitor=monitor)

    @block
    def TPSP_rtl(self, monitor=False):
        """
        Logic to implement the TPSP interface
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """

        @always_seq(self.spclk.posedge, reset=self.reset_n)
        def state_machine():
            if self.reset_n == ACTIVE_LOW:
                self.jtag_interface.TCK.next = bool(1)
                self.jtag_interface.TMS.next = bool(1)
                self.jtag_interface.TRST.next = bool(1)
                self.tdi.next = bool(0)
                self.spio_en.next = bool(0)
                self.spio_out.next = bool(0)
                self.state.next = t_State.START
                self.power_usage_register.next = START_POWER
                self.thermal_register.next = START_TEMP

            else:
                if self.state == t_State.START:
                    self.jtag_interface.TCK.next = bool(1)
                    self.jtag_interface.TMS.next = bool(1)
                    self.tdi.next = bool(0)
                    self.state.next = t_State.TMS

                elif self.state == t_State.TMS:
                    self.spio_tms.next = self.spio_in
                    self.jtag_interface.TCK.next = bool(0)
                    self.state.next = t_State.TDI
                    self.power_usage_register.next = TMS_POWER
                    self.thermal_register.next = TMS_TEMP

                elif self.state == t_State.TDI:
                    self.jtag_interface.TMS.next = self.spio_tms
                    self.tdi.next = self.spio_in
                    if self.tdo_en:
                        self.spio_en.next = bool(1)
                        self.spio_out.next = self.tdo
                    else:
                        self.spio_en.next = bool(0)
                        self.spio_out.next = bool(0)
                    self.state.next = t_State.TDO
                    self.power_usage_register.next = TDI_POWER
                    self.thermal_register.next = TDI_TEMP

                elif self.state == t_State.TDO:
                    self.spio_en.next = bool(0)  # Disable the spio_out output
                    self.jtag_interface.TCK.next = bool(1)
                    self.state.next = t_State.TMS
                    self.power_usage_register.next = TDO_POWER
                    self.thermal_register.next = TDO_TEMP

                else:
                    raise ValueError("Undefined state")

        if not monitor:
            return state_machine
        else:
            @instance
            def monitor_power_usage():
                print("\t\tTPSP({:s}).power_usage_register:".format(self.name),
                      self.power_usage_register)
                while 1:
                    yield self.power_usage_register
                    print("\t\tTPSP({:s}).power_usage_register:".format(self.name),
                          self.power_usage_register)

            @instance
            def monitor_tempurature():
                print("\t\tTPSP({:s}).thermal_register:".format(self.name), self.thermal_register)
                while 1:
                    yield self.thermal_register
                    print("\t\tTPSP({:s}).thermal_register:".format(self.name),
                          self.thermal_register)

            @instance
            def monitor_state():
                print("\t\tTPSP({:s}).state:".format(self.name), self.state)
                while 1:
                    yield self.state
                    print("\t\tTPSP({:s}).state:".format(self.name), self.state)

            @instance
            def monitor_reset_n():
                print("\t\tTPSP({:s}).reset_n:".format(self.name), self.reset_n)
                while 1:
                    yield self.reset_n
                    print("\t\tTPSP({:s}).reset_n:".format(self.name), self.reset_n)

            @instance
            def monitor_spclk():
                print("\t\tTPSP({:s}).spclk:".format(self.name), self.spclk)
                while 1:
                    yield self.spclk
                    print("\t\tTPSP({:s}).spclk:".format(self.name), self.spclk)

            @instance
            def monitor_spio_in():
                print("\t\tTPSP({:s}).spio_in:".format(self.name), self.spio_in)
                while 1:
                    yield self.spio_in
                    print("\t\tTPSP({:s}).spio_in:".format(self.name),
                          self.spio_in)

            @instance
            def monitor_spio_en():
                print("\t\tTPSP({:s}).spio_en:".format(self.name), self.spio_en)
                while 1:
                    yield self.spio_en
                    print("\t\tTPSP({:s}).spio_en:".format(self.name),
                          self.spio_en)

            @instance
            def monitor_spio_out():
                print("\t\tTPSP({:s}).spio_out:".format(self.name), self.spio_out)
                while 1:
                    yield self.spio_out
                    print("\t\tTPSP({:s}).spio_out:".format(self.name),
                          self.spio_out)

            @instance
            def monitor_tdi():
                print("\t\tTPSP({:s}).tdi:".format(self.name), self.tdi)
                while 1:
                    yield self.tdi
                    print("\t\tTPSP({:s}).tdi:".format(self.name),
                          self.tdi)

            @instance
            def monitor_tms():
                print("\t\tTPSP({:s}).tms:".format(self.name), self.jtag_interface.TMS)
                while 1:
                    yield self.jtag_interface.TMS
                    print("\t\tTPSP({:s}).tms:".format(self.name),
                          self.jtag_interface.TMS)

            @instance
            def monitor_tdo():
                print("\t\tTPSP({:s}).tdo:".format(self.name), self.tdo)
                while 1:
                    yield self.tdo
                    print("\t\tTPSP({:s}).tdo:".format(self.name),
                          self.tdo)

            @instance
            def monitor_tdo_en():
                print("\t\tTPSP({:s}).tdo_en:".format(self.name), self.tdo_en)
                while 1:
                    yield self.tdo_en
                    print("\t\tTPSP({:s}).tdo_en:".format(self.name),
                          self.tdo_en)

            @instance
            def monitor_tck():
                print("\t\tTPSP({:s}).tck:".format(self.name), self.jtag_interface.TCK)
                while 1:
                    yield self.jtag_interface.TCK
                    print("\t\tTPSP({:s}).tck:".format(self.name),
                          self.jtag_interface.TCK)

            @instance
            def monitor_spio_tms():
                print("\t\tTPSP({:s}).spio_tms:".format(self.name), self.spio_tms)
                while 1:
                    yield self.spio_tms
                    print("\t\tTPSP({:s}).spio_tms:".format(self.name),
                          self.spio_tms)

            return state_machine, monitor_reset_n, monitor_spclk, monitor_spio_in, monitor_spio_en, \
                monitor_spio_out, monitor_tdi, monitor_tdo, monitor_tdo_en, monitor_tms, monitor_tck, \
                monitor_state, monitor_power_usage, monitor_tempurature, monitor_spio_tms

    @staticmethod
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
        reset_n = ResetSignal(1, active=0, async=True)
        power_usage = Signal(intbv(0, min=0, max=101))
        thermal = Signal(intbv(0, min=0, max=101))

        tpsp_inst = TPSP('DEMO', spclk, reset_n, spio_in, spio_en, spio_out,
                          jtag_interface, tdi, tdo, tdo_en, power_usage, thermal)
        tpsp_inst.toVerilog()
        tpsp_inst.toVHDL()

    @staticmethod
    @block
    def testbench(monitor=False):
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
        reset_n = ResetSignal(1, active=0, async=True)
        power_usage = Signal(intbv(0, min=0, max=101))
        thermal = Signal(intbv(0, min=0, max=101))

        tpsp_inst = TPSP('DEMO', spclk, reset_n, spio_in, spio_en, spio_out,
                          jtag_interface, tdi, tdo, tdo_en, power_usage, thermal)

        @always(delay(10))
        def clkgen():
            spclk.next = not spclk

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

        return tpsp_inst.TPSP_rtl(monitor=monitor), clkgen, stimulus

if __name__ == '__main__':
    tb = TPSP.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    TPSP.convert()
