"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

I2C Client/Slave logic
Based on the concepts from: https://dlbeer.co.nz/articles/i2c.html Verilog code fragments.
Some of the logic had to be corrected to eliminate contention issues on SDA with host and client driving low
at the same time.
"""
from myhdl import *
from hdl.common.ram import ram
from hdl.common.rom import rom
import os
import os.path


# State Machine logic controlling the interface
STATE_IDLE, STATE_DEV_ADDR, STATE_READ, STATE_IDX_PTR, STATE_WRITE = range(5)


period = 20  # clk frequency = 50 MHz


@block
def I2CClient(path, name, reset_n, scl_i, sda_t, sda_o, sda_i,
              device_address, write_address, write_data, update,
              read_address, read_data, capture,
              monitor=False):
    """
    I2C Client interface to portal registers
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param reset_n: Reset signal for state machine. 0=Reset, 1=No reset (reset_n = ResetSignal(1, active=0, isasync=True))
    :param scl_i: Input Signal for I2C SCL clock pin
    :param sda_t: Output enable Signal for I2C SDA data pin
    :param sda_o: Output Signal for I2C data pin
    :param sda_i: Input Signal for I2C data pin
    :param device_address: The I2C device address for this slave
            Signal(intbv(0x55)[7:])
    :param write_address: The address/index of the external register/memory to be written to as requested by I2C command
    :param write_data: The data to be written to the external register/memory
    :param update: Latch signal for when the I2C interface has data available on the write interface
    :param read_address: The address/index of the external register/memory to be read from as requested by I2C command
    :param read_data: The data bus where the data to be read is to be placed by the external interface
    :param capture: A Latch signal for when the I2C interface has acquired the data from the external interface
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    # Start detector logic
    start_detect = Signal(bool(0))
    start_resetter = Signal(bool(1))
    start_rst = Signal(bool(1))
    # Stop detector logic
    stop_detect = Signal(bool(0))
    stop_resetter = Signal(bool(0))
    stop_rst = Signal(bool(0))
    # Modulo-9 Counter to preserve the cycle State
    bit_counter = Signal(intbv(0, min=0, max=9))
    reader_bit = Signal(bool(0))
    lsb_bit = Signal(bool(0))
    ack_bit = Signal(bool(0))
    # Input shift register logic
    input_shift = Signal(intbv(0)[8:])
    address_detect = Signal(bool(0))
    read_write_bit = Signal(bool(0))
    # Master ACK detection logic
    master_ack = Signal(bool(0))
    # State Machine logic controlling the interface
    state = Signal(intbv(0, min=0, max=5))
    write_strobe = Signal(bool(0))
    # Register transfer logic
    # index_pointer = Signal(intbv(0)[8:])
    # Read of registers needs to be done with an output_shift register
    # that gets latched before the ACK BIT
    output_shift = Signal(intbv(0)[8:])
    # Output Driver logic
    output_control = Signal(bool(0))

    @always_comb
    def start_detector0():
        start_rst.next = not reset_n or start_resetter

    @always(sda_i.negedge, start_rst.posedge)
    def start_detector1():
        if start_rst:
            start_detect.next = bool(0)
        else:
            start_detect.next = scl_i

    @always_seq(scl_i.posedge, reset=reset_n)
    def start_detector2():
        start_resetter.next = start_detect

    @always_comb
    def stop_detector0():
        stop_rst.next = not reset_n or stop_resetter

    # may have issue with sda being Tristate if None
    @always(stop_rst.posedge, sda_i.posedge)
    def stop_detector1():
        if stop_rst:
            stop_detect.next = bool(0)
        else:
            if scl_i == bool(0):
                stop_detect.next = bool(0)
            else:
                stop_detect.next = bool(1)

    @always_seq(scl_i.posedge, reset=reset_n)
    def stop_detector2():
        stop_resetter.next = stop_detect

    @always_comb
    def state_counter0():
        reader_bit.next = (bit_counter == 6) and (not start_detect)
        lsb_bit.next = (bit_counter == 7) and (not start_detect)
        ack_bit.next = (bit_counter == 8) and (not start_detect)

    @always(scl_i.negedge)
    def state_counter1():
        if ack_bit or start_detect:
            bit_counter.next = 0
        else:
            bit_counter.next = bit_counter + 1

    @always_comb
    def shift_register0():
        address_detect.next = (input_shift[8:1] == device_address)
        read_write_bit.next = input_shift[0]

    @always(scl_i.posedge)
    def shift_register1():
        if not reset_n:
            input_shift.next = intbv(0)[8:]
        elif not ack_bit:
            input_shift.next = concat(input_shift[7:0], sda_i)

    @always(scl_i.posedge)
    def master_ack0():
        if ack_bit:
            master_ack.next = not sda_i
        # Added
        else:
            master_ack.next = bool(0)

    @always_comb
    def state_mach0():
        write_strobe.next = (state == STATE_WRITE) and ack_bit

    @always_seq(scl_i.negedge, reset=reset_n)
    def state_mach1():
        if start_detect:
            state.next = STATE_DEV_ADDR
        elif ack_bit:
            if state == STATE_IDLE:
                state.next = STATE_IDLE
            elif state == STATE_DEV_ADDR:
                if not address_detect:
                    state.next = STATE_IDLE
                elif read_write_bit:
                    state.next = STATE_READ
                else:
                    state.next = STATE_IDX_PTR
            elif state == STATE_READ:
                if master_ack:
                    state.next = STATE_READ
                else:
                    state.next = STATE_IDLE
            elif state == STATE_IDX_PTR:
                state.next = STATE_WRITE
            elif state == STATE_WRITE:
                state.next = STATE_WRITE

    @always_seq(scl_i.negedge, reset=reset_n)
    def reg_trans0():
        # if not reset_n:
        #     index_pointer.next = intbv(0)[8:]
        # elif stop_detect:
        if stop_detect:
            write_address.next = intbv(0)[8:]
            read_address.next = intbv(0)[8:]
        elif ack_bit:
            if state == STATE_IDX_PTR:
                write_address.next = input_shift
                read_address.next = input_shift

    @always(scl_i.negedge)
    def reg_trans1():
        if write_strobe:
            write_data.next = input_shift
            update.next = bool(1)
        else:
            update.next = bool(0)

    @always(scl_i.negedge)
    def reg_trans2():
        if lsb_bit:
            output_shift.next = read_data
            capture.next = bool(1)
        else:
            output_shift.next = concat(output_shift[7:0], bool(0))
            capture.next = bool(0)

    @always_comb
    def output0():
        if output_control:
            sda_o.next = bool(1)  # Really 'Z' but SDA has to be a TristateSignal open collector implementation
            sda_t.next = bool(0)
        else:
            sda_o.next = bool(0)
            sda_t.next = bool(1)

    @always_seq(scl_i.negedge, reset=reset_n)
    def output1():
        if start_detect:
            output_control.next = bool(1)
        elif lsb_bit:
            output_control.next = not (((state == STATE_DEV_ADDR) and address_detect) or
                                            (state == STATE_IDX_PTR) or
                                            (state == STATE_WRITE))
        elif ack_bit:
            # Deliver the first bit of the next slave-to-master transfer, if applicable.
            if (((state == STATE_READ) and master_ack) or
                    ((state == STATE_DEV_ADDR) and address_detect and read_write_bit)):
                output_control.next = output_shift[7]
            else:
                output_control.next = bool(1)
        elif state == STATE_READ:
            output_control.next = output_shift[7]
        else:
            output_control.next = bool(1)

    if not monitor:
        return start_detector0, start_detector1, start_detector2, stop_detector0, stop_detector1, stop_detector2, \
               state_counter0, state_counter1, shift_register0, shift_register1, master_ack0, state_mach0, \
               state_mach1, reg_trans0, reg_trans1, reg_trans2, output0, output1
    else:
        @instance
        def monitor_start_detect():
            print("\t\tI2CClient({:s}): start_detect".format(path + '.' + name), start_detect)
            while 1:
                yield start_detect
                print("\t\tI2CClient({:s}): start_detect".format(path + '.' + name), start_detect)

        @instance
        def monitor_start_resetter():
            print("\t\tI2CClient({:s}): start_resetter".format(path + '.' + name), start_resetter)
            while 1:
                yield start_resetter
                print("\t\tI2CClient({:s}): start_resetter".format(path + '.' + name), start_resetter)

        @instance
        def monitor_start_rst():
            print("\t\tI2CClient({:s}): start_rst".format(path + '.' + name), start_rst)
            while 1:
                yield start_rst
                print("\t\tI2CClient({:s}): start_rst".format(path + '.' + name), start_rst)

        @instance
        def monitor_stop_detect():
            print("\t\tI2CClient({:s}): stop_detect".format(path + '.' + name), stop_detect)
            while 1:
                yield stop_detect
                print("\t\tI2CClient({:s}): stop_detect".format(path + '.' + name), stop_detect)

        @instance
        def monitor_stop_resetter():
            print("\t\tI2CClient({:s}): stop_resetter".format(path + '.' + name), stop_resetter)
            while 1:
                yield stop_resetter
                print("\t\tI2CClient({:s}): stop_resetter".format(path + '.' + name), stop_resetter)

        @instance
        def monitor_stop_rst():
            print("\t\tI2CClient({:s}): stop_rst".format(path + '.' + name), stop_rst)
            while 1:
                yield stop_rst
                print("\t\tI2CClient({:s}): stop_rst".format(path + '.' + name), stop_rst)

        @instance
        def monitor_lsb_bit():
            print("\t\tI2CClient({:s}): lsb_bit".format(path + '.' + name), lsb_bit)
            while 1:
                yield lsb_bit
                print("\t\tI2CClient({:s}): lsb_bit".format(path + '.' + name), lsb_bit)

        @instance
        def monitor_ack_bit():
            print("\t\tI2CClient({:s}): ack_bit".format(path + '.' + name), ack_bit)
            while 1:
                yield ack_bit
                print("\t\tI2CClient({:s}): ack_bit".format(path + '.' + name), ack_bit)

        @instance
        def monitor_read_write_bit():
            print("\t\tI2CClient({:s}): read_write_bit".format(path + '.' + name), read_write_bit)
            while 1:
                yield read_write_bit
                print("\t\tI2CClient({:s}): read_write_bit".format(path + '.' + name), read_write_bit)

        @instance
        def monitor_master_ack():
            print("\t\tI2CClient({:s}): master_ack".format(path + '.' + name), master_ack)
            while 1:
                yield master_ack
                print("\t\tI2CClient({:s}): master_ack".format(path + '.' + name), master_ack)

        @instance
        def monitor_write_strobe():
            print("\t\tI2CClient({:s}): write_strobe".format(path + '.' + name), write_strobe)
            while 1:
                yield write_strobe
                print("\t\tI2CClient({:s}): write_strobe".format(path + '.' + name), write_strobe)

        @instance
        def monitor_output_control():
            print("\t\tI2CClient({:s}): output_control".format(path + '.' + name), output_control)
            while 1:
                yield output_control
                print("\t\tI2CClient({:s}): output_control".format(path + '.' + name), output_control)

        @instance
        def monitor_sda_i():
            print("\t\tI2CClient({:s}): sda_i".format(path + '.' + name), sda_i)
            while 1:
                yield sda_i
                print("\t\tI2CClient({:s}): sda_i".format(path + '.' + name), sda_i)

        @instance
        def monitor_sda_o():
            print("\t\tI2CClient({:s}): sda_o".format(path + '.' + name), sda_o)
            while 1:
                yield sda_o
                print("\t\tI2CClient({:s}): sda_o".format(path + '.' + name), sda_o)

        @instance
        def monitor_sda_t():
            print("\t\tI2CClient({:s}): sda_t".format(path + '.' + name), sda_t)
            while 1:
                yield sda_t
                print("\t\tI2CClient({:s}): sda_t".format(path + '.' + name), sda_t)

        @instance
        def monitor_scl_i():
            print("\t\tI2CClient({:s}): scl_i".format(path + '.' + name), scl_i)
            while 1:
                yield scl_i
                print("\t\tI2CClient({:s}): scl_i".format(path + '.' + name), scl_i)

        @instance
        def monitor_output_shift():
            print("\t\tI2CClient({:s}): output_shift".format(path + '.' + name), hex(output_shift))
            while 1:
                yield output_shift
                print("\t\tI2CClient({:s}): output_shift".format(path + '.' + name), hex(output_shift))

        @instance
        def monitor_input_shift():
            print("\t\tI2CClient({:s}): input_shift".format(path + '.' + name), hex(input_shift))
            while 1:
                yield input_shift
                print("\t\tI2CClient({:s}): input_shift".format(path + '.' + name), hex(input_shift))

        @instance
        def monitor_state():
            s = ["STATE_IDLE", "STATE_DEV_ADDR", "STATE_READ", "STATE_IDX_PTR", "STATE_WRITE"]
            print("\t\tI2CClient({:s}): state".format(path + '.' + name), s[state])
            while 1:
                yield state
                print("\t\tI2CClient({:s}): state".format(path + '.' + name), s[state])

        @instance
        def monitor_read_address():
            print("\t\tI2CClient({:s}): read_address".format(path + '.' + name), hex(read_address))
            while 1:
                yield read_address
                print("\t\tI2CClient({:s}): read_address".format(path + '.' + name), hex(read_address))

        @instance
        def monitor_write_address():
            print("\t\tI2CClient({:s}): write_address".format(path + '.' + name), hex(write_address))
            while 1:
                yield write_address
                print("\t\tI2CClient({:s}): write_address".format(path + '.' + name), hex(write_address))

        @instance
        def monitor_update():
            print("\t\tI2CClient({:s}): update".format(path + '.' + name), update)
            while 1:
                yield update
                print("\t\tI2CClient({:s}): update".format(path + '.' + name), update)

        @instance
        def monitor_capture():
            print("\t\tI2CClient({:s}): capture".format(path + '.' + name), capture)
            while 1:
                yield capture
                print("\t\tI2CClient({:s}): capture".format(path + '.' + name), capture)

        @instance
        def monitor_reader_bit():
            print("\t\tI2CClient({:s}): reader_bit".format(path + '.' + name), reader_bit)
            while 1:
                yield reader_bit
                print("\t\tI2CClient({:s}): reader_bit".format(path + '.' + name), reader_bit)

        @instance
        def monitor_bit_counter():
            print("\t\tI2CClient({:s}): bit_counter".format(path + '.' + name), bit_counter)
            while 1:
                yield bit_counter
                print("\t\tI2CClient({:s}): bit_counter".format(path + '.' + name), bit_counter)

        return start_detector0, start_detector1, start_detector2, stop_detector0, stop_detector1, stop_detector2, \
            state_counter0, state_counter1, shift_register0, shift_register1, master_ack0, state_mach0, \
            state_mach1, reg_trans0, reg_trans1, reg_trans2, output0, output1, \
            monitor_start_detect, monitor_start_resetter, monitor_start_rst, monitor_stop_detect, \
            monitor_stop_resetter, monitor_stop_rst, monitor_lsb_bit, monitor_ack_bit, \
            monitor_read_write_bit, monitor_master_ack, monitor_write_strobe, monitor_output_control, \
            monitor_sda_i, monitor_scl_i, monitor_output_shift, monitor_input_shift, monitor_state, \
            monitor_sda_o, monitor_sda_t, monitor_bit_counter, monitor_capture, \
            monitor_read_address, monitor_update, monitor_write_address, monitor_reader_bit


I2C_DEBUG = True

# def i2c_setDEBUG():
#     I2C_DEBUG = True


def i2c_setSCL(SCL, val):
    """

    :param SCL:
    :return:
    """
    @always(SCL)
    def logic():
        # Do nothing here
        pass
    SCL.next = val
    return logic


i2c_setSCL.vhdl_code =\
"""
$SCL <= $val;
"""
i2c_setSCL.verilog_code =\
"""
assign $SCL = $val;
"""


def i2c_setSDA(SDA, val):
    """

    :param SDA:
    :return:
    """
    @always(SDA)
    def logic():
        # Do nothing here
        pass
    SDA.next = val
    return logic


i2c_setSCL.vhdl_code =\
"""
$SDA <= $val;
"""
i2c_setSCL.verilog_code =\
"""
assign $SDA = $val;
"""


def i2c_start(SCL, SDA):
    """

    :param SCL:
    :param SDA:
    :return:
    """
    @always(SCL)
    def logic():
        # Do nothing here
        pass

    if I2C_DEBUG:
        print("[i2c_start C:1 D:1 D:0 C:0]")
    SCL.next = bool(1)
    SDA.next = None
    yield delay(10)
    SDA.next = bool(0)
    yield delay(10)
    SCL.next = bool(0)
    yield delay(10)
    return logic


i2c_start.vhdl_code = \
    """
    i2c_setSCL($SCL, '1');
    i2c_setSDA($SDA, 'Z');
    wait for (20 / 2) * 1 ns;
    i2c_setSDA($SDA, '0');
    wait for (20 / 2) * 1 ns;
    i2c_setSCL($SCL, '0');
    wait for (20 / 2) * 1 ns;
    """
i2c_start.verilog_code = \
    """
    i2c_setSCL($SCL, (1 != 0));
    i2c_setSDA($SDA, 1'bz);
    # 10;
    i2c_setSDA($SDA, 1'b0);
    # 10;
    i2c_setSCL($SCL, (0 != 0));
    # 10;
    """


def i2c_stop(SCL, SDA):
    """

    :param SCL:
    :param SDA:
    :return:
    """
    @always(SCL)
    def logic():
        # Do nothing here
        pass
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
    return logic


i2c_stop.vhdl_code = \
    """
    i2c_setSCL($SCL, '0');
    wait for (20 / 2) * 1 ns;
    i2c_setSDA($SDA, '0');
    wait for (20 / 2) * 1 ns;
    i2c_setSCL($SCL, '1');
    wait for (20 / 2) * 1 ns;
    i2c_setSDA($SDA, 'Z');
    wait for (20 / 2) * 1 ns;
    """
i2c_stop.verilog_code = \
    """
    i2c_setSCL($SCL, (0 !0 0));
    # 10;
    i2c_setSDA($SDA, 1'b0);
    # 10;
    i2c_setSCL($SCL, (1 != 0));
    # 10;
    i2c_setSDA($SDA, 1'bz);
    # 10;
    """


def i2c_slave_ack(ack, SCL, SDA):
    """

    :param ack:
    :param SCL:
    :param SDA:
    :return:
    """
    @always(SCL)
    def logic():
        # Do nothing here
        pass
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
    return logic


i2c_slave_ack.vhdl_code = \
    """
    $SCL <= '1';
    wait for (20 / 2) * 1 ns;
    if ($SDA = '0') then
        $ack <= '0';
    else
        $ack <= '1';
    end if;
    wait for (20 / 2) * 1 ns;
    $SCL <= '0';
    wait for (20 / 2) * 1 ns;
    if ($ack = '1') then
        assert False report "i2c_slave_ack: ACK FAILED!" severity Failure;
    end if;
    """
i2c_slave_ack.verilog_code = \
    """
    assign $SCL = (1 != 0);
    # 10;
    if ($SDA == 1'b0) begin
        assign $ack = (0 != 0);
    end
    else begin
        assign $ack = (1 != 0);
    end
    # 10;
    assign $SCL = (0 != 0);
    # 10;
    if ($ack == (1 != 0)) begin
        $display("*** AssertionError *** i2c_slave_ack: ACK FAILED!");
    end
    """


def i2c_init(SCL, SDA):
    """

    :param SCL:
    :param SDA:
    :return:
    """
    # @always(SCL)
    # def logic():
    #     # Do nothing here
    #     pass
    if I2C_DEBUG:
        print("[i2c_init C:1 D:1]")
    SCL.next = bool(1)
    SDA.next = None
    yield delay(10)
    # return logic


i2c_init.vhdl_code = \
    """
    i2c_setSCL($SCL, '1');
    i2c_setSDA($SDA, 'Z');
    wait for (20 / 2) * 1 ns;
    """
i2c_init.verilog_code = \
    """
    i2c_setSCL($SCL, (1 != 0));
    i2c_setSDA($SDA, 1'bz);
    # 10;
    """


def i2c_writebit(bit, SCL, SDA):
    """

    :param bit:
    :param SCL:
    :param SDA:
    :return:
    """
    @always(SCL)
    def logic():
        # Do nothing here
        pass
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
    return logic


i2c_writebit.vhdl_code = \
    """
    if ($bit) then
        $SDA <= 'Z';
    else
        $SDA <= '0';
    end if;
    wait for (20 / 2) * 1 ns;
    $SCL <= '1';
    wait for (20 / 2) * 1 ns;
    $SCL <= '0';
    $SDA <= 'Z';
    wait for (20 / 2) * 1 ns;
    """
i2c_writebit.verilog_code = \
    """
    if ($bit) begin
        assign $SDA = 1'bz;
    end
    else begin
        assign $SDA = 1'b0;
    end
    # 10;
    assign $SCL = (1 != 0);
    # 10;
    assign $SCL = (0 != 0);
    assign $SDA = 1'bz;
    # 10;
    """


def i2c_readbit(bit, SCL, SDA):
    """

    :param bit:
    :param SCL:
    :param SDA:
    :return:
    """
    @always(SCL)
    def logic():
        # Do nothing here
        pass
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
    return logic


i2c_readbit.vhdl_code = \
    """
    $SCL <= '1';
    wait for (20 / 2) * 1 ns;
    if ($SDA = '0') then
        $bit <= '0';
    else
        $bit <= '1';
    end if;
    $SCL <= '0';
    wait for (20 / 2) * 1 ns;
    """
i2c_readbit.verilog_code = \
    """
    assign $SCL = (1 != 0);
    # 10;
    if ($SDA = 1'b0) begin
        assign $bit = (0 != 0);
    end
    else begin
        assign $bit = (1 != 0);
    end
    assign $SCL = (0 != 0);
    # 10;
    """


def i2c_reset_bus(SCL, SDA):
    """

    :param SCL:
    :param SDA:
    :return:
    """
    @always(SCL)
    def logic():
        # Do nothing here
        pass
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
    return logic


i2c_reset_bus.vhdl_code = \
    """
    i2c_init($SCL, $SDA);
    if (($SCL = (1 != 0) and ($SDA = 1'bz)) then
         assert False report "BUS has already been released!" severity Debug;
    else
        i2c_start($SCL, $SDA);
        for i in 0 to 9-1 loop
            $SCL <= '0';
            wait for (20 / 2) * 1 ns;
            $SCL <= '1';
            wait
            $SCL <= '0';
            wait for (20 / 2) * 1 ns;
            if ($SDA = '0') then
                assert False report "SDA is still stuck at LOW!" severity Failure;
            end if;
            i2c_start($SCL, $SDA);
            i2c_stop($SCL, $SDA);
        end loop;
    end if;
    """


def i2c_master_ack(ack, SCL, SDA):
    """

    :param ack:
    :param SCL:
    :param SDA:
    :return:
    """
    @always(SCL)
    def logic():
        # Do nothing here
        pass
    yield i2c_writebit(ack, SCL, SDA)
    return logic


i2c_master_ack.vhdl_code = \
    """
    i2c_writebit($ack, $SCL, $SDA);
    """


def i2c_write_data(val, SCL, SDA):
    """

    :param val:
    :param SCL:
    :param SDA:
    :return:
    """
    @always(SCL)
    def logic():
        # Do nothing here
        pass
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
    return logic


i2c_write_data.vhdl_code = \
    """
    signal data: unsigned(7 downto 0) := 8X"00";
    signal ack: std_logic := '0';data <= to_unsigned($val, 8);
    for i in 0 to 8-1 loop
        i2c_writebit(data(7 - i), $SCL, $SDA);
    end loop;
    i2c_slave_ack(ack, $SCL, $SDA);
    if (ack = '1') then
        assert False report "SLAVE failed to ACK!" severity Failure;
    end if;
    """


def i2c_read_data(val, ack, SCL, SDA):
    """

    :param val:
    :param ack:
    :param SCL:
    :param SDA:
    :return:
    """
    @always(SCL)
    def logic():
        # Do nothing here
        pass
    if I2C_DEBUG:
        print("[i2c_read_data")
    bit = Signal(bool(0))
    for i in range(8):
        yield i2c_readbit(bit, SCL, SDA)
        val.next[7 - i] = bit
    yield i2c_master_ack(ack, SCL, SDA)
    if I2C_DEBUG:
        print("End i2c_read_data]")
    return logic


i2c_read_data.vhdl_code = \
    """
    signal bit: std_logic := '0';
    for i in 0 to 8-1 loop
        i2c_readbit(bit, $SCL, $SDA);
        $val(7 - i) <= bit
    end loop;
    i2c_master_ack(ack, $SCL, $SDA);
    """


def i2c_read_reg(DevAddress, RegAddress, val, SCL, SDA):
    """

    :param DevAddress:
    :param RegAddress:
    :param val:
    :param SCL:
    :param SDA:
    :return:
    """
    @always(SCL)
    def logic():
        # Do nothing here
        pass
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
    return logic


i2c_read_reg.vhdl_code = \
    """
    signal ack : std_logic := '1';
    i2c_start($SCL, $SDA);
    i2c_write_data(($DevAddress << 1) & 0xFE, $SCL, $SDA);
    i2c_write_data($RegAddress, $SCL, $SDA);
    i2c_start($SCL, $SDA);
    i2c_write_data(($DevAddress << 1) | 1, $SCL, $SDA);
    i2c_read_data($val, ack, $SCL, $SDA);
    i2c_stop($SCL, $SDA);
    """


def i2c_write_reg(DevAddress, RegAddress, val, SCL, SDA):
    """

    :param DevAddress:
    :param RegAddress:
    :param val:
    :param SCL:
    :param SDA:
    :return:
    """
    @always(SCL)
    def logic():
        # Do nothing here
        pass
    if I2C_DEBUG:
        print("[i2c_write_reg(", hex((DevAddress << 1) & 0xFE), ", ", hex(RegAddress), ", ", bin(val), "}")
    yield i2c_start(SCL, SDA)
    yield i2c_write_data((DevAddress << 1) & 0xFE, SCL, SDA)
    yield i2c_write_data(RegAddress, SCL, SDA)
    yield i2c_write_data(val, SCL, SDA)
    yield i2c_stop(SCL, SDA)
    if I2C_DEBUG:
        print("End i2c_write_reg")
    return logic


i2c_write_reg.vhdl_code = \
    """
    i2c_start($SCL, $SDA);
    i2c_write_data(($DevAddress << 1) & 0xFE, $SCL, $SDA);
    i2c_write_data($RegAddress, $SCL, $SDA);
    i2c_write_data($val, $SCL, $SDA);
    i2c_stop($SCL, $SDA);
    """


def i2c_write_n_read_reg(DevAddress, RegAddress, Data, val, SCL, SDA):
    """

    :param DevAddress:
    :param RegAddress:
    :param Data:
    :param val:
    :param SCL:
    :param SDA:
    :return:
    """
    @always(SCL)
    def logic():
        # Do nothing here
        pass
    if I2C_DEBUG:
        print("[i2c_write_n_read_reg")
    yield i2c_write_reg(DevAddress, RegAddress, Data, SCL, SDA)
    yield i2c_read_reg(DevAddress, RegAddress, val, SCL, SDA)
    if I2C_DEBUG:
        print("End i2c_write_n_read_reg]")
    return logic


i2c_write_n_read_reg.vhdl_code = \
    """
    i2c_write_reg($DevAddress, $RegAddress, $Data, $SCL, $SDA);
    i2c_read_reg($DevAddress, $RegAddress, $val, $SCL, $SDA);
    """


@block
def I2CClient_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    N = 5
    reset_n = ResetSignal(1, 0, True)
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
    device_address = Signal(intbv(0x55)[7::0])
    contention = Signal(bool(0))
    # write_registers = [Signal(intbv(0)[8:]) for _ in range(N)]
    # write_addresses = [i for i in range(N)]
    # read_addresses = [i for i in range(N)]
    update = Signal(bool(0))
    write_address = Signal(intbv(0)[8:])
    ram_address = Signal(intbv(0)[8:])
    ram_read_address = Signal(intbv(0)[8:])
    write_data = Signal(intbv(0)[8:])
    ram_dout = Signal(intbv(0)[8:])
    ram_we = Signal(bool(0))
    ram_clk = Signal(bool(0))
    ram_inst = ram(ram_dout, write_data, ram_address, ram_we, ram_clk, depth=N)
    # read_registers = [Signal(intbv(i)[8:]) for i in range(N)]
    capture = Signal(bool(0))
    read_address = Signal(intbv(0)[8:])
    read_data = Signal(intbv(0)[8:])
    # read_registers = (i for i in range(N))
    read_registers = (0, 1, 2, 3, 4)
    rom_inst = rom(read_data, read_address, read_registers)
    ack = Signal(bool(0))
    val = Signal(intbv(0)[8:])
    bit = Signal(bool(0))
    # da_data = intbv(0)[8:]
    # ra_data = intbv(0)[8:]
    # da2_data = intbv(0)[8:]
    # ra2_data = intbv(0)[8:]
    # da3_data = intbv(0)[8:]
    # ra3_data = intbv(0)[8:]
    clk = Signal(bool(0))
    local_update = Signal(bool(0))
    local_update_rst = Signal(bool(0))
    local_update_resetter = Signal(bool(0))

    # i2cclient_inst = I2CClient('TOP', 'I2CC0', reset_n, scl_t, scl_o, scl_i, sda_t, sda_o, sda_i,
    i2cclient_inst = I2CClient('TOP', 'I2CC0', reset_n, scl_i, sda_t, sda_o, sda_i,
                               device_address, write_address, write_data, update,
                               read_address, read_data, capture,
                               monitor=monitor)

    @always_comb
    def update_detector4():
        local_update_rst.next = not reset_n or local_update_resetter

    @always(clk.negedge, local_update_rst.posedge)
    def update_detector5():
        if local_update_rst:
            local_update.next = bool(0)
        else:
            local_update.next = update

    @always_seq(clk.posedge, reset=reset_n)
    def update_detector6():
        local_update_resetter.next = local_update

    @always(clk.posedge)
    def client_write():
        # write_registers[write_addresses[write_address]].next = write_data
        if local_update == bool(1):
            ram_address.next = write_address
            ram_we.next = bool(1)
            ram_clk.next = bool(1)
        else:
            ram_we.next = bool(0)
            ram_clk.next = bool(0)
            ram_address.next = ram_read_address

    # @instance
    # def stimulus():
    #     """
    #     Perform instruction decoding for various instructions
    #     :return:
    #     """
    #     # i2c_setDEBUG()
    #     # Reset the I2CClient
    #     reset_n.next = bool(0)
    #     scldriver.next = bool(1)
    #     yield delay(10)
    #     scldriver.next = bool(0)
    #     yield delay(10)
    #     reset_n.next = bool(1)
    #     scldriver.next = bool(1)
    #     yield delay(10)
    #     scldriver.next = bool(0)
    #     yield delay(10)
    #     yield i2c_init(scldriver, sdadriver)
    #     for i in range(N):
    #         yield i2c_write_reg(device_address, i, i, scldriver, sdadriver)
    #     for i in range(N):
    #         print("write_registers[", i, "] == ", i)
    #         assert(write_registers[i] == i)
    #     val = Signal(intbv(0)[8:])
    #     for i in range(N):
    #         yield i2c_read_reg(device_address, i, val, scldriver, sdadriver)
    #         print("val == ", i, " => ", val, " == ", i)
    #         assert(val == i)
    #
    #     raise StopSimulation()

    @instance
    def clkgen():
        while True:
            clk.next = not clk
            yield delay(period)

    @instance
    def stimulus():
        """
        Perform instruction decoding for various instructions
        Unroll call tree so toVHDL and toVerilog are able to generate test bench
        :return:
        """
        da_data = intbv(0)[8:]
        ra_data = intbv(0)[8:]
        da2_data = intbv(0)[8:]
        ra2_data = intbv(0)[8:]
        da3_data = intbv(0)[8:]
        ra3_data = intbv(0)[8:]
        # i2c_setDEBUG()
        # Reset the I2CClient
        reset_n.next = bool(0)
        scl_i.next = bool(1)
        yield delay(10)
        scl_i.next = bool(0)
        yield delay(10)
        reset_n.next = bool(1)
        scl_i.next = bool(1)
        yield delay(10)
        scl_i.next = bool(0)
        yield delay(10)

        # yield i2c_init(scldriver, sdadriver)
        if I2C_DEBUG:
            print("[i2c_init C:1 D:1]")
        scl_i.next = bool(1)
        sda_i.next = bool(1)
        yield delay(10)

        for i in range(N):
            # (Begin) yield i2c_write_reg(device_address, i, i, scldriver, sdadriver)
            if I2C_DEBUG:
                print("[i2c_write_reg(", hex((device_address << 1) & 0xFE), ", ", hex(i), ", ", bin(i), ")")
            # (Begin) yield i2c_start(SCL, SDA)
            if I2C_DEBUG:
                print("[i2c_start C:1 D:1 D:0 C:0]")
            scl_i.next = bool(1)
            sda_i.next = bool(1)
            yield delay(10)
            sda_i.next = bool(0)
            yield delay(10)
            scl_i.next = bool(0)
            yield delay(10)
            # (End) yield i2c_start(SCL, SDA)
            # (Begin) yield i2c_write_data((DevAddress << 1) & 0xFE, SCL, SDA)
            if I2C_DEBUG:
                print("[i2c_write_data")
            da_data = intbv((device_address << 1) & 0xFE)[8:]
            for j in range(8):
                # (Begin) yield i2c_writebit(data[7 - j], SCL, SDA)
                if I2C_DEBUG:
                    print("[i2c_writebit D:", int(da_data[7 - j]), " C:1 C:0 D:1]")
                if da_data[7 - j]:
                    sda_i.next = bool(1)
                else:
                    sda_i.next = bool(0)
                yield delay(10)
                scl_i.next = bool(1)
                yield delay(10)
                scl_i.next = bool(0)
                # yield delay(10)
                sda_i.next = bool(1)
                yield delay(10)
                # (End) yield i2c_writebit(data[7 - j], SCL, SDA)
            # (Begin) yield i2c_slave_ack(ack, SCL, SDA)
            scl_i.next = bool(1)
            yield delay(10)
            # if sdadriver._sig.val == bool(0):
            if sda_o == bool(0) and sda_t == bool(1):
                ack.next = bool(0)
            else:
                ack.next = bool(1)
            yield delay(10)
            scl_i.next = bool(0)
            yield delay(10)
            # if ack.next == bool(1):
            if ack == bool(1):
                print("i2c_slave_ack: ACK FAILED!")
            if I2C_DEBUG:
                print("[i2c_slave_ack C:1 D:(", int(ack), ") C:0]")
            # (End) yield i2c_slave_ack(ack, SCL, SDA)

            if ack == bool(1):
                print("SLAVE failed to ACK!")
            if I2C_DEBUG:
                print("End i2c_write_data]")
            # (End) yield i2c_write_data((DevAddress << 1) & 0xFE, SCL, SDA)
            # (Begin) yield i2c_write_data(RegAddress, SCL, SDA)
            if I2C_DEBUG:
                print("[i2c_write_data")
            ra_data = intbv(i)[8:]
            for j in range(8):
                # (Begin) yield i2c_writebit(data[7 - j], SCL, SDA)
                if I2C_DEBUG:
                    print("[i2c_writebit D:", int(ra_data[7 - j]), " C:1 C:0 D:1]")
                if ra_data[7 - j]:
                    sda_i.next = bool(1)
                else:
                    sda_i.next = bool(0)
                yield delay(10)
                scl_i.next = bool(1)
                yield delay(10)
                scl_i.next = bool(0)
                # yield delay(10)
                sda_i.next = bool(1)
                yield delay(10)
                # (End) yield i2c_writebit(data[7 - j], SCL, SDA)
            # (Begin) yield i2c_slave_ack(ack, SCL, SDA)
            scl_i.next = bool(1)
            yield delay(10)
            # if sdadriver._sig.val == bool(0):
            if sda_o == bool(0) and sda_t == bool(1):
                ack.next = bool(0)
            else:
                ack.next = bool(1)
            yield delay(10)
            scl_i.next = bool(0)
            yield delay(10)
            # if ack.next == bool(1):
            if ack == bool(1):
                print("i2c_slave_ack: ACK FAILED!")
            if I2C_DEBUG:
                print("[i2c_slave_ack C:1 D:(", int(ack), ") C:0]")
            # (End) yield i2c_slave_ack(ack, SCL, SDA)

            if ack == bool(1):
                print("SLAVE failed to ACK!")
            if I2C_DEBUG:
                print("End i2c_write_data]")
            # (End) yield i2c_write_data(RegAddress, SCL, SDA)

            # (Begin) yield i2c_write_data(val, SCL, SDA)
            if I2C_DEBUG:
                print("[i2c_write_data")
            val_data = intbv(i)[8:]
            for j in range(8):
                # (Begin) yield i2c_writebit(data[7 - j], SCL, SDA)
                if I2C_DEBUG:
                    print("[i2c_writebit D:", int(val_data[7 - j]), " C:1 C:0 D:1]")
                if val_data[7 - j]:
                    sda_i.next = bool(1)
                else:
                    sda_i.next = bool(0)
                yield delay(10)
                scl_i.next = bool(1)
                yield delay(10)
                scl_i.next = bool(0)
                # yield delay(10)
                sda_i.next = bool(1)
                yield delay(10)
                # (End) yield i2c_writebit(data[7 - j], SCL, SDA)
            # (Begin) yield i2c_slave_ack(ack, SCL, SDA)
            scl_i.next = bool(1)
            yield delay(10)
            # if sdadriver._sig.val == bool(0):
            if sda_o == bool(0) and sda_t == bool(1):
                ack.next = bool(0)
            else:
                ack.next = bool(1)
            yield delay(10)
            scl_i.next = bool(0)
            yield delay(10)
            # if ack.next == bool(1):
            if ack == bool(1):
                print("i2c_slave_ack: ACK FAILED!")
            if I2C_DEBUG:
                print("[i2c_slave_ack C:1 D:(", int(ack), ") C:0]")
            # (End) yield i2c_slave_ack(ack, SCL, SDA)

            if ack == bool(1):
                print("SLAVE failed to ACK!")
            if I2C_DEBUG:
                print("End i2c_write_data]")
            # (End) yield i2c_write_data(val, SCL, SDA)
            # (Begin) yield i2c_stop(SCL, SDA)
            if I2C_DEBUG:
                print("[i2c_stop C:0 D:0 C:1 D:1]")
            scl_i.next = bool(0)
            yield delay(10)
            sda_i.next = bool(0)
            yield delay(10)
            scl_i.next = bool(1)
            yield delay(10)
            sda_i.next = bool(1)
            yield delay(10)
            # (End) yield i2c_stop(SCL, SDA)

            if I2C_DEBUG:
                print("End i2c_write_reg")
            # (End) yield i2c_write_reg(device_address, i, i, scldriver, sdadriver)

        # #############################################################################################################
        # Write Verify
        # #############################################################################################################
        yield delay(10)
        for i in range(N):
            ram_read_address.next = intbv(i)[8:]
            yield clk.posedge
            yield clk.negedge
            yield clk.posedge
            print("ram[", ram_read_address, "] == ", i)
            print("ram[ ", ram_read_address, " ] = ", ram_dout)
            assert(ram_dout == i)
        val.next = intbv(0)[8:]
        for i in range(N):
            # (Begin) yield i2c_read_reg(device_address, i, val, scldriver, sdadriver)
            if I2C_DEBUG:
                print("[i2c_read_reg")
            # (Begin) yield i2c_start(SCL, SDA)
            if I2C_DEBUG:
                print("[i2c_start C:1 D:1 D:0 C:0]")
            scl_i.next = bool(1)
            sda_i.next = bool(1)
            yield delay(10)
            sda_i.next = bool(0)
            yield delay(10)
            scl_i.next = bool(0)
            yield delay(10)
            # (End) yield i2c_start(SCL, SDA)
            # (Begin) yield i2c_write_data((DevAddress << 1) & 0xFE, SCL, SDA)
            if I2C_DEBUG:
                print("[i2c_write_data")
            da2_data = intbv((device_address << 1) & 0xFE)[8:]
            for j in range(8):
                # (Begin) yield i2c_writebit(data[7 - j], SCL, SDA)
                if I2C_DEBUG:
                    print("[i2c_writebit D:", int(da2_data[7 - j]), " C:1 C:0 D:1]")
                if da2_data[7 - j]:
                    sda_i.next = bool(1)
                else:
                    sda_i.next = bool(0)
                yield delay(10)
                scl_i.next = bool(1)
                yield delay(10)
                scl_i.next = bool(0)
                # yield delay(10)
                sda_i.next = bool(1)
                yield delay(10)
                # (End) yield i2c_writebit(data[7 - j], SCL, SDA)
            # (Begin) yield i2c_slave_ack(ack, SCL, SDA)
            scl_i.next = bool(1)
            yield delay(10)
            # if sdadriver._sig.val == bool(0):
            if sda_o == bool(0) and sda_t == bool(1):
                ack.next = bool(0)
            else:
                ack.next = bool(1)
            yield delay(10)
            scl_i.next = bool(0)
            yield delay(10)
            # if ack.next == bool(1):
            if ack == bool(1):
                print("i2c_slave_ack: ACK FAILED!")
            if I2C_DEBUG:
                print("[i2c_slave_ack C:1 D:(", int(ack), ") C:0]")
            # (End) yield i2c_slave_ack(ack, SCL, SDA)

            if ack == bool(1):
                print("SLAVE failed to ACK!")
            if I2C_DEBUG:
                print("End i2c_write_data]")
            # (End) yield i2c_write_data((DevAddress << 1) & 0xFE, SCL, SDA)
            # (Begin) yield i2c_write_data(RegAddress, SCL, SDA)
            if I2C_DEBUG:
                print("[i2c_write_data")
            ra2_data = intbv(i)[8:]
            for j in range(8):
                # (Begin) yield i2c_writebit(data[7 - j], SCL, SDA)
                if I2C_DEBUG:
                    print("[i2c_writebit D:", int(ra2_data[7 - j]), " C:1 C:0 D:1]")
                if ra2_data[7 - j]:
                    sda_i.next = bool(1)
                else:
                    sda_i.next = bool(0)
                yield delay(10)
                scl_i.next = bool(1)
                yield delay(10)
                scl_i.next = bool(0)
                # yield delay(10)
                sda_i.next = bool(1)
                yield delay(10)
                # (End) yield i2c_writebit(data[7 - j], SCL, SDA)
            # (Begin) yield i2c_slave_ack(ack, SCL, SDA)
            scl_i.next = bool(1)
            yield delay(10)
            # if sdadriver._sig.val == bool(0):
            if sda_o == bool(0) and sda_t == bool(1):
                ack.next = bool(0)
            else:
                ack.next = bool(1)
            yield delay(10)
            scl_i.next = bool(0)
            yield delay(10)
            # if ack.next == bool(1):
            if ack == bool(1):
                print("i2c_slave_ack: ACK FAILED!")
            if I2C_DEBUG:
                print("[i2c_slave_ack C:1 D:(", int(ack), ") C:0]")
            # (End) yield i2c_slave_ack(ack, SCL, SDA)

            if ack == bool(1):
                print("SLAVE failed to ACK!")
            if I2C_DEBUG:
                print("End i2c_write_data]")
            # (End) yield i2c_write_data(RegAddress, SCL, SDA)
            # (Begin) yield i2c_start(SCL, SDA)
            if I2C_DEBUG:
                print("[i2c_start C:1 D:1 D:0 C:0]")
            scl_i.next = bool(1)
            sda_i.next = bool(1)
            yield delay(10)
            sda_i.next = bool(0)
            yield delay(10)
            scl_i.next = bool(0)
            yield delay(10)
            # (End) yield i2c_start(SCL, SDA)
            # (Begin) yield i2c_write_data((DevAddress << 1) | 1, SCL, SDA)
            if I2C_DEBUG:
                print("[i2c_write_data")
            da3_data = intbv((device_address << 1) | 1)[8:]
            for j in range(8):
                # (Begin) yield i2c_writebit(data[7 - j], SCL, SDA)
                if I2C_DEBUG:
                    print("[i2c_writebit D:", int(da3_data[7 - j]), " C:1 C:0 D:1]")
                if da3_data[7 - j]:
                    sda_i.next = bool(1)
                else:
                    sda_i.next = bool(0)
                yield delay(10)
                scl_i.next = bool(1)
                yield delay(10)
                scl_i.next = bool(0)
                # yield delay(10)
                sda_i.next = bool(1)
                yield delay(10)
                # (End) yield i2c_writebit(data[7 - j], SCL, SDA)
            # (Begin) yield i2c_slave_ack(ack, SCL, SDA)
            scl_i.next = bool(1)
            yield delay(10)
            # if sdadriver._sig.val == bool(0):
            if sda_o == bool(0) and sda_t == bool(1):
                ack.next = bool(0)
            else:
                ack.next = bool(1)
            yield delay(10)
            scl_i.next = bool(0)
            yield delay(10)
            # if ack.next == bool(1):
            if ack == bool(1):
                print("i2c_slave_ack: ACK FAILED!")
            if I2C_DEBUG:
                print("[i2c_slave_ack C:1 D:(", int(ack.next), ") C:0]")
            # (End) yield i2c_slave_ack(ack, SCL, SDA)

            if ack == bool(1):
                print("SLAVE failed to ACK!")
            if I2C_DEBUG:
                print("End i2c_write_data]")
            # (End) yield i2c_write_data((DevAddress << 1) | 1, SCL, SDA)
            # (Begin) yield i2c_read_data(val, ack, SCL, SDA)
            if I2C_DEBUG:
                print("[i2c_read_data")
            for k in range(8):
                # (Begin) yield i2c_readbit(bit, SCL, SDA)
                scl_i.next = bool(1)
                yield delay(10)
                # if sdadriver._sig.val == bool(0):
                if sda_o == bool(0) and sda_t == bool(1):
                    bit.next = bool(0)
                else:
                    bit.next = bool(1)
                scl_i.next = bool(0)
                yield delay(10)
                if I2C_DEBUG:
                    print("[i2c_readbit C:1 D:(", int(bit), ") C:0]")
                # (End) yield i2c_readbit(bit, SCL, SDA)
                val.next[7 - k] = bit
            # (Begin) yield i2c_master_ack(ack, SCL, SDA)
            # (Begin) yield i2c_writebit(ack, SCL, SDA)
            if I2C_DEBUG:
                print("[i2c_writebit D:", int(ack), " C:1 C:0 D:1]")
            if ack:
                sda_i.next = bool(1)
            else:
                sda_i.next = bool(0)
            yield delay(10)
            scl_i.next = bool(1)
            yield delay(10)
            scl_i.next = bool(0)
            # yield delay(10)
            sda_i.next = bool(1)
            yield delay(10)
            # (End) yield i2c_writebit(ack, SCL, SDA)
            # (End) yield i2c_master_ack(ack, SCL, SDA)
            if I2C_DEBUG:
                print("End i2c_read_data]")
            # (End) yield i2c_read_data(val, ack, SCL, SDA)
            # (Begin) yield i2c_stop(SCL, SDA)
            if I2C_DEBUG:
                print("[i2c_stop C:0 D:0 C:1 D:1]")
            scl_i.next = bool(0)
            yield delay(10)
            sda_i.next = bool(0)
            yield delay(10)
            scl_i.next = bool(1)
            yield delay(10)
            sda_i.next = bool(1)
            yield delay(10)
            # (End) yield i2c_stop(SCL, SDA)
            if I2C_DEBUG:
                print("End i2c_read_reg]")
            # (End) yield i2c_read_reg(device_address, i, val, scldriver, sdadriver)
            # #########################################################################################################
            # Read Verify
            # #########################################################################################################
            print("val == ", i, " => ", val, " == ", i)
            assert(val == i)

        raise StopSimulation()

    # return i2cclient_inst, stimulus
    # return i2cclient_inst, stimulus, client, contention_monitor, client_write, client_read
    return i2cclient_inst, stimulus, client_write, ram_inst, rom_inst, clkgen, \
           update_detector4, update_detector5, update_detector6


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    N = 5
    reset_n = ResetSignal(1, 0, True)
    scl = TristateSignal(bool(0))
    sda = TristateSignal(bool(0))
    # scl_t = Signal(bool(0))
    # scl_o = Signal(bool(0))
    scl_i = Signal(bool(0))
    sda_t = Signal(bool(0))
    sda_o = Signal(bool(0))
    sda_i = Signal(bool(0))
    device_address = Signal(intbv(0x55)[7::0])
    update = Signal(bool(0))
    capture = Signal(bool(0))
    write_address = Signal(intbv(0)[8:])
    write_data = Signal(intbv(0)[8:])
    read_address = Signal(intbv(0)[8:])
    read_data = Signal(intbv(0)[8:])

    i2cclient_inst = I2CClient('TOP', 'I2CC0', reset_n, scl_i, sda_t, sda_o, sda_i,
                               device_address, write_address, write_data, update,
                               read_address, read_data, capture,
                               monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    i2cclient_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="I2CClient")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    i2cclient_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="I2CClient")
    tb = I2CClient_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="I2CClient_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="I2CClient_tb")


def main():
    tb = I2CClient_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
