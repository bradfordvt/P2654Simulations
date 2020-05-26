"""

"""
from myhdl import *
from hdl.clients.jtag.cells.InputCell import *


@block
def bypass(si, select, capturedr, shiftdr, tck, so):
    pi = Signal(bool(0))
    ce = Signal(bool(0))
    se = Signal(bool(0))
    input_cell_inst = InputCell(pi, si, ce, se, tck, so)

    @always_comb
    def comb_process():
        ce.next = select and capturedr
        se.next = select and shiftdr

    return input_cell_inst, comb_process
