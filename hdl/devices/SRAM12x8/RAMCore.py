"""
Copyright (c) 2020 Bradford G. Van Treuren
See the licence file in the top directory

IP Logic for SRAM example to perform standard
memory testing use case for P2654 simulation.
"""
from myhdl import *


class RAMCore:
    def __init__(self, din, dout, waddr, raddr, we, clk, data_width=8, addr_width=16):
        self.din = din
        self.dout = dout
        self.waddr = waddr
        self.raddr = raddr
        self.we = we
        self.clk = clk
        self.data_width = data_width
        self.addr_width = addr_width

    @block
    def rtl(self):
        memory = [Signal(intbv(0)[self.data_width:]) for _ in range(2 ** self.addr_width)]

        @always(self.clk.posedge)
        def memory_process():
            if self.we:
                memory[self.waddr.val].next = self.din

        @always_comb
        def out_process():
            self.dout.next = memory[self.raddr.val]

        return memory_process, out_process
