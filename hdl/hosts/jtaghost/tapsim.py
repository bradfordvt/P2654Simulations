"""
Copyright (c) 2020 Bradford G. Van Treuren
See the licence file in the top directory
"""
from myhdl import *
from hdl.hosts.jtaghost.bram import RAM, RAMInterface
from hdl.standards.s1149dot1.JTAGInterface import JTAGInterface


SI_EXIT2_DR, SI_EXIT1_DR, SI_SHIFT_DR, SI_PAUSE_DR, SI_SELECT_IR, SI_UPDATE_DR, SI_CAPTURE_DR, SI_SELECT_DR, \
    SI_EXIT2_IR, SI_EXIT1_IR, SI_SHIFT_IR, SI_PAUSE_IR, SI_RUN_TEST_IDLE, SI_UPDATE_IR, SI_CAPTURE_IR, \
    SI_TEST_LOGIC_RESET = range(16)

jtag_state_transitions = [
    [SI_UPDATE_DR, SI_SHIFT_DR],  # SI_EXIT2_DR
    [SI_UPDATE_DR, SI_PAUSE_DR],  # SI_EXIT1_DR
    [SI_EXIT1_DR, SI_SHIFT_DR],  # SI_SHIFT_DR
    [SI_EXIT2_DR, SI_PAUSE_DR],  # SI_PAUSE_DR
    [SI_TEST_LOGIC_RESET, SI_CAPTURE_IR],  # SI_SELECT_IR
    [SI_SELECT_DR, SI_RUN_TEST_IDLE],  # SI_UPDATE_DR
    [SI_EXIT1_DR, SI_SHIFT_DR],  # SI_CAPTURE_DR
    [SI_SELECT_IR, SI_CAPTURE_DR],  # SI_SELECT_DR
    [SI_UPDATE_IR, SI_SHIFT_IR],  # SI_EXIT2_IR
    [SI_UPDATE_IR, SI_PAUSE_IR],  # SI_EXIT1_IR
    [SI_EXIT1_IR, SI_SHIFT_IR],  # SI_SHIFT_IR
    [SI_EXIT2_IR, SI_PAUSE_IR],  # SI_PAUSE_IR
    [SI_SELECT_DR, SI_RUN_TEST_IDLE],  # SI_RUN_TEST_IDLE
    [SI_SELECT_DR, SI_RUN_TEST_IDLE],  # SI_UPDATE_IR
    [SI_EXIT1_IR, SI_SHIFT_IR],  # SI_CAPTURE_IR
    [SI_TEST_LOGIC_RESET, SI_RUN_TEST_IDLE]  # SI_TEST_LOGIC_RESET
]

#
# This table contains the TMS value to be used to take the NEXT STEP on
# the path to the desired state.  The array index is the current state,
# and the bit position is the desired endstate.  To find out which state
# is used as the intermediate state, look up the TMS value in the
# jtag_state_transitions[] table.
#

jtag_path_map = [
    0xFFF0, 0xFFF0, 0xFFFB, 0xFFF7, 0x8000, 0xEFDF, 0xFFBB, 0xEF10,
    0xF0FF, 0xF0FF, 0xFBFF, 0xF7FF, 0xEFFF, 0xCFFF, 0xBBFF, 0x8000
]

# Master states
IDLE, GOTO_STATE, GOTO_START, PRE_SHIFT, SHIFT, TAP_RESET, CLEAR_BUFFER, MDONE, MASTER_MAX = range(9)

# GOTO new state states
GOTO_IDLE, GOTO_NEXT1, GOTO_NEXT2, GOTO_NEXT3, GOTO_NEXT4, GOTO_NEXT5, GOTO_NEXT6, GOTO_NEXT7, GOTO_NEXT8, \
    GOTO_NEXT9, GOTO_NEXT10, GOTO_NEXT11, GOTO_NEXT12, GOTO_NEXT13, GOTO_NEXT14, GOTO_NEXT15, GOTO_NEXT16, \
    GOTO_NEXT17, GOTO_NEXT18, GOTO_NEXT19, GOTO_DONE, \
    GOTO_MAX = range(22)

# Shift states
SHIFT_IDLE, SHIFT_START, SHIFT_SCAN1, SHIFT_CYCLE1, SHIFT_DIVIDER1, SHIFT_CYCLE2, SHIFT_CYCLE3, SHIFT_DIVIDER2, \
    SHIFT_CYCLE4, SHIFT_CYCLE5, SHIFT_DIVIDER3, SHIFT_SCAN2, SHIFT_CYCLE6, SHIFT_CYCLE7, SHIFT_DIVIDER4, \
    SHIFT_CYCLE8, SHIFT_CYCLE9, SHIFT_CYCLE10, SHIFT_PAD1, SHIFT_PAD2, SHIFT_END, SHIFT_DONE, SHIFT_MAX = range(23)

# Reset states
RESET_IDLE, RESET_TMS1, RESET_TMS2, RESET_DONE, RESET_MAX = range(5)

# Commands
NONE, SCAN, RESET, STATE, COMMAND_MAX = range(5)


class TAPControllerInterface:
    def __init__(self, clk, reset_n, addr_width=10, data_width=8):
        self.clk = clk
        self.reset_n = reset_n
        # Control Part
        self.command = Signal(intbv(val=NONE, min=NONE, max=COMMAND_MAX))
        self.go_strobe = Signal(bool(0))
        self.busy = Signal(bool(0))
        self.clock_divider = Signal(intbv(0)[32:])
        # JTAG Part
        self.chain_length = Signal(intbv(0)[16:])
        self.tdo = Signal(bool(0))
        self.tdi = Signal(bool(0))
        self.jtag_interface = JTAGInterface()
        self.scan_state = Signal(intbv(SI_TEST_LOGIC_RESET)[4:])
        self.end_state = Signal(intbv(SI_TEST_LOGIC_RESET)[4:])
        self.cur_state = Signal(intbv(SI_TEST_LOGIC_RESET)[4:])
        # Ram Part
        self.addr = Signal(intbv(0)[addr_width:])
        self.wr = Signal(bool(0))
        self.din = Signal(intbv(0)[data_width:])
        self.dout = Signal(intbv(0)[data_width:])
        self.read_data = Signal(intbv(0)[data_width:])
        self.addr_width = addr_width
        self.data_width = data_width


class TAPSim:
    def __init__(self, parent, name, controller_interface, monitor=False):
        self.parent = parent
        self.name = name
        self.controller_interface = controller_interface
        self.monitor = monitor
        # self.clk = clk
        # self.reset = reset
        # self.tdi = tdi
        # self.tck = tck
        # self.tms = tms
        # self.trst = trst
        # self.tdo = tdo
        # self.command = command
        # self.status_register = sr
        # self.addr = addr
        # self.wr = wr
        # self.din = din
        # self.dout = dout
        # self.clock_divider = divider
        # self.chain_length = chain_length
        # self.scan_state = scan_state
        # self.end_state = end_state

    @block
    def rtl(self):
        master_state = Signal(intbv(IDLE))
        shift_state = Signal(intbv(SHIFT_IDLE, min=SHIFT_IDLE, max=SHIFT_MAX))
        shift_tck = Signal(bool(1))
        shift_tms = Signal(bool(1))
        shift_tdi = Signal(bool(1))
        bit_count = Signal(intbv(0)[32:])
        divider_cnt = Signal(intbv(0)[32:])
        shift_remainder = Signal(intbv(0)[32:])
        scan_tdo_bit = Signal(bool(0))
        scan_tms = Signal(bool(0))
        end_tms = Signal(bool(0))

        goto_state = Signal(intbv(GOTO_IDLE, min=GOTO_IDLE, max=GOTO_MAX))
        goto_tck = Signal(bool(1))
        goto_tms = Signal(bool(1))
        goto_count = Signal(intbv(0)[32:])
        exit_tms = Signal(bool(0))

        reset_state = Signal(intbv(RESET_IDLE, min=RESET_IDLE, max=RESET_MAX))
        reset_tck = Signal(bool(1))
        reset_tms = Signal(bool(1))
        reset_count = Signal(intbv(0, min=0, max=6))

        target_state = Signal(intbv(SI_TEST_LOGIC_RESET)[8:])
        trigger = Signal(bool(0))

        ram_interface = RAMInterface(addr_width=10, data_width=8)
        jtag_bram = RAM(ram_interface)
        bram_adr = Signal(intbv(0)[10:])

        @always_comb
        def ram_addr():
            ram_interface.Ard.next = bram_adr
            ram_interface.Awr.next = bram_adr
            ram_interface.clk.next = self.controller_interface.clk
            ram_interface.reset_n.next = self.controller_interface.reset_n

        @always_comb
        def ram_process():
            """
            BlockRAM Control
            """
            self.controller_interface.dout.next = ram_interface.Dout
            if shift_state == SHIFT_IDLE:
                bram_adr.next = self.controller_interface.addr
            else:
                bram_adr.next = bit_count[13:3]

        @always(self.controller_interface.go_strobe.posedge)
        def trigger_process1():
            trigger.next = True

        @always(self.controller_interface.busy.posedge)
        def trigger_process2():
            trigger.next = False

        @always(self.controller_interface.clk.posedge)
        def master_process():
            if master_state == IDLE:
                if self.controller_interface.command == SCAN and trigger:
                    self.controller_interface.busy.next = True
                    master_state.next = PRE_SHIFT
                elif self.controller_interface.command == RESET and trigger:
                    self.controller_interface.busy.next = True
                    master_state.next = TAP_RESET
                elif self.controller_interface.command == STATE and trigger:
                    self.controller_interface.busy.next = True
                    target_state.next = self.controller_interface.end_state
                    master_state.next = GOTO_STATE
            elif master_state == PRE_SHIFT:
                master_state.next = CLEAR_BUFFER
            elif master_state == CLEAR_BUFFER:
                target_state.next = self.controller_interface.scan_state
                master_state.next = GOTO_START
            elif master_state == GOTO_START:
                if goto_state == GOTO_DONE:
                    master_state.next = SHIFT
            elif master_state == SHIFT:
                if shift_state == SHIFT_DONE:
                    target_state.next = self.controller_interface.end_state
                    master_state.next = GOTO_STATE
            elif master_state == GOTO_STATE:
                if goto_state == GOTO_DONE:
                    master_state.next = MDONE
            elif master_state == TAP_RESET:
                if reset_state == RESET_DONE:
                    master_state.next = MDONE
            elif master_state == MDONE:
                self.controller_interface.busy.next = False
                if not self.controller_interface.go_strobe:
                    master_state.next = IDLE

        @always(self.controller_interface.clk.posedge)
        def goto_process():
            if goto_state == GOTO_IDLE:
                if master_state == GOTO_STATE or master_state == GOTO_START:
                    goto_state.next = GOTO_NEXT1
            elif goto_state == GOTO_NEXT1:
                if self.controller_interface.cur_state == target_state:
                    # We are already in the desired state.  If it is a
                    # stable state or shift state,
                    # loop here.  Otherwise do nothing (no clock cycles).
                    if target_state == SI_RUN_TEST_IDLE or \
                            target_state == SI_SHIFT_DR or \
                            target_state == SI_PAUSE_DR or \
                            target_state == SI_SHIFT_IR or \
                            target_state == SI_PAUSE_IR:
                        goto_state.next = GOTO_NEXT2
                    elif target_state == SI_TEST_LOGIC_RESET:
                        goto_state.next = GOTO_NEXT8
                else:
                    goto_count.next = 0
                    goto_state.next = GOTO_NEXT14
            elif goto_state == GOTO_NEXT2:
                divider_cnt.next = 0
                goto_state.next = GOTO_NEXT3
            elif goto_state == GOTO_NEXT3:
                if divider_cnt == self.controller_interface.clock_divider:
                    goto_state.next = GOTO_NEXT4
                else:
                    divider_cnt.next = divider_cnt + 1
            elif goto_state == GOTO_NEXT4:
                goto_tck.next = False
                goto_tms.next = False
                goto_state.next = GOTO_NEXT5
            elif goto_state == GOTO_NEXT5:
                divider_cnt.next = 0
                goto_state.next = GOTO_NEXT6
            elif goto_state == GOTO_NEXT6:
                if divider_cnt == self.controller_interface.clock_divider:
                    shift_state.next = GOTO_NEXT7
                else:
                    divider_cnt.next = divider_cnt + 1
            elif goto_state == GOTO_NEXT7:
                goto_tck.next = True
                goto_tms.next = False
                goto_state.next = GOTO_DONE
            elif goto_state == GOTO_NEXT8:
                divider_cnt.next = 0
                goto_state.next = GOTO_NEXT9
            elif goto_state == GOTO_NEXT9:
                if divider_cnt == self.controller_interface.clock_divider:
                    goto_state.next = GOTO_NEXT10
                else:
                    divider_cnt.next = divider_cnt + 1
            elif goto_state == GOTO_NEXT10:
                goto_tck.next = False
                goto_tms.next = True
                goto_state.next = GOTO_NEXT11
            elif goto_state == GOTO_NEXT11:
                divider_cnt.next = 0
                goto_state.next = GOTO_NEXT12
            elif goto_state == GOTO_NEXT12:
                if divider_cnt == self.controller_interface.clock_divider:
                    shift_state.next = GOTO_NEXT13
                else:
                    divider_cnt.next = divider_cnt + 1
            elif goto_state == GOTO_NEXT13:
                goto_tck.next = True
                goto_tms.next = True
                goto_state.next = GOTO_DONE
            elif goto_state == GOTO_NEXT14:
                if (self.controller_interface.cur_state != target_state) and (goto_count < 9):
                    # Get TMS value to take a step toward desired state
                    if jtag_path_map[self.controller_interface.cur_state] & (1 << target_state):
                        exit_tms.next = True
                    else:
                        exit_tms.next = False
                    goto_state.next = GOTO_NEXT15
                else:
                    goto_state.next = GOTO_DONE
            elif goto_state == GOTO_NEXT15:
                if exit_tms:
                    self.controller_interface.cur_state.next = jtag_state_transitions[self.controller_interface.cur_state][0]
                else:
                    self.controller_interface.cur_state.next = jtag_state_transitions[self.controller_interface.cur_state][1]
                divider_cnt.next = 0
                goto_state.next = GOTO_NEXT16
            elif goto_state == GOTO_NEXT16:
                if divider_cnt == self.controller_interface.clock_divider:
                    goto_state.next = GOTO_NEXT17
                else:
                    divider_cnt.next = divider_cnt + 1
            elif goto_state == GOTO_NEXT17:
                goto_tms.next = exit_tms
                goto_tck.next = False
                goto_state.next = GOTO_NEXT18
            elif goto_state == GOTO_NEXT18:
                if divider_cnt == self.controller_interface.clock_divider:
                    goto_state.next = GOTO_NEXT19
                else:
                    divider_cnt.next = divider_cnt + 1
            elif goto_state == GOTO_NEXT19:
                goto_tck.next = True
                goto_count.next = goto_count + 1
                goto_state.next = GOTO_NEXT14
            elif goto_state == GOTO_DONE:
                assert(self.controller_interface.cur_state == target_state)
                goto_tms.next = True  # De-assert TMS control from goto state logic influence on master TMS
                goto_state.next = GOTO_IDLE

        @always(self.controller_interface.clk.posedge)
        def shift_process():
            if shift_state == SHIFT_IDLE:
                ram_interface.Write.next = self.controller_interface.wr
                ram_interface.Din.next = self.controller_interface.din
                if master_state == SHIFT:
                    shift_state.next = SHIFT_START
            elif shift_state == SHIFT_START:
                ram_interface.Write.next = False  # Free up write interface for scan DMA logic below
                if self.controller_interface.cur_state == SI_TEST_LOGIC_RESET:
                    scan_tms.next = True
                else:
                    scan_tms.next = False
                if jtag_path_map[self.controller_interface.cur_state] & (1 << self.controller_interface.end_state):
                    end_tms.next = True
                else:
                    end_tms.next = False
                bit_count.next = 0
                shift_state.next = SHIFT_SCAN1
            elif shift_state == SHIFT_SCAN1:
                ram_interface.Write.next = False
                if bit_count < self.controller_interface.chain_length - 1:
                    shift_state.next = SHIFT_CYCLE1
                else:
                    shift_state.next = SHIFT_SCAN2
            elif shift_state == SHIFT_CYCLE1:
                divider_cnt.next = 0
                shift_state.next = SHIFT_DIVIDER1
            elif shift_state == SHIFT_DIVIDER1:
                if divider_cnt == self.controller_interface.clock_divider:
                    shift_state.next = SHIFT_CYCLE2
                else:
                    divider_cnt.next = divider_cnt + 1
            elif shift_state == SHIFT_CYCLE2:
                shift_tck.next = False
                shift_tms.next = scan_tms
                shift_tdi.next = ram_interface.Dout[bit_count % 8]
                # shift_tdi.next = tdi_buffer[bit_count >> 2] & (1 << (bit_count & 7))
                shift_state.next = SHIFT_CYCLE3
            elif shift_state == SHIFT_CYCLE3:
                divider_cnt.next = 0
                shift_state.next = SHIFT_DIVIDER2
            elif shift_state == SHIFT_DIVIDER2:
                if divider_cnt == self.controller_interface.clock_divider:
                    shift_state.next = SHIFT_CYCLE4
                else:
                    divider_cnt.next = divider_cnt + 1
            elif shift_state == SHIFT_CYCLE4:
                shift_tck.next = True
                shift_tms.next = scan_tms
                shift_tdi.next = ram_interface.Dout[bit_count % 8]
                # shift_tdi.next = tdi_buffer[bit_count >> 2] & (1 << (bit_count & 7))
                shift_state.next = SHIFT_CYCLE5
            elif shift_state == SHIFT_CYCLE5:
                ram_interface.Din.next = ram_interface.Dout
                ram_interface.Din.next[bit_count % 8] = self.controller_interface.tdo
                ram_interface.Write.next = True
                bit_count.next = bit_count + 1
                # if self.tdo:
                #     tdo_buffer.next[bit_count >> 2] |= (1 << (bit_count & 7))
                # else:
                #     tdo_buffer.next[bit_count >> 2] &= ~(1 << (bit_count & 7))
                shift_state.next = SHIFT_SCAN1
            elif shift_state == SHIFT_SCAN2:
                shift_state.next = SHIFT_CYCLE6
            elif shift_state == SHIFT_CYCLE6:
                divider_cnt.next = 0
                shift_state.next = SHIFT_DIVIDER3
            elif shift_state == SHIFT_DIVIDER3:
                if divider_cnt == self.controller_interface.clock_divider:
                    shift_state.next = SHIFT_CYCLE7
                else:
                    divider_cnt.next = divider_cnt + 1
            elif shift_state == SHIFT_CYCLE7:
                shift_tck.next = False
                shift_tms.next = end_tms
                shift_tdi.next = ram_interface.Dout[bit_count % 8]
                # shift_tdi.next = tdi_buffer[bit_count >> 2] & (1 << (bit_count & 7))
                shift_state.next = SHIFT_CYCLE8
            elif shift_state == SHIFT_CYCLE8:
                divider_cnt.next = 0
                shift_state.next = SHIFT_DIVIDER4
            elif shift_state == SHIFT_DIVIDER4:
                if divider_cnt == self.controller_interface.clock_divider:
                    shift_state.next = SHIFT_CYCLE9
                else:
                    divider_cnt.next = divider_cnt + 1
            elif shift_state == SHIFT_CYCLE9:
                shift_tck.next = True
                shift_tms.next = end_tms
                shift_tdi.next = ram_interface.Dout[bit_count % 8]
                # shift_tdi.next = tdi_buffer[bit_count >> 2] & (1 << (bit_count & 7))
                shift_state.next = SHIFT_CYCLE10
            elif shift_state == SHIFT_CYCLE10:
                ram_interface.Din.next = ram_interface.Dout
                ram_interface.Din.next[bit_count % 8] = self.controller_interface.tdo
                ram_interface.Write.next = True
                # if self.tdo:
                #     tdo_buffer.next[bit_count >> 2] |= (1 << (bit_count & 7))
                # else:
                #     tdo_buffer.next[bit_count >> 2] &= ~(1 << (bit_count & 7))
                shift_state.next = SHIFT_PAD1
            elif shift_state == SHIFT_PAD1:
                ram_interface.Write.next = False
                shift_remainder.next = self.controller_interface.chain_length % 8
                shift_state.next = SHIFT_PAD2
            elif shift_state == SHIFT_PAD2:
                # if shift_remainder:
                #     tdo_buffer.next[chain_length >> 2] = \
                #         tdo_buffer[chain_length >> 2] & (intbv(0xFF)[8:] >> (8 - shift_remainder))
                shift_state.next = SHIFT_END
            elif shift_state == SHIFT_END:
                if end_tms:
                    self.controller_interface.cur_state.next = jtag_state_transitions[self.controller_interface.cur_state][0]
                else:
                    self.controller_interface.cur_state.next = jtag_state_transitions[self.controller_interface.cur_state][1]
                shift_state.next = SHIFT_DONE
            elif shift_state == SHIFT_DONE:
                if master_state != SHIFT:
                    shift_tms.next = True  # De-assert TMS control from shift state logic influence on master TMS
                    shift_state.next = SHIFT_IDLE

        @always(self.controller_interface.clk.posedge)
        def reset_process():
            if reset_state == RESET_IDLE:
                if master_state == TAP_RESET:
                    reset_count.next = 0
                    reset_state.next = RESET_TMS1
            elif reset_state == RESET_TMS1:
                if reset_count < 5:
                    reset_tck.next = False
                    reset_tms.next = True
                    reset_state.next = RESET_TMS2
                else:
                    reset_state.next = RESET_DONE
            elif reset_state == RESET_TMS2:
                reset_tck.next = True
                reset_count.next = reset_count + 1
                reset_state.next = RESET_TMS1
            elif reset_state == RESET_DONE:
                reset_tms.next = True  # De-assert TMS control from shift state logic influence on master TMS
                reset_state.next = RESET_IDLE

        @always_comb
        def tms_process():
            self.controller_interface.jtag_interface.TMS.next = shift_tms and goto_tms and reset_tms

        @always_comb
        def tck_process():
            self.controller_interface.jtag_interface.TCK.next = shift_tck and goto_tck and reset_tck

        @always_comb
        def tdi_process():
            self.controller_interface.tdi.next = shift_tdi

        return master_process, goto_process, shift_process, reset_process, jtag_bram, ram_addr, ram_process, \
                tms_process, tck_process, tdi_process, trigger_process1, trigger_process2
