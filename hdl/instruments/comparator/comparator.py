"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Simulation of a comparator comparator
"""
from myhdl import *
import os
import os.path

period = 20  # clk frequency = 50 MHz


@block
def comparator(path, name, clock, reset_n, temperature,
               low_register, high_register,
               status_register, monitor=False):
    """

    :param path: Dot path of the path of this instance
    :param name: Instance name for debug logger (path instance)
    :param clock: Clock signal used to change state
    :param reset_n: Reset signal for state machine. 0=Reset, 1=No reset
    :param temperature: Register where output value of temperature
    :param low_register: Low temperature setting for good range
    :param high_register: High temperature setting for good range
    :param status_register: Status of comparison Signal(intbv(0)[8:])
            Bit0: 1=Temperature fell below low value, 0=Temperature at or above low value
            Bit1: 1=Temperature above high value, 0=Temperature at or below high value
            Bits2-7: Reserved (default to 0)
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    @always(clock.posedge)
    def compare_temp():
        if reset_n == bool(0):
            status_register.next[0] = bool(0)
            status_register.next[1] = bool(0)
        else:
            if temperature < low_register:
                status_register.next[0] = bool(1)
            else:
                status_register.next[0] = bool(0)
            if temperature > high_register:
                status_register.next[1] = bool(1)
            else:
                status_register.next[1] = bool(0)

    if not monitor:
        return compare_temp
    else:
        @instance
        def monitor_temperature():
            print("\t\tcomparator({:s}): temperature".format(path + '.' + name), int(temperature))
            while 1:
                yield temperature
                print("\t\tcomparator({:s}): temperature".format(path + '.' + name), int(temperature))

        @instance
        def monitor_low_register():
            print("\t\tcomparator({:s}): low_register".format(path + '.' + name), int(low_register))
            while 1:
                yield low_register
                print("\t\tcomparator({:s}): low_register".format(path + '.' + name), int(low_register))

        @instance
        def monitor_high_register():
            print("\t\tcomparator({:s}): high_register".format(path + '.' + name), int(high_register))
            while 1:
                yield high_register
                print("\t\tcomparator({:s}): high_register".format(path + '.' + name), int(high_register))

        @instance
        def monitor_status_register():
            print("\t\tcomparator({:s}): status_register".format(path + '.' + name), status_register)
            while 1:
                yield status_register
                print("\t\tcomparator({:s}): status_register".format(path + '.' + name), status_register)

        return compare_temp, monitor_temperature, monitor_low_register, monitor_high_register, \
            monitor_status_register



@block
def comparator_tb(monitor=False):
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
    status_register = Signal(intbv(0)[8:])

    comp_inst = comparator('TOP', 'COMP0', clock, reset_n, temperature,
                           low_register, high_register, status_register, monitor=monitor)

    @instance
    def clkgen():
        while True:
            clock.next = not clock
            yield delay(1)

    @instance
    def stimulus():
        """
        Perform simulated temperature measurements
        :return:
        """
        # Reset the comparator
        reset_n.next = bool(0)
        yield delay(10)
        reset_n.next = bool(1)
        yield delay(10)
        assert(status_register[0] == bool(0))
        assert(status_register[1] == bool(0))

        ####################################################
        temperature.next = 80
        low_register.next = 75
        high_register.next = 400
        yield delay(10)
        assert (status_register[0] == bool(0))
        assert (status_register[1] == bool(0))

        temperature.next = 75
        low_register.next = 75
        yield delay(10)
        assert (status_register[0] == bool(0))
        assert (status_register[1] == bool(0))

        temperature.next = 70
        low_register.next = 75
        yield delay(10)
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

    return comp_inst, clkgen, stimulus


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
    status_register = Signal(intbv(0)[8:])

    comp_inst = comparator('TOP', 'COMP0', clock, reset_n, temperature,
                           low_register, high_register, status_register, monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    comp_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="comparator")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    comp_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="comparator")
    tb = comparator_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="comparator_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="comparator_tb")


def main():
    tb = comparator_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
