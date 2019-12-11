"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""


from myhdl import *


period = 20  # clk frequency = 50 MHz


@block
def wbsyscon(clk_o, rst_o):
    clk = Signal(bool(0))
    rst = Signal(bool(0))

    @instance
    def clk_gen():
        while True:
            clk.next = not clk
            yield delay(period // 2)

    @instance
    def power_on_reset_gen():
        yield delay(period * 2)
        rst.next = True
        yield delay(period)
        rst.next = False

    @always_comb
    def comb0():
        clk_o.next = clk
        rst_o.next = rst

    return clk_gen, power_on_reset_gen, comb0
