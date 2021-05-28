"""

"""
from myhdl import *
from hdl.devices.SN74ABT8244A.cells.InputCell import InputCell
from hdl.devices.SN74ABT8244A.cells.OutputCell import OutputCell
from hdl.devices.SN74ABT8244A.cells.ControlCell import ControlCell


class bsr:
    def __init__(self, si, select, capturedr, shiftdr, updatedr, tck, so, extest,
                 OE_NEG1, Y1_o, Y1_e, Y2_o, Y2_e, A1, A2, OE_NEG2):
        self.tdi = si
        self.select = select
        self.capturedr = capturedr
        self.shiftdr = shiftdr
        self.updatedr = updatedr
        self.tck = tck
        self.tdo = so
        self.extest = extest
        self.OE_NEG1 = OE_NEG1
        self.Y1_o = Y1_o
        self.Y1_e = Y1_e
        self.Y2_o = Y2_o
        self.Y2_e = Y2_e
        self.A1 = A1
        self.A2 = A2
        self.OE_NEG2 = OE_NEG2
        self.tms = None
        self.trst = None

    def configure_jtag(self, tdi, tck, tms, trst, tdo):
        # self.tdi = tdi
        # self.tck = tck
        self.tms = tms
        self.trst = trst
        # self.tdo = tdo

    @block
    def rtl(self):
        ce = Signal(bool(0))
        se = Signal(bool(0))
        ue = Signal(bool(0))
        sis = [Signal(bool(0)) for _ in range(18)]
        oe1 = Signal(bool(0))
        oe2 = Signal(bool(0))
        oe_neg1 = Signal(bool(0))
        oe_neg2 = Signal(bool(0))

        z4_out_cell = OutputCell(self.A2[3], sis[0], ce, se, ue, self.extest,
                                 self.tck, self.tdo, oe_neg2, self.Y2_o[3], self.Y2_e[3])
        z3_out_cell = OutputCell(self.A2[2], sis[1], ce, se, ue, self.extest,
                                 self.tck, sis[0], oe_neg2, self.Y2_o[2], self.Y2_e[2])
        z2_out_cell = OutputCell(self.A2[1], sis[2], ce, se, ue, self.extest,
                                 self.tck, sis[1], oe_neg2, self.Y2_o[1], self.Y2_e[1])
        z1_out_cell = OutputCell(self.A2[0], sis[3], ce, se, ue, self.extest,
                                 self.tck, sis[2], oe_neg2, self.Y2_o[0], self.Y2_e[0])
        y4_out_cell = OutputCell(self.A1[3], sis[4], ce, se, ue, self.extest,
                                 self.tck, sis[3], oe_neg1, self.Y1_o[3], self.Y1_e[3])
        y3_out_cell = OutputCell(self.A1[2], sis[5], ce, se, ue, self.extest,
                                 self.tck, sis[4], oe_neg1, self.Y1_o[2], self.Y1_e[2])
        y2_out_cell = OutputCell(self.A1[1], sis[6], ce, se, ue, self.extest,
                                 self.tck, sis[5], oe_neg1, self.Y1_o[1], self.Y1_e[1])
        y1_out_cell = OutputCell(self.A1[0], sis[7], ce, se, ue, self.extest,
                                 self.tck, sis[6], oe_neg1, self.Y1_o[0], self.Y1_e[0])
        b4_inp_cell = InputCell(self.A2[3], sis[8], ce, se, self.tck, sis[7])
        b3_inp_cell = InputCell(self.A2[2], sis[9], ce, se, self.tck, sis[8])
        b2_inp_cell = InputCell(self.A2[1], sis[10], ce, se, self.tck, sis[9])
        b1_inp_cell = InputCell(self.A2[0], sis[11], ce, se, self.tck, sis[10])
        a4_inp_cell = InputCell(self.A1[3], sis[12], ce, se, self.tck, sis[11])
        a3_inp_cell = InputCell(self.A1[2], sis[13], ce, se, self.tck, sis[12])
        a2_inp_cell = InputCell(self.A1[1], sis[14], ce, se, self.tck, sis[13])
        a1_inp_cell = InputCell(self.A1[0], sis[15], ce, se, self.tck, sis[14])
        c2_ctl_cell = ControlCell(self.OE_NEG2, sis[16], ce, se, ue, self.extest,
                                  self.tck, sis[15], oe2)
        c1_ctl_cell = ControlCell(self.OE_NEG1, self.tdi, ce, se, ue, self.extest,
                                  self.tck, sis[16], oe1)

        # z4_out_cell.configure_jtag(sis[16], self.tck, None, None, self.tdo)
        # z3_out_cell.configure_jtag(sis[15], self.tck, None, None, sis[16])
        # z2_out_cell.configure_jtag(sis[14], self.tck, None, None, sis[15])
        # z1_out_cell.configure_jtag(sis[13], self.tck, None, None, sis[14])
        # y4_out_cell.configure_jtag(sis[12], self.tck, None, None, sis[13])
        # y3_out_cell.configure_jtag(sis[11], self.tck, None, None, sis[12])
        # y2_out_cell.configure_jtag(sis[10], self.tck, None, None, sis[11])
        # y1_out_cell.configure_jtag(sis[9], self.tck, None, None, sis[10])
        # b4_inp_cell.configure_jtag(sis[8], self.tck, None, None, sis[9])
        # b3_inp_cell.configure_jtag(sis[7], self.tck, None, None, sis[8])
        # b2_inp_cell.configure_jtag(sis[6], self.tck, None, None, sis[7])
        # b1_inp_cell.configure_jtag(sis[5], self.tck, None, None, sis[6])
        # a4_inp_cell.configure_jtag(sis[4], self.tck, None, None, sis[5])
        # a3_inp_cell.configure_jtag(sis[3], self.tck, None, None, sis[4])
        # a2_inp_cell.configure_jtag(sis[2], self.tck, None, None, sis[3])
        # a1_inp_cell.configure_jtag(sis[1], self.tck, None, None, sis[2])
        # c2_ctl_cell.configure_jtag(sis[0], self.tck, None, None, sis[1])
        # c1_ctl_cell.configure_jtag(self.tdi, self.tck, None, None, sis[0])

        @always_comb
        def comb_process():
            ce.next = self.select and self.capturedr
            se.next = self.select and self.shiftdr
            ue.next = self.select and self.updatedr

        @always_comb
        def oe_process():
            oe_neg1.next = not oe1
            oe_neg2.next = not oe2

        return comb_process, oe_process, z4_out_cell.rtl(), z3_out_cell.rtl(), z2_out_cell.rtl(), z1_out_cell.rtl(), \
               y4_out_cell.rtl(), y3_out_cell.rtl(), y2_out_cell.rtl(), y1_out_cell.rtl(), \
               b4_inp_cell.rtl(), b3_inp_cell.rtl(), b2_inp_cell.rtl(), b1_inp_cell.rtl(), \
               a4_inp_cell.rtl(), a3_inp_cell.rtl(), a2_inp_cell.rtl(), a1_inp_cell.rtl(), \
               c2_ctl_cell.rtl(), c1_ctl_cell.rtl()
