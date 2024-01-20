#!/usr/bin/env python
"""
    Simulation device for Jeff Rearick's I2C_construction_20231003 example.

    Simulation device for Jeff Rearick's I2C_construction_20231003 example.

   Copyright 2024 VT Enterprises Consulting Services

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

__authors__ = ["Bradford G. Van Treuren"]
__contact__ = "bradvt59@gmail.com"
__copyright__ = "Copyright 2024, VT Enterprises Consulting Services"
__credits__ = ["Bradford G. Van Treuren"]
__date__ = "2024/01/17"
__deprecated__ = False
__email__ = "bradvt59@gmail.com"
__license__ = "Apache 2.0"
__maintainer__ = "Bradford G. Van Treuren"
__status__ = "Alpha/Experimental"
__version__ = "0.0.1"

from myhdl import *
import os
import os.path

from hdl.clients.I2CClient.i2cslave_RW import i2cslave_RW
from hdl.clients.I2CClient.registerInterface import registerInterface
from hdl.hosts.i2chost.i2c_interface import i2c_if
from hdl.instruments.JeffBBExInstr.jeffbbexinstr import jeffbbexinstr
from hdl.standards.s1687.IJTAGInterface import IJTAGInterface
from hdl.standards.s1687.SReg import SReg
from hdl.standards.s1687.sib_mux_pre import sib_mux_pre

period = 20  # clk frequency = 50 MHz


@block
def jeffbbexnetwork(path: str,
                    name: str,
                    ijtag_interface: IJTAGInterface,
                    si: Signal(bool(0)),
                    so: Signal(bool(0)),
                    monitor=False):
    """
        IEEE 1687 Scan Network for this device
                (INSTR_IN)  (INSTR_OUT)                                 +-------+
                     ^         |                                        v       |
                     |         v                                      -----     |
        (Chain1)=>(I_REG)-->(O_REG)-->(JEFFBBEXINSTR)-->(OTHER_REG)-->| 1 |     |
            ^                                         +-------------->| 0 |-->(SIB)--+
            |                                                         -----          |
            +------------------------------------------------------------------------+
        :param path: Path string to the instance
        :param name: The instance name of the network
        :param ijtag_interface: An IEEE 1687 ScanInterface for the network
        :param si: ScaInput port
        :param so: ScanOutput port
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return:
    """
    dummy_output = Signal(intbv(0)[4:])
    dummy_input = Signal(intbv(0)[4:])
    instr_input = Signal(intbv(0)[4:])
    instr_output = Signal(intbv(0)[4:])
    other_input = Signal(intbv(0)[8:])
    other_output = Signal(intbv(0)[8:])
    i_reg_so = Signal(bool(0))
    o_reg_so = Signal(bool(0))
    instr_reg_so = Signal(bool(0))
    other_reg_si = Signal(bool(0))
    other_reg_so = Signal(bool(0))
    to_ijtag_interface = IJTAGInterface()
    i_reg_inst = SReg(path + '.' + name,
                      'I_REG',
                      si,
                      ijtag_interface,
                      i_reg_so,
                      instr_input,
                      dummy_output,
                      dr_width=4,
                      monitor=monitor
                      )
    o_reg_inst = SReg(path + '.' + name,
                      'O_REG',
                      i_reg_so,
                      ijtag_interface,
                      o_reg_so,
                      dummy_input,
                      instr_output,
                      dr_width=4,
                      monitor=monitor
                      )
    instr_inst = jeffbbexinstr(path + '.' + name,
                               'JEFFBBEXINSTR',
                               instr_input,
                               instr_output,
                               ijtag_interface,
                               o_reg_so,
                               instr_reg_so,
                               monitor=monitor)
    sib_inst = sib_mux_pre(path + '.' + name,
                           'SIB',
                           instr_reg_so,
                           ijtag_interface,
                           so,
                           other_reg_si,
                           to_ijtag_interface,
                           other_reg_so,
                           monitor=monitor
                           )
    other_reg_inst = SReg(path + '.' + name,
                          'OTHER_REG',
                          other_reg_si,
                          to_ijtag_interface,
                          other_reg_so,
                          other_input,
                          other_output,
                          dr_width=8,
                          monitor=monitor
                          )

    if monitor == False:
        return i_reg_inst, o_reg_inst, jeffbbexinstr, other_reg_inst, sib_inst
    else:
        @instance
        def monitor_si():
            print("\t\tjeffbbexnetwork({:s}): si".format(path + "." + name), si)
            while 1:
                yield si
                print("\t\tjeffbbexnetwork({:s}): si".format(path + "." + name), si)
        @instance
        def monitor_so():
            print("\t\tjeffbbexnetwork({:s}): so".format(path + "." + name), so)
            while 1:
                yield so
                print("\t\tjeffbbexnetwork({:s}): so".format(path + "." + name), so)

        @instance
        def monitor_instr_input():
            print("\t\tjeffbbexnetwork({:s}): instr_input".format(path + "." + name), instr_input)
            while 1:
                yield instr_input
                print("\t\tjeffbbexnetwork({:s}): instr_input".format(path + "." + name), instr_input)

        @instance
        def monitor_instr_output():
            print("\t\tjeffbbexnetwork({:s}): instr_output".format(path + "." + name), instr_output)
            while 1:
                yield instr_output
                print("\t\tjeffbbexnetwork({:s}): instr_output".format(path + "." + name), instr_output)

        @instance
        def monitor_i_reg_so():
            print("\t\tjeffbbexnetwork({:s}): i_reg_so".format(path + "." + name), i_reg_so)
            while 1:
                yield i_reg_so
                print("\t\tjeffbbexnetwork({:s}): i_reg_so".format(path + "." + name), i_reg_so)

        @instance
        def monitor_o_reg_so():
            print("\t\tjeffbbexnetwork({:s}): o_reg_so".format(path + "." + name), o_reg_so)
            while 1:
                yield o_reg_so
                print("\t\tjeffbbexnetwork({:s}): o_reg_so".format(path + "." + name), o_reg_so)

        @instance
        def monitor_instr_reg_so():
            print("\t\tjeffbbexnetwork({:s}): instr_reg_so".format(path + "." + name), instr_reg_so)
            while 1:
                yield instr_reg_so
                print("\t\tjeffbbexnetwork({:s}): instr_reg_so".format(path + "." + name), instr_reg_so)

        @instance
        def monitor_other_reg_si():
            print("\t\tjeffbbexnetwork({:s}): other_reg_si".format(path + "." + name), other_reg_si)
            while 1:
                yield other_reg_si
                print("\t\tjeffbbexnetwork({:s}): other_reg_si".format(path + "." + name), other_reg_si)

        @instance
        def monitor_other_reg_so():
            print("\t\tjeffbbexnetwork({:s}): other_reg_so".format(path + "." + name), other_reg_so)
            while 1:
                yield other_reg_so
                print("\t\tjeffbbexnetwork({:s}): other_reg_so".format(path + "." + name), other_reg_so)

        return (monitor_si, monitor_so, monitor_instr_input, monitor_instr_output,
                monitor_i_reg_so, monitor_o_reg_so, monitor_instr_reg_so, monitor_other_reg_si,
                monitor_other_reg_so,
                i_reg_inst, o_reg_inst, jeffbbexinstr, other_reg_inst, sib_inst)


class JeffBBDevice:
    def __init__(self, clk_o, rst_o):
        self.clk_o = clk_o
        self.rst_o = rst_o
        # I2C Signals
        self.scl_o = None
        self.scl_i = None
        self.scl_e = None
        self.sda_o = None
        self.sda_i = None
        self.sda_e = None

        # I2C Client signals for attached client of interface
        self.reset_n = ResetSignal(1, 0, True)
        self.device_address = Signal(intbv(0x55)[7::0])
        self.write_address = Signal(intbv(0)[8:])
        self.write_data = Signal(intbv(0)[8:])
        self.update = Signal(bool(0))
        self.read_address = Signal(intbv(0)[8:])
        self.read_data = Signal(intbv(0)[8:])
        self.capture = Signal(bool(0))

    def configure_i2c(self, scl_o, scl_i, scl_e, sda_o, sda_i, sda_e):
        self.scl_o = scl_o
        self.scl_i = scl_i
        self.scl_e = scl_e
        self.sda_o = sda_o
        self.sda_i = sda_i
        self.sda_e = sda_e

    @block
    def rtl(self, monitor=True):

        i2c_interface_c = i2c_if(self.clk_o, self.rst_o)
        myReg0 = Signal(intbv(0)[8:])
        myReg1 = Signal(intbv(0)[8:])
        myReg2 = Signal(intbv(0)[8:])
        myReg3 = Signal(intbv(0)[8:])
        myReg4 = Signal(intbv(0x12)[8:])
        myReg5 = Signal(intbv(0x34)[8:])
        myReg6 = Signal(intbv(0x56)[8:])
        myReg7 = Signal(intbv(0x78)[8:])
        writeEn = Signal(bool(0))
        dataIn = Signal(intbv(0)[8:])
        dataOut = Signal(intbv(0)[8:])
        regAddr = Signal(modbv(0)[8:])
        i2c_client_inst = i2cslave_RW(i2c_interface_c.scl_i, i2c_interface_c.sda_i, i2c_interface_c.sda_e, self.reset_n,
                                      dataIn, dataOut, regAddr, writeEn, autoincrement=True)
        register_interface_inst = registerInterface(self.clk_o, regAddr, dataOut, writeEn, dataIn,
                                                    myReg0, myReg1, myReg2, myReg3, myReg4, myReg5, myReg6, myReg7)

        ijtag_interface = IJTAGInterface( )
        si = Signal(bool(0))
        so = Signal(bool(0))
        chain1_inst = jeffbbexnetwork('TopLevel.JeffDevice',
                                      'JeffDevice',
                                      ijtag_interface,
                                      si,
                                      so,
                                      monitor=monitor)

        @always_comb
        def bb_ijtag():
            ijtag_interface.CLOCK.next = myReg0[0]
            si.next = myReg0[1]
            ijtag_interface.SELECT.next = myReg0[2]
            ijtag_interface.CAPTURE.next = myReg0[3]
            ijtag_interface.SHIFT.next = myReg0[4]
            ijtag_interface.UPDATE.next = myReg0[5]
            ijtag_interface.RESET.next = myReg0[6]
            myReg1.next[0] = so

        @instance
        def power_on_reset_gen():
            self.reset_n.next = False
            yield delay(10)
            self.reset_n.next = True

        # build up the netlist for the device here
        @always_comb
        def netlist():
            if not self.sda_e:
                i2c_interface_c.sda_i.next = self.sda_e
            else:
                i2c_interface_c.sda_i.next = True
            if not self.scl_e:
                i2c_interface_c.scl_i.next = self.scl_e
            else:
                i2c_interface_c.scl_i.next = True
            if not i2c_interface_c.sda_e:
                self.sda_i.next = i2c_interface_c.sda_e
            else:
                self.sda_i.next = True
            # if not i2c_interface_c.scl_e:
            #     self.scl_i.next = i2c_interface_c.scl_e
            # else:
            #     self.scl_i.next = True
            self.scl_i.next = True

        return (netlist, i2c_client_inst, power_on_reset_gen, register_interface_inst,
                chain1_inst, bb_ijtag)

