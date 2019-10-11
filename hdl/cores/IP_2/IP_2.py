"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

IP Logic for IP_2 core of the Rearick Use Case Model
"""
from myhdl import *
from hdl.standards.s1687.IJTAGInterface import IJTAGInterface
from hdl.standards.s1687.sib_mux_post import sib_mux_post
from hdl.standards.s1687.SReg import SReg
from hdl.instruments.power_supply_monitor.power_supply_monitor import power_supply_monitor
from hdl.instruments.noise_maker.noise_maker import noise_maker
from hdl.instruments.noise_maker.noise_maker import MAX_STAGES, MAX_TOGGLES
import os
import os.path

period = 20  # clk frequency = 50 MHz


@block
def IP_2(path, name, ijtag_si, ijtag_so, from_ijtag_interface,
         fast_ck, ck,
         pu_mbist1, pu_mbist2, pu_mbist3, pu_mbist4, pu_mbist5,
         monitor=False):
    """
    Logic core IP_2 for Rearick use case model.  This IP defines the 1687 network topology for the IP_2 network.
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param ijtag_si: The ScanInterface SI for this 1687 network.
    :param ijtag_so: The ScanInterface SO for this 1687 network.
    :param from_ijtag_interface: The ScanInterface signals of SELECT, CAPTURE, SHIFT, UPDATE, RESET, and CLOCK
                    for this 1687 network.
    :param fast_ck: Sampling clock for when to sample the voltage value of VDD. Signal(bool(0)) type.
    :param ck: Clock signal to define the window to apply the noise in.
    :param pu_mbist1: Signal(intbv(0, min=0, max=101)) signal from MBIST1 representing 0 - 100% power usage
            that changes over time depending on the operation being performed.  The power monitor would
            monitor this value and report how much total power in the system is being used.
    :param pu_mbist2: Signal(intbv(0, min=0, max=101)) signal from MBIST2 representing 0 - 100% power usage
            that changes over time depending on the operation being performed.  The power monitor would
            monitor this value and report how much total power in the system is being used.
    :param pu_mbist3: Signal(intbv(0, min=0, max=101)) signal from MBIST3 representing 0 - 100% power usage
            that changes over time depending on the operation being performed.  The power monitor would
            monitor this value and report how much total power in the system is being used.
    :param pu_mbist4: Signal(intbv(0, min=0, max=101)) signal from MBIST4 representing 0 - 100% power usage
            that changes over time depending on the operation being performed.  The power monitor would
            monitor this value and report how much total power in the system is being used.
    :param pu_mbist5: Signal(intbv(0, min=0, max=101)) signal from MBIST5 representing 0 - 100% power usage
            that changes over time depending on the operation being performed.  The power monitor would
            monitor this value and report how much total power in the system is being used.
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: list of generators for the IP_2 logic for simulation.
    """
    noise = Signal(intbv(0, min=0, max=MAX_TOGGLES*MAX_STAGES))
    sib1_to_ijtag_interface = IJTAGInterface()
    sib1_to_sib2_so = Signal(bool(0))
    sib1_to_si = Signal(bool(0))
    sib1_from_so = Signal(bool(0))
    ref_to_delta_so = Signal(bool(0))
    delta_to_nf_so = Signal(bool(0))
    nf_to_status_so = Signal(bool(0))
    reference = Signal(intbv(0)[16:])
    delta = Signal(intbv(0)[8:])
    noise_flag = Signal(intbv(1)[1:])
    status = Signal(intbv(0)[2:])
    dummy = Signal(intbv(0)[2:])
    over = Signal(bool(0))
    under = Signal(bool(0))
    sib1_inst = sib_mux_post(path + "." + name, "SIB1", ijtag_si, from_ijtag_interface, sib1_to_sib2_so,
                             sib1_to_si, sib1_to_ijtag_interface, sib1_from_so, monitor=monitor)
    reference_SReg_inst = SReg(path + "." + name, "reference", sib1_to_si, sib1_to_ijtag_interface, ref_to_delta_so,
                               reference, reference, dr_width=16, monitor=monitor)
    delta_SReg_inst = SReg(path + "." + name, "delta", ref_to_delta_so, sib1_to_ijtag_interface, delta_to_nf_so,
                           delta, delta, dr_width=8, monitor=monitor)
    nf_SReg_inst = SReg(path + "." + name, "noise_flag", delta_to_nf_so, sib1_to_ijtag_interface, nf_to_status_so,
                        noise_flag, noise_flag, dr_width=1, monitor=monitor)
    status_SReg_inst = SReg(path + "." + name, "status", nf_to_status_so, sib1_to_ijtag_interface, sib1_from_so,
                            status, dummy, dr_width=2, monitor=monitor)
    sib2_to_ijtag_interface = IJTAGInterface()
    sib2_to_si = Signal(bool(0))
    sib2_from_so = Signal(bool(0))
    toggles_to_stages_so = Signal(bool(0))
    num_toggles = Signal(intbv(0, min=0, max=MAX_TOGGLES))
    num_stages = Signal(intbv(0, min=0, max=MAX_STAGES))
    sib2_inst = sib_mux_post(path + "." + name, "SIB2", sib1_to_sib2_so, from_ijtag_interface, ijtag_so,
                             sib2_to_si, sib2_to_ijtag_interface, sib2_from_so, monitor=monitor)
    num_toggles_SReg_inst = SReg(path + "." + name, "num_toggles", sib2_to_si, sib2_to_ijtag_interface,
                                 toggles_to_stages_so, num_toggles, num_toggles, dr_width=5, monitor=monitor)
    num_stages_SReg_inst = SReg(path + "." + name, "num_stages", toggles_to_stages_so, sib2_to_ijtag_interface,
                                sib2_from_so, num_stages, num_stages, dr_width=4, monitor=monitor)
    psm_inst = power_supply_monitor(path + "." + name, "PSM0", reference, delta, fast_ck, over, under,
                                    noise, pu_mbist1, pu_mbist2, pu_mbist3, pu_mbist4, pu_mbist5,
                                    noise_flag, monitor=monitor)
    nm_inst = noise_maker(path + "." + name, "NM0", num_toggles, num_stages, ck, noise, monitor=monitor)

    @always_comb
    def over_under_status():
        status.next[0] = under
        status.next[1] = over

    if monitor == False:
        return sib1_inst, reference_SReg_inst, delta_SReg_inst, nf_SReg_inst, status_SReg_inst, \
            sib2_inst, num_toggles_SReg_inst, num_stages_SReg_inst, psm_inst, nm_inst, over_under_status
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
        def monitor_noise_flag():
            print("\t\tIP_2({:s}): noise_flag".format(path + '.' + name), noise_flag)
            while 1:
                yield noise_flag
                print("\t\tIP_2({:s}): noise_flag".format(path + '.' + name), noise_flag)

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

        return sib1_inst, reference_SReg_inst, delta_SReg_inst, nf_SReg_inst, status_SReg_inst, \
            sib2_inst, num_toggles_SReg_inst, num_stages_SReg_inst, psm_inst, nm_inst, over_under_status, \
            monitor_ijtag_si, monitor_ijtag_so, monitor_noise_flag, monitor_from_ijtag_interface_SELECT, \
            monitor_from_ijtag_interface_CAPTURE, monitor_from_ijtag_interface_SHIFT, \
            monitor_from_ijtag_interface_UPDATE, monitor_from_ijtag_interface_RESET, \
            monitor_from_ijtag_interface_CLOCK


@block
def IP_2_tb(monitor=False):
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
    fast_ck = Signal(L)
    ck = Signal(L)
    pu_mbist1 = Signal(intbv(0, min=0, max=101))
    pu_mbist2 = Signal(intbv(0, min=0, max=101))
    pu_mbist3 = Signal(intbv(0, min=0, max=101))
    pu_mbist4 = Signal(intbv(0, min=0, max=101))
    pu_mbist5 = Signal(intbv(0, min=0, max=101))

    sib1_0 = '0'
    sib1_1 = '1'
    sib2_0 = '0'
    sib2_1 = '1'
    reg0 = '0000000000000000'
    delta0 = '00000000'
    delta1 = '10110010'
    nf0 = '0'
    stat0 = '00'
    width0 = len(sib1_0) + len(sib2_0)
    width = len(sib1_0) + len(reg0) + len(delta0) + len(nf0) + len(stat0) + len(sib2_0)
    sibs00 = Signal(intbv(sib1_0 + sib2_0)[2:])
    sibs10 = Signal(intbv(sib1_1 + sib2_0)[2:])
    si1 = Signal(intbv(sib1_1 + reg0 + delta0 + nf0 + stat0 + sib2_0)[width:])
    so1 = Signal(intbv(sib1_1 + reg0 + delta0 + nf0 + stat0 + sib2_0)[width:])
    si2 = Signal(intbv(sib1_1 + reg0 + delta1 + nf0 + stat0 + sib2_0)[width:])
    so2 = Signal(intbv(sib1_1 + reg0 + delta0 + nf0 + stat0 + sib2_0)[width:])
    si3 = Signal(intbv(sib1_1 + reg0 + delta0 + nf0 + stat0 + sib2_0)[width:])
    so3 = Signal(intbv(sib1_1 + reg0 + delta1 + nf0 + stat0 + sib2_0)[width:])

    ip2_inst = IP_2("TOP", "IP[2]", ijtag_si, ijtag_so, from_ijtag_interface,
                    fast_ck, ck,
                    pu_mbist1, pu_mbist2, pu_mbist3, pu_mbist4, pu_mbist5,
                    monitor=monitor)

    # print simulation data to file
    file_data = open("IP_2.csv", 'w')  # file for saving data
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
    def fast_ckgen():
        while True:
            fast_ck.next = not fast_ck
            yield delay(period // 10)

    @instance
    def ckgen():
        while True:
            ck.next = not ck
            yield delay(period)

    @instance
    def ijtagckgen():
        while True:
            from_ijtag_interface.CLOCK.next = not from_ijtag_interface.CLOCK
            yield delay(period // 2)

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
        # First C, S(00), U is so == bin(00)?
        print("First C, S(00), U is so == bin(00)?")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        for i in range(width0):
            # Write Shift value
            from_ijtag_interface.CAPTURE.next = L
            from_ijtag_interface.SHIFT.next = H
            print("ijtag_si.next = sibs00[i], sibs00[", i, "] = ", sibs00[i])
            ijtag_si.next = sibs00[i]  # ########################################################### SHIFT
            print("sibs00[", i, "] = ", sibs00[i], ", ijtag_so = ", ijtag_so)
            yield from_ijtag_interface.CLOCK.posedge
            assert(ijtag_so == sibs00[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H

        # Select SIB1 to open secondary network
        # Second C, S(10), U is so == bin(00)? SIB1 should now be enabled
        print("Select SIB1 network.  Second C, S(10), U is so == bin(00)? SIB1 should now be enabled")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.UPDATE.next = L
        from_ijtag_interface.CAPTURE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        for i in range(width0):
            # Write Shift value
            from_ijtag_interface.CAPTURE.next = L
            from_ijtag_interface.SHIFT.next = H
            print("ijtag_si.next = sibs10[i], sibs10[", i, "] = ", sibs10[i])
            ijtag_si.next = sibs10[i]  # ########################################################### SHIFT
            print("sibs00[", i, "] = ", sibs00[i], ", ijtag_so = ", ijtag_so)
            yield from_ijtag_interface.CLOCK.posedge
            assert(ijtag_so == sibs00[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H

        # Scan safe data through secondary network to verify the network is working
        # Third C, S(10), U is so == bin(00)? 16:8:1:2 bits required from SI to SO for reference:delta:nf:status.
        print("Scan safe data through SIB1 network. Third C, S(10), U is so == bin(00)?")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.UPDATE.next = L
        from_ijtag_interface.CAPTURE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        print("width = ", width)
        for i in range(width):
            # Write Shift value
            from_ijtag_interface.CAPTURE.next = L
            from_ijtag_interface.SHIFT.next = H
            print("ijtag_si.next = si1[i], si1[", i, "] = ", si1[i])
            ijtag_si.next = si1[i]  # ########################################################### SHIFT
            print("so1[", i, "] = ", so1[i], ", ijtag_so = ", ijtag_so)
            yield from_ijtag_interface.CLOCK.posedge
            assert(ijtag_so == so1[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H

        # Scan delta data through secondary network to verify the network is working
        # Forth C, S(10), U is so == bin(00)? 16:8:1:2:1:1 bits required from SI to SO for reference:delta:nf:status:sib1:sib2.
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
            print("ijtag_si.next = si2[i], si2[", i, "] = ", si2[i])
            ijtag_si.next = si2[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("so2[", i, "] = ", so2[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == so2[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H

        # Now test if the delta data persisted correctly
        # Fifth C, S(10), U is so == bin(00)? 16:8:1:2:1:1 bits required from SI to SO for reference:delta:nf:status:sib1:sib2.
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
            print("ijtag_si.next = si3[i], si3[", i, "] = ", si3[i])
            ijtag_si.next = si3[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print(">> so3[", i, "] = ", so3[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == so3[i])
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

    return ip2_inst, ijtagckgen, fast_ckgen, ckgen, stimulus


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
    fast_ck = Signal(L)
    ck = Signal(L)
    pu_mbist1 = Signal(intbv(0, min=0, max=101))
    pu_mbist2 = Signal(intbv(0, min=0, max=101))
    pu_mbist3 = Signal(intbv(0, min=0, max=101))
    pu_mbist4 = Signal(intbv(0, min=0, max=101))
    pu_mbist5 = Signal(intbv(0, min=0, max=101))

    ip2_inst = IP_2("TOP", "IP[2]", ijtag_si, ijtag_so, from_ijtag_interface,
                    fast_ck, ck,
                    pu_mbist1, pu_mbist2, pu_mbist3, pu_mbist4, pu_mbist5,
                    monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    ip2_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="IP_2")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    ip2_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="IP_2")
    tb = IP_2_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="IP_2_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="IP_2_tb")


def main():
    tb = IP_2_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
