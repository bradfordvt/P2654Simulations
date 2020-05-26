"""
Copyright (c) 2020 Bradford G. Van Treuren
See the licence file in the top directory

IP Logic for SDRAM example to perform standard
memory testing use case for P2654 simulation.
"""
from myhdl import *
from hdl.devices.SRAM12x8.RAMCore import RAMCore
import os


period = 20  # clk frequency = 50 MHz


class SRAM12x8:
    def __init__(self, parent, name, address, data, we, clk):
        self.parent = parent
        self.name = name
        self.address = address
        self.data = data
        self.we = we
        self.clk = clk
        self.data_driver = data.driver()
        self.address_driver = address.driver()
        self.addr_width = 12
        self.data_width = 8
        self.written = False

    @block
    def rtl(self):
        din = Signal(intbv(0)[self.data_width:])
        dout = Signal(intbv(0)[self.data_width:])
        waddr = Signal(intbv(0)[self.addr_width:])
        raddr = Signal(intbv(0)[self.addr_width:])
        ram_inst = RAMCore(din, dout, waddr, raddr, self.we, self.clk,
                           data_width=self.data_width, addr_width=self.addr_width)

        @always_comb
        def addr_process():
            if self.address.val is not None:  # Not 'Z'
                waddr.next = self.address
                raddr.next = self.address
            else:
                waddr.next = intbv(0)[self.addr_width:]
                raddr.next = intbv(0)[self.addr_width:]

        @always_comb
        def input_process():
            if self.data.val is None:
                return
            elif self.data_driver.val is None:
                din.next = self.data

        @always_comb
        def output_process():
            if self.we:
                self.data_driver.next = None
            else:
                self.data_driver.next = dout

        return ram_inst.rtl(), addr_process, input_process, output_process


@block
def SRAM12x8_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    data_width = 8
    addr_width = 12
    data = TristateSignal(intbv(0)[data_width:])
    address = TristateSignal(intbv(0)[addr_width:])
    d = Signal(intbv(0)[data_width:])
    a = Signal(intbv(0)[addr_width:])
    we = Signal(bool(0))
    clk = Signal(bool(0))
    addr_range = 2**addr_width
    data_driver = data.driver()
    address_driver = address.driver()

    inst = SRAM12x8("TOP", "SRAM12x8", address, data, we, clk)

    # @always_comb
    # def addr_process():
    #     address_driver.next = a
    #
    # @always_comb
    # def data_process():
    #     # if we:
    #     #     data_driver.next = d
    #     data_driver.next = d
    #
    @instance
    def clkgen():
        while True:
            clk.next = not clk
            yield delay(period // 2)

    @instance
    def stimulus():
        """
        :return:
        """
        # Test data signals
        we.next = True
        yield delay(1)
        data_driver.next = intbv(0)[data_width:]
        address_driver.next = intbv(0)[addr_width:]
        yield clk.posedge
        for i in range(data_width):
            we.next = True
            yield delay(1)
            data_driver.next = intbv(1 << i)[data_width:]
            yield clk.posedge
            data_driver.next = None
            yield delay(1)
            we.next = False
            yield delay(1)
            assert(data == intbv(1 << i)[data_width:])

        # Test address signals
        we.next = True
        yield delay(1)
        data_driver.next = intbv(0)[data_width:]
        address_driver.next = intbv(0)[addr_width:]
        yield clk.posedge
        for i in range(addr_width):
            we.next = True
            yield delay(1)
            data_driver.next = intbv(i % 2**data_width)[data_width:]
            address_driver.next = intbv(1 << i)[addr_width:]
            yield clk.posedge
            data_driver.next = None
            yield delay(1)
            we.next = False
            yield delay(1)

        we.next = False
        yield delay(1)
        data_driver.next = None
        address_driver.next = intbv(0)[addr_width:]
        yield clk.posedge

        for i in range(addr_width):
            we.next = False
            yield delay(1)
            data_driver.next = None
            address_driver.next = intbv(1 << i)[addr_width:]
            yield clk.posedge
            assert(data == i % 2**data_width)

        raise StopSimulation()

    return inst.rtl(), clkgen, stimulus  #, addr_process, data_process


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    data_width = 8
    addr_width = 12
    data = TristateSignal(intbv(0)[data_width:])
    address = TristateSignal(intbv(0)[addr_width:])
    we = Signal(bool(0))
    clk = Signal(bool(0))

    inst = SRAM12x8("TOP", "SRAM12x8", address, data, we, clk)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    inst.rtl().convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SRAM12x8")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    inst.rtl().convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SRAM12x8")
    tb = SRAM12x8_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SRAM12x8_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SRAM12x8_tb")


def main():
    tb = SRAM12x8_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    # convert()


if __name__ == '__main__':
    main()


