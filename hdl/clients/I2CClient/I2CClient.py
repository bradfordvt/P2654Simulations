"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

I2C Client/Slave logic
Based on the concepts from: https://dlbeer.co.nz/articles/i2c.html Verilog code fragments.
Some of the logic had to be corrected to eliminate contention issues on SDA with host and client driving low
at the same time.
"""
from myhdl import *
import os
import os.path


class I2CClient:
    """
    Class structure implementing the RTL for the instrument.
    """
    # State Machine logic controlling the interface
    STATE_IDLE, STATE_DEV_ADDR, STATE_READ, STATE_IDX_PTR, STATE_WRITE = range(5)

    def __init__(self, path, name, reset_n, scl_t, scl_o, scl_i, sda_t, sda_o, sda_i,
                 device_address, write_registers, read_registers, update, capture,
                 write_addresses, read_addresses):
        """
        I2C Client interface to portal registers
        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logger (path instance)
        :param reset_n: Reset signal for state machine. 0=Reset, 1=No reset (reset_n = ResetSignal(1, active=0, isasync=True))
        :param scl_t: Output enable Signal for I2C SCL clock pin
        :param scl_o: Output Signal for I2C SCL clock pin
        :param scl_i: Input Signal for I2C SCL clock pin
        :param sda_t: Output enable Signal for I2C SDA data pin
        :param sda_o: Output Signal for I2C data pin
        :param sda_i: Input Signal for I2C data pin
        :param device_address: The I2C device address for this slave
                Signal(intbv(0x55)[7:])
        :param write_registers: A list of register signals to write to [Signal(intbv(0)[8:])]
        :param read_registers: A list of register signals to read from [Signal(intbv(0)[8:])]
        :param update: A list of signals corresponding to write_registers that signals the
                    I2C interface updated the register contents
        :param capture: A list of signals corresponding to read_registers that signals the
                    I2C interface has read the register contents
        :param write_addresses: Associate list defining the register address for each index in write_registers
        :param read_addresses: Associate list defining the register address for each index in read_registers
        """
        self.path = path
        self.name = name
        self. reset_n = reset_n
        self.scl_t = scl_t
        self.scl_o = scl_o
        self.scl_i = scl_i
        self.sda_t = sda_t
        self.sda_o = sda_o
        self.sda_i = sda_i
        self.device_address = device_address
        self.write_registers = write_registers
        self.read_registers = read_registers
        self.update = update
        self.capture = capture
        self.write_addresses = write_addresses
        self.read_addresses = read_addresses
        # Start detector logic
        self.start_detect = Signal(bool(0))
        self.start_resetter = Signal(bool(1))
        self.start_rst = Signal(bool(1))
        # Stop detector logic
        self.stop_detect = Signal(bool(0))
        self.stop_resetter = Signal(bool(0))
        self.stop_rst = Signal(bool(0))
        # Modulo-9 Counter to preserve the cycle State
        self.bit_counter = Signal(intbv(0, min=0, max=9))
        self.reader_bit = Signal(bool(0))
        self.lsb_bit = Signal(bool(0))
        self.ack_bit = Signal(bool(0))
        # Input shift register logic
        self.input_shift = Signal(intbv(0)[8:])
        # self.device_address = Signal(intbv(0)[7:])
        self.address_detect = Signal(bool(0))
        self.read_write_bit = Signal(bool(0))
        # Master ACK detection logic
        self.master_ack = Signal(bool(0))
        # State Machine logic controlling the interface
        self.state = Signal(intbv(0, min=0, max=5))
        self.write_strobe = Signal(bool(0))
        # Register transfer logic
        self.index_pointer = Signal(intbv(0)[8:])
        # Read of registers needs to be done with an output_shift register
        # that gets latched before the ACK BIT
        self.output_shift = Signal(intbv(0)[8:])
        # Output Driver logic
        self.output_control = Signal(bool(0))
        self.read_done = Signal(bool(0))

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
        return self.i2cclient_rtl(monitor=monitor)

    @block
    def i2cclient_rtl(self, monitor=False):
        """
        The logic for the thermometer
        :return: The generator methods performing the logic decisions
        """
        @always_comb
        def start_detector0():
            self.start_rst.next = not self.reset_n or self.start_resetter

        @always(self.sda_i.negedge, self.start_rst.posedge)
        def start_detector1():
            if self.start_rst:
                self.start_detect.next = bool(0)
            else:
                self.start_detect.next = self.scl_i

        # @always(self.scl_i.posedge, self.reset_n.negedge)
        # def start_detector2():
        #     if self.reset_n == bool(0):
        #         self.start_resetter.next = bool(0)
        #     else:
        #         self.start_resetter.next = self.start_detect

        @always_seq(self.scl_i.posedge, reset=self.reset_n)
        def start_detector2():
            self.start_resetter.next = self.start_detect

        @always_comb
        def stop_detector0():
            self.stop_rst.next = not self.reset_n or self.stop_resetter

        # may have issue with self.sda being Tristate if None
        @always(self.stop_rst.posedge, self.sda_i.posedge)
        def stop_detector1():
            if self.stop_rst:
                self.stop_detect.next = bool(0)
            else:
                if self.scl_i == bool(0):
                    self.stop_detect.next = bool(0)
                else:
                    self.stop_detect.next = bool(1)

        # @always(self.scl_i.posedge, self.reset_n.negedge)
        # def stop_detector2():
        #     if not self.reset_n:
        #         self.stop_resetter.next = bool(0)
        #     else:
        #         self.stop_resetter.next = self.stop_detect

        @always_seq(self.scl_i.posedge, reset=self.reset_n)
        def stop_detector2():
            self.stop_resetter.next = self.stop_detect

        @always_comb
        def state_counter0():
            self.reader_bit.next = (self.bit_counter == 6) and (not self.start_detect)
            self.lsb_bit.next = (self.bit_counter == 7) and (not self.start_detect)
            self.ack_bit.next = (self.bit_counter == 8) and (not self.start_detect)

        @always(self.scl_i.negedge)
        def state_counter1():
            if self.ack_bit or self.start_detect:
                self.bit_counter.next = 0
            else:
                self.bit_counter.next = self.bit_counter + 1

        @always_comb
        def shift_register0():
            self.address_detect.next = (self.input_shift[8:1] == self.device_address)
            self.read_write_bit.next = self.input_shift[0]

        @always(self.scl_i.posedge)
        def shift_register1():
            if not self.ack_bit:
                self.input_shift.next = concat(self.input_shift[7:0], self.sda_i)

        @always(self.scl_i.posedge)
        def master_ack0():
            if self.ack_bit:
                self.master_ack.next = not self.sda_i
            # Added
            else:
                self.master_ack.next = bool(0)

        @always_comb
        def state_mach0():
            self.write_strobe.next = (self.state == I2CClient.STATE_WRITE) and self.ack_bit

        @always_seq(self.scl_i.negedge, reset=self.reset_n)
        def state_mach1():
            # if not self.reset_n:
            #     self.state.next = I2CClient.STATE_IDLE
            #elif self.start_detect:
            if self.start_detect:
                self.state.next = I2CClient.STATE_DEV_ADDR
            elif self.ack_bit:
                if self.state == I2CClient.STATE_IDLE:
                    self.state.next = I2CClient.STATE_IDLE
                elif self.state == I2CClient.STATE_DEV_ADDR:
                    if not self.address_detect:
                        self.state.next = I2CClient.STATE_IDLE
                    elif self.read_write_bit:
                        self.state.next = I2CClient.STATE_READ
                    else:
                        self.state.next = I2CClient.STATE_IDX_PTR
                elif self.state == I2CClient.STATE_READ:
                    if self.master_ack:
                        self.state.next = I2CClient.STATE_READ
                    else:
                        self.state.next = I2CClient.STATE_IDLE
                elif self.state == I2CClient.STATE_IDX_PTR:
                    self.state.next = I2CClient.STATE_WRITE
                elif self.state == I2CClient.STATE_WRITE:
                    self.state.next = I2CClient.STATE_WRITE

        @always_seq(self.scl_i.negedge, reset=self.reset_n)
        def reg_trans0():
            # if not self.reset_n:
            #     self.index_pointer.next = intbv(0)[8:]
            # elif self.stop_detect:
            if self.stop_detect:
                self.index_pointer.next = intbv(0)[8:]
            elif self.ack_bit:
                if self.state == I2CClient.STATE_IDX_PTR:
                    self.index_pointer.next = self.input_shift

        @always(self.reset_n.negedge)
        def reg_trans1_5():
            if not self.reset_n:
                for i in range(len(self.write_registers)):
                    self.write_registers[i].next = intbv(0)[8:]

        @always(self.scl_i.negedge)
        def reg_trans1():
            if self.write_strobe and self.index_pointer < len(self.write_registers):
                self.write_registers[self.index_pointer].next = self.input_shift
                self.update[self.index_pointer].next = bool(1)
            else:
                self.update[self.index_pointer].next = bool(0)

        @always(self.scl_i.negedge)
        def reg_trans2():
            if self.lsb_bit:
                if self.index_pointer < len(self.read_registers):
                    self.output_shift.next = self.read_registers[self.index_pointer]
                    self.capture[self.index_pointer].next = bool(1)
            else:
                self.output_shift.next = concat(self.output_shift[7:0], bool(0))
                self.capture[self.index_pointer].next = bool(0)

        @always_comb
        def output0():
            if self.output_control:
                self.sda_o.next = bool(1)  # Really 'Z' but SDA has to be a TristateSignal
                self.sda_t.next = bool(0)
            else:
                self.sda_o.next = bool(0)
                self.sda_t.next = bool(1)

        @always_seq(self.scl_i.negedge, reset=self.reset_n)
        def output1():
            # if not self.reset_n:
            #     self.output_control.next = bool(1)
            # elif self.start_detect:
            if self.start_detect:
                self.output_control.next = bool(1)
            elif self.lsb_bit:
                self.output_control.next = not (((self.state == I2CClient.STATE_DEV_ADDR) and self.address_detect) or
                                                (self.state == I2CClient.STATE_IDX_PTR) or
                                                (self.state == I2CClient.STATE_WRITE))
            elif self.ack_bit:
                # Deliver the first bit of the next slave-to-master transfer, if applicable.
                if (((self.state == I2CClient.STATE_READ) and self.master_ack) or
                        ((self.state == I2CClient.STATE_DEV_ADDR) and self.address_detect and self.read_write_bit)):
                    self.output_control.next = self.output_shift[7]
                else:
                    self.output_control.next = bool(1)
            elif self.state == I2CClient.STATE_READ:
                self.output_control.next = self.output_shift[7]
            else:
                self.output_control.next = bool(1)

        if not monitor:
            return start_detector0, start_detector1, start_detector2, stop_detector0, stop_detector1, stop_detector2,\
                   state_counter0, state_counter1, shift_register0, shift_register1, master_ack0, state_mach0,\
                   state_mach1, reg_trans0, reg_trans1, reg_trans2, output0, output1, reg_trans1_5
        else:
            @instance
            def monitor_start_detect():
                print("\t\tI2CClient({:s}): start_detect".format(self.path + '.' + self.name), self.start_detect)
                while 1:
                    yield self.start_detect
                    print("\t\tI2CClient({:s}): start_detect".format(self.path + '.' + self.name), self.start_detect)

            @instance
            def monitor_start_resetter():
                print("\t\tI2CClient({:s}): start_resetter".format(self.path + '.' + self.name), self.start_resetter)
                while 1:
                    yield self.start_resetter
                    print("\t\tI2CClient({:s}): start_resetter".format(self.path + '.' + self.name), self.start_resetter)

            @instance
            def monitor_start_rst():
                print("\t\tI2CClient({:s}): start_rst".format(self.path + '.' + self.name), self.start_rst)
                while 1:
                    yield self.start_rst
                    print("\t\tI2CClient({:s}): start_rst".format(self.path + '.' + self.name), self.start_rst)

            @instance
            def monitor_stop_detect():
                print("\t\tI2CClient({:s}): stop_detect".format(self.path + '.' + self.name), self.stop_detect)
                while 1:
                    yield self.stop_detect
                    print("\t\tI2CClient({:s}): stop_detect".format(self.path + '.' + self.name), self.stop_detect)

            @instance
            def monitor_stop_resetter():
                print("\t\tI2CClient({:s}): stop_resetter".format(self.path + '.' + self.name), self.stop_resetter)
                while 1:
                    yield self.stop_resetter
                    print("\t\tI2CClient({:s}): stop_resetter".format(self.path + '.' + self.name), self.stop_resetter)

            @instance
            def monitor_stop_rst():
                print("\t\tI2CClient({:s}): stop_rst".format(self.path + '.' + self.name), self.stop_rst)
                while 1:
                    yield self.stop_rst
                    print("\t\tI2CClient({:s}): stop_rst".format(self.path + '.' + self.name), self.stop_rst)

            @instance
            def monitor_lsb_bit():
                print("\t\tI2CClient({:s}): lsb_bit".format(self.path + '.' + self.name), self.lsb_bit)
                while 1:
                    yield self.lsb_bit
                    print("\t\tI2CClient({:s}): lsb_bit".format(self.path + '.' + self.name), self.lsb_bit)

            @instance
            def monitor_ack_bit():
                print("\t\tI2CClient({:s}): ack_bit".format(self.path + '.' + self.name), self.ack_bit)
                while 1:
                    yield self.ack_bit
                    print("\t\tI2CClient({:s}): ack_bit".format(self.path + '.' + self.name), self.ack_bit)

            @instance
            def monitor_read_write_bit():
                print("\t\tI2CClient({:s}): read_write_bit".format(self.path + '.' + self.name), self.read_write_bit)
                while 1:
                    yield self.read_write_bit
                    print("\t\tI2CClient({:s}): read_write_bit".format(self.path + '.' + self.name), self.read_write_bit)

            @instance
            def monitor_master_ack():
                print("\t\tI2CClient({:s}): master_ack".format(self.path + '.' + self.name), self.master_ack)
                while 1:
                    yield self.master_ack
                    print("\t\tI2CClient({:s}): master_ack".format(self.path + '.' + self.name), self.master_ack)

            @instance
            def monitor_write_strobe():
                print("\t\tI2CClient({:s}): write_strobe".format(self.path + '.' + self.name), self.write_strobe)
                while 1:
                    yield self.write_strobe
                    print("\t\tI2CClient({:s}): write_strobe".format(self.path + '.' + self.name), self.write_strobe)

            @instance
            def monitor_output_control():
                print("\t\tI2CClient({:s}): output_control".format(self.path + '.' + self.name), self.output_control)
                while 1:
                    yield self.output_control
                    print("\t\tI2CClient({:s}): output_control".format(self.path + '.' + self.name), self.output_control)

            @instance
            def monitor_sda_i():
                print("\t\tI2CClient({:s}): sda_i".format(self.path + '.' + self.name), self.sda_i)
                while 1:
                    yield self.sda_i
                    print("\t\tI2CClient({:s}): sda_i".format(self.path + '.' + self.name), self.sda_i)

            @instance
            def monitor_sda_o():
                print("\t\tI2CClient({:s}): sda_o".format(self.path + '.' + self.name), self.sda_o)
                while 1:
                    yield self.sda_o
                    print("\t\tI2CClient({:s}): sda_o".format(self.path + '.' + self.name), self.sda_o)

            @instance
            def monitor_sda_t():
                print("\t\tI2CClient({:s}): sda_t".format(self.path + '.' + self.name), self.sda_t)
                while 1:
                    yield self.sda_t
                    print("\t\tI2CClient({:s}): sda_t".format(self.path + '.' + self.name), self.sda_t)

            @instance
            def monitor_scl_i():
                print("\t\tI2CClient({:s}): scl_i".format(self.path + '.' + self.name), self.scl_i)
                while 1:
                    yield self.scl_i
                    print("\t\tI2CClient({:s}): scl_i".format(self.path + '.' + self.name), self.scl_i)

            @instance
            def monitor_output_shift():
                print("\t\tI2CClient({:s}): output_shift".format(self.path + '.' + self.name), hex(self.output_shift))
                while 1:
                    yield self.output_shift
                    print("\t\tI2CClient({:s}): output_shift".format(self.path + '.' + self.name), hex(self.output_shift))

            @instance
            def monitor_input_shift():
                print("\t\tI2CClient({:s}): input_shift".format(self.path + '.' + self.name), hex(self.input_shift))
                while 1:
                    yield self.input_shift
                    print("\t\tI2CClient({:s}): input_shift".format(self.path + '.' + self.name), hex(self.input_shift))

            @instance
            def monitor_state():
                s = ["STATE_IDLE", "STATE_DEV_ADDR", "STATE_READ", "STATE_IDX_PTR", "STATE_WRITE"]
                print("\t\tI2CClient({:s}): state".format(self.path + '.' + self.name), s[self.state])
                while 1:
                    yield self.state
                    print("\t\tI2CClient({:s}): state".format(self.path + '.' + self.name), s[self.state])

            return start_detector0, start_detector1, start_detector2, stop_detector0, stop_detector1, stop_detector2,\
                   state_counter0, state_counter1, shift_register0, shift_register1, master_ack0, state_mach0,\
                   state_mach1, reg_trans0, reg_trans1, reg_trans2, output0, output1,\
                   monitor_start_detect, monitor_start_resetter, monitor_start_rst, monitor_stop_detect, \
                   monitor_stop_resetter, monitor_stop_rst, monitor_lsb_bit, monitor_ack_bit, \
                   monitor_read_write_bit, monitor_master_ack, monitor_write_strobe, monitor_output_control, \
                   monitor_sda_i, monitor_scl_i, monitor_output_shift, monitor_input_shift, monitor_state, \
                   monitor_sda_o, monitor_sda_t, reg_trans1_5

    @staticmethod
    def convert():
        """
        Convert the myHDL design into VHDL and Verilog
        :return:
        """
        N = 5
        reset_n = ResetSignal(1, active=0, isasync=True)
        scl = TristateSignal(bool(0))
        sda = TristateSignal(bool(0))
        scl_t = Signal(bool(0))
        scl_o = Signal(bool(0))
        scl_i = Signal(bool(0))
        sda_t = Signal(bool(0))
        sda_o = Signal(bool(0))
        sda_i = Signal(bool(0))
        write_registers = [Signal(intbv(0)[8:]) for _ in range(N)]
        read_registers = [Signal(intbv(0)[8:]) for _ in range(N)]
        device_address = Signal(intbv(0x55)[7::0])
        write_addresses = [i for i in range(N)]
        read_addresses = [i for i in range(N)]
        update = [Signal(bool(0)) for _ in range(N)]
        capture = [Signal(bool(0)) for _ in range(N)]

        i2cclient_inst = I2CClient('TOP', 'I2CC0', reset_n, scl_t, scl_o, scl_i, sda_t, sda_o, sda_i,
                                    device_address, write_registers, read_registers, update, capture,
                                    write_addresses, read_addresses)

        i2cclient_inst.toVerilog()
        i2cclient_inst.toVHDL()

    @staticmethod
    @block
    def testbench(monitor=False):
        """
        Test bench interface for a quick test of the operation of the design
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """
        N = 5
        reset_n = ResetSignal(1, active=0, isasync=True)
        scl = TristateSignal(bool(0))
        sda = TristateSignal(bool(0))
        scldriver = scl.driver()
        sdadriver = sda.driver()
        scldriver1 = scl.driver()
        sdadriver1 = sda.driver()
        scl_t = Signal(bool(0))
        scl_o = Signal(bool(0))
        scl_i = Signal(bool(0))
        sda_t = Signal(bool(0))
        sda_o = Signal(bool(0))
        sda_i = Signal(bool(0))
        write_registers = [Signal(intbv(0)[8:]) for _ in range(N)]
        read_registers = [Signal(intbv(i)[8:]) for i in range(N)]
        device_address = Signal(intbv(0x55)[7::0])
        write_addresses = [i for i in range(N)]
        read_addresses = [i for i in range(N)]
        update = [Signal(bool(0)) for _ in range(N)]
        capture = [Signal(bool(0)) for _ in range(N)]
        contention = Signal(bool(0))

        i2cclient_inst = I2CClient('TOP', 'I2CC0', reset_n, scl_t, scl_o, scl_i, sda_t, sda_o, sda_i,
                                    device_address, write_registers, read_registers, update, capture,
                                    write_addresses, read_addresses)

        I2C_DEBUG = True

        def i2c_setDEBUG():
            global I2C_DEBUG
            I2C_DEBUG = True

        def i2c_start(SCL, SDA):
            '''
            '''
            if I2C_DEBUG:
                print("[i2c_start C:1 D:1 D:0 C:0]")
            SCL.next = bool(1)
            SDA.next = None
            yield delay(10)
            SDA.next = bool(0)
            yield delay(10)
            SCL.next = bool(0)
            yield delay(10)

        def i2c_stop(SCL, SDA):
            '''
            '''
            if I2C_DEBUG:
                print("[i2c_stop C:0 D:0 C:1 D:1]")
            SCL.next = bool(0)
            yield delay(10)
            SDA.next = bool(0)
            yield delay(10)
            SCL.next = bool(1)
            yield delay(10)
            SDA.next = None
            yield delay(10)

        def i2c_slave_ack(ack, SCL, SDA):
            '''
            '''
            SCL.next = bool(1)
            yield delay(10)
            if SDA._sig.val == bool(0):
                ack.next = bool(0)
            else:
                ack.next = bool(1)
            yield delay(10)
            SCL.next = bool(0)
            yield delay(10)
            if ack.next == bool(1):
                print("i2c_slave_ack: ACK FAILED!")
            if I2C_DEBUG:
                print("[i2c_slave_ack C:1 D:(", int(ack.next), ") C:0]")

        def i2c_init(SCL, SDA):
            '''
            '''
            if I2C_DEBUG:
                print("[i2c_init C:1 D:1]")
            SCL.next = bool(1)
            SDA.next = None
            yield delay(10)

        def i2c_writebit(bit, SCL, SDA):
            '''
            '''
            if I2C_DEBUG:
                print("[i2c_writebit D:", int(bit), " C:1 C:0 D:1]")
            if bit:
                SDA.next = None
            else:
                SDA.next = bool(0)
            yield delay(10)
            SCL.next = bool(1)
            yield delay(10)
            SCL.next = bool(0)
            # yield delay(10)
            SDA.next = None
            yield delay(10)

        def i2c_readbit(bit, SCL, SDA):
            '''
            '''
            SCL.next = bool(1)
            yield delay(10)
            if SDA._sig.val == bool(0):
                bit.next = bool(0)
            else:
                bit.next = bool(1)
            SCL.next = bool(0)
            yield delay(10)
            if I2C_DEBUG:
                print("[i2c_readbit C:1 D:(", int(bit), ") C:0]")

        def i2c_reset_bus(SCL, SDA):
            '''
            '''
            yield i2c_init(SCL, SDA)
            if SCL == bool(1) and SDA == None:
                print("BUS has already been released!")
            else:
                yield i2c_start(SCL, SDA)
                for i in range(9):
                    SCL.next = bool(0)
                    yield delay(10)
                    SCL.next = bool(1)
                    yield delay(10)
                    SCL.next = bool(0)
                    yield delay(10)
                    if SDA != bool(0):
                        break
                if SDA == bool(0):
                    print("SDA is still stuck at LOW!")
                yield i2c_start(SCL, SDA)
                yield i2c_stop(SCL, SDA)

        def i2c_master_ack(ack, SCL, SDA):
            '''
            '''
            yield i2c_writebit(ack, SCL, SDA)

        def i2c_write_data(val, SCL, SDA):
            '''
            '''
            if I2C_DEBUG:
                print("[i2c_write_data")
            data = intbv(val)[8:]
            for i in range(8):
                yield i2c_writebit(data[7 - i], SCL, SDA)
            ack = Signal(bool(0))
            yield i2c_slave_ack(ack, SCL, SDA)
            if ack == bool(1):
                print("SLAVE failed to ACK!")
            if I2C_DEBUG:
                print("End i2c_write_data]")

        def i2c_read_data(val, ack, SCL, SDA):
            '''
            '''
            if I2C_DEBUG:
                print("[i2c_read_data")
            bit = Signal(bool(0))
            for i in range(8):
                yield i2c_readbit(bit, SCL, SDA)
                val.next[7 - i] = bit
            yield i2c_master_ack(ack, SCL, SDA)
            if I2C_DEBUG:
                print("End i2c_read_data]")

        def i2c_read_reg(DevAddress, RegAddress, val, SCL, SDA):
            '''
            '''
            if I2C_DEBUG:
                print("[i2c_read_reg")
            yield i2c_start(SCL, SDA)
            yield i2c_write_data((DevAddress << 1) & 0xFE, SCL, SDA)
            yield i2c_write_data(RegAddress, SCL, SDA)
            yield i2c_start(SCL, SDA)
            yield i2c_write_data((DevAddress << 1) | 1, SCL, SDA)
            # yield i2c_write_data(RegAddress, SCL, SDA)
            ack = Signal(bool(1))
            yield i2c_read_data(val, ack, SCL, SDA)
            yield i2c_stop(SCL, SDA)
            if I2C_DEBUG:
                print("End i2c_read_reg]")

        def i2c_write_reg(DevAddress, RegAddress, val, SCL, SDA):
            '''
            '''
            if I2C_DEBUG:
                print("[i2c_write_reg(", hex((DevAddress << 1) & 0xFE), ", ", hex(RegAddress), ", ", bin(val), "}")
            yield i2c_start(SCL, SDA)
            yield i2c_write_data((DevAddress << 1) & 0xFE, SCL, SDA)
            yield i2c_write_data(RegAddress, SCL, SDA)
            yield i2c_write_data(val, SCL, SDA)
            yield i2c_stop(SCL, SDA)
            if I2C_DEBUG:
                print("End i2c_write_reg")

        def i2c_write_n_read_reg(DevAddress, RegAddress, Data, val, SCL, SDA):
            '''
            '''
            if I2C_DEBUG:
                print("[i2c_write_n_read_reg")
            yield i2c_write_reg(DevAddress, RegAddress, Data, SCL, SDA)
            yield i2c_read_reg(DevAddress, RegAddress, val, SCL, SDA)
            if I2C_DEBUG:
                print("End i2c_write_n_read_reg]")

        @always_comb
        def client():
            if sda == bool(0):
                sda_i.next = bool(0)
            else:
                sda_i.next = bool(1)
            if sda_t == bool(1) and sda_o == bool(0):
                sdadriver1.next = bool(0)
            else:
                sdadriver1.next = None
            if scl == bool(0):
                scl_i.next = bool(0)
            else:
                scl_i.next = bool(1)
            if scl_t == bool(1) and scl_o == bool(0):
                scldriver1.next = bool(0)
            else:
                scldriver1.next = None

        @always_comb
        def contention_monitor():
            if sdadriver == bool(0) and sdadriver1 == bool(0):
                contention.next = bool(1)
            else:
                contention.next = bool(0)

        @instance
        def stimulus():
            """
            Perform instruction decoding for various instructions
            :return:
            """
            i2c_setDEBUG()
            # Reset the I2CClient
            reset_n.next = bool(0)
            scldriver.next = bool(1)
            yield delay(10)
            scldriver.next = bool(0)
            yield delay(10)
            reset_n.next = bool(1)
            scldriver.next = bool(1)
            yield delay(10)
            scldriver.next = bool(0)
            yield delay(10)
            yield i2c_init(scldriver, sdadriver)
            # for i in range(N):
            #     yield i2c_write_reg(device_address, i, i, scldriver, sdadriver)
            # for i in range(N):
            #     print("write_registers[", i, "] == ", i)
            #     assert(write_registers[i] == i)
            val = Signal(intbv(0)[8:])
            for i in range(N):
                yield i2c_read_reg(device_address, i, val, scldriver, sdadriver)
                print("val == ", i, " => ", val, " == ", i)
                assert(val == i)

            raise StopSimulation()

        return i2cclient_inst.i2cclient_rtl(monitor=monitor), stimulus, client, contention_monitor


if __name__ == '__main__':
    tb = I2CClient.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    I2CClient.convert()
