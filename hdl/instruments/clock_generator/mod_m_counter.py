"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Clock Generator
Based on the myHDL design at https://buildmedia.readthedocs.org/media/pdf/fpga-designs-with-myhdl/latest/fpga-designs-with-myhdl.pdf.
"""
from myhdl import *
import os
import os.path


class mod_m_counter:
    def __init__(self, path, name, clk, reset_n, complete_tick, count, M, N):
        """
        Modulo M counter
        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logger (path instance)
        :param clk: Reference Clock
        :param reset_n: Reset signal to reset the logic
        :param complete_tick: Output clock
        :param count: The internal counter value
        :param M: Max count
        :param N: minimum bits required to represent M
        """
        self.path = path
        self.name = name
        self.clk = clk
        self.reset_n = reset_n
        self.complete_tick = complete_tick
        self.count = count
        self.M = M
        self.N = N
        self.count_reg = Signal(intbv(0)[N:0])
        self.count_next = Signal(intbv(0)[N:0])

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
        return self.mod_m_counter_rtl(monitor=monitor)

    @block
    def mod_m_counter_rtl(self, monitor=False):
        """
        The logic for the Clock Generator
        :return: The generator methods performing the logic decisions
        """

        @always(self.clk.posedge, self.reset_n.negedge)
        def logic_reg():
            if self.reset_n == 0:
                self.count_reg.next = 0
            else:
                self.count_reg.next = self.count_next

        @ always_comb
        def logic_next():
            if self.count_reg == self.M - 1:
                self.count_next.next = 0
                self.complete_tick.next = 1
            else:
                self.count_next.next = self.count_reg + 1
                self.complete_tick.next = 0

        @ always_comb
        def out_val():
            self.count.next = self.count_reg

        if not monitor:
            return out_val, logic_next, logic_reg
        else:
            @instance
            def monitor_clk():
                print("\t\tmod_m_counter({:s}): clk".format(self.path + '.' + self.name), self.clk)
                while 1:
                    yield self.clk
                    print("\t\tmod_m_counter({:s}): clk".format(self.path + '.' + self.name), self.clk)

            @instance
            def monitor_reset_n():
                print("\t\tmod_m_counter({:s}): reset_n".format(self.path + '.' + self.name), self.reset_n)
                while 1:
                    yield self.reset_n
                    print("\t\tmod_m_counter({:s}): reset_n".format(self.path + '.' + self.name), self.reset_n)

            @instance
            def monitor_complete_tick():
                print("\t\tmod_m_counter({:s}): complete_tick".format(self.path + '.' + self.name), self.complete_tick)
                while 1:
                    yield self.complete_tick
                    print("\t\tmod_m_counter({:s}): complete_tick".format(self.path + '.' + self.name), self.complete_tick)

            return out_val, logic_next, logic_reg,\
                monitor_reset_n, monitor_clk, monitor_complete_tick

    @staticmethod
    def convert():
        """
        Convert the myHDL design into VHDL and Verilog
        :return:
        """
        N = 3
        M = 5
        clk = Signal(bool(0))
        reset_n = Signal(bool(1))
        complete_tick = Signal(bool(0))
        count = Signal(intbv(0)[N:0])

        cg_inst = mod_m_counter('TOP', 'CG0', clk, reset_n, complete_tick, count, M, N)

        cg_inst.toVerilog()
        cg_inst.toVHDL()

    @staticmethod
    @block
    def testbench(monitor=False):
        """
        Test bench interface for a quick test of the operation of the design
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """
        H = bool(1)
        L = bool(0)
        N = 3
        M = 5
        clk = Signal(bool(0))
        reset_n = Signal(bool(1))
        complete_tick = Signal(bool(0))
        count = Signal(intbv(0)[N:0])
        num_ticks = 0

        cg_inst = mod_m_counter('TOP', 'CG0', clk, reset_n, complete_tick, count, M, N)

        @always(delay(10))
        def clkgen():
            # 50 MHz clock, 20 nsec period
            clk.next = not clk

        @instance
        def monitor_complete_tick():
            nonlocal num_ticks
            nonlocal complete_tick
            while 1:
                yield complete_tick.posedge
                num_ticks += 1

        @instance
        def stimulus():
            """
            Perform instruction decoding for various instructions
            :return:
            """
            nonlocal num_ticks
            # Reset the Clock Generator
            reset_n.next = bool(0)
            yield delay(10)
            reset_n.next = bool(1)
            yield delay(10000)
            print("num_ticks = ", num_ticks)
            assert(num_ticks == 100)

            raise StopSimulation()

        return cg_inst.mod_m_counter_rtl(monitor=monitor), clkgen, monitor_complete_tick, stimulus


if __name__ == '__main__':
    tb = mod_m_counter.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    mod_m_counter.convert()
