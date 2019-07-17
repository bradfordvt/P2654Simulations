"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

"""
from myhdl import *


class RAM:
    """

    """
    def __init__(self, clk, reset_n, Write, Awr, Ard, Din, Dout, addr_width=10, data_width=8):
        """

        :param clk:
        :param reset_n:
        :param Write:
        :param Awr:
        :param Ard:
        :param Din:
        :param Dout:
        :param addr_width:
        :param data_width:
        """
        self.clk = clk
        self.reset_n = reset_n
        self.Write = Write
        self.Awr = Awr
        self.Ard = Ard
        self.Din = Din
        self.Dout = Dout
        self.addr_width = addr_width
        self.data_width = data_width
        self.memory = [Signal(intbv(0)[data_width:]) for _ in range(2**addr_width)]

    def rtl(self, monitor=False):
        """
        Wrapper around the RTL logic to get a meaningful name during conversion
        :param monitor:
        :return:
        """
        return self.RAM_rtl(monitor=monitor)

    @block
    def RAM_rtl(self, monitor=False):
        """
        Logic to implement the JTAGHost JTAGCtrlMaster BRAM block
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """
        @always_seq(self.clk.posedge, reset=self.reset_n)
        def memory_process():
            if self.Write == 1:
                self.memory[self.Awr].next = self.Din
            # print("self.Ard = ", self.Ard)

        @always_comb
        def out_process():
            self.Dout.next = self.memory[self.Ard]

        return memory_process, out_process

