"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

"""
from myhdl import *


class RAMInterface:
    def __init__(self, addr_width=10, data_width=8):
        self.clk = Signal(bool(0))
        self.reset_n = ResetSignal(1, 0, True)
        self.Write = Signal(bool(0))
        self.Awr = Signal(intbv(0)[addr_width:])
        self.Ard = Signal(intbv(0)[addr_width:])
        self.Din = Signal(intbv(0)[data_width:])
        self.Dout = Signal(intbv(0)[data_width:])
        self.addr_width = addr_width
        self.data_width = data_width


@block
def RAM(ram_interface):
    """

    :param ram_interface: Signal interface to block RAM device
    """
    memory = [Signal(intbv(0)[ram_interface.data_width:]) for _ in range(2**ram_interface.addr_width)]

    @always_seq(ram_interface.clk.posedge, reset=ram_interface.reset_n)
    def memory_process():
        if ram_interface.Write == 1:
            memory[ram_interface.Awr.val].next = ram_interface.Din
        # print("Ard = ", ram_interface.Ard)

    @always_comb
    def out_process():
        ram_interface.Dout.next = memory[ram_interface.Ard.val]

    return memory_process, out_process

