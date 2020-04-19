"""

Based on https://opencores.org/websvn/filedetails?repname=spi_master_slave&path=%2Fspi_master_slave%2Ftrunk%2Frtl%2Fspi_master_slave%2Fspi_slave.vhd
--      This block is the SPI slave interface, implemented in one single entity.
--      All internal core operations are synchronous to the external SPI clock, and follows the general SPI de-facto standard.
--      The parallel read/write interface is synchronous to a supplied system master clock, 'clk_i'.
--      Synchronization for the parallel ports is provided by input data request and write enable lines, and output data valid line.
--      Fully pipelined cross-clock circuitry guarantees that no setup artifacts occur on the buffers that are accessed by the two
--      clock domains.
--
--      The block is very simple to use, and has parallel inputs and outputs that behave like a synchronous memory i/o.
--      It is parameterizable via generics for the data width ('N'), SPI mode (CPHA and CPOL), and lookahead prefetch
--      signaling ('PREFETCH').
--
--      PARALLEL WRITE INTERFACE
--      The parallel interface has a input port 'di_i' and an output port 'do_o'.
--      Parallel load is controlled using 3 signals: 'di_i', 'di_req_o' and 'wren_i'.
--      When the core needs input data, a look ahead data request strobe , 'di_req_o' is pulsed 'PREFETCH' 'spi_sck_i'
--      cycles in advance to synchronize a user pipelined memory or fifo to present the next input data at 'di_i'
--      in time to have continuous clock at the spi bus, to allow back-to-back continuous load.
--      The data request strobe on 'di_req_o' is 2 'clk_i' clock cycles long.
--      The write to 'di_i' must occur at most one 'spi_sck_i' cycle before actual load to the core shift register, to avoid
--      race conditions at the register transfer.
--      The user circuit places data at the 'di_i' port and strobes the 'wren_i' line for one rising edge of 'clk_i'.
--      For a pipelined sync RAM, a PREFETCH of 3 cycles allows an address generator to present the new adress to the RAM in one
--      cycle, and the RAM to respond in one more cycle, in time for 'di_i' to be latched by the interface one clock before transfer.
--      If the user sequencer needs a different value for PREFETCH, the generic can be altered at instantiation time.
--      The 'wren_i' write enable strobe must be valid at least one setup time before the rising edge of the last clock cycle,
--      if continuous transmission is intended.
--      When the interface is idle ('spi_ssel_i' is HIGH), the top bit of the latched 'di_i' port is presented at port 'spi_miso_o'.
--
--      PARALLEL WRITE PIPELINED SEQUENCE
--      =================================
--                     __    __    __    __    __    __    __
--      clk_i       __/  \__/  \__/  \__/  \__/  \__/  \__/  \...     -- parallel interface clock
--                           ___________
--      di_req_o    ________/           \_____________________...     -- 'di_req_o' asserted on rising edge of 'clk_i'
--                  ______________ ___________________________...
--      di_i        __old_data____X______new_data_____________...     -- user circuit loads data on 'di_i' at next 'clk_i' rising edge
--                                             ________
--      wren_i      __________________________/        \______...     -- 'wren_i' enables latch on rising edge of 'clk_i'
--
--
--      PARALLEL READ INTERFACE
--      An internal buffer is used to copy the internal shift register data to drive the 'do_o' port. When a complete
--      word is received, the core shift register is transferred to the buffer, at the rising edge of the spi clock, 'spi_sck_i'.
--      The signal 'do_valid_o' is strobed 3 'clk_i' clocks after, to directly drive a synchronous memory or fifo write enable.
--      'do_valid_o' is synchronous to the parallel interface clock, and changes only on rising edges of 'clk_i'.
--      When the interface is idle, data at the 'do_o' port holds the last word received.
--
--      PARALLEL READ PIPELINED SEQUENCE
--      ================================
--                      ______        ______        ______        ______
--      clk_spi_i   ___/ bit1 \______/ bitN \______/bitN-1\______/bitN-2\__...  -- spi base clock
--                     __    __    __    __    __    __    __    __    __
--      clk_i       __/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \__/  \_...  -- parallel interface clock
--                  _________________ _____________________________________...  -- 1) received data is transferred to 'do_buffer_reg'
--      do_o        __old_data_______X__________new_data___________________...  --    after last bit received, at next shift clock.
--                                                   ____________
--      do_valid_o  ________________________________/            \_________...  -- 2) 'do_valid_o' strobed for 2 'clk_i' cycles
--                                                                              --    on the 3rd 'clk_i' rising edge.
--
--
--      This design was originally targeted to a Spartan-6 platform, synthesized with XST and normal constraints.
--
------------------------------ COPYRIGHT NOTICE -----------------------------------------------------------------------
--
--      This file is part of the SPI MASTER/SLAVE INTERFACE project http://opencores.org/project,spi_master_slave
--
--      Author(s):      Jonny Doin, jdoin@opencores.org, jonnydoin@gmail.com
--
--      Copyright (C) 2011 Jonny Doin
--      -----------------------------
--
--      This source file may be used and distributed without restriction provided that this copyright statement is not
--      removed from the file and that any derivative work contains the original copyright notice and the associated
--      disclaimer.
--
--      This source file is free software; you can redistribute it and/or modify it under the terms of the GNU Lesser
--      General Public License as published by the Free Software Foundation; either version 2.1 of the License, or
--      (at your option) any later version.
--
--      This source is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
--      warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
--      details.
--
--      You should have received a copy of the GNU Lesser General Public License along with this source; if not, download
--      it from http://www.gnu.org/licenses/lgpl.txt
--
"""
from myhdl import *


@block
def spi_slave(clk_i, spi_ssel_i, spi_sck_i, spi_mosi_i, spi_miso_o,
              di_req_o, di_i, wren_i, wr_ack_o, do_valid_o, do_o,
              do_transfer_o, wren_o, rx_bit_next_o, state_dbg_o, sh_reg_dbg_o,
              N=32, CPOL=False, CPHA=False, PREFETCH=3):
    """

    :param clk_i: internal interface clock (clocks di/do registers)
    :param spi_ssel_i: spi bus slave select line
    :param spi_sck_i: spi bus sck clock (clocks the shift register core)
    :param spi_mosi_i: spi bus mosi input
    :param spi_miso_o: spi bus spi_miso_o output
    :param di_req_o: preload lookahead data request line
    :param di_i: parallel load data in (clocked in on rising edge of clk_i)
    :param wren_i: user data write enable
    :param wr_ack_o: write acknowledge
    :param do_valid_o: do_o data valid strobe, valid during one clk_i rising edge.
    :param do_o: parallel output (clocked out on falling clk_i)
    # debug ports: can be removed for the application circuit
    :param do_transfer_o: debug: internal transfer driver
    :param wren_o: debug: internal state of the wren_i pulse stretcher
    :param rx_bit_next_o: internal rx bit
    :param state_dbg_o: internal state register
    :param sh_reg_dbg_o: debug: internal shift register
    :param N: 32bit serial word length is default
    :param CPOL: SPI mode selection (mode 0 default)
    :param CPHA: CPOL = clock polarity, CPHA = clock phase.
    :param PREFETCH: prefetch lookahead cycles
    :return:
    """

    # constants to control FlipFlop synthesis
    SHIFT_EDGE = not (CPOL != CPHA)  # MOSI data is captured and shifted at this SCK edge
    CHANGE_EDGE = (CPOL != CPHA)  # MISO data is updated at this SCK edge
    print("SHIFT_EDGE = ", SHIFT_EDGE)
    print("CHANGE_EDGE = ", CHANGE_EDGE)

    # ------------------------------------------------------------------------------------------
    # -- GLOBAL RESET:
    # --      all signals are initialized to zero at GSR (global set/reset) by giving explicit
    # --      initialization values at declaration. This is needed for all Xilinx FPGAs, and
    # --      especially for the Spartan-6 and newer CLB architectures, where a local reset can
    # --      reduce the usability of the slice registers, due to the need to share the control
    # --      set (RESET/PRESET, CLOCK ENABLE and CLOCK) by all 8 registers in a slice.
    # --      By using GSR for the initialization, and reducing RESET local init to the really
    # --      essential, the model achieves better LUT/FF packing and CLB usability.
    # ------------------------------------------------------------------------------------------
    # internal state signals for register and combinatorial stages
    state_next = Signal(intbv(0)[N:])  # state 0 is idle state
    state_reg = Signal(intbv(0)[N:])  # state 0 is idle state
    # shifter signals for register and combinatorial stages
    sh_next = Signal(intbv(0)[N:])
    sh_reg = Signal(intbv(0)[N:])
    # mosi and miso connections
    rx_bit_next = Signal(bool(0))  # sample of MOSI input
    tx_bit_next = Signal(bool(0))
    tx_bit_reg = Signal(bool(0))  # drives MISO during sequential logic
    preload_miso = Signal(bool(0))  # controls the MISO MUX
    # buffered di_i data signals for register and combinatorial stages
    di_reg = Signal(intbv(0)[N:])
    # internal wren_i stretcher for fsm combinatorial stage
    wren = Signal(bool(0))
    wr_ack_next = Signal(bool(0))
    wr_ack_reg = Signal(bool(0))
    # buffered do_o data signals for register and combinatorial stages
    do_buffer_next = Signal(intbv(0)[N:])
    do_buffer_reg = Signal(intbv(0)[N:])
    # internal signal to flag transfer to do_buffer_reg
    do_transfer_next = Signal(bool(0))
    do_transfer_reg = Signal(bool(0))
    # internal input data request signal
    di_req_next = Signal(bool(0))
    di_req_reg = Signal(bool(0))
    # cross-clock do_valid_o logic
    do_valid_next = Signal(bool(0))
    do_valid_A = Signal(bool(0))
    do_valid_B = Signal(bool(0))
    do_valid_C = Signal(bool(0))
    do_valid_D = Signal(bool(0))
    do_valid_o_reg = Signal(bool(0))
    # cross-clock di_req_o logic
    di_req_o_next = Signal(bool(0))
    di_req_o_A = Signal(bool(0))
    di_req_o_B = Signal(bool(0))
    di_req_o_C = Signal(bool(0))
    di_req_o_D = Signal(bool(0))
    di_req_o_reg = Signal(bool(0))
    # --=============================================================================================
    # --  GENERICS CONSTRAINTS CHECKING
    # --=============================================================================================
    # minimum word width is 8 bits
    assert N >= 8, "Generic parameter 'N' error: SPI shift register size needs to be 8 bits minimum"
    # maximum prefetch lookahead check
    assert PREFETCH <= N-5, "Generic parameter 'PREFETCH' error: lookahead count out of range, needs to be N-5 maximum"

    # --=============================================================================================
    # --  GENERATE BLOCKS
    # --=============================================================================================

    # --=============================================================================================
    # --  DATA INPUTS
    # --=============================================================================================
    # connect rx bit input
    @always_comb
    def rx_bit_proc():
        rx_bit_next.next = spi_mosi_i

    # --=============================================================================================
    # --  CROSS-CLOCK PIPELINE TRANSFER LOGIC
    # --=============================================================================================
    # do_valid_o and di_req_o strobe output logic
    # this is a delayed pulse generator with a ripple-transfer FFD pipeline, that generates a
    # fixed-length delayed pulse for the output flags, at the parallel clock domain
    @always(clk_i.posedge)
    def out_transfer_proc():
        # clock at parallel port clock
        # do_transfer_reg -> do_valid_o_reg
        do_valid_A.next = do_transfer_reg  # the input signal must be at least 2 clocks long
        do_valid_B.next = do_valid_A  # feed it to a ripple chain of FFDs
        do_valid_C.next = do_valid_B
        do_valid_D.next = do_valid_C
        do_valid_o_reg.next = do_valid_next  # registered output pulse
        # --------------------------------
        # di_req_reg -> di_req_o_reg
        di_req_o_A.next = di_req_reg  # the input signal must be at least 2 clocks long
        di_req_o_B.next = di_req_o_A  # feed it to a ripple chain of FFDs
        di_req_o_C.next = di_req_o_B
        di_req_o_D.next = di_req_o_C
        di_req_o_reg.next = di_req_o_next  # registered output pulse
        # generate a 2-clocks pulse at the 3rd clock cycle
        do_valid_next.next = do_valid_A and do_valid_B and not do_valid_D
        di_req_o_next.next = di_req_o_A and di_req_o_B and not di_req_o_D

    @always(wren_i.negedge)
    def in_transfer_proc_di():
        di_reg.next = di_i  # parallel data input buffer register

    # parallel load input registers: data register and write enable
    @always(clk_i.posedge)
    def in_transfer_proc():
        # registered data input, input register with clock enable
        # if wren_i:
        #     di_reg.next = di_i  # parallel data input buffer register

        # stretch wren pulse to be detected by spi fsm (ffd with sync preset and sync reset)
        if wren_i:  # wren_i is the sync preset for wren
            wren.next = True
        elif wr_ack_reg:  # wr_ack is the sync reset for wren
            wren.next = False

    # --=============================================================================================
    # --  REGISTER TRANSFER PROCESSES
    # --=============================================================================================
    # fsm state and data registers change on spi SHIFT_EDGE
    @instance
    def core_reg_proc():
        while True:
            # FFD registers clocked on SHIFT edge and cleared on idle (spi_ssel_i = 1)
            # state fsm register (fdr)
            if SHIFT_EDGE:
                yield spi_sck_i.posedge
            else:
                yield spi_sck_i.negedge
            if spi_ssel_i:  # async clr
                state_reg.next = 0  # state falls back to idle when slave not selected
            elif spi_sck_i == SHIFT_EDGE:  # on SHIFT edge, update state register
                state_reg.next = state_next  # core fsm changes state with spi SHIFT clock

            # FFD registers clocked on SHIFT edge
            # rtl core registers (fd)
            if spi_sck_i == SHIFT_EDGE:  # on fsm state change, update all core registers
                sh_reg.next = sh_next  # core shift register
                do_buffer_reg.next = do_buffer_next  # registered data output
                do_transfer_reg.next = do_transfer_next  # cross-clock transfer flag
                di_req_reg.next = di_req_next  # input data request
                wr_ack_reg.next = wr_ack_next  # wren ack for data load synchronization

    @instance
    def core_reg_proc_change():
        while True:
            # FFD registers clocked on CHANGE edge and cleared on idle (spi_ssel_i = 1)
            # miso MUX preload control register (fdp)
            if CHANGE_EDGE:
                yield spi_sck_i.posedge
            else:
                yield spi_sck_i.negedge
            if spi_ssel_i:  # async preset
                preload_miso.next = True  # miso MUX sees top bit of parallel input when slave not selected
            elif spi_sck_i == CHANGE_EDGE:  # on CHANGE edge, change to tx_reg output
                preload_miso.next = spi_ssel_i  # miso MUX sees tx_bit_reg when it is driven by SCK
            # FFD registers clocked on CHANGE edge
            # tx_bit register (fd)
            if spi_sck_i == CHANGE_EDGE:
                tx_bit_reg.next = tx_bit_next  # update MISO driver from the MSb

    # --=============================================================================================
    # --  COMBINATORIAL LOGIC PROCESSES
    # --=============================================================================================
    # state and datapath combinatorial logic

    @always_comb
    def core_combi_proc_a():
        if state_reg == 2:  # transfer received data to do_buffer_reg on next cycle
            do_buffer_next.next = sh_next  # get next data directly into rx buffer

    @always_comb
    def core_combi_proc():
        # all output signals are assigned to (avoid latches)
        sh_next.next = sh_reg  # shift register
        tx_bit_next.next = tx_bit_reg  # MISO driver
        do_buffer_next.next = do_buffer_reg  # output data buffer
        do_transfer_next.next = do_transfer_reg  # output data flag
        wr_ack_next.next = wr_ack_reg  # write enable acknowledge
        di_req_next.next = di_req_reg  # data input request
        state_next.next = state_reg  # fsm control state
        if state_reg == N:  # deassert 'di_rdy' and stretch do_valid
            wr_ack_next.next = False  # acknowledge data in transfer
            di_req_next.next = False  # prefetch data request: deassert when shifting data
            tx_bit_next.next = sh_reg[N-1]  # output next MSbit
            sh_next.next[N:1] = sh_reg[N-1:0]  # shift inner bits
            sh_next.next[0] = rx_bit_next  # shift in rx bit into LSb
            state_next.next = state_reg - 1  # update next state at each sck pulse
        # elif int(state_reg.val) in [i for i in range(PREFETCH + 3, N)]:  # remove 'do_transfer' and shift bits
        elif state_reg >= (PREFETCH + 3) and state_reg < N:  # remove 'do_transfer' and shift bits
            do_transfer_next.next = False  # reset 'do_valid' transfer signal
            di_req_next.next = False  # prefetch data request: deassert when shifting data
            wr_ack_next.next = False  # remove data load ack for all but the load stages
            tx_bit_next.next = sh_reg[N-1]  # output next MSbit
            sh_next.next[N:1] = sh_reg[N-1:0]  # shift inner bits
            sh_next.next[0] = rx_bit_next  # shift in rx bit into LSb
            state_next.next = state_reg - 1  # update next state at each sck pulse
        # elif int(state_reg.val) in [i for i in range(3, PREFETCH + 2)]:
        elif state_reg >= 3 and state_reg <= (PREFETCH + 2):
            di_req_next.next = True  # request data in advance to allow for pipeline delays
            wr_ack_next.next = False  # remove data load ack for all but the load stages
            tx_bit_next.next = sh_reg[N-1]  # output next MSbit
            sh_next.next[N:1] = sh_reg[N-1:0]  # shift inner bits
            sh_next.next[0] = rx_bit_next  # shift in rx bit into LSb
            state_next.next = state_reg - 1  # update next state at each sck pulse
        elif state_reg == 2:  # transfer received data to do_buffer_reg on next cycle
            di_req_next.next = True  # request data in advance to allow for pipeline delays
            wr_ack_next.next = False  # remove data load ack for all but the load stages
            tx_bit_next.next = sh_reg[N-1]  # output next MSbit
            sh_next.next[N:1] = sh_reg[N-1:0]  # shift inner bits
            sh_next.next[0] = rx_bit_next  # shift in rx bit into LSb
            do_transfer_next.next = True  # signal transfer to do_buffer on next cycle
            # do_buffer_next.next = sh_next  # get next data directly into rx buffer
            state_next.next = state_reg - 1  # update next state at each sck pulse
        elif state_reg == 1:  # transfer rx data to do_buffer and restart if new data is written
            sh_next.next[0] = rx_bit_next  # shift in rx bit into LSb
            di_req_next.next = False  # prefetch data request: deassert when shifting data
            state_next.next = N  # next state is top bit of new data
            if wren:  # load tx register if valid data present at di_reg
                wr_ack_next.next = True  # acknowledge data in transfer
                sh_next.next[N:1] = di_reg[N-1:0]  # shift inner bits
                tx_bit_next.next = di_reg[N-1]  # first output bit comes from the MSb of parallel data
            else:
                wr_ack_next.next = False  # no data reload for continuous transfer mode
                sh_next.next[N:1] = intbv(0)[N-1:]  # clear transmit shift register
                tx_bit_next.next = False  # send ZERO
        elif state_reg == 0:
            sh_next.next[0] = rx_bit_next  # shift in rx bit into LSb
            sh_next.next[N:1] = di_reg[N-1:0]  # shift inner bits
            tx_bit_next.next = di_reg[N-1]  # first output bit comes from the MSb of parallel data
            wr_ack_next.next = True  # acknowledge data in transfer
            di_req_next.next = False  # prefetch data request: deassert when shifting data
            do_transfer_next.next = False  # clear signal transfer to do_buffer
            state_next.next = N  # next state is top bit of new data
        else:
            state_next.next = 0  # safe state

    # --=============================================================================================
    # --  OUTPUT LOGIC PROCESSES
    # --=============================================================================================
    # data output processes
    @always_comb
    def do_o_proc():
        do_o.next = do_buffer_reg  # do_o always available

    @always_comb
    def do_valid_o_proc():
        do_valid_o.next = do_valid_o_reg  # copy registered do_valid_o to output

    @always_comb
    def di_req_o_proc():
        di_req_o.next = di_req_o_reg  # copy registered di_req_o to output

    @always_comb
    def wr_ack_o_proc():
        wr_ack_o.next = wr_ack_reg  # copy registered wr_ack_o to output

    # -----------------------------------------------------------------------------------------------
    # -- MISO driver process: preload top bit of parallel data to MOSI at reset
    # -----------------------------------------------------------------------------------------------
    # this is a MUX that selects the combinatorial next tx bit at reset, and the registered tx bit
    # at sequential operation. The mux gives us a preload of the first bit, simplifying the shifter logic.
    @always_comb
    def spi_miso_o_proc():
        if preload_miso:
            spi_miso_o.next = di_reg[N-1]  # copy top bit of parallel data at reset
        else:
            spi_miso_o.next = tx_bit_reg  # copy top bit of shifter at sequential operation

    # --=============================================================================================
    # --  DEBUG LOGIC PROCESSES
    # --=============================================================================================
    # these signals are useful for verification, and can be deleted after debug.
    @always_comb
    def do_transfer_proc():
        do_transfer_o.next = do_transfer_reg

    @always_comb
    def state_debug_proc():
        state_dbg_o.next = state_reg  # export internal state to debug

    @always_comb
    def rx_bit_next_proc():
        rx_bit_next_o.next = rx_bit_next

    @always_comb
    def wren_o_proc():
        wren_o.next = wren

    @always_comb
    def sh_reg_debug_proc():
        sh_reg_dbg_o.next = sh_reg  # export sh_reg to debug

    return rx_bit_proc, out_transfer_proc, in_transfer_proc, core_reg_proc, core_combi_proc, core_combi_proc_a, \
           do_o_proc, do_valid_o_proc, di_req_o_proc, wr_ack_o_proc, spi_miso_o_proc, \
           do_transfer_proc, state_debug_proc, rx_bit_next_proc, wren_o_proc, sh_reg_debug_proc, \
           in_transfer_proc_di, core_reg_proc_change
