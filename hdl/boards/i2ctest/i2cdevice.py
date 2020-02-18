"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
#########
I2C
#########
Address 0x00001C00 I2C prer [low byte] (clock prescale register)
Address 0x00001C01 I2C prer [high byte] (clock prescale register)
Address 0x00001C02 I2C ctr (control register)
Address 0x00001C03 I2C rxr (receive register)
Address 0x00001C04 I2C sr (status register)
Address 0x00001C05 I2C txr #########
(transmit register)
Address 0x00001C06 I2C cr (command register)
Address 0x00001C07 I2C Reserved

/ *
*Definitions
for the Opencores i2c master core
* /

/ *--- Definitions
for i2c master's registers --- */

/ *----- Read - write
access * /

# define OC_I2C_PRER_LO 0x00     /* Low byte clock prescaler register  */
# define OC_I2C_PRER_HI 0x01     /* High byte clock prescaler register */
# define OC_I2C_CTR     0x02     /* Control register                   */

/ *----- Write - only
registers * /

# define OC_I2C_TXR     0x03     /* Transmit byte register             */
# define OC_I2C_CR      0x04     /* Command register                   */

/ *----- Read - only
registers * /

# define OC_I2C_RXR     0x03     /* Receive byte register              */
# define OC_I2C_SR      0x04     /* Status register                    */

/ *----- Bits
definition * /

/ *----- Control
register * /

# define OC_I2C_EN (1<<7)        /* Core enable bit:                   */
/ *1 - core is enabled * /
/ *0 - core is disabled * /
# define OC_I2C_IEN (1<<6)       /* Interrupt enable bit               */
/ *1 - Interrupt
enabled * /
/ *0 - Interrupt
disabled * /
/ *Other
bits in CR
are
reserved * /

/ *----- Command
register
bits * /

# define OC_I2C_STA (1<<7)       /* Generate (repeated) start condition*/
# define OC_I2C_STO (1<<6)       /* Generate stop condition            */
# define OC_I2C_RD  (1<<5)       /* Read from slave                    */
# define OC_I2C_WR  (1<<4)       /* Write to slave                     */
# define OC_I2C_ACK (1<<3)       /* Acknowledge from slave             */
/ *1 - ACK * /
/ *0 - NACK * /
# define OC_I2C_IACK (1<<0)      /* Interrupt acknowledge              */

/ *----- Status
register
bits * /

# define OC_I2C_RXACK (1<<7)     /* ACK received from slave            */
/ *1 - ACK * /
/ *0 - NACK * /
# define OC_I2C_BUSY  (1<<6)     /* Busy bit                           */
# define OC_I2C_TIP   (1<<1)     /* Transfer in progress               */
# define OC_I2C_IF    (1<<0)     /* Interrupt flag                     */

/ *bit
testing and setting
macros * /

# define OC_ISSET(reg,bitmask)       ((reg)&(bitmask))
# define OC_ISCLEAR(reg,bitmask)     (!(OC_ISSET(reg,bitmask)))
# define OC_BITSET(reg,bitmask)      ((reg)|(bitmask))
# define OC_BITCLEAR(reg,bitmask)    ((reg)|(~(bitmask)))
# define OC_BITTOGGLE(reg,bitmask)   ((reg)^(bitmask))
# define OC_REGMOVE(reg,value)       ((reg)=(value))
"""

from myhdl import *
from hdl.hosts.i2chost.i2c_interface import i2c_if
# from hdl.clients.I2CClient.I2CClient import I2CClient
# from hdl.clients.i2cslave.i2cslavetop import i2cslavetop
# from hdl.common.ram import ram
# from hdl.common.rom import rom
# import os
# import os.path
from hdl.clients.I2CClient.i2cslave_RW import i2cslave_RW


period = 20  # clk frequency = 50 MHz


class I2CDevice:
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

        # self.local_update = Signal(bool(0))
        # self.local_update_rst = Signal(bool(0))
        # self.local_update_resetter = Signal(bool(0))
        #
        # self.ram_address = Signal(intbv(0)[8:])
        # self.ram_read_address = Signal(intbv(0)[8:])
        # self.ram_dout = Signal(intbv(0)[8:])
        # self.ram_we = Signal(bool(0))
        # self.ram_clk = Signal(bool(0))
        # self.local_update = Signal(bool(0))
        # self.local_update_rst = Signal(bool(0))
        # self.local_update_resetter = Signal(bool(0))
        # self.N = 5
        #
        # self.read_registers = (0, 1, 2, 3, 4)
        # self.rom_address = Signal(intbv(0)[8:])
        # self.rom_dout = Signal(intbv(0)[8:])

    def configure_i2c(self, scl_o, scl_i, scl_e, sda_o, sda_i, sda_e):
        self.scl_o = scl_o
        self.scl_i = scl_i
        self.scl_e = scl_e
        self.sda_o = sda_o
        self.sda_i = sda_i
        self.sda_e = sda_e

    @block
    def rtl(self):

        i2c_interface_c = i2c_if(self.clk_o, self.rst_o)
        # i2c_client_inst = I2CClient('DEMO', 'I2C_CLIENT0', self.reset_n,
        #                             i2c_interface_c.scl_i, i2c_interface_c.sda_e,
        #                             i2c_interface_c.sda_o, i2c_interface_c.sda_i,
        #                             self.device_address, self.write_address, self.write_data, self.update,
        #                             self.read_address, self.read_data, self.capture,
        #                             monitor=True)
        # ram_inst = ram(self.ram_dout, self.write_data, self.ram_address, self.ram_we, self.ram_clk, depth=self.N)
        # rom_inst = rom(self.rom_dout, self.rom_address, self.read_registers)
        # myReg0 = Signal(intbv(0)[8:])
        # i2c_client_inst = i2cslavetop(self.clk_o, self.rst_o, i2c_interface_c.sda_i, i2c_interface_c.sda_o,
        #                               i2c_interface_c.sda_e, i2c_interface_c.scl_i, myReg0)
        reg_00 = Signal(intbv(0)[8:])
        reg_01 = Signal(intbv(0)[8:])
        reg_02 = Signal(intbv(0)[8:])
        reg_00_latch = Signal(bool(0))
        reg_01_latch = Signal(bool(0))
        reg_02_latch = Signal(bool(0))
        i2c_client_inst = i2cslave_RW(i2c_interface_c.scl_i, i2c_interface_c.sda_i, i2c_interface_c.sda_e, self.reset_n,
                                      reg_00, reg_01, reg_02, reg_00_latch, reg_01_latch, reg_02_latch)

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

        # @always_comb
        # def update_detector4():
        #     self.local_update_rst.next = not self.reset_n or self.local_update_resetter
        #
        # @always(self.clk_o.negedge, self.local_update_rst.posedge)
        # def update_detector5():
        #     if self.local_update_rst:
        #         self.local_update.next = bool(0)
        #     else:
        #         self.local_update.next = self.update
        #
        # @always_seq(self.clk_o.posedge, reset=self.reset_n)
        # def update_detector6():
        #     self.local_update_resetter.next = self.local_update
        #
        # @always(self.clk_o.posedge)
        # def client_write():
        #     if self.local_update == bool(1):
        #         if self.write_address < self.N:  # A RAM address and not a ROM address
        #             self.ram_address.next = self.write_address
        #             self.ram_we.next = bool(1)
        #             self.ram_clk.next = bool(1)
        #
        # @always_comb
        # def client_read():
        #     if self.read_address < self.N:  # A RAM address and not a ROM address
        #         self.ram_we.next = bool(0)
        #         self.ram_clk.next = bool(0)
        #         self.ram_address.next = self.read_address
        #         self.read_data.next = self.ram_dout
        #     elif self.read_address >= self.N and self.read_address < self.N + 5:
        #         self.rom_address.next = self.read_address
        #         self.read_data.next = self.rom_dout

        return netlist, i2c_client_inst, power_on_reset_gen
               # update_detector4, update_detector5, update_detector6, client_write, client_read

