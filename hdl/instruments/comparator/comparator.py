"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Simulation of a comparator comparator
"""
from myhdl import *
import os
import os.path


class comparator:
    """
    Class structure implementing the RTL for the instrument.
    """
    def __init__(self, parent, name, clock, reset_n, temperature,
                 low_register, high_register,
                 status_register):
        """

        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logger (path instance)
        :param clock: Clock signal used to change state
        :param reset_n: Reset signal for state machine. 0=Reset, 1=No reset
        :param temperature: Register where output value of temperature
        :param low_register: Low temperature setting for good range
        :param high_register: High temperature setting for good range
        :param status_register: Status of comparison [Signal(bool(0)), Signal(bool(0))]
                Bit0: 1=Temperature fell below low value, 0=Temperature at or above low value
                Bit1: 1=Temperature above high value, 0=Temperature at or below high value
        """
        self.parent = parent
        self.name = name
        self.clock = clock
        self.reset_n = reset_n
        self.temperature = temperature
        self.low_register = low_register
        self.high_register = high_register
        self.status_register = status_register

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
        return self.comparator_rtl(monitor=monitor)

    @block
    def comparator_rtl(self, monitor=False):
        """
        The logic for the comparator
        :return: The generator methods performing the logic decisions
        """
        @always(self.clock.posedge)
        def compare_temp():
            if self.reset_n == bool(0):
                self.status_register[0].next = bool(0)
                self.status_register[1].next = bool(0)
            else:
                if self.temperature < self.low_register:
                    self.status_register[0].next = bool(1)
                else:
                    self.status_register[0].next = bool(0)
                if self.temperature > self.high_register:
                    self.status_register[1].next = bool(1)
                else:
                    self.status_register[1].next = bool(0)

        if not monitor:
            return compare_temp
        else:
            @instance
            def monitor_temperature():
                print("\t\tcomparator({:s}): temperature".format(self.parent + '.' + self.name), int(self.temperature))
                while 1:
                    yield self.temperature
                    print("\t\tcomparator({:s}): temperature".format(self.parent + '.' + self.name), int(self.temperature))

            @instance
            def monitor_low_register():
                print("\t\tcomparator({:s}): low_register".format(self.parent + '.' + self.name), int(self.low_register))
                while 1:
                    yield self.low_register
                    print("\t\tcomparator({:s}): low_register".format(self.parent + '.' + self.name), int(self.low_register))

            @instance
            def monitor_high_register():
                print("\t\tcomparator({:s}): high_register".format(self.parent + '.' + self.name), int(self.high_register))
                while 1:
                    yield self.high_register
                    print("\t\tcomparator({:s}): high_register".format(self.parent + '.' + self.name), int(self.high_register))

            @instance
            def monitor_status_register():
                print("\t\tcomparator({:s}): status_register".format(self.parent + '.' + self.name), self.status_register)
                while 1:
                    yield self.status_register
                    print("\t\tcomparator({:s}): status_register".format(self.parent + '.' + self.name), self.status_register)

            return compare_temp, monitor_temperature, monitor_low_register, monitor_high_register, \
                monitor_status_register

    @staticmethod
    def convert():
        """
        Convert the myHDL design into VHDL and Verilog
        :return:
        """
        clock = Signal(bool(0))
        reset_n = Signal(bool(1))
        temperature = Signal(intbv(70, min=0, max=451))
        low_register = Signal(intbv(0, min=0, max=451))
        high_register = Signal(intbv(0, min=0, max=451))
        status_register = [Signal(bool(0)) for _ in range(2)]

        comp_inst = comparator('TOP', 'COMP0', clock, reset_n, temperature,
                               low_register, high_register, status_register)

        comp_inst.toVerilog()
        comp_inst.toVHDL()

    @staticmethod
    @block
    def testbench(monitor=False):
        """
        Test bench interface for a quick test of the operation of the design
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """
        clock = Signal(bool(0))
        reset_n = Signal(bool(1))
        temperature = Signal(intbv(70, min=0, max=451))
        low_register = Signal(intbv(70, min=0, max=451))
        high_register = Signal(intbv(400, min=0, max=451))
        status_register = [Signal(bool(0)) for _ in range(2)]

        comp_inst = comparator('TOP', 'COMP0', clock, reset_n, temperature,
                               low_register, high_register, status_register)

        @always(delay(1))
        def clkgen():
            clock.next = not clock

        @instance
        def stimulus():
            """
            Perform simulated temperature measurements
            :return:
            """
            # Reset the comparator
            reset_n.next = bool(0)
            yield delay(1)
            reset_n.next = bool(1)
            yield delay(10)
            assert(status_register[0] == bool(0))
            assert(status_register[1] == bool(0))

            ####################################################
            temperature.next = 80
            low_register.next = 75
            high_register.next = 400
            yield delay(1)
            assert (status_register[0] == bool(0))
            assert (status_register[1] == bool(0))

            temperature.next = 75
            low_register.next = 75
            yield delay(1)
            assert (status_register[0] == bool(0))
            assert (status_register[1] == bool(0))

            temperature.next = 70
            low_register.next = 75
            yield delay(1)
            assert (status_register[0] == bool(1))
            assert (status_register[1] == bool(0))

            temperature.next = 400
            low_register.next = 75
            yield delay(10)
            assert (status_register[0] == bool(0))
            assert (status_register[1] == bool(0))

            temperature.next = 401
            low_register.next = 75
            yield delay(10)
            assert (status_register[0] == bool(0))
            assert (status_register[1] == bool(1))

            temperature.next = 399
            low_register.next = 75
            yield delay(10)
            assert (status_register[0] == bool(0))
            assert (status_register[1] == bool(0))

            raise StopSimulation()

        return comp_inst.comparator_rtl(monitor=monitor), clkgen, stimulus


if __name__ == '__main__':
    tb = comparator.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    comparator.convert()
