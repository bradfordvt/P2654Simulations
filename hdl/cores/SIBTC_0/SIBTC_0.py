"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Test Case for a sib_mux_post with a single 8 bit register wired to sub-network
"""
from myhdl import *
from hdl.standards.s1687.IJTAGInterface import IJTAGInterface
from hdl.standards.s1687.sib_mux_post import sib_mux_post
from hdl.standards.s1687.SReg import SReg
import os
import os.path

period = 20  # clk frequency = 50 MHz


@block
def SIBTC_0(path, name, ijtag_si, ijtag_so, from_ijtag_interface, monitor=False):
    """
    Logic core SIBTC_0 test case logic of sib_mux_post with a single 8 bit register on the sub-network
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param ijtag_si: The ScanInterface SI for this 1687 network.
    :param ijtag_so: The ScanInterface SO for this 1687 network.
    :param from_ijtag_interface: The ScanInterface signals of SELECT, CAPTURE, SHIFT, UPDATE, RESET, and CLOCK
                    for this 1687 network.
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: list of generators for the IP_2 logic for simulation.
    """
    sib1_to_ijtag_interface = IJTAGInterface()
    sib1_to_si = Signal(bool(0))
    sib1_from_so = Signal(bool(0))
    delta = Signal(intbv(0)[8:])
    sib1_inst = sib_mux_post(path + "." + name, "SIB1", ijtag_si, from_ijtag_interface, ijtag_so,
                             sib1_to_si, sib1_to_ijtag_interface, sib1_from_so, monitor=monitor)
    delta_SReg_inst = SReg(path + "." + name, "delta", sib1_to_si, sib1_to_ijtag_interface, sib1_from_so,
                           delta, delta, dr_width=8, monitor=monitor)

    if monitor == False:
        return sib1_inst, delta_SReg_inst
    else:
        @instance
        def monitor_ijtag_si():
            print("\t\tIP_2({:s}): ijtag_si".format(path + '.' + name), ijtag_si)
            while 1:
                yield ijtag_si
                print("\t\tIP_2({:s}): ijtag_si".format(path + '.' + name), ijtag_si)

        @instance
        def monitor_ijtag_so():
            print("\t\tIP_2({:s}): ijtag_so".format(path + '.' + name), ijtag_so)
            while 1:
                yield ijtag_so
                print("\t\tIP_2({:s}): ijtag_so".format(path + '.' + name), ijtag_so)

        @instance
        def monitor_from_ijtag_interface_SELECT():
            print("\t\tIP_2({:s}): from_ijtag_interface.SELECT".format(path + '.' + name), from_ijtag_interface.SELECT)
            while 1:
                yield from_ijtag_interface.SELECT
                print("\t\tIP_2({:s}): from_ijtag_interface.SELECT".format(path + '.' + name), from_ijtag_interface.SELECT)

        @instance
        def monitor_from_ijtag_interface_CAPTURE():
            print("\t\tIP_2({:s}): from_ijtag_interface.CAPTURE".format(path + '.' + name), from_ijtag_interface.CAPTURE)
            while 1:
                yield from_ijtag_interface.CAPTURE
                print("\t\tIP_2({:s}): from_ijtag_interface.CAPTURE".format(path + '.' + name), from_ijtag_interface.CAPTURE)

        @instance
        def monitor_from_ijtag_interface_SHIFT():
            print("\t\tIP_2({:s}): from_ijtag_interface.SHIFT".format(path + '.' + name), from_ijtag_interface.SHIFT)
            while 1:
                yield from_ijtag_interface.SHIFT
                print("\t\tIP_2({:s}): from_ijtag_interface.SHIFT".format(path + '.' + name), from_ijtag_interface.SHIFT)

        @instance
        def monitor_from_ijtag_interface_UPDATE():
            print("\t\tIP_2({:s}): from_ijtag_interface.UPDATE".format(path + '.' + name), from_ijtag_interface.UPDATE)
            while 1:
                yield from_ijtag_interface.UPDATE
                print("\t\tIP_2({:s}): from_ijtag_interface.UPDATE".format(path + '.' + name), from_ijtag_interface.UPDATE)

        @instance
        def monitor_from_ijtag_interface_RESET():
            print("\t\tIP_2({:s}): from_ijtag_interface.RESET".format(path + '.' + name), from_ijtag_interface.RESET)
            while 1:
                yield from_ijtag_interface.RESET
                print("\t\tIP_2({:s}): from_ijtag_interface.RESET".format(path + '.' + name), from_ijtag_interface.RESET)

        @instance
        def monitor_from_ijtag_interface_CLOCK():
            print("\t\tIP_2({:s}): from_ijtag_interface.CLOCK".format(path + '.' + name), from_ijtag_interface.CLOCK)
            while 1:
                yield from_ijtag_interface.CLOCK
                print("\t\tIP_2({:s}): from_ijtag_interface.CLOCK".format(path + '.' + name), from_ijtag_interface.CLOCK)

        return sib1_inst, delta_SReg_inst, \
            monitor_ijtag_si, monitor_ijtag_so, monitor_from_ijtag_interface_SELECT, \
            monitor_from_ijtag_interface_CAPTURE, monitor_from_ijtag_interface_SHIFT, \
            monitor_from_ijtag_interface_UPDATE, monitor_from_ijtag_interface_RESET, \
            monitor_from_ijtag_interface_CLOCK


@block
def SIBTC_0_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    H = bool(1)
    L = bool(0)
    ijtag_si = Signal(L)
    ijtag_so = Signal(L)
    from_ijtag_interface = IJTAGInterface()

    sib0 = '0'
    sib1 = '1'
    delta0 = '00000000'
    delta1 = '10110010'
    width = len(sib0) + len(delta0)
    # si0 = intbv(sib0 + delta0)
    si1 = Signal(intbv(sib1 + delta0)[width:])
    si2 = Signal(intbv(sib1 + delta1)[width:])
    so0 = Signal(intbv(sib1 + delta0)[width:])
    so1 = Signal(intbv(sib1 + delta0)[width:])
    so2 = Signal(intbv(sib1 + delta1)[width:])

    sib_inst = SIBTC_0("TOP", "SIBTC[0]", ijtag_si, ijtag_so, from_ijtag_interface, monitor=monitor)

    @instance
    def clkgen():
        while True:
            from_ijtag_interface.CLOCK.next = not from_ijtag_interface.CLOCK
            yield delay(period // 2)

    # print simulation data to file
    file_data = open("SIBTC_0.csv", 'w')  # file for saving data
    # print header to file
    print("{0},{1},{2},{3},{4},{5}".format("si", "ce", "se", "ue", "sel", "so"),
          file=file_data)
    # print data on each tap_interface.ClockDR
    @always(from_ijtag_interface.CLOCK.posedge)
    def print_data():
        """
        """
        # print in file
        # print.format is not supported in MyHDL 1.0
        print(ijtag_si, ",", from_ijtag_interface.CAPTURE, ",", from_ijtag_interface.SHIFT, ",",
              from_ijtag_interface.UPDATE, ",", from_ijtag_interface.SELECT, ",", ijtag_so, file=file_data)

    @instance
    def stimulus():
        """
        Perform instruction decoding for various instructions
        :return:
        """
        # Reset the network
        from_ijtag_interface.RESET.next = H
        yield delay(1)
        from_ijtag_interface.RESET.next = L
        yield delay(1)

        # Shift deselect pattern through SIB1 and SIB2 to ensure network is in bypass state
        # Start the Capture transition operation
        # First C, S(0), U is so == bin(0)?
        print("First C, S(0), U is so == bin(0)?")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        ijtag_si.next = L  # ########################################################### SHIFT(0) SIB1
        yield from_ijtag_interface.CLOCK.posedge
        assert (ijtag_so == L)
        yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        # Select SIB1 to open secondary network
        # Second C, S(1), U is so == bin(0)? SIB1 should now be enabled
        print("Select SIB1 network.  Second C, S(1), U is so == bin(0)? SIB1 should now be enabled")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.UPDATE.next = L
        from_ijtag_interface.CAPTURE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        ijtag_si.next = H  # ########################################################### SHIFT(1) SIB1
        yield from_ijtag_interface.CLOCK.posedge
        assert(ijtag_so == L)
        yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        # Scan safe data through secondary network to verify the network is working
        # Third C, S(1), U is so == bin(1)? 16:8:1:2 bits required from SI to SO for reference:delta:nf:status.
        print("Scan safe data through SIB1 network. Third C, S(10), U is so == bin(00)?")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.UPDATE.next = L
        from_ijtag_interface.CAPTURE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        for i in range(width):
            # Write Shift value
            from_ijtag_interface.CAPTURE.next = L
            from_ijtag_interface.SHIFT.next = H
            print("ijtag_si.next = si1[i], si1[", i, "] = ", si1[i])
            ijtag_si.next = si1[i]  # ########################################################### SHIFT
            print("so0[", i, "] = ", so0[i], ", ijtag_so = ", ijtag_so)
            yield from_ijtag_interface.CLOCK.posedge
            assert(ijtag_so == so0[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H

        # Scan delta data through secondary network to verify the network is working
        # Forth C, S(10), U is so == bin(00)? 16:8:1:2:1:1 bits required from SI to SO for reference:delta:nf:status:sib1:sib2.
        print("Scan safe data through SIB1 network. Third C, S(1), U is so == bin(0)?")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.UPDATE.next = L
        from_ijtag_interface.CAPTURE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        for i in range(width):
            # Write Shift value
            from_ijtag_interface.CAPTURE.next = L
            from_ijtag_interface.SHIFT.next = H
            print("ijtag_si.next = si2[i], si2[", i, "] = ", si2[i])
            ijtag_si.next = si2[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("so1[", i, "] = ", so1[i], ", ijtag_so = ", ijtag_so)
            # assert(ijtag_so == so1[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H

        # Now test if the delta data persisted correctly
        # Fifth C, S(1), U is so == bin(0)? 8:1 bits required from SI to SO for delta:sib1.
        print("Scan safe data through SIB1 network. Third C, S(1), U is so == bin(0)?")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.UPDATE.next = L
        from_ijtag_interface.CAPTURE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        for i in range(width):
            # Write Shift value
            from_ijtag_interface.CAPTURE.next = L
            from_ijtag_interface.SHIFT.next = H
            print("ijtag_si.next = si1[i], si[", i, "] = ", si1[i])
            ijtag_si.next = si1[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print(">> so2[", i, "] = ", so2[i], ", ijtag_so = ", ijtag_so)
            # ###########################assert(ijtag_so == so[i])
            # assert (ijtag_so == so2[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge

        raise StopSimulation()

    return sib_inst, clkgen, stimulus


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    H = bool(1)
    L = bool(0)
    ijtag_si = Signal(L)
    ijtag_so = Signal(L)
    from_ijtag_interface = IJTAGInterface()

    sib_inst = SIBTC_0("TOP", "SIBTC[0]", ijtag_si, ijtag_so, from_ijtag_interface, monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    sib_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SIBTC_0")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    sib_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SIBTC_0")
    tb = SIBTC_0_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SIBTC_0_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SIBTC_0_tb")


def main():
    tb = SIBTC_0_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
