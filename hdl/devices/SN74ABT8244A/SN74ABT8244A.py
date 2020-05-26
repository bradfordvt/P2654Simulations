"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

IP Logic for Pure JTAG device core containing BSR, BYPASS, and IDCODE registers to perform standard
interconnect testing use case for P2654 simulation.
"""
from myhdl import *
from hdl.devices.SN74ABT8244A.SN74ABT8244ACore import SN74ABT8244ACore
import os


period = 20  # clk frequency = 50 MHz


class SN74ABT8244A:
    def __init__(self, parent, name,
                 OE_NEG1, Y1, Y2, A1, A2, OE_NEG2,
                 tdo_padoe_o, tdi, tck, tms, tdo
                 ):
        """

        :param parent:
        :param name:
        :param OE_NEG1: Input signal to control the A1/Y1 output enable
        :param Y1: Array of Tristate signals for output
        :param Y2: Array of Tristate signals for output
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
        self.Y1 = Y1
        self.Y2 = Y2
        self.A1 = A1
        self.A2 = A2
        self.Y1Driver = [Y1[i].driver() for i in range(4)]
        self.Y2Driver = [Y2[i].driver() for i in range(4)]
        self.Y1_o = [Signal(bool(0)) for _ in range(4)]
        self.Y1_e = [Signal(bool(0)) for _ in range(4)]
        self.Y2_o = [Signal(bool(0)) for _ in range(4)]
        self.Y2_e = [Signal(bool(0)) for _ in range(4)]
        # JTAG signals
        self.tdo_padoe_o = tdo_padoe_o

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
        core_inst = SN74ABT8244ACore(self.parent + "." + self.name, "SN74ABT8244Core", self.OE_NEG1,
                                     self.Y1_o, self.Y1_e, self.Y2_o, self.Y2_e, self.A1, self.A2,
                                     self.OE_NEG2, self.tdo_padoe_o, self.tdi, self.tck, self.tms, self.tdo)
        print("SN74ABT8244A: self.tdo => ", hex(id(self.tdo)))

        @always_comb
        def output_process():
            for i in range(4):
                if self.Y1_e[i]:
                    if self.Y1_o[i]:
                        self.Y1Driver[i].next = True
                    else:
                        self.Y1Driver[i].next = False
                else:
                    self.Y1Driver[i].next = None
                if self.Y2_e[i]:
                    if self.Y2_o[i]:
                        self.Y2Driver[i].next = True
                    else:
                        self.Y2Driver[i].next = False
                else:
                    self.Y2Driver[i].next = None

        core_inst.configure_jtag(self.tdi, self.tck, self.tms, self.tdo)

        return core_inst.rtl(), output_process


@block
def SN74ABT8244A_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    width = 4
    Y1 = [TristateSignal(False) for _ in range(width)]
    Y2 = [TristateSignal(False) for _ in range(width)]
    A1 = [Signal(bool(0)) for _ in range(width)]
    A2 = [Signal(bool(0)) for _ in range(width)]
    tdi = Signal(bool(0))
    tdo = Signal(bool(0))
    tms = Signal(bool(0))
    tck = Signal(bool(0))
    trst = Signal(bool(0))
    oe_neg1 = Signal(bool(1))
    oe_neg2 = Signal(bool(1))
    tdo_padoe_o = Signal(bool(0))

    inst = SN74ABT8244A("TOP", "SN74ABT8244", oe_neg1, Y1, Y2, A1, A2, oe_neg2,
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
        disabled = [TristateSignal(None) for _ in range(4)]
        A1[0].next = True
        for i in range(1, 4):
            A1[i].next = False
        for i in range(4):
            A2[i].next = False
        A2[2].next = True
        oe_neg1.next = False
        oe_neg2.next = False
        yield delay(1)
        print("Y1 = ", Y1)
        print("A1 = ", A1)
        assert (Y1 == A1)
        print("Y2 = ", Y2)
        print("A2 = ", A2)
        assert (Y2 == A2)
        A1[0].next = False
        A1[1].next = True
        A2[2].next = False
        A2[3].next = True
        yield delay(1)
        assert (Y1 == A1)
        assert (Y2 == A2)
        oe_neg1.next = True
        oe_neg2.next = True
        yield delay(1)
        print("Y1 = ", Y1)
        print("disabled = ", disabled)
        assert (Y1 == disabled)
        assert (Y2 == disabled)

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

    inst = SN74ABT8244A("TOP", "SN74ABT8245", dir, A, B, oe, tdo_padoe_o, tdi, tck, tms, tdo)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    inst.rtl().convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SN74ABT8244A")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    inst.rtl().convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SN74ABT8244A")
    tb = SN74ABT8244A_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SN74ABT8244A_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SN74ABT8244A_tb")


def main():
    tb = SN74ABT8244A_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    # convert()


if __name__ == '__main__':
    main()
