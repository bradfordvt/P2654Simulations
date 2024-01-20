#!/usr/bin/env python
"""
    Simulation test board for Jeff Rearick's I2C_construction_20231003 example.

    Simulation test board for Jeff Rearick's I2C_construction_20231003 example.

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
__copyright__ = "Copyright 2023, VT Enterprises Consulting Services"
__credits__ = ["Bradford G. Van Treuren"]
__date__ = "2024/01/20"
__deprecated__ = False
__email__ = "bradvt59@gmail.com"
__license__ = "Apache 2.0"
__maintainer__ = "Bradford G. Van Treuren"
__status__ = "Alpha/Experimental"
__version__ = "0.0.1"

from myhdl import *

# from hdl.experimental.pseudo_led import pseudo_led
from hdl.boards.i2ctest.i2cdevice import I2CDevice
from hdl.boards.common.AbstractBoard import AbstractBoard


class jeffbbexbrd(AbstractBoard):
    def __init__(self):
        super().__init__()

        self.clk = Signal(bool(0))
        # self.state0 = Signal(bool(0))
        # self.state1 = Signal(bool(0))
        # self.state2 = Signal(bool(0))
        # self.state3 = Signal(bool(0))
        # self.state4 = Signal(bool(0))
        #
        # self.led0 = None
        # self.led1 = None
        # self.led2 = None
        # self.led3 = None
        # self.led4 = None
        self.i2c_device = None

    def configure_syscon(self, clk_o, rst_o):
        self.clk_o = clk_o
        self.rst_o = rst_o


    @block
    def rtl(self):

        # self.led0 = pseudo_led(self.clk, self.state0, color="WHITE")
        # self.led1 = pseudo_led(self.clk, self.state1, color="RED")
        # self.led2 = pseudo_led(self.clk, self.state2, color="GREEN")
        # self.led3 = pseudo_led(self.clk, self.state3, color="YELLOW")
        # self.led4 = pseudo_led(self.clk, self.state4, color="BLUE")
        self.i2c_device = I2CDevice(self.clk_o, self.rst_o)
        self.i2c_device.configure_i2c(self.scl_o, self.scl_i, self.scl_e, self.sda_o, self.sda_i, self.sda_e)

        # build up the netlist for the board here
        @always_comb
        def netlist():
            # Wire the LEDs to the GPIO Signals
            # self.state0.next = self.o_gpio[0]
            # self.state1.next = self.o_gpio[1]
            # self.state2.next = self.o_gpio[2]
            # self.state3.next = self.o_gpio[3]
            # self.state4.next = self.o_gpio[4]
            # self.i_gpio.next = self.o_gpio
            # Wire the LED controller clock to the WB clock
            self.clk.next = self.clk_o

        # return self.led0, self.led1, self.led2, self.led3, self.led4, netlist, \
        #        self.i2c_device.rtl()
        return netlist, self.i2c_device.rtl()
