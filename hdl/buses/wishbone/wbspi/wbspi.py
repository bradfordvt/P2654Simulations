"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Purpose: This is the wishbone interface to the spi_master
hdl.hosts.spihost.spi2.spi_master

Register Map:
Address: 0 Data Transmit Register
Address: 1 Data Receive Register
"""

from myhdl import *
from hdl.hosts.spihost.spi2.spi_master import spi_master

@block
def wbspi(i_clk, i_reset, i_wb_cyc, i_wb_stb, i_wb_we, i_wb_addr, i_wb_data, o_wb_data, o_wb_ack,
          spi_ssel_o, spi_sck_o, spi_mosi_o, spi_miso_i, N=32, PREFETCH=2):
    txreg = Signal(intbv(0)[N:])
    rxreg = Signal(intbv(0)[N:])
    tx_register_cycle = Signal(bool(0))
    rx_register_cycle = Signal(bool(0))
    # Parallel interface
    di_req_o = Signal(bool(0))
    di_i = Signal(intbv(0)[N:])
    wren_i = Signal(bool(0))
    wr_ack_o = Signal(bool(0))
    do_valid_o = Signal(bool(0))
    do_o = Signal(intbv(0)[N:])
    # Debug signals
    sck_ena_o = Signal(bool(0))
    sck_ena_ce_o = Signal(bool(0))
    do_transfer_o = Signal(bool(0))
    wren_o = Signal(bool(0))
    rx_bit_reg_o = Signal(bool(0))
    state_dbg_o = Signal(intbv(0)[N:])
    core_clk_o = Signal(bool(0))
    core_n_clk_o = Signal(bool(0))
    core_ce_o  = Signal(bool(0))
    core_n_ce_o = Signal(bool(0))
    sh_reg_dbg_o = Signal(intbv(0)[N:])
    # wait state generation
    ws_count = Signal(modbv(0, min=0, max=N+3))
    ws_ack_delay = Signal(bool(0))
    ws_latch = Signal(bool(0))
    tx_ack = Signal(bool(0))
    tx_ack_o = Signal(bool(0))
    tx_req = Signal(bool(1))
    rws_count = Signal(modbv(0, min=0, max=21))
    rws_ack_delay = Signal(bool(0))
    rws_latch = Signal(bool(0))
    rx_ack = Signal(bool(0))
    rx_ack_o = Signal(bool(0))
    tx_cnt = Signal(intbv(0, min=0, max=6))

    spi_inst = spi_master(i_clk, i_clk, i_reset,
                          spi_ssel_o, spi_sck_o, spi_mosi_o, spi_miso_i,
                          di_req_o, di_i, wren_i, wr_ack_o, do_valid_o, do_o,
                          sck_ena_o, sck_ena_ce_o, do_transfer_o, wren_o, rx_bit_reg_o, state_dbg_o,
                          core_clk_o, core_n_clk_o, core_ce_o, core_n_ce_o, sh_reg_dbg_o,
                          N=N, CPOL=0, CPHA=0, PREFETCH=PREFETCH, SPI_2X_CLK_DIV=5)

    @always(i_clk.posedge)
    def addr_decode():
        tx_register_cycle.next = False
        rx_register_cycle.next = False
        if i_wb_cyc and i_wb_stb and (i_wb_addr[10] == 1):  # Register cycle
            if i_wb_addr[10:] == intbv(0x30)[10:]:  # Data Transmit Register
                tx_register_cycle.next = True
                txreg.next = i_wb_data[N:]
            elif i_wb_addr[10:] == intbv(0x31)[10:]:  # Data Receive Register
                rx_register_cycle.next = True
            else:
                pass

    @always(i_clk.posedge)
    def i_cycle():
        if (tx_register_cycle == True) and i_wb_we:
            di_i.next = txreg

    # @always(i_clk.posedge)
    @always_comb
    def o_cycle():
        if rx_register_cycle == True:
            if N == 32:
                o_wb_data.next = rxreg
            else:
                o_wb_data.next = concat(Signal(intbv(0)[32-N:]), rxreg)

    @always(i_clk.posedge)
    def ack_trigger():
        if tx_register_cycle and do_valid_o:
            tx_ack.next = True
            tx_cnt.next = 0
        elif tx_cnt < 5:
            tx_cnt.next = tx_cnt + 1
        else:
            tx_ack.next = False

    @always(i_clk.posedge)
    def rack_trigger():
        if rx_register_cycle:
            rws_ack_delay.next = True
        else:
            rws_ack_delay.next = False

    @always(i_clk.posedge)
    def ack():
        if rx_ack and i_wb_stb:
            o_wb_ack.next = True
        elif tx_ack and i_wb_stb:
            o_wb_ack.next = True
        else:
            o_wb_ack.next = False

    @instance
    def rwait():
        while True:
            yield rx_register_cycle.posedge
            for _ in range(20):
                yield i_clk.posedge
            rx_ack_o.next = True
            for _ in range(5):
                yield i_clk.posedge
            rx_ack_o.next = False

    @always(i_clk.posedge)
    def rwait_proc():
        if rx_ack_o and i_wb_stb:
            rx_ack.next = True
        else:
            rx_ack.next = False

    @always(do_valid_o.posedge)
    def read():
        if do_valid_o:
            rxreg.next = do_o

    @always(i_clk.posedge)
    def request():
        if di_req_o:
            tx_req.next = True
        else:
            tx_req.next = False

    @instance
    def wren_proc():
        while True:
            yield tx_register_cycle.posedge
            for _ in range(5):
                yield i_clk.posedge
            wren_i.next = True
            for _ in range(5):
                yield i_clk.posedge
            wren_i.next = False

    return spi_inst, addr_decode, i_cycle, o_cycle, ack, ack_trigger, read, request, wren_proc, \
            rack_trigger, rwait, rwait_proc
