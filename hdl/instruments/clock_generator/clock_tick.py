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


class clock_tick:
    def __init__(self, path, name, clk, reset_n, clk_pulse, M, N):
        """
        Clock pulse generator
        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logger (path instance)
        :param clk: Reference Clock
        :param reset_n: Reset signal to reset the logic
        :param clk_pulse: Output clock pulse
        :param M: Max count
        :param N: minimum bits required to represent M
        """
        self.path = path
        self.name = name
        self.clk = clk
        self.reset_n = reset_n
        self.clk_pulse = clk_pulse
        self.M = M
        self.N = N
        self.count = Signal(intbv(0)[N:0])

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
        return self.clock_tick_rtl(monitor=monitor)

    @block
    def clock_tick_rtl(self, monitor=False):
        """
        The logic for the Clock Generator
        :return: The generator methods performing the logic decisions
        """
        mod_m_counter_inst = mod_m_counter(self.clk, self.reset_n, self.clk_pulse, self.count, self.M, self.N)
        return mod_m_counter_inst.rtl(monitor=monitor)
