"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
from hdl.rhea import Global, Clock, Reset
from hdl.rhea.system import Register, RegisterFile
from hdl.rhea.system import Barebone, Wishbone, AvalonMM, AXI4Lite
from hdl.standards.s1149dot1.JTAGInterface import JTAGInterface


class JTAGHost:
    """
    The host side instrument logic for a TAP Controller device.
    TAPHost contains an example of logic to be able to control a JTAGInterface.
    """
    def __init__(self, clock, reset_n, base_addr, jtag_interface, tdi, tdo):
        """
        Constructor to instantiate a TAPHost core instance
        :param clock: Clock used to latch data and manipulate TAP State Machine
        :param reset_n: Active low signal to initialize the TAPHost to a deterministic default state
        :param base_addr: The base address of this instance in the memory map
        :param jtag_interface: An instance of the jtag_interface signals
        :param tdi: Test Data signal going to the UUT
        :param tdo: Test Data signal coming from the UUT
        """
        self.clock = clock
        self.reset_n = reset_n
        self.base_addr = base_addr
        self.jtag_interface = jtag_interface
        self.mminst = self.__regfilesys(self.clock, self.reset_n)

    def toVHDL(self):
        """
        Converts the myHDL logic into VHDL
        :return:
        """
        self.rtl(monitor=False).convert(hdl="VHDL", initial_values=True)

    def toVerilog(self):
        """
        Converts the myHDL logic into Verilog
        :return:
        """
        self.rtl(monitor=False).convert(hdl="Verilog", initial_values=True)

    def rtl(self, monitor=False):
        """
        Wrapper around the RTL logic to get a meaningful name during conversion
        :param monitor:
        :return:
        """
        return self.MBISTSimulatedInstrument_rtl(monitor=monitor)

    @block
    def TAPHost_rtl(self, monitor=False):
        """
        Logic to implement the TAPHost Controller
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """
        scan_inst = ScanBlock(self.mminst)
        @always_seq(self.clock.posedge, reset=self.reset_n)
        def state_machine():
            if self.reset_n == ACTIVE_LOW:
                # self.__set_status_register(intbv('00000'))
                # self.__set_control_register(intbv('000000'))
                self.status_register[0].next = bool(0)
                self.status_register[1].next = bool(0)
                self.status_register[2].next = bool(0)
                self.status_register[3].next = bool(0)
                self.status_register[4].next = bool(0)
                self.control_register[0].next = bool(0)
                self.control_register[1].next = bool(0)
                self.control_register[2].next = bool(0)
                self.control_register[3].next = bool(0)
                self.control_register[4].next = bool(0)
                self.control_register[5].next = bool(0)
                self.id_count.next = 0
                self.td_count.next = 0
                self.ad_count.next = 0
                self.state.next = t_State.IDLE
                self.power_usage_register.next = IDLE_POWER
                self.thermal_register.next = IDLE_TEMP

            else:
                if self.state == t_State.IDLE:
                    if self.control_register[0] == bool(1):
                        self.status_register[0].next = bool(0)
                        self.state.next = t_State.START
                        self.power_usage_register.next = START_POWER
                        self.thermal_register.next = START_TEMP

    def __build_regfile(self):
        """ Build a register file definition.
        This register file definition is loosely based off the gemac_simple ...
        """
        regfile = RegisterFile()
        regfile.add_register(Register(name='data_out_fifo', width=16, access='rw', default=0, addr=self.base_addr))
        regfile.add_register(Register(name='data_in_fifo', width=16, access='rw', default=0, addr=self.base_addr+2))
        regfile.add_register(Register(name='tms_macro', width=16, access='rw', default=0, addr=self.base_addr+4))
        regfile.add_register(Register(name='scan_count_low', width=16, access='rw', default=0, addr=self.base_addr+6))
        regfile.add_register(Register(name='scan_count_high', width=16, access='rw', default=0, addr=self.base_addr+8))
        regfile.add_register(Register(name='control', width=16, access='rw', default=0, addr=self.base_addr+10))
        # @todo: add the named bits
        regfile.add_register(Register(name='status', width=16, access='ro', default=0, addr=self.base_addr+12))
        # @todo: add the named bits

        return regfile


    @block
    def __memmap_component(self, glbl, csrbus, cio, user_regfile=None):
        """
        Ports
        -----
        :param glbl: global signals, clock, reset, enable, etc.
        :param csrbus: memory-mapped bus
        :param cio: component IO
        :param user_regfile:
        """
        if user_regfile is None:
            regfile = self.__build_regfile()
        else:
            regfile = user_regfile

        self.regfile_inst = csrbus.add(glbl, regfile, peripheral_name='TAPHost')

        @always_comb
        def beh_assign():
            s = concat(regfile.macaddr0[:2], regfile.control[6:])
            cio.next = s

        return self.regfile_inst, beh_assign


    @block
    def __regfilesys(self, clock, reset):
        """
        """
        glbl = Global(clock, reset)
        csrbus = Wishbone(glbl, data_width=16, address_width=16)
        cio = Signal(intbv(0)[8:])

        mminst = self.__memmap_component(glbl, csrbus, cio)

        return mminst
