"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
Ported over from Verilog version found at: https://github.com/ZipCPU/xulalx25soc/blob/master/rtl/wbgpio.v
// Purpose:	This extremely simple GPIO controller, although minimally
//		featured, is designed to control up to sixteen general purpose
//	input and sixteen general purpose output lines of a module from a
//	single address on a 32-bit wishbone bus.
//
//	Input GPIO values are contained in the top 16-bits.  Any change in
//	input values will generate an interrupt.
//
//	Output GPIO values are contained in the bottom 16-bits.  To change an
//	output GPIO value, writes to this port must also set a bit in the
//	upper sixteen bits.  Hence, to set GPIO output zero, one would write
//	a 0x010001 to the port, whereas a 0x010000 would clear the bit.  This
//	interface makes it possible to change only the bit of interest, without
//	needing to capture and maintain the prior bit values--something that
//	might be difficult from a interrupt context within a CPU.
//
//	Unlike other controllers, this controller offers no capability to
//	change input/output direction, or to implement pull-up or pull-down
//	resistors.  It simply changes and adjusts the values going out the
//	output pins, while allowing a user to read the values on the input
//	pins.
//
//	Any change of an input pin value will result in the generation of an
//	interrupt signal.
"""

from myhdl import *


@block
def wbgpio(i_clk, i_wb_cyc, i_wb_stb, i_wb_we, i_wb_data, o_wb_data, i_gpio, o_gpio, o_ack, o_int, NIN=16, NOUT=16,
           DEFAULT=intbv(0)[16:]):
    x_gpio = Signal(DEFAULT)
    q_gpio = Signal(DEFAULT)
    r_gpio = Signal(DEFAULT)
    hi_bits = Signal(intbv(0)[16:])
    low_bits = Signal(intbv(0)[16:])

    @always(i_clk.posedge)
    def logic0():
        if i_wb_stb and i_wb_we:
            # print("*******************************************************************************")
            # print("wbgpio.logic0: i_wb_data = ", hex(i_wb_data), ", ", bin(i_wb_data))
            # print("wbgpio.logic0: ~i_wb_data = ", ~i_wb_data)
            # print("wdgpio.logic0: ~i_wb_data[(NOUT +  16 - 1):16] = ", ~i_wb_data[(NOUT + 16 - 1):16])
            # print("wbgpio.logic0: i_wb_data[(NOUT - 1):0] = ", i_wb_data[(NOUT - 1):0])
            # print("wbgpio.logic0: i_wb_data[(NOUT + 16 - 1):16] = ", i_wb_data[(NOUT + 16 - 1):16])
            # print("wbgpio.logic0: (i_wb_data[(NOUT - 1):0]) & (i_wb_data[(NOUT + 16 - 1):16]) = ", (i_wb_data[(NOUT - 1):0]) & (i_wb_data[(NOUT + 16 - 1):16]))
            # print("wbgpio.logic0: (o_gpio & (~i_wb_data[(NOUT + 16 - 1):16])) | ((i_wb_data[(NOUT - 1):0]) & (i_wb_data[(NOUT + 16 - 1):16])) = ", (o_gpio & (~i_wb_data[(NOUT + 16 - 1):16])) | ((i_wb_data[(NOUT - 1):0]) & (i_wb_data[(NOUT + 16 - 1):16])))
            # print("*******************************************************************************")
            # o_gpio.next = (o_gpio & (~i_wb_data[(NOUT + 16 - 1):16])) | (
            #             (i_wb_data[(NOUT - 1):0]) & (i_wb_data[(NOUT + 16 - 1):16]))
            o_gpio.next = i_wb_data[(NOUT - 1):0]
            # print("wbgpio.logic0: o_gpio.next = ", hex(o_gpio.next), ", ", bin(o_gpio.next))

    @always(i_clk.posedge)
    def logic1():
        x_gpio.next = i_gpio
        q_gpio.next = x_gpio
        r_gpio.next = q_gpio
        o_int.next = (x_gpio != r_gpio)

    @always_comb
    def comb0():
        hi_bits.next[NIN:] = r_gpio
        low_bits.next[NOUT:] = o_gpio
        if NIN < 16:
            hi_bits.next[16:NIN] = 0
        if NOUT < 16:
            low_bits.next[16:NOUT] = 0

    @always_comb
    def comb1():
        o_wb_data.next = concat(hi_bits, low_bits)

    @always(i_clk.posedge)
    def logic2():
        # print("wbgpio.logic2: i_wb_stb = ", i_wb_stb, ", i_wb_cyc = ", i_wb_cyc)
        o_ack.next = i_wb_stb and i_wb_cyc

    return logic0, logic1, logic2, comb0, comb1
