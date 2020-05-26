"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

IP Logic for Pure JTAG device core containing BSR, BYPASS, and IDCODE registers to perform standard
interconnect testing use case for P2654 simulation.
"""
from myhdl import *
from hdl.devices.SN74ABT8244A.tap.tap_defines import *
from hdl.devices.SN74ABT8244A.tap.tap_top import *
from hdl.devices.SN74ABT8244A.registers.bsr import bsr


period = 20  # clk frequency = 50 MHz


class SN74ABT8244ACore:
    def __init__(self, parent, name,
                 OE_NEG1, Y1_o, Y1_e, Y2_o, Y2_e, A1, A2, OE_NEG2,
                 tdo_padoe_o, tdi, tck, tms, tdo
                 ):
        """

        :param parent:
        :param name:
        :param OE_NEG1: Input signal to control the A1/Y1 output enable
        :param Y1_o: Array of data signals for output
        :param Y1_e: Array of enable signals for output
        :param Y2_o: Array of data signals for output
        :param Y2_e: Array of enable signals for output
        :param A1: Array of Signals as inputs
        :param A2: Array of Signals as inputs
        :param OE_NEG2: Input signal to control the A2/Y2 output enable
        :param tdo_padoe_o: tdo_padoe_o = Signal(bool(0)) Output enable for TDO
        """
        self.parent = parent
        self.name = name
        # OE Signals
        self.OE_NEG1 = OE_NEG1
        self.OE_NEG2 = OE_NEG2
        # IO Signals
        self.Y1_o = Y1_o
        self.Y1_e = Y1_e
        self.Y2_o = Y2_o
        self.Y2_e = Y2_e
        self.A1 = A1
        self.A2 = A2
        # JTAG signals
        self.tdo_padoe_o = tdo_padoe_o

        # JTAG signals for attached client of interface
        self.tck = tck
        self.tms = tms
        self.tdi = tdi
        self.tdo = tdo

    def configure_jtag(self, tdi, tck, tms, tdo):
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
                      extest_select_o, self.OE_NEG1, self.Y1_o, self.Y1_e, self.Y2_o, self.Y2_e,
                      self.A1, self.A2, self.OE_NEG2)
        tap_inst.configure_jtag(self.tdi, self.tck, self.tms, trst, self.tdo)
        bsr_reg.configure_jtag(tdo_o, self.tck, self.tms, trst, self.tdo)
        print("SN74ABT8244ACore: self.tdo => ", hex(id(self.tdo)))

        @always_comb
        def select_process():
            # select_bypass.next = not extest_select_o and not sample_preload_select_o and \
            #                         not mbist_select_o and not debug_select_o
            bsr_select.next = extest_select_o or sample_preload_select_o

        return tap_inst.rtl(), bsr_reg.rtl(), select_process


@block
def SN74ABT8244ACore_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    width = 4
    Y1_o = [Signal(bool(0)) for _ in range(width)]
    Y1_e = [Signal(bool(0)) for _ in range(width)]
    Y2_o = [Signal(bool(0)) for _ in range(width)]
    Y2_e = [Signal(bool(0)) for _ in range(width)]
    A1 = [Signal(bool(0)) for _ in range(width)]
    A2 = [Signal(bool(0)) for _ in range(width)]
    tdi = Signal(bool(0))
    tdo = Signal(bool(0))
    tms = Signal(bool(0))
    tck = Signal(bool(0))
    trst = Signal(bool(0))
    oe_neg1 = Signal(bool(0))
    oe_neg2 = Signal(bool(0))
    tdo_padoe_o = Signal(bool(0))

    inst = SN74ABT8244ACore("TOP", "SN74ABT8244Core", oe_neg1, Y1_o, Y1_e, Y2_o, Y2_e, A1, A2, oe_neg2,
                            tdo_padoe_o, tdi, tck, tms, tdo)

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
        disabled = [Signal(bool(0)) for _ in range(4)]
        enabled = [Signal(bool(1)) for _ in range(4)]
        A1[0].next = True
        for i in range(1, 4):
            A1[i].next = False
        for i in range(4):
            A2[i].next = False
        A2[2].next = True
        oe_neg1.next = False
        oe_neg2.next = False
        yield delay(1)
        print("Y1_o = ", Y1_o)
        print("A1 = ", A1)
        assert(Y1_o == A1)
        print("Y1_e = ", Y1_e)
        print("enabled = ", enabled)
        assert(Y1_e == enabled)
        print("Y2_o = ", Y2_o)
        print("A2 = ", A2)
        assert(Y2_o == A2)
        print("Y2_e = ", Y2_e)
        print("enabled = ", enabled)
        assert(Y2_e == enabled)
        A1[0].next = False
        A1[1].next = True
        A2[2].next = False
        A2[3].next = True
        yield delay(1)
        assert(Y1_o == A1)
        assert(Y1_e == enabled)
        assert(Y2_o == A2)
        assert(Y2_e == enabled)
        oe_neg1.next = True
        oe_neg2.next = True
        yield delay(1)
        assert(Y1_e == disabled)
        assert(Y2_e == disabled)

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

    inst = SN74ABT8244ACore("TOP", "SN74ABT8244ACore", dir, A, B, oe, tdo_padoe_o, tdi, tck, tms, tdo)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    inst.rtl().convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SN74ABT8244ACore")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    inst.rtl().convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SN74ABT8244ACore")
    tb = SN74ABT8244ACore_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SN74ABT8244ACore_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SN74ABT8244ACore_tb")


def main():
    tb = SN74ABT8244ACore_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    # convert()


if __name__ == '__main__':
    main()
