"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import block, delay, instance


@block
def clk_driver(clk, period=20):

    low_time = int(period / 2)
    high_time = period - low_time

    @instance
    def drive_clk():
        while True:
            yield delay(low_time)
            clk.next = 1
            yield delay(high_time)
            clk.next = 0

    return drive_clk
