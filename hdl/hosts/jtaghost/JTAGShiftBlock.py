"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *


ACTIVE_LOW = 0


class JTAGShiftBlock:
    """
    Logic to perform the data shift operation from the input fifo to si and from so to output fifo.
    Data shifting is synchronized to TCK of the TAP state machine.
    Data is only shifted when shift_en = bool(1).
    Uses rhea.system.stream.fifobus.py as the FIFO interface description.
    """
    IDLE, SHIFT = range(2)  # State machine shift states

    def __init__(self, tck, reset_n, shift_en, si_fifo_bus, so_fifo_bus, shift_count, si, so, data_width=16):
        """
        Data shift block of TAPHost used to shift data out of the JTAG port and capture data into the JTAG port
        :param tck: Test Clock to shift by
        :param reset_n: Active low reset to initialize the block to a deterministic default state
        :param shift_en: Shift enable allowing for shifting of the data from/to the JTAG port
        :param si_fifo_bus: Fifo bus to a FIFO instance where the data from si is to be stored to
        :param so_fifo_bus: Fifo bus to a FIFO instance where the data to so will be extracted from
        :param shift_count: The number of bits to shift out starting with the right most bit of first word
        :param si: The port where the JTAG data will be read from
        :param so: The port where the JTAG data will be written to
        """
        self.tck = tck
        self.reset_n = reset_n
        self.shift_en = shift_en
        self.si_fifo_bus = si_fifo_bus
        self.so_fifo_bus = so_fifo_bus
        self.shift_count = shift_count
        self.si = si
        self.so = so
        self.data_width = data_width
        self.data_in = Signal(intbv(0)[self.data_width:])
        self.data_out = Signal(intbv(0)[self.data_width:])
        self.read_shift_state = TAPShiftBlock.IDLE
        self.write_shift_state = TAPShiftBlock.IDLE
        self.read_index = modbv(0, min=0, max=16)
        self.write_index = modbv(0, min=0, max=16)
        self.bit_count = modbv(0, min=0, max=2**self.data_width)

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
        return self.TAPShiftBlock_rtl(monitor=monitor)

    @block
    def TAPShiftBlock_rtl(self, monitor=False):
        """
        Logic to implement the TAPHost Controller's TAPShiftBlock
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """
        @always_seq(self.tck.posedge, reset=self.reset_n)
        def so_state_machine():
            if self.reset_n == ACTIVE_LOW:
                self.data_in = Signal(intbv(0)[self.data_width:])
                self.data_out = Signal(intbv(0)[self.data_width:])
                self.shift_count = 0
                self.write_index = modbv(0, min=0, max=16)
                self.bit_count = modbv(0, min=0, max=2**self.data_width)
                self.write_shift_state.next = TAPShiftBlock.IDLE

            else:
                if self.write_shift_state == TAPShiftBlock.IDLE:
                    if self.shift_en == bool(1):
                        self.write_shift_state.next = TAPShiftBlock.SHIFT
                        if self.shift_count != modbv(0, min=0, max=self.data_width):
                            # Start the first shift operation now while transitioning
                            if self.write_index == modbv(0, min=0, max=self.data_width):
                                self.so_fifo_bus.readtrans()
                                self.data_out = self.so_fifo_bus.get_read_data()
                            if self.bit_count < self.shift_count:
                                if self.data_out & (1 << self.write_index):
                                    self.so.next = bool(1)
                                else:
                                    self.so.next = bool(0)
                                self.write_index = self.write_index + 1
                                self.bit_count = self.bit_count + 1

                elif self.write_shift_state == TAPShiftBlock.SHIFT:
                    if self.shift_en == bool(0):
                        self.write_shift_state.next = TAPShiftBlock.IDLE
                        self.write_index = modbv(0, min=0, max=16)
                        self.bit_count = modbv(0, min=0, max=2**self.data_width)
                    else:
                        # Shift the next bit
                        if self.write_index == modbv(0, min=0, max=self.data_width):
                            self.so_fifo_bus.readtrans()
                            self.data_out = self.so_fifo_bus.get_read_data()
                        if self.bit_count < self.shift_count:
                            if self.data_out & (1 << self.write_index):
                                self.so.next = bool(1)
                            else:
                                self.so.next = bool(0)
                            self.write_index = self.write_index + 1
                            self.bit_count = self.bit_count + 1

        @always_seq(self.tck.negedge, reset=self.reset_n)
        def si_state_machine():
            if self.reset_n == ACTIVE_LOW:
                self.read_index = modbv(0, min=0, max=16)
                self.read_shift_state.next = TAPShiftBlock.IDLE

            else:
                if self.read_shift_state == TAPShiftBlock.IDLE:
                    if self.shift_en == bool(1):
                        self.read_shift_state.next = TAPShiftBlock.SHIFT
                        if self.shift_count != modbv(0, min=0, max=self.data_width):
                            # Start the first shift operation now while transitioning
                            if self.bit_count < self.shift_count:
                                if self.si:
                                    self.data_in = self.data_in | (1 << self.read_index)
                                else:
                                    self.data_in = self.data_in & (~(1 << self.read_index))
                                self.so.next = self.data_in & (1 << self.write_index)
                                self.read_index = self.read_index + 1
                            if self.read_index == modbv(0, min=0, max=self.data_width):
                                self.si_fifo_bus.writetrans(self.data_in)

                elif self.read_shift_state == TAPShiftBlock.SHIFT:
                    if self.shift_en == bool(0):
                        self.read_shift_state.next = TAPShiftBlock.IDLE
                        self.read_index = modbv(0, min=0, max=16)
                    else:
                        # Shift the next bit
                        if self.bit_count < self.shift_count:
                            if self.si:
                                self.data_in = self.data_in | (1 << self.read_index)
                            else:
                                self.data_in = self.data_in & (~(1 << self.read_index))
                            self.so.next = self.data_in & (1 << self.write_index)
                            self.read_index = self.read_index + 1
                        if self.read_index == modbv(0, min=0, max=self.data_width):
                            self.si_fifo_bus.writetrans(self.data_in)

        return so_state_machine, si_state_machine
