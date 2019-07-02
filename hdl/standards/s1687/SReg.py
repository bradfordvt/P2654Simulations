"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import logging
import os
import os.path
from hdl.common.ScanRegister import ScanRegister
from hdl.standards.s1687.IJTAGInterface import IJTAGInterface


class SReg:
    def __init__(self, path, name, si, ijtag_interface, so, di, do, dr_width=9):
        """
        Creates a Module SReg for IEEE 1687 with the following interface:
        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logging (path instance)
        :param si: ScanInPort
        :param ijtag_interface: IJTAGInterface defining the control signals for this register
        :param so: ScanOutPort
        :param di: DataInPort [Signal(bool(0) for _ in range(dr_width)]
        :param do: DataOutPort [Signal(bool(0) for _ in range(dr_width)]
        :param sr: ScanRegister object associated with this SReg
        :param dr_width: The width of the DI/DO interfaces and size of the SR
        """
        logging.info("Constructing SReg instance ({:s}).".format(path + '.' + name))
        self.path = path
        self.name = name
        self.si = si
        self.ijtag_interface = ijtag_interface
        self.so = so
        self.di = di
        self.do = do
        self.dr_width = dr_width
        self.sr_inst = ScanRegister(
                                    self.path + '.' + self.name,
                                    'ScanRegister' + self.name[-1],
                                    self.si,
                                    self.ijtag_interface.CAPTURE,
                                    self.ijtag_interface.SHIFT,
                                    self.ijtag_interface.UPDATE,
                                    self.ijtag_interface.SELECT,
                                    self.ijtag_interface.RESET,
                                    self.ijtag_interface.CLOCK,
                                    self.so,
                                    self.di,
                                    self.do,
                                    self.dr_width
                                    )

    def toVHDL(self):
        """
        Converts the myHDL logic into VHDL
        :return:
        """
        vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
        if not os.path.exists(vhdl_dir):
            os.mkdir(vhdl_dir, mode=0o777)
        self.rtl(monitor=False).convert(hdl="VHDL", initial_values=True, directory=vhdl_dir)

    def toVerilog(self):
        """
        Converts the myHDL logic into Verilog
        :return:
        """
        verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
        if not os.path.exists(verilog_dir):
            os.mkdir(verilog_dir, mode=0o777)
        self.rtl(monitor=False).convert(hdl="Verilog", initial_values=True, directory=verilog_dir)

    def rtl(self, monitor=False):
        """
        Wrapper around the RTL logic to get a meaningful name during conversion
        :param monitor:
        :return:
        """
        return self.SReg_rtl(monitor=monitor)

    @block
    def SReg_rtl(self, monitor=False):
        """
        The logic for the SReg
        Delegate logic to the ScanRegister object instance associated with this design
        :return: The generator methods performing the logic decisions
        """
        logging.debug("SReg({:s}).rtl()".format(self.path + '.' + self.name))
        return self.sr_inst.ScanRegister_rtl(monitor=monitor)

    @staticmethod
    def convert():
        """
        Convert the myHDL design into VHDL and Verilog
        :return:
        """
        dr_width = 9
        si = Signal(bool(0))
        so = Signal(bool(0))
        di = [Signal(bool(0)) for _ in range(dr_width)]
        do = [Signal(bool(0)) for _ in range(dr_width)]
        ijtag_interface = IJTAGInterface()

        sreg_inst = SReg('TOP', 'SReg0', si, ijtag_interface, so, di, do, dr_width=9)

        sreg_inst.toVerilog()
        sreg_inst.toVHDL()

    @staticmethod
    @block
    def testbench(monitor=False):
        """
        Test bench interface for a quick test of the operation of the design
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """
        dr_width = 9
        si = Signal(bool(0))
        so = Signal(bool(0))
        di = [Signal(bool(0)) for _ in range(dr_width)]
        di[dr_width - 1] = Signal(bool(1))
        di[dr_width - 5] = Signal(bool(1))
        do = [Signal(bool(0)) for _ in range(dr_width)]
        si_data = [Signal(bool(0)) for _ in range(dr_width)]
        si_data[dr_width - 5] = Signal(bool(1))
        si_data[dr_width - 7] = Signal(bool(1))
        so_data = [Signal(bool(0)) for _ in range(dr_width)]
        ijtag_interface = IJTAGInterface()

        sreg_inst = SReg('TOP', 'SReg0', si, ijtag_interface, so, di, do, dr_width=9)

        @always(delay(10))
        def clkgen():
            ijtag_interface.CLOCK.next = not ijtag_interface.CLOCK

        @instance
        def stimulus():
            """
            Not true IJTAG protocol, but used to exercise the state machine with the fewest cycles
            :return:
            """
            H = bool(1)
            L = bool(0)
            # Reset the instrument
            ijtag_interface.RESET.next = bool(0)
            yield delay(10)
            ijtag_interface.RESET.next = bool(1)
            yield delay(10)
            # Start the Capture transition operation
            yield ijtag_interface.CLOCK.posedge
            # Write Capture value
            ijtag_interface.CAPTURE.next = H
            yield ijtag_interface.CLOCK.negedge
            yield ijtag_interface.CLOCK.posedge
            # Write Shift value
            ijtag_interface.CAPTURE.next = L
            ijtag_interface.SHIFT.next = H
            yield ijtag_interface.CLOCK.negedge
            for i in range(dr_width):
                si.next = si_data[dr_width - 1 - i]
                yield ijtag_interface.CLOCK.posedge
                yield ijtag_interface.CLOCK.negedge
                so_data[dr_width - 1 - i].next = so
            # Write Update value
            ijtag_interface.SHIFT.next = L
            ijtag_interface.UPDATE.next = H
            yield ijtag_interface.CLOCK.negedge
            yield ijtag_interface.CLOCK.posedge
            for j in range(dr_width):
                if j == 0 or j == 4:
                    assert(so_data[dr_width - 1 - j] == bool(1))
                else:
                    assert(so_data[dr_width - 1 - j] == bool(0))
            for j in range(dr_width):
                if j == 4 or j == 6:
                    assert(do[dr_width - 1 - j] == bool(1))
                else:
                    assert(do[dr_width - 1 - j] == bool(0))

            raise StopSimulation()

        return sreg_inst.SReg_rtl(monitor=monitor), clkgen, stimulus


if __name__ == '__main__':
    tb = SReg.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    SReg.convert()
