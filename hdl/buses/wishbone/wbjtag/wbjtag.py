"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Purpose: This is the wishbone interface to the JTAGMasterController
hdl.hosts.jtaghost.JTAG_Ctrl_Master

Register Map: (11-bit address)
Addresses: 0 - 1023 Vector Buffer Memory (8-bit data bus as lowest 8 bits)
Address: 1024 Start State Register (4-bit lowest 4 bits)
Address: 1025 End State Register (4-bit lowest 4 bits)
Address: 1026 Bit Count (16-bit lowest 16 bits)
Address: 1027 Control Register
            bit 0: Scan start/stop: 1=start scan, 0=stop scan
Address: 1028 Status Register
            bit 0: 1=busy scanning, 0=done scanning
"""

from myhdl import *
from hdl.hosts.jtaghost.JTAG_Ctrl_Master import JTAGCtrlMaster, RUN_TEST_IDLE, TEST_LOGIC_RESET, PAUSE_DR, PAUSE_IR
from hdl.hosts.jtaghost.JTAG_Ctrl_Master import JTAGCtrlMasterInterface


@block
def wbjtag(i_clk, i_reset, i_wb_cyc, i_wb_stb, i_wb_we, wb_addr, i_wb_data, o_wb_data, o_wb_ack,
           tdi, tdo, tck, tms, trst, monitor=False):
    start_state_register = Signal(intbv(TEST_LOGIC_RESET)[4:])
    end_state_register = Signal(intbv(RUN_TEST_IDLE)[4:])
    bit_count_register = Signal(intbv(0)[16:])
    control_register = Signal(intbv(0)[8:])
    status_register = Signal(intbv(0)[8:])
    bram_cycle = Signal(bool(0))
    start_state_register_cycle = Signal(bool(0))
    end_state_register_cycle = Signal(bool(0))
    bit_count_register_cycle = Signal(bool(0))
    control_register_cycle = Signal(bool(0))
    status_register_cycle = Signal(bool(0))
    reset_n = ResetSignal(1, 0, True)
    shift_start = Signal(bool(0))
    shift_started = Signal(bool(0))

    control_interface = JTAGCtrlMasterInterface(i_clk, reset_n, addr_width=10, data_width=8)
    # Redefine the ports to match the ATE ports
    control_interface.jtag_interface.TCK = tck
    control_interface.jtag_interface.TMS = tms
    control_interface.jtag_interface.TRST = trst
    control_interface.tdi = tdi
    control_interface.tdo = tdo
    jtag_ctrl_master = JTAGCtrlMaster("wishbone", "wbjtag", control_interface, monitor=monitor)

    @always_comb
    def reset():
        reset_n.next = not i_reset

    @always_comb
    def comb0():
        # control_interface.clk.next = i_clk
        # control_interface.reset_n.next = reset_n
        status_register.next[0] = 1 if control_interface.busy else 0
        # tck.next = control_interface.jtag_interface.TCK
        # tms.next = control_interface.jtag_interface.TMS
        # trst.next = control_interface.jtag_interface.TRST
        # tdi.next = control_interface.tdi
        # tdo.next = control_interface.tdo
        control_interface.bit_count.next = bit_count_register
        control_interface.state_start.next = start_state_register
        control_interface.state_end.next = end_state_register

    @always(i_clk.posedge)
    def addr_decode():
        bram_cycle.next = False
        start_state_register_cycle.next = False
        end_state_register_cycle.next = False
        bit_count_register_cycle.next = False
        control_register_cycle.next = False
        status_register_cycle.next = False
        if i_wb_cyc and i_wb_stb and (wb_addr[10] == 0):  # Block RAM cycle
            bram_cycle.next = True
        elif i_wb_cyc and i_wb_stb and (wb_addr[10] == 1):  # Register cycle
            if wb_addr[10:] == intbv(0)[10:]:  # Start State Register
                start_state_register_cycle.next = True
            elif wb_addr[10:] == intbv(1)[10:]:  # End State Register
                end_state_register_cycle.next = True
            elif wb_addr[10:] == intbv(2)[10:]:  # Bit Count Register
                bit_count_register_cycle.next = True
            elif wb_addr[10:] == intbv(3)[10:]:  # Control Register
                control_register_cycle.next = True
            elif wb_addr[10:] == intbv(4)[10:]:  # Status Register
                status_register_cycle.next = True
            else:
                pass

    @always(i_clk.posedge)
    def io_cycle():
        if bram_cycle:
            control_interface.addr.next = wb_addr[10:]
            control_interface.din.next = i_wb_data[8:]
            control_interface.wr.next = i_wb_we
        else:
            control_interface.wr.next = False
        if start_state_register_cycle and i_wb_we:
            start_state_register.next = i_wb_data[4:]
        elif end_state_register_cycle and i_wb_we:
            end_state_register.next = i_wb_data[4:]
        elif bit_count_register_cycle and i_wb_we:
            bit_count_register.next = i_wb_data[16:]
        elif control_register_cycle and i_wb_we:
            control_register.next[0] = i_wb_data[0]
        elif status_register_cycle and i_wb_we:
            status_register.next[0] = i_wb_data[0]

    # @always(i_clk.posedge)
    @always_comb
    def o_cycle():
        if bram_cycle and not i_wb_we:
            o_wb_data.next = concat(Signal(intbv(0)[24:]), control_interface.dout)
        elif start_state_register_cycle:
            o_wb_data.next = concat(Signal(intbv(0)[28:]), start_state_register)
        elif end_state_register_cycle:
            o_wb_data.next = concat(Signal(intbv(0)[28:]), end_state_register)
        elif control_register_cycle:
            o_wb_data.next = concat(Signal(intbv(0)[31:]), control_register[0])
        elif status_register_cycle:
            o_wb_data.next = concat(Signal(intbv(0)[31:]), status_register[0])

    @always(i_clk.posedge)
    def ack():
        # if bram_cycle or start_state_register_cycle or end_state_register_cycle or control_register_cycle or status_register_cycle:
        #     o_wb_ack.next = True
        # else:
        #     o_wb_ack.next = False
        o_wb_ack.next = i_wb_stb and i_wb_cyc

    @always(i_clk.posedge)
    def strobe0():
        if control_register[0] == 1 and not shift_start:
            control_interface.shift_strobe.next = True
            shift_start.next = True
        elif shift_started:
            control_interface.shift_strobe.next = False
        elif control_register[0] == 0:
            shift_start.next = False

    @always(i_clk.posedge)
    def strobe1():
        if control_interface.shift_strobe and control_interface.busy:
            shift_started.next = True
        elif control_interface.busy:
            shift_started.next = True
        else:
            shift_started.next = False

    return jtag_ctrl_master, comb0, addr_decode, io_cycle, o_cycle, ack, strobe0, strobe1
