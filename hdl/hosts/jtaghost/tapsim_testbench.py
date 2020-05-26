"""
Copyright (c) 2020 Bradford G. Van Treuren
See the licence file in the top directory
"""
from hdl.hosts.jtaghost.tapsim import *


period = 20  # clk frequency = 50 MHz


@block
def tapsim_testbench(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    addr_width = 10
    data_width = 8
    clk = Signal(bool(0))
    reset_n = ResetSignal(1, 0, True)
    controller_interface = TAPControllerInterface(clk, reset_n, addr_width=addr_width, data_width=data_width)

    ir_tdi_vector = [Signal(intbv(0x55)[data_width:]), Signal(intbv(0x19)[data_width:])]
    ir_tdo_vector = [Signal(intbv(0)[data_width:]), Signal(intbv(0)[data_width:])]
    dr_tdi_vector = [Signal(intbv(0xA5)[data_width:]), Signal(intbv(0x66)[data_width:])]
    dr_tdo_vector = [Signal(intbv(0)[data_width:]), Signal(intbv(0)[data_width:])]
    count = 15

    ts_inst = TAPSim("TOP", "TAPSim0", controller_interface, monitor=monitor)
    @instance
    def clkgen():
        while True:
            clk.next = not clk
            yield delay(period // 2)

    @always_seq(clk.posedge, reset=reset_n)
    def loopback():
        controller_interface.tdo.next = controller_interface.tdi

    @instance
    def stimulus():
        """
        Scan an IR followed by a scan of a DR
        :return:
        """
        H = bool(1)
        L = bool(0)
        # Reset the instrument
        reset_n.next = False
        yield delay(2)
        reset_n.next = True
        yield delay(50)
        # Scan the IR
        controller_interface.scan_state.next = SI_SHIFT_IR
        controller_interface.end_state.next = SI_RUN_TEST_IDLE
        # Fill the TAPSim data buffer memory with tdi data
        num_full_words = int(count // data_width)
        remainder = count % data_width
        addr = 0
        for i in range(num_full_words):
            data = ir_tdi_vector[i]
            # yield write_vector(clk, waddr, din, wr, addr, data)
            yield clk.negedge
            controller_interface.addr.next = addr
            controller_interface.din.next = data
            controller_interface.wr.next = True
            yield clk.posedge
            yield clk.negedge
            controller_interface.wr.next = False
            yield clk.posedge
            addr += 1
        # Now write out the remaining bits that may be a partial word in size, but a full word needs to be written
        if remainder > 0:
            data = ir_tdi_vector[num_full_words]
            # yield write_vector(clk, waddr, din, wr, addr, data)
            yield clk.negedge
            controller_interface.addr.next = addr
            controller_interface.din.next = data
            controller_interface.wr.next = True
            yield clk.posedge
            yield clk.negedge
            controller_interface.wr.next = False
            yield clk.posedge

        # Now start the scan operation
        controller_interface.chain_length.next = intbv(count)[addr_width:]
        controller_interface.scan_state.next = SI_SHIFT_IR
        controller_interface.end_state.next = SI_RUN_TEST_IDLE
        controller_interface.command.next = SCAN
        yield clk.negedge
        yield controller_interface.busy.posedge
        controller_interface.go_strobe.next = False
        yield controller_interface.busy.negedge
        # Scan completed, now fetch the captured data
        addr = 0
        for i in range(num_full_words):
            # yield read_vector(clk, raddr, wr, read_data, dout, addr)
            yield clk.negedge
            controller_interface.addr.next = addr
            controller_interface.wr.next = False
            yield clk.posedge
            # controller_interface.read_data.next = controller_interface.dout
            rdata = int(controller_interface.dout)
            yield clk.negedge
            yield clk.posedge
            # data = get_read_data(read_data)
            # data = controller_interface.read_data
            # ir_tdo_vector[i] = int(data)
            ir_tdo_vector[i].next = rdata
            addr += 1
        # Now read out the remaining bits that may be a partial word in size, but a full word needs to be read
        if remainder > 0:
            # yield read_vector(clk, raddr, wr, read_data, dout, addr)
            yield clk.negedge
            controller_interface.addr.next = addr
            controller_interface.wr.next = False
            yield clk.posedge
            # controller_interface.read_data.next = controller_interface.dout
            rdata = int(controller_interface.dout)
            yield clk.negedge
            yield clk.posedge
            # data = get_read_data(read_data)
            # data = controller_interface.read_data
            ir_tdo_vector[num_full_words].next = rdata

        print("ir_tdo_vector = ", ir_tdo_vector)
        yield delay(1)
        assert(ir_tdo_vector[0] == 0x55)  # Captured TDO value returned to ir_tdo_vector
        assert(ir_tdo_vector[1] == 0x19)  # Captured TDO value returned to ir_tdo_vector

        start = SI_SHIFT_DR
        end = SI_RUN_TEST_IDLE
        # Fill the JTAGCtrlMaster data buffer memory with tdi data
        num_full_words = int(count // data_width)
        remainder = count % data_width
        addr = 0
        for i in range(num_full_words):
            data = dr_tdi_vector[i]
            # yield write_vector(clk, waddr, din, wr, addr, data)
            yield controller_interface.clk.negedge
            controller_interface.addr.next = addr
            controller_interface.din.next = data
            controller_interface.wr.next = True
            yield controller_interface.clk.posedge
            yield controller_interface.clk.negedge
            controller_interface.wr.next = False
            yield controller_interface.clk.posedge
            addr += 1
        # Now write out the remaining bits that may be a partial word in size, but a full word needs to be written
        if remainder > 0:
            data = dr_tdi_vector[num_full_words]
            # yield write_vector(clk, waddr, din, wr, addr, data)
            yield controller_interface.clk.negedge
            controller_interface.addr.next = addr
            controller_interface.din.next = data
            controller_interface.wr.next = True
            yield controller_interface.clk.posedge
            yield controller_interface.clk.negedge
            controller_interface.wr.next = False
            yield controller_interface.clk.posedge

        # Now start the scan operation
        controller_interface.chain_length.next = intbv(count)[addr_width:]
        controller_interface.go_strobe.next = True
        controller_interface.scan_state.next = start
        controller_interface.end_state.next = end
        yield controller_interface.busy.posedge
        controller_interface.go_strobe.next = False
        yield controller_interface.busy.negedge
        # Scan completed, now fetch the captured data
        addr = 0
        for i in range(num_full_words):
            # yield read_vector(clk, raddr, wr, read_data, dout, addr)
            yield controller_interface.clk.negedge
            controller_interface.addr.next = addr
            controller_interface.wr.next = False
            yield controller_interface.clk.posedge
            # controller_interface.read_data.next = controller_interface.dout
            rdata = int(controller_interface.dout)
            yield controller_interface.clk.negedge
            yield controller_interface.clk.posedge

            # data = get_read_data(read_data)
            #data = controller_interface.read_data
            # print("controller_interface.read_data = ", controller_interface.read_data)
            print("rdata0 = ", rdata)
            dr_tdo_vector[i].next = rdata
            addr += 1
        # Now read out the remaining bits that may be a partial word in size, but a full word needs to be read
        if remainder > 0:
            # yield read_vector(clk, raddr, wr, read_data, dout, addr)
            yield controller_interface.clk.negedge
            controller_interface.addr.next = addr
            controller_interface.wr.next = False
            yield controller_interface.clk.posedge
            # controller_interface.read_data.next = controller_interface.dout
            # print("controller_interface.read_data = ", controller_interface.read_data)
            rdata = int(controller_interface.dout)
            print("data1 = ", rdata)
            yield controller_interface.clk.negedge
            yield controller_interface.clk.posedge

            # data = get_read_data(read_data)
            # data = controller_interface.read_data
            dr_tdo_vector[num_full_words].next = rdata
        yield delay(1)
        print("dr_tdo_vector = ", dr_tdo_vector)
        assert(dr_tdo_vector[0] == 0xA5)  # Captured TDO value returned to dr_tdo_vector
        assert(dr_tdo_vector[1] == 0x66)  # Captured TDO value returned to dr_tdo_vector
        raise StopSimulation()

    return ts_inst.rtl(), clkgen, stimulus, loopback


# def convert():
#     """
#     Convert the myHDL design into VHDL and Verilog
#     :return:
#     """
#     clk = Signal(bool(0))
#     reset_n = ResetSignal(1, 0, True)
#
#     control_instance = JTAGCtrlMasterInterface(clk, reset_n, addr_width=10, data_width=8)
#
#     jcm_inst = JTAGCtrlMaster('DEMO', 'JCM0',
#                               control_instance,
#                               monitor=False
#                               )
#
#     vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
#     if not os.path.exists(vhdl_dir):
#         os.mkdir(vhdl_dir, mode=0o777)
#     jcm_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="JTAGCtrlMaster")
#     verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
#     if not os.path.exists(verilog_dir):
#         os.mkdir(verilog_dir, mode=0o777)
#     jcm_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="JTAGCtrlMaster")
#     tb = JTAGCtrlMaster_tb(monitor=False)
#     tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="JTAGCtrlMaster_tb")
#     tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="JTAGCtrlMaster_tb")


def main():
    tb = tapsim_testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    # convert()


if __name__ == '__main__':
    main()
