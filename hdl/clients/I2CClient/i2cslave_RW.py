'''
Created on Apr 1, 2016

@author: vantreur
'''

from myhdl import *


@block
def i2cslave_RW(SCL, SDA, SDAS, RST, reg_00, reg_01, reg_02, reg_00_latch, reg_01_latch, reg_02_latch):
    '''
    SCL is a TristateSignal representing the I2C Clock pin
    SDA Since myHDL does not yet support Tri-state signal, this is the SDA from the master.
    SDAS Since myHDL does not yet support Tri-state signals, this is the return SDA signal.
    Both SCL and SDA could be driven by the master or slave during a transfer cycle.
    The Slave drives the SCL signal only if a clock stretch is required to indicate
    the slave needs more time to handle the request.  This implementation does not
    support clock stretching.
    RST is the active low master reset to the instrument
    reg_00 is assumed to be the write only register for the P1687.1 interface
    reg_01 is assumed to be the read only register for the P1687.1 interface 
    reg_02 is assumed to be the read only register for the P1687.1 interface for status
    reg_00_latch signal to notify that reg_00 has been updated (e.g., we)
    reg_01_latch signal to notify that reg_01 has been read from slave (e.g., re)
    reg_02_latch signal to notify that reg_02 has been read from slave (e.g., re)
    '''
    # Start detector logic
    start_detect = Signal(bool(0))
    start_resetter = Signal(bool(1))
    start_rst = Signal(bool(1))
    
    @always_comb
    def start_detector0():
        start_rst.next = not RST or start_resetter
               
    @always(start_rst.posedge,SDA.negedge)
    def start_detector1():
        if start_rst:
            # print "start_detector1: start_rst"
            start_detect.next = bool(0)
        else:
            # print "start_detector1: SCL=",int(SCL)
            start_detect.next = SCL
            
    @always(SCL.posedge,RST.negedge)
    def start_detector2():
        if not RST:
            start_resetter.next = bool(0)
        else:
            start_resetter.next =  start_detect
     
    # Stop detector logic
    stop_detect = Signal(bool(0))
    stop_resetter = Signal(bool(0))
    stop_rst = Signal(bool(0))
    
    @always_comb
    def stop_detector0():
        stop_rst.next = not RST or stop_resetter

    @always(stop_rst.posedge,SDA.posedge)        
    def stop_detector1():
        if stop_rst:
            stop_detect.next = bool(0)
        else:
            stop_detect.next = SCL
            
    @always(SCL.posedge,RST.negedge)
    def stop_detector2():
        if not RST:
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
        
    @always(SCL.negedge, RST.negedge)
    def state_counter1():
        if not RST:
            bit_counter.next = modbv(0, min=0, max=9)
        elif ack_bit or start_detect:
            # print "state_counter1: Resetting bit_counter to 0."
            bit_counter.next = modbv(0, min=0, max=9)
        else:
            # print "state_counter1: bit_counter being set to ", bit_counter + modbv(1, min=0, max=9)
            bit_counter.next = bit_counter + modbv(1, min=0, max=9)
            
    # Input shift register logic
    input_shift = Signal(intbv(0)[8:])
    device_address = Signal(intbv(0x3C)[7:])
    address_detect = Signal(bool(0))
    read_write_bit = Signal(bool(0))
    
    @always_comb
    def shift_register0():
        address_detect.next = (input_shift[8:1] == device_address)
        read_write_bit.next = input_shift[0]
        # print "shift_register0: input_shift[0]=", int(input_shift[0])
        
    # @always(SCL.posedge,RST.negedge)
    @always(SCL.posedge)
    def shift_register1():
        if not ack_bit:
            # print("shift_register1: iput_shift=%x" % input_shift)
            input_shift.next = concat(input_shift[7:0], SDA)
            
    # Master ACK detection logic
    master_ack = Signal(bool(0))
    
    @always(SCL.posedge)
    def master_ack0():
        if ack_bit:
            master_ack.next = not SDA
            
    # State Machine logic controlling the interface
    STATE_IDLE, STATE_DEV_ADDR, STATE_READ, STATE_IDX_PTR, STATE_WRITE = range(5)
    state = Signal(intbv(0, min=0, max=5))
    write_strobe = Signal(bool(0))
    
    @always_comb
    def state_mach0():
        # print "state_mach0: Setting write_strobe to ",bin((state == STATE_WRITE) and ack_bit)
        write_strobe.next = (state == STATE_WRITE) and ack_bit
        
    @always(SCL.negedge,RST.negedge)
    def state_mach1():
        if not RST:
            # print "state_mach1: not RST"
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
    index_pointer = Signal(intbv(0)[8:])
    
    @always(SCL.negedge, RST.negedge)
    def reg_trans0():
        if not RST:
            index_pointer.next = intbv(0)[8:]
        # elif stop_detect:
        #     index_pointer.next = intbv(0)[8:]
        elif ack_bit:
            if state == STATE_IDX_PTR:
                index_pointer.next = input_shift
            #else:
            #    index_pointer.next = index_pointer + 1
    # reg_00 is an example of a register at register address 0 to be written to  
    '''
    # define reg_00 as this in the top level        
    reg_00 = Signal(intbv(0)[8:])
    '''
    
    @always(SCL.negedge,RST.negedge)
    def reg_trans1():
        if not RST:
            reg_00.next = intbv(0)[8:]
        elif write_strobe and (index_pointer == 0):
            reg_00.next = input_shift
            reg_00_latch.next = bool(1)
            # print "i2cslave_RW.reg_trans1: Saving reg_00 as 0b: ",bin(input_shift)
        elif write_strobe and (index_pointer == 1):
            reg_01.next = input_shift
            reg_01_latch.next = bool(1)
        else:
            reg_00_latch.next = bool(0)
            reg_01_latch.next = bool(0)

    # Read of registers needs to be done with an output_shift register
    # that gets latched before the ACK BIT
    output_shift = Signal(intbv(0)[8:])
    '''
    # define reg_01 as this in the top level
    reg_01 = Signal(intbv(0)[8:])
    '''
    
    @always(SCL.negedge)
    def reg_trans2():
        if lsb_bit:
            if index_pointer == 0:
                output_shift.next = reg_00
            elif index_pointer == 1:
                output_shift.next = reg_01
            elif index_pointer == 2:
                output_shift.next = reg_02
        else:
            # print("reg_trans2: output_shift = 0x%x" % output_shift)
            output_shift.next = concat(output_shift[7:0], bool(0))

    # Output Driver logic
    output_control = Signal(bool(0))

    @always_comb
    def output0():
        if output_control:
            SDAS.next = bool(1)
        else:
            SDAS.next = bool(0)
            
    @always(SCL.negedge,RST.negedge)
    def output1():
        if not RST:
            SDAS.next = bool(1)
        elif start_detect:
            SDAS.next = bool(1)
        elif lsb_bit:
            SDAS.next = not (((state == STATE_DEV_ADDR) and address_detect) or
                                       (state == STATE_IDX_PTR) or
                                       (state == STATE_WRITE))
        elif ack_bit:
            # Deliver the first bit of the next slave-to-master transfer, if applicable.
            if (((state == STATE_READ) and master_ack) or
               ((state == STATE_DEV_ADDR) and address_detect and read_write_bit)):
                # print "output1: Deliver the first bit of the next slave-to-master transfer."
                SDAS.next = output_shift[7]
            else:
                SDAS.next = bool(1)
        elif state == STATE_READ:
            # print "output1: Writing bit in STATE_READ (", int(output_shift[7]), ")"
            SDAS.next = output_shift[7]
        else:
            SDAS.next = bool(1)
                    
    return start_detector0, start_detector1, start_detector2, stop_detector0, stop_detector1, stop_detector2, state_counter0, state_counter1, shift_register0, shift_register1, master_ack0, state_mach0, state_mach1, reg_trans0, reg_trans1, reg_trans2, output1