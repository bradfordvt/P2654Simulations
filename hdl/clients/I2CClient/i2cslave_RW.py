'''
Created on Apr 1, 2016

@author: vantreur
'''

from myhdl import *


@block
def i2cslave_RW(scl_i, sda_i, sda_oen, reset_n, dataIn, dataOut, regAddr, writeEn, autoincrement=False):
    """
    :param scl_i: I2C Clock pin
    :param sda_i: I2C data input
    :param sda_oen: I2C data output enable of the Open Collector data bus
    :param reset_n: Active low reset to the slave
    :param dataIn: Signal(intbv(0)[8:]) data bus to be read by the I2C bus
    :param dataOut: Signal(intbv(0)[8:]) data bus to be written to by the I2C bus
    :param regAddr: Signal(modbv(0)[8:]) register address to be read or written to
    :param writeEn: Write enable signal triggering the writing to a register
    """
    # Start detector logic
    start_detect = Signal(bool(0))
    start_resetter = Signal(bool(1))
    start_reset_n = Signal(bool(1))
    
    @always_comb
    def start_detector0():
        start_reset_n.next = not reset_n or start_resetter
               
    @always(start_reset_n.posedge,sda_i.negedge)
    def start_detector1():
        if start_reset_n:
            # print "start_detector1: start_reset_n"
            start_detect.next = bool(0)
        else:
            # print "start_detector1: scl_i=",int(scl_i)
            start_detect.next = scl_i
            
    @always(scl_i.posedge,reset_n.negedge)
    def start_detector2():
        if not reset_n:
            start_resetter.next = bool(0)
        else:
            start_resetter.next =  start_detect
     
    # Stop detector logic
    stop_detect = Signal(bool(0))
    stop_resetter = Signal(bool(0))
    stop_reset_n = Signal(bool(0))
    
    @always_comb
    def stop_detector0():
        stop_reset_n.next = not reset_n or stop_resetter

    @always(stop_reset_n.posedge,sda_i.posedge)        
    def stop_detector1():
        if stop_reset_n:
            stop_detect.next = bool(0)
        else:
            stop_detect.next = scl_i
            
    @always(scl_i.posedge,reset_n.negedge)
    def stop_detector2():
        if not reset_n:
            stop_resetter.next = bool(0)
        else:
            stop_resetter.next = stop_detect
               
    # Modulo-9 Counter to preserve the cycle State
    bit_counter = Signal(modbv(0, min=0, max=9))
    
    reader_bit = Signal(bool(0))
    lsb_bit = Signal(bool(0))
    ack_bit = Signal(bool(0))
    
    @always_comb
    def state_counter0():
        # print "state_counter0: lsb_bit being set to ", int((bit_counter == 7) and (not start_detect))
        # print "state_counter0: ack_bit being set to ", int((bit_counter == 8) and (not start_detect))
        reader_bit.next = (bit_counter == 6) and (not start_detect)
        lsb_bit.next = (bit_counter == 7) and (not start_detect)
        ack_bit.next = (bit_counter == 8) and (not start_detect)
        
    @always(scl_i.negedge, reset_n.negedge)
    def state_counter1():
        if not reset_n:
            bit_counter.next = modbv(0, min=0, max=9)
        elif ack_bit or start_detect:
            # print "state_counter1: Resetting bit_counter to 0."
            bit_counter.next = modbv(0, min=0, max=9)
        else:
            # print "state_counter1: bit_counter being set to ", bit_counter + modbv(1, min=0, max=9)
            bit_counter.next = bit_counter + modbv(1, min=0, max=9)
            
    # Input shift register logic
    device_address = Signal(intbv(0x3C)[7:])
    address_detect = Signal(bool(0))
    read_write_bit = Signal(bool(0))
    
    @always_comb
    def shift_register0():
        address_detect.next = (dataOut[8:1] == device_address)
        read_write_bit.next = dataOut[0]
        # print "shift_register0: dataOut[0]=", int(dataOut[0])
        
    # @always(scl_i.posedge,reset_n.negedge)
    @always(scl_i.posedge)
    def shift_register1():
        if not ack_bit:
            # print("shift_register1: iput_shift=%x" % dataOut)
            dataOut.next = concat(dataOut[7:0], sda_i)
            
    # Master ACK detection logic
    master_ack = Signal(bool(0))
    
    @always(scl_i.posedge)
    def master_ack0():
        if ack_bit:
            master_ack.next = not sda_i
            
    # State Machine logic controlling the interface
    STATE_IDLE, STATE_DEV_ADDR, STATE_READ, STATE_IDX_PTR, STATE_WRITE = range(5)
    state = Signal(intbv(0, min=0, max=5))

    @always_comb
    def state_mach0():
        # print "state_mach0: Setting writeEn to ",bin((state == STATE_WRITE) and ack_bit)
        writeEn.next = (state == STATE_WRITE) and ack_bit
        
    @always(scl_i.negedge,reset_n.negedge)
    def state_mach1():
        if not reset_n:
            # print "state_mach1: not reset_n"
            # print "state_mach1: moving to STATE_IDLE"
            state.next = STATE_IDLE
        elif start_detect:
            # print "state_mach1: start_detect"
            # print "state_mach1: moving to STATE_DEV_ADDR"
            state.next = STATE_DEV_ADDR
        elif ack_bit:
            if state == STATE_IDLE:
                # print "state_mach1: moving to STATE_IDLE from STATE_IDLE"
                state.next = STATE_IDLE
            elif state == STATE_DEV_ADDR:
                if not address_detect:
                    # print "state_mach1: not address_detect"
                    # print "state_mach1: moving to STATE_IDLE from STATE_DEV_ADDR"
                    state.next = STATE_IDLE
                elif read_write_bit:
                    # print "state_mach1: read_write_bit"
                    # print "state_mach1: moving to STATE_READ from STATE_DEV_ADDR"
                    state.next = STATE_READ
                else:
                    # print "state_mach1: moving to STATE_IDX_PTR from STATE_DEV_ADDR"
                    state.next = STATE_IDX_PTR
            elif state == STATE_READ:
                if master_ack:
                    # print "state_mach1: master_ack"
                    # print "state_mach1: moving to STATE_READ from STATE_READ"
                    state.next = STATE_READ
                else:
                    # print "state_mach1: moving to STATE_IDLE from STATE_READ"
                    state.next = STATE_IDLE
            elif state == STATE_IDX_PTR:
                # print "state_mach1: moving to STATE_WRITE from STATE_IDX_PTR"
                state.next = STATE_WRITE
            elif state == STATE_WRITE:
                # print "state_mach1: moving to STATE_WRITE from STATE_WRITE"
                state.next = STATE_WRITE
                
    # Register transfer logic
    # Read of registers needs to be done with an dataIn register
    # that gets latched before the ACK BIT
    txData = Signal(intbv(0)[8:])

    @always(scl_i.negedge, reset_n.negedge)
    def reg_trans0():
        if not reset_n:
            regAddr.next = modbv(0)[8:]
        elif ack_bit:
            if state == STATE_IDX_PTR:
                regAddr.next = dataOut
            elif autoincrement:
                regAddr.next = regAddr + 1

    # Read of registers needs to be done with an dataIn register
    # that gets latched before the ACK BIT

    @always(scl_i.negedge)
    def reg_trans2():
        if lsb_bit:
            txData.next = dataIn
        else:
            txData.next = concat(txData[7:0], bool(0))

    # Output Driver logic
    output_control = Signal(bool(0))

    @always_comb
    def output0():
        if output_control:
            sda_oen.next = bool(1)
        else:
            sda_oen.next = bool(0)
            
    @always(scl_i.negedge,reset_n.negedge)
    def output1():
        if not reset_n:
            sda_oen.next = bool(1)
        elif start_detect:
            sda_oen.next = bool(1)
        elif lsb_bit:
            sda_oen.next = not (((state == STATE_DEV_ADDR) and address_detect) or
                                       (state == STATE_IDX_PTR) or
                                       (state == STATE_WRITE))
        elif ack_bit:
            # Deliver the first bit of the next slave-to-master transfer, if applicable.
            if (((state == STATE_READ) and master_ack) or
               ((state == STATE_DEV_ADDR) and address_detect and read_write_bit)):
                # print "output1: Deliver the first bit of the next slave-to-master transfer."
                sda_oen.next = txData[7]
            else:
                sda_oen.next = bool(1)
        elif state == STATE_READ:
            # print "output1: Writing bit in STATE_READ (", int(dataIn[7]), ")"
            sda_oen.next = txData[7]
        else:
            sda_oen.next = bool(1)
                    
    return start_detector0, start_detector1, start_detector2, stop_detector0, stop_detector1, stop_detector2, state_counter0, state_counter1, shift_register0, shift_register1, master_ack0, state_mach0, state_mach1, reg_trans0, reg_trans2, output1