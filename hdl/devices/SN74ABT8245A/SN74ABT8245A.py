"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

IP Logic for Pure JTAG device core containing BSR, BYPASS, and IDCODE registers to perform standard
interconnect testing use case for P2654 simulation.
"""
from myhdl import *
from hdl.devices.SN74ABT8245A.SN74ABT8245ACore import SN74ABT8245ACore
import os


period = 20  # clk frequency = 50 MHz


class SN74ABT8245A:
    def __init__(self, parent, name,
                 DIR, A, B, OE_NEG,
                 tdo_padoe_o, tdi, tck, tms, tdo
                 ):
        """

        :param parent:
        :param name:
        :param DIR: Direction Control Signal (0=B to A, 1=A to B)
        :param A: 8-bit Bidirectional Data Bus (Tristate bus)
        :param B: 8-bit Bidirectional Data Bus (Tristate bus)
        :param OE_NEG: Input signal to control the A/B output enable (0=enabled, 1=disabled)
        :param tdo_padoe_o: tdo_padoe_o = Signal(bool(0)) Output enable for TDO
        """
        self.parent = parent
        self.name = name
        # OE Signals
        self.DIR = DIR
        self.OE_NEG = OE_NEG
        # IO Signals
        self.B = B
        self.A = A
        self.ADriver = [A[i].driver() for i in range(8)]
        self.BDriver = [B[i].driver() for i in range(8)]
        self.A_i = [Signal(bool(0)) for _ in range(8)]
        self.A_o = [Signal(bool(0)) for _ in range(8)]
        self.A_e = [Signal(bool(0)) for _ in range(8)]
        self.B_i = [Signal(bool(0)) for _ in range(8)]
        self.B_o = [Signal(bool(0)) for _ in range(8)]
        self.B_e = [Signal(bool(0)) for _ in range(8)]

        # JTAG signals
        self.tdo_padoe_o = tdo_padoe_o
        self.oeb = Signal(bool(0))
        self.oea = Signal(bool(0))

        # JTAG signals for attached client of interface
        self.tck = tck
        self.tms = tms
        self.tdi = tdi
        self.tdo = tdo
        self.trst = None

    def configure_jtag(self, tdi, tck, tms, trst, tdo):
        self.tck = tck
        self.tms = tms
        self.trst = trst
        self.tdi = tdi
        self.tdo = tdo

    @block
    def rtl(self, monitor=False):
        core_inst = SN74ABT8245ACore(self.parent + "." + self.name, "SN74ABT8245ACore",
                                     self.DIR, self.A_i, self.A_o, self.A_e,
                                     self.B_i, self.B_o, self.B_e, self.OE_NEG,
                                     self.tdo_padoe_o, self.tdi, self.tck, self.tms, self.tdo)

        @always_comb
        def input_process():
            for i in range(8):
                if self.A[i].val:
                    self.A_i[i].next = True
                else:
                    self.A_i[i].next = False
                if self.B[i].val:
                    self.B_i[i].next = True
                else:
                    self.B_i[i].next = False

        @always_comb
        def output_process():
            for i in range(8):
                if self.A_e[i]:
                    if self.A_o[i]:
                        self.ADriver[i].next = True
                    else:
                        self.ADriver[i].next = False
                else:
                    self.ADriver[i].next = None
                if self.B_e[i]:
                    if self.B_o[i]:
                        self.BDriver[i].next = True
                    else:
                        self.BDriver[i].next = False
                else:
                    self.BDriver[i].next = None

        return core_inst.rtl(), input_process, output_process


@block
def SN74ABT8245A_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    width = 8
    A = [TristateSignal(False) for _ in range(width)]
    B = [TristateSignal(False) for _ in range(width)]
    tdi = Signal(bool(0))
    tdo = Signal(bool(0))
    tms = Signal(bool(0))
    tck = Signal(bool(0))
    trst = Signal(bool(0))
    dir = Signal(bool(0))
    oe = Signal(bool(1))
    tdo_padoe_o = Signal(bool(0))

    inst = SN74ABT8245A("TOP", "SN74ABT8245", dir, A, B, oe, tdo_padoe_o, tdi, tck, tms, tdo)

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
        ADrivers = [A[i].driver() for i in range(8)]
        BDrivers = [B[i].driver() for i in range(8)]
        for i in range(8):
            BDrivers[i].next = None
        ADrivers[0].next = True
        for i in range(1, 8):
            ADrivers[i].next = False
        dir.next = True
        oe.next = False
        yield delay(1)
        assert(B == A)
        ADrivers[0].next = False
        ADrivers[1].next = True
        yield delay(1)
        assert(B == A)
        dir.next = False
        for i in range(8):
            ADrivers[i].next = None
        yield delay(1)
        BDrivers[0].next = True
        for i in range(1, 8):
            BDrivers[i].next = False
        yield delay(1)
        print("A = ", A)
        print("B = ", B)
        assert(A == B)
        BDrivers[0].next = False
        BDrivers[5].next = True
        yield delay(1)
        print("A = ", A)
        print("B = ", B)
        assert(A == B)

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

    inst = SN74ABT8245A("TOP", "SN74ABT8245", dir, A, B, oe, tdo_padoe_o, tdi, tck, tms, tdo)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    inst.rtl().convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SN74ABT8245A")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    inst.rtl().convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SN74ABT8245A")
    tb = SN74ABT8245A_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SN74ABT8245A_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SN74ABT8245A_tb")


def main():
    tb = SN74ABT8245A_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    # convert()


if __name__ == '__main__':
    main()

