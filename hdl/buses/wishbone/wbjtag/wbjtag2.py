"""
Copyright (c) 2020 Bradford G. Van Treuren
See the licence file in the top directory

Purpose: This is the wishbone interface to the TAPSim
hdl.hosts.jtaghost.TAPSim

Register Map: (11-bit address)
Addresses: 0 - 1023 Vector Buffer Memory (8-bit data bus as lowest 8 bits)
Address: 1024 Scan State Register (4-bit lowest 4 bits)
Address: 1025 End State Register (4-bit lowest 4 bits)
Address: 1026 Chain Length (16-bit lowest 16 bits)
Address: 1027 Control Register
            bit 0: Command start/stop: 1=start command, 0=stop command
Address: 1028 Status Register
            bit 0: 1=busy scanning, 0=done scanning
Address: 1029 Command Register (3-bit lowest 3 bits)
"""
from hdl.hosts.jtaghost.tapsim import *


@block
def wbjtag2(i_clk, i_reset, i_wb_cyc, i_wb_stb, i_wb_we, wb_addr, i_wb_data, o_wb_data, o_wb_ack,
            tdi, tdo, tck, tms, trst, monitor=False):
    scan_state_register = Signal(intbv(SI_TEST_LOGIC_RESET)[4:])
    end_state_register = Signal(intbv(SI_RUN_TEST_IDLE)[4:])
    chain_length_register = Signal(intbv(0)[16:])
    control_register = Signal(intbv(0)[8:])
    status_register = Signal(intbv(0)[8:])
    command_register = Signal(intbv(0)[8:])
    bram_cycle = Signal(bool(0))
    scan_state_register_cycle = Signal(bool(0))
    end_state_register_cycle = Signal(bool(0))
    chain_length_register_cycle = Signal(bool(0))
    control_register_cycle = Signal(bool(0))
    status_register_cycle = Signal(bool(0))
    command_register_cycle = Signal(bool(0))
    reset_n = ResetSignal(1, 0, True)

    control_interface = TAPControllerInterface(i_clk, reset_n, addr_width=10, data_width=8)
    # Redefine the ports to match the ATE ports
    control_interface.jtag_interface.TCK = tck
    control_interface.jtag_interface.TMS = tms
    control_interface.jtag_interface.TRST = trst
    control_interface.tdi = tdi
    control_interface.tdo = tdo
    jtag_ctrl_master = TAPSim("wishbone", "wbjtag2", control_interface, monitor=monitor)
    print("wbjtag2: tdo => ", hex(id(tdo)))

    @always_comb
    def reset():
        reset_n.next = not i_reset

    @always_comb
    def comb0():
        status_register.next[0] = 1 if control_interface.busy else 0
        control_interface.chain_length.next = chain_length_register
        control_interface.scan_state.next = scan_state_register
        control_interface.end_state.next = end_state_register
        control_interface.command.next = command_register
        control_interface.go_strobe.next = control_register[0]

    @always(i_clk.posedge)
    def addr_decode():
        bram_cycle.next = False
        scan_state_register_cycle.next = False
        end_state_register_cycle.next = False
        chain_length_register_cycle.next = False
        control_register_cycle.next = False
        status_register_cycle.next = False
        command_register_cycle.next = False
        if i_wb_cyc and i_wb_stb and (wb_addr[10] == 0):  # Block RAM cycle
            bram_cycle.next = True
        elif i_wb_cyc and i_wb_stb and (wb_addr[10] == 1):  # Register cycle
            if wb_addr[10:] == intbv(0)[10:]:  # Start State Register
                scan_state_register_cycle.next = True
            elif wb_addr[10:] == intbv(1)[10:]:  # End State Register
                end_state_register_cycle.next = True
            elif wb_addr[10:] == intbv(2)[10:]:  # Bit Count Register
                chain_length_register_cycle.next = True
            elif wb_addr[10:] == intbv(3)[10:]:  # Control Register
                control_register_cycle.next = True
            elif wb_addr[10:] == intbv(4)[10:]:  # Status Register
                status_register_cycle.next = True
            elif wb_addr[10:] == intbv(5)[10:]:  # Status Register
                command_register_cycle.next = True
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
        if scan_state_register_cycle and i_wb_we:
            scan_state_register.next = i_wb_data[4:]
        elif end_state_register_cycle and i_wb_we:
            end_state_register.next = i_wb_data[4:]
        elif chain_length_register_cycle and i_wb_we:
            chain_length_register.next = i_wb_data[16:]
        elif control_register_cycle and i_wb_we:
            control_register.next[0] = i_wb_data[0]
        elif status_register_cycle and i_wb_we:
            status_register.next[0] = i_wb_data[0]
        elif command_register_cycle and i_wb_we:
            command_register.next[0] = i_wb_data[3:]

    # @always(i_clk.posedge)
    @always_comb
    def o_cycle():
        if bram_cycle and not i_wb_we:
            o_wb_data.next = concat(Signal(intbv(0)[24:]), control_interface.dout)
        elif scan_state_register_cycle:
            o_wb_data.next = concat(Signal(intbv(0)[28:]), scan_state_register)
        elif end_state_register_cycle:
            o_wb_data.next = concat(Signal(intbv(0)[28:]), end_state_register)
        elif control_register_cycle:
            o_wb_data.next = concat(Signal(intbv(0)[31:]), control_register[0])
        elif status_register_cycle:
            o_wb_data.next = concat(Signal(intbv(0)[31:]), status_register[0])
        elif command_register_cycle:
            o_wb_data.next = concat(Signal(intbv(0)[29:]), command_register[3:])

    @always(i_clk.posedge)
    def ack():
        o_wb_ack.next = i_wb_stb and i_wb_cyc

    return jtag_ctrl_master.rtl(), comb0, addr_decode, io_cycle, o_cycle, ack
