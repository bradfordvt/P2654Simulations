"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Clock Generator
Based on the myHDL design at https://buildmedia.readthedocs.org/media/pdf/fpga-designs-with-myhdl/latest/fpga-designs-with-myhdl.pdf.
"""
from myhdl import *
import os
import os.path
from hdl.instruments.clock_generator.mod_m_counter import mod_m_counter

period = 20  # clk frequency = 50 MHz


@block
def clock_tick(path, name, clk, reset_n, clk_pulse, M=5, N=3, monitor=False):
    """
    Clock pulse generator
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param clk: Reference Clock
    :param reset_n: Reset signal to reset the logic
    :param clk_pulse: Output clock pulse
    :param M: Max count
    :param N: minimum bits required to represent M
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    count = Signal(intbv(0)[N:0])

    mod_m_counter_inst = mod_m_counter(path + name, "MMC0", clk, reset_n, clk_pulse, count, M=M, N=N, monitor=monitor)
    return mod_m_counter_inst


@block
def clock_tick_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    H = bool(1)
    L = bool(0)
    N = 3
    M = Signal(intbv(5)[N:])
    clk = Signal(bool(0))
    reset_n = Signal(bool(1))
    complete_tick = Signal(bool(0))
    num_ticks = Signal(intbv(0, min=0, max=200))

    cg_inst = clock_tick('TOP', 'CG0', clk, reset_n, complete_tick, M, N, monitor=monitor)

    @instance
    def clkgen():
        while True:
            # 50 MHz clock, 20 nsec period
            clk.next = not clk
            yield delay(period // 2)

    @instance
    def monitor_complete_tick():
        while 1:
            yield complete_tick.posedge
            num_ticks.next = num_ticks + 1

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
        yield delay(10000)
        # print("num_ticks = ", int(num_ticks))
        assert(int(num_ticks) == 100)

        raise StopSimulation()

    return cg_inst, clkgen, monitor_complete_tick, stimulus


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    N = 3
    M = Signal(intbv(5)[N:])
    clk = Signal(bool(0))
    reset_n = Signal(bool(1))
    complete_tick = Signal(bool(0))

    cg_inst = clock_tick('TOP', 'CG0', clk, reset_n, complete_tick, M, N, monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    cg_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="clock_tick")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    cg_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="clock_tick")
    tb = clock_tick_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="clock_tick_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="clock_tick_tb")


def main():
    tb = clock_tick_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
