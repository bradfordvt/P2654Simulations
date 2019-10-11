"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Clock Frequency Counter
Based on the VHDL design at https://surf-vhdl.com/compute-frequency-clock/.
"""
from myhdl import *
from hdl.instruments.clock_generator.clock_tick import clock_tick
from hdl.instruments.clock_counter.clock_freq_counter import clock_freq_counter
import os
import os.path

period = 20  # clk frequency = 50 MHz


@block
def IP_1(path, name, clk, reset_n, o_clock_freq, count_max=255, monitor=False):
    """
    Logic to represent the IP_1 core of the Rearick use case model
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param clk: Reference Clock
    :param reset_n: Reset signal to reset the logic
    :param o_clock_freq: Signal(intbv(0)[16:]) The count of ticks on clk_pulse (Output to register port)
    :param count_max: Amount of clk ticks before clk_pulse ticks (Input from register port)
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: List of generators used for simulation of this instance
    """
    clk_pulse = Signal(bool(0))
    # int_count_max = int(count_max)
    ck_tick_inst = clock_tick(path + "." + name, "CKTICK0", clk, reset_n, clk_pulse, M=count_max, N=8, monitor=monitor)
    cfc_inst = clock_freq_counter(path + "." + name, "CFC0", clk, reset_n, clk_pulse, o_clock_freq, monitor=monitor)

    if monitor == False:
        return ck_tick_inst, cfc_inst
    else:
        @instance
        def monitor_clk_pulse():
            print("\t\tIP_1({:s}): clk_pulse".format(path + '.' + name), clk_pulse)
            while 1:
                yield clk_pulse
                print("\t\tIP_1({:s}): clk_pulse".format(path + '.' + name), clk_pulse)

        @instance
        def monitor_o_clock_freq():
            print("\t\tIP_1({:s}): o_clock_freq".format(path + '.' + name), o_clock_freq)
            while 1:
                yield o_clock_freq
                print("\t\tIP_1({:s}): o_clock_freq".format(path + '.' + name), o_clock_freq)

        return ck_tick_inst, cfc_inst, monitor_clk_pulse, monitor_o_clock_freq


@block
def IP_1_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    clk = Signal(bool(0))
    reset_n = Signal(bool(1))
    o_clock_freq = Signal(modbv(0)[16:])
    count_max = Signal(intbv(5)[8:])

    ip1_inst = IP_1('TOP', 'IP_1[0]', clk, reset_n, o_clock_freq, count_max=count_max, monitor=monitor)

    @instance
    def clkgen():
        while True:
            # 50 MHz clock, 20 nsec period
            clk.next = not clk
            yield delay(period // 2)

    @instance
    def stimulus():
        """
        Perform instruction decoding for various instructions
        :return:
        """
        # Reset the Clock Generator
        reset_n.next = bool(0)
        yield delay(10)
        reset_n.next = bool(1)
        yield delay(100000)
        print("o_clock_freq = ", int(o_clock_freq))
        assert(int(o_clock_freq) == 819)

        raise StopSimulation()

    return ip1_inst, clkgen, stimulus


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    clk = Signal(bool(0))
    reset_n = Signal(bool(1))
    o_clock_freq = Signal(modbv(0)[16:])
    count_max = Signal(intbv(5)[8:])

    ip1_inst = IP_1('TOP', 'IP_1[0]', clk, reset_n, o_clock_freq, count_max=count_max, monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    ip1_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="IP_1")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    ip1_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="IP_1")
    tb = IP_1_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="IP_1_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="IP_1_tb")


def main():
    tb = IP_1_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
