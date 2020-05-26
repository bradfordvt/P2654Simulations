"""

"""
from myhdl import *
from hdl.clients.jtag.cells.BiDirectionalCell import BiDirectionalCell
from hdl.clients.jtag.cells.ControlCell import ControlCell


class bsr:
    def __init__(self, si, select, capturedr, shiftdr, updatedr, tck, so, extest,
                 DIR, A_i, A_o, A_e, B_i, B_o, B_e, OE_NEG):
        self.tdi = si
        self.select = select
        self.capturedr = capturedr
        self.shiftdr = shiftdr
        self.updatedr = updatedr
        self.tck = tck
        self.tdo = so
        self.extest = extest
        self.DIR = DIR
        self.A_i = A_i
        self.A_o = A_o
        self.A_e = A_e
        self.B_i = B_i
        self.B_o = B_o
        self.B_e = B_e
        self.OE_NEG = OE_NEG

    @block
    def rtl(self):
        ce = Signal(bool(0))
        se = Signal(bool(0))
        ue = Signal(bool(0))
        sis = [Signal(bool(0)) for _ in range(18)]
        acore = [Signal(bool(0)) for _ in range(8)]
        bcore = [Signal(bool(0)) for _ in range(8)]
        dir = Signal(bool(1))
        oe_neg = Signal(bool(1))
        oea = Signal(bool(0))
        oeb = Signal(bool(0))
        b8_out_cell = BiDirectionalCell(acore[7], bcore[7], sis[16], ce, se, ue, self.extest, self.tck, self.tdo, oeb, self.B_i[7], self.B_o[7], self.B_e[7])
        b7_out_cell = BiDirectionalCell(acore[6], bcore[6], sis[15], ce, se, ue, self.extest, self.tck, sis[16], oeb, self.B_i[6], self.B_o[6], self.B_e[6])
        b6_out_cell = BiDirectionalCell(acore[5], bcore[5], sis[14], ce, se, ue, self.extest, self.tck, sis[15], oeb, self.B_i[5], self.B_o[5], self.B_e[5])
        b5_out_cell = BiDirectionalCell(acore[4], bcore[4], sis[13], ce, se, ue, self.extest, self.tck, sis[14], oeb, self.B_i[4], self.B_o[4], self.B_e[4])
        b4_out_cell = BiDirectionalCell(acore[3], bcore[3], sis[12], ce, se, ue, self.extest, self.tck, sis[13], oeb, self.B_i[3], self.B_o[3], self.B_e[3])
        b3_out_cell = BiDirectionalCell(acore[2], bcore[2], sis[11], ce, se, ue, self.extest, self.tck, sis[12], oeb, self.B_i[2], self.B_o[2], self.B_e[2])
        b2_out_cell = BiDirectionalCell(acore[1], bcore[1], sis[10], ce, se, ue, self.extest, self.tck, sis[11], oeb, self.B_i[1], self.B_o[1], self.B_e[1])
        b1_out_cell = BiDirectionalCell(acore[0], bcore[0], sis[9], ce, se, ue, self.extest, self.tck, sis[10], oeb, self.B_i[0], self.B_o[0], self.B_e[0])
        a8_out_cell = BiDirectionalCell(bcore[7], acore[7], sis[8], ce, se, ue, self.extest, self.tck, sis[9], oea, self.A_i[7], self.A_o[7], self.A_e[7])
        a7_out_cell = BiDirectionalCell(bcore[6], acore[6], sis[7], ce, se, ue, self.extest, self.tck, sis[8], oea, self.A_i[6], self.A_o[6], self.A_e[6])
        a6_out_cell = BiDirectionalCell(bcore[5], acore[5], sis[6], ce, se, ue, self.extest, self.tck, sis[7], oea, self.A_i[5], self.A_o[5], self.A_e[5])
        a5_out_cell = BiDirectionalCell(bcore[4], acore[4], sis[5], ce, se, ue, self.extest, self.tck, sis[6], oea, self.A_i[4], self.A_o[4], self.A_e[4])
        a4_out_cell = BiDirectionalCell(bcore[3], acore[3], sis[4], ce, se, ue, self.extest, self.tck, sis[5], oea, self.A_i[3], self.A_o[3], self.A_e[3])
        a3_out_cell = BiDirectionalCell(bcore[2], acore[2], sis[3], ce, se, ue, self.extest, self.tck, sis[4], oea, self.A_i[2], self.A_o[2], self.A_e[2])
        a2_out_cell = BiDirectionalCell(bcore[1], acore[1], sis[2], ce, se, ue, self.extest, self.tck, sis[3], oea, self.A_i[1], self.A_o[1], self.A_e[1])
        a1_out_cell = BiDirectionalCell(bcore[0], acore[0], sis[1], ce, se, ue, self.extest, self.tck, sis[2], oea, self.A_i[0], self.A_o[0], self.A_e[0])
        oe_in_ctl_cell = ControlCell(self.OE_NEG, sis[0], ce, se, ue, self.extest, self.tck, sis[1], oe_neg)
        dir_ctl_cell = ControlCell(self.DIR, self.tdi, ce, se, ue, self.extest, self.tck, sis[0], dir)

        @always_comb
        def comb_process():
            ce.next = self.select and self.capturedr
            se.next = self.select and self.shiftdr
            ue.next = self.select and self.updatedr
            oea.next = not dir and not oe_neg
            oeb.next = not oe_neg and dir

        return comb_process, b8_out_cell, b7_out_cell, b6_out_cell, b5_out_cell, \
               b4_out_cell, b3_out_cell, b2_out_cell, b1_out_cell, \
               a8_out_cell, a7_out_cell, a6_out_cell, a5_out_cell, \
               a4_out_cell, a3_out_cell, a2_out_cell, a1_out_cell, \
               dir_ctl_cell.rtl(), oe_in_ctl_cell.rtl()
