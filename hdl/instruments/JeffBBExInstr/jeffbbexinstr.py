#!/usr/bin/env python
"""
    Simulation instrument for Jeff Rearick's I2C_construction_20231003 example.

    Simulation instrument for Jeff Rearick's I2C_construction_20231003 example.

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
__date__ = "2024/01/16"
__deprecated__ = False
__email__ = "bradvt59@gmail.com"
__license__ = "Apache 2.0"
__maintainer__ = "Bradford G. Van Treuren"
__status__ = "Alpha/Experimental"
__version__ = "0.0.1"

from myhdl import *
import os
import os.path
from hdl.standards.s1687.IJTAGInterface import IJTAGInterface
from hdl.standards.s1687.SReg import SReg

period = 20  # clk frequency = 50 MHz


@block
def jeffbbexinstr(path: str,
                  name: str,
                  instr_input: Signal(intbv(0, _nrbits=4)),
                  instr_output: Signal(intbv(0, _nrbits=4)),
                  ijtag_interface: IJTAGInterface,
                  si,
                  so,
                  monitor=False
                  ):
    """
    Simulation instrument for Jeff Rearick's I2C_construction example
    :param path: Path string to the instance
    :param name: The instance name of the instrument
    :param instr_input: 4 bit data_interface to an input register
    :param instr_output: 4 bit data_interface from an output register
    :param ijtag_interface: An IEEE 1687 ScanInterface to INSTR_REG scan register in the instrument
    :param si: ScaInput port
    :param so: ScanOutput port
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return:
    """
    instr_in_reg = Signal(intbv(0)[4:])
    instr_out_reg = Signal(intbv(0xF)[4:])
    data_reg_in = Signal(intbv(0)[16:])
    data_reg_out = Signal(intbv(0)[16:])
    instr_reg_inst = SReg(path + '.' + name,
                          'INSTR_REG',
                          si,
                          ijtag_interface,
                          so,
                          data_reg_in,
                          data_reg_out,
                          dr_width=16,
                          monitor=monitor
                          )

    @always_comb
    def reset_logic():
        reset_n.next = not ijtag_interface.RESET

    @always_comb
    def dio_logic():
        instr_in_reg.next = instr_input
        instr_output.next = instr_out_reg


    if monitor == False:
        return instr_reg_inst, reset_logic
    else:
        @instance
        def monitor_si():
            print("\t\tjeffbbexinstr({:s}): si".format(path + "." + name), si)
            while 1:
                yield si
                print("\t\tjeffbbexinstr({:s}): si".format(path + "." + name), si)

        @instance
        def monitor_so():
            print("\t\tjeffbbexinstr({:s}): so".format(path + "." + name), so)
            while 1:
                yield so
                print("\t\tjeffbbexinstr({:s}) so:".format(path + "." + name), so)

        @instance
        def monitor_data_reg_in():
            print("\t\tjeffbbexinstr({:s}): data_reg_in".format(path + "." + name), data_reg_in)
            while 1:
                yield data_reg_in
                print("\t\tjeffbbexinstr({:s}): data_reg_in".format(path + "." + name), data_reg_in)

        @instance
        def monitor_data_reg_out():
            print("\t\tjeffbbexinstr({:s}): data_reg_out".format(path + "." + name), data_reg_out)
            while 1:
                yield data_reg_out
                print("\t\tjeffbbexinstr({:s}) data_reg_out:".format(path + "." + name), data_reg_out)

        @instance
        def monitor_instr_in_reg():
            print("\t\tjeffbbexinstr({:s}): instr_in_reg".format(path + "." + name), instr_in_reg)
            while 1:
                yield instr_in_reg
                print("\t\tjeffbbexinstr({:s}) instr_in_reg:".format(path + "." + name), instr_in_reg)

        @instance
        def monitor_instr_out_reg():
            print("\t\tjeffbbexinstr({:s}): instr_out_reg".format(path + "." + name), instr_out_reg)
            while 1:
                yield instr_out_reg
                print("\t\tjeffbbexinstr({:s}) instr_out_reg:".format(path + "." + name), instr_out_reg)

        return (monitor_si, monitor_so, monitor_data_reg_in, monitor_data_reg_out, monitor_instr_in_reg,
                monitor_instr_out_reg, instr_reg_inst, reset_logic)


