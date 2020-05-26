"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

IP Logic for Pure JTAG device core containing BSR, BYPASS, and IDCODE registers to perform standard
interconnect testing use case for P2654 simulation.
"""
from myhdl import *
from hdl.devices.SN74ABT8245A.tap.tap_defines import *
from hdl.devices.SN74ABT8245A.tap.tap_top import *
from hdl.devices.SN74ABT8245A.registers.bsr import bsr
import os


period = 20  # clk frequency = 50 MHz


class SN74ABT8245ACore:
    def __init__(self, parent, name,
                 DIR, A_i, A_o, A_e, B_i, B_o, B_e, OE_NEG,
                 tdo_padoe_o, tdi, tck, tms, tdo
                 ):
        """

        :param parent:
        :param name:
        :param DIR: Direction Control Signal (0=B to A, 1=A to B)
        :param A_i: 8-bit Input Data Bus
        :param A_o: 8-bit Output Data Bus
        :param A_e: 8-bit Enable Control Bus
        :param B_i: 8-bit Input Data Bus
        :param B_o: 8-bit Output Data Bus
        :param B_e: 8-bit Enable Control Bus
        :param OE_NEG: Input signal to control the A/B output enable (0=enabled, 1=disabled)
        :param tdo_padoe_o: tdo_padoe_o = Signal(bool(0)) Output enable for TDO
        """
        self.parent = parent
        self.name = name
        # OE Signals
        self.DIR = DIR
        self.OE_NEG = OE_NEG
        # IO Signals
        self.A_i = A_i
        self.A_o = A_o
        self.A_e = A_e
        self.B_i = B_i
        self.B_o = B_o
        self.B_e = B_e
        # self.B = [B[i] for i in range(8)]
        # self.A = [A[i] for i in range(8)]
        # JTAG signals
        self.tdo_padoe_o = tdo_padoe_o
        self.oeb = Signal(bool(0))
        self.oea = Signal(bool(0))

        # JTAG signals for attached client of interface
        self.tck = tck
        self.tms = tms
        self.tdi = tdi
        self.tdo = tdo

    @block
    def rtl(self, monitor=False):
        reset_n = Signal(bool(1))

        capture_dr_o = Signal(bool(0))
        shift_dr_o = Signal(bool(0))
        pause_dr_o = Signal(bool(0))
        update_dr_o = Signal(bool(0))

        debug_tdi_i = Signal(bool(0))
        bs_chain_tdi_i = Signal(bool(0))
        mbist_tdi_i = Signal(bool(0))

        tdo_o = Signal(bool(0))
        trst = Signal(bool(0))

        # select_bypass = Signal(bool(0))
        extest_select_o = Signal(bool(0))
        sample_preload_select_o = Signal(bool(0))
        mbist_select_o = Signal(bool(0))
        debug_select_o = Signal(bool(0))
        bsr_select = Signal(bool(0))

        # bypass_so = Signal(bool(0))
        bsr_so = Signal(bool(0))

        tap_inst = tap_top(# JTAG pads
            self.tms,  # JTAG test mode select pad
            self.tck,  # JTAG test clock pad
            trst,  # JTAG test reset pad
            self.tdi,  # JTAG test data input pad
            self.tdo,  # JTAG test data output pad
            self.tdo_padoe_o,  # Output enable for JTAG test data output pad

            # TAP states
            shift_dr_o,
            pause_dr_o,
            update_dr_o,
            capture_dr_o,

            # Select signals for boundary scan or mbist
            extest_select_o,
            sample_preload_select_o,
            mbist_select_o,
            debug_select_o,

            # TDO signal that is connected to TDI of sub-modules.
            tdo_o,

            # TDI signals from sub-modules
            debug_tdi_i,    # from debug module
            bs_chain_tdi_i, # from Boundary Scan Chain
            mbist_tdi_i     # from Mbist Chain
            )
        # bypass_reg = bypass(tdo_o, select_bypass, capture_dr_o, shift_dr_o, self.jtag_interface.TCK, bypass_so)
        bsr_reg = bsr(tdo_o, bsr_select, capture_dr_o, shift_dr_o, update_dr_o, self.tck, bs_chain_tdi_i,
                      extest_select_o, self.DIR, self.A_i, self.A_o, self.A_e, self.B_i, self.B_o, self.B_e,
                      self.OE_NEG)

        @always_comb
        def select_process():
            # select_bypass.next = not extest_select_o and not sample_preload_select_o and \
            #                         not mbist_select_o and not debug_select_o
            bsr_select.next = extest_select_o or sample_preload_select_o

        @always_comb
        def oe_process():
            self.oea.next = not self.DIR and not self.OE_NEG
            self.oeb.next = not self.OE_NEG and self.DIR

        return tap_inst.rtl(), bsr_reg.rtl(), select_process, oe_process


@block
def SN74ABT8245ACore_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    width = 8
    A_i = [Signal(bool(0)) for _ in range(width)]
    A_o = [Signal(bool(0)) for _ in range(width)]
    A_e = [Signal(bool(0)) for _ in range(width)]
    B_i = [Signal(bool(0)) for _ in range(width)]
    B_o = [Signal(bool(0)) for _ in range(width)]
    B_e = [Signal(bool(0)) for _ in range(width)]
    tdi = Signal(bool(0))
    tdo = Signal(bool(0))
    tms = Signal(bool(0))
    tck = Signal(bool(0))
    trst = Signal(bool(0))
    dir = Signal(bool(0))
    oe = Signal(bool(0))
    tdo_padoe_o = Signal(bool(0))

    inst = SN74ABT8245ACore("TOP", "SN74ABT8245Core", dir, A_i, A_o, A_e, B_i, B_o, B_e,
                            oe, tdo_padoe_o, tdi, tck, tms, tdo)

    @instance
    def clkgen():
        while True:
            tck.next = not tck
            yield delay(period // 2)

    @instance
    def stimulus():
        """
        :return:
        """
        disabled = [Signal(bool(0)) for _ in range(8)]
        enabled = [Signal(bool(1)) for _ in range(8)]
        A_i[0].next = True
        for i in range(1, 8):
            A_i[i].next = False
        dir.next = True
        oe.next = False
        yield delay(1)
        assert(B_o == A_i)
        assert(B_e == enabled)
        assert(A_e == disabled)
        A_i[0].next = False
        A_i[1].next = True
        yield delay(1)
        assert(B_o == A_i)
        assert(B_e == enabled)
        assert(A_e == disabled)
        dir.next = False
        B_i[0].next = True
        for i in range(1, 8):
            B_i[i].next = False
        yield delay(1)
        print("A_o = ", A_o)
        print("B_i = ", B_i)
        assert(A_o == B_i)
        assert(B_e == disabled)
        assert(A_e == enabled)
        B_i[0].next = False
        B_i[5].next = True
        yield delay(1)
        print("A_o = ", A_o)
        print("B_i = ", B_i)
        assert(A_o == B_i)
        assert(B_e == disabled)
        assert(A_e == enabled)

        raise StopSimulation()

    return inst.rtl(), clkgen, stimulus


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    width = 8
    A = [TristateSignal(bool(0)) for _ in range(width)]
    B = [TristateSignal(bool(0)) for _ in range(width)]
    tdi = Signal(bool(0))
    tdo = Signal(bool(0))
    tms = Signal(bool(0))
    tck = Signal(bool(0))
    trst = Signal(bool(0))
    dir = Signal(bool(0))
    oe = Signal(bool(0))
    tdo_padoe_o = Signal(bool(0))

    inst = SN74ABT8245ACore("TOP", "SN74ABT8245ACore", dir, A, B, oe, tdo_padoe_o, tdi, tck, tms, tdo)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    inst.rtl().convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SN74ABT8245ACore")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    inst.rtl().convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SN74ABT8245ACore")
    tb = SN74ABT8245ACore_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SN74ABT8245ACore_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SN74ABT8245ACore_tb")


def main():
    tb = SN74ABT8245ACore_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    # convert()


if __name__ == '__main__':
    main()

