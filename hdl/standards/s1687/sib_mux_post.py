"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import os
import os.path
from hdl.standards.s1687.IJTAGInterface import IJTAGInterface

period = 20  # clk frequency = 50 MHz


@block
def sib_mux_post(path, name, si, from_ijtag_interface, so, to_si, to_ijtag_interface, from_so, monitor=False):
    """
    This code implements the logic from Figure F.10 in the IEEE Std 1687 standard.
    Segment-Insertion-Bit (SIB) to allow the overall scan chain to be of variable length.
    Creates a Module SIB for IEEE 1687 with the following interface:
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logging (path instance)
    :param si: Scan Input from host interface
    :param from_ijtag_interface: IJTAGInterface defining the control signals for this register "from" side
    :param so: Scan Output to host interface from SIB
    :param to_si: Scan Input to instrument interface
    :param to_ijtag_interface: IJTAGInterface defining the control signals for this register "to" side
    :param from_so: Scan Output from instrument interface
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    update_bit = Signal(bool(0))
    tsr_data = Signal(bool(0))
    
    @always(from_ijtag_interface.CLOCK.posedge)
    def captureFF():
        # print("Entering captureFF")
        if from_ijtag_interface.SELECT and from_ijtag_interface.CAPTURE:
            # print("SEL and CE")
            tsr_data.next = update_bit
        elif from_ijtag_interface.SELECT and from_ijtag_interface.SHIFT:
            # print("captureFF: SI=", si)
            to_si.next = tsr_data
            tsr_data.next = si
        else:
            to_si.next = to_si

    @always(from_ijtag_interface.CLOCK.negedge)
    def updateFF():
        # print("Entering updateFF")
        if from_ijtag_interface.RESET == bool(1):
            update_bit.next = bool(0)
        elif from_ijtag_interface.SELECT and from_ijtag_interface.UPDATE:
            # print("SEL and UE")
            # update_bit.next = to_si
            update_bit.next = tsr_data
        else:
            update_bit.next = update_bit

    @always_comb
    def Mux_post():
        if update_bit == bool(1):
            so.next = from_so
        else:
            so.next = tsr_data

    @always_comb
    def sel():
        to_ijtag_interface.RESET.next = from_ijtag_interface.RESET
        to_ijtag_interface.CLOCK.next = from_ijtag_interface.CLOCK
        if update_bit and from_ijtag_interface.SELECT:
            to_ijtag_interface.SELECT.next = from_ijtag_interface.SELECT
            to_ijtag_interface.CAPTURE.next = from_ijtag_interface.CAPTURE
            to_ijtag_interface.SHIFT.next = from_ijtag_interface.SHIFT
            to_ijtag_interface.UPDATE.next = from_ijtag_interface.UPDATE
        else:
            to_ijtag_interface.SELECT.next = bool(0)
            to_ijtag_interface.CAPTURE.next = bool(0)
            to_ijtag_interface.SHIFT.next = bool(0)
            to_ijtag_interface.UPDATE.next = bool(0)

    if not monitor:
        return captureFF, updateFF, Mux_post, sel
    else:
        @instance
        def monitor_update_bit():
            print("\t\tsib_mux_post({:s}): update_bit".format(path + "." + name), update_bit)
            while 1:
                yield update_bit
                print("\t\tsib_mux_post({:s}): update_bit".format(path + "." + name), update_bit)

        @instance
        def monitor_si():
            print("\t\tsib_mux_post({:s}): si".format(path + "." + name), si)
            while 1:
                yield si
                print("\t\tsib_mux_post({:s}): si".format(path + "." + name), si)

        @instance
        def monitor_so():
            print("\t\tsib_mux_post({:s}): so".format(path + "." + name), so)
            while 1:
                yield so
                print("\t\tsib_mux_post({:s}) so:".format(path + "." + name), so)

        @instance
        def monitor_from_so():
            print("\t\tsib_mux_post({:s}): from_so".format(path + "." + name), from_so)
            while 1:
                yield from_so
                print("\t\tsib_mux_post({:s}): from_so".format(path + "." + name), from_so)

        @instance
        def monitor_to_si():
            print("\t\tsib_mux_post({:s}): to_si".format(path + "." + name), to_si)
            while 1:
                yield to_si
                print("\t\tsib_mux_post({:s}) to_si:".format(path + "." + name), to_si)

        @instance
        def monitor_from_ijtag_interface_capture():
            print("\t\tsib_mux_post({:s}): from_ijtag_interface.CAPTURE".format(path + "." + name),
                  from_ijtag_interface.CAPTURE)
            while 1:
                yield from_ijtag_interface.CAPTURE
                print("\t\tsib_mux_post({:s}): from_ijtag_interface.CAPTURE".format(path + "." + name),
                      from_ijtag_interface.CAPTURE)

        @instance
        def monitor_from_ijtag_interface_shift():
            print("\t\tsib_mux_post({:s}): from_ijtag_interface.SHIFT".format(path + "." + name),
                  from_ijtag_interface.SHIFT)
            while 1:
                yield from_ijtag_interface.SHIFT
                print("\t\tsib_mux_post({:s}) from_ijtag_interface.SHIFT:".format(path + "." + name),
                      from_ijtag_interface.SHIFT)

        @instance
        def monitor_from_ijtag_interface_update():
            print("\t\tsib_mux_post({:s}): from_ijtag_interface.UPDATE".format(path + "." + name),
                  from_ijtag_interface.UPDATE)
            while 1:
                yield from_ijtag_interface.UPDATE
                print("\t\tsib_mux_post({:s}): from_ijtag_interface.UPDATE".format(path + "." + name),
                      from_ijtag_interface.UPDATE)

        @instance
        def monitor_from_ijtag_interface_select():
            print("\t\tsib_mux_post({:s}): from_ijtag_interface.SELECT".format(path + "." + name),
                  from_ijtag_interface.SELECT)
            while 1:
                yield from_ijtag_interface.SELECT
                print("\t\tsib_mux_post({:s}) from_ijtag_interface.SELECT:".format(path + "." + name),
                      from_ijtag_interface.SELECT)

        @instance
        def monitor_from_ijtag_interface_reset():
            print("\t\tsib_mux_post({:s}): from_ijtag_interface.RESET".format(path + "." + name),
                  from_ijtag_interface.RESET)
            while 1:
                yield from_ijtag_interface.RESET
                print("\t\tsib_mux_post({:s}) from_ijtag_interface.RESET:".format(path + "." + name),
                      from_ijtag_interface.RESET)

        @instance
        def monitor_to_ijtag_interface_capture():
            print("\t\tsib_mux_post({:s}): to_ijtag_interface.CAPTURE".format(path + "." + name),
                  to_ijtag_interface.CAPTURE)
            while 1:
                yield to_ijtag_interface.CAPTURE
                print("\t\tsib_mux_post({:s}): to_ijtag_interface.CAPTURE".format(path + "." + name),
                      to_ijtag_interface.CAPTURE)

        @instance
        def monitor_to_ijtag_interface_shift():
            print("\t\tsib_mux_post({:s}): to_ijtag_interface.SHIFT".format(path + "." + name),
                  to_ijtag_interface.SHIFT)
            while 1:
                yield to_ijtag_interface.SHIFT
                print("\t\tsib_mux_post({:s}) to_ijtag_interface.SHIFT:".format(path + "." + name),
                      to_ijtag_interface.SHIFT)

        @instance
        def monitor_to_ijtag_interface_update():
            print("\t\tsib_mux_post({:s}): to_ijtag_interface.UPDATE".format(path + "." + name),
                  to_ijtag_interface.UPDATE)
            while 1:
                yield to_ijtag_interface.UPDATE
                print("\t\tsib_mux_post({:s}): to_ijtag_interface.UPDATE".format(path + "." + name),
                      to_ijtag_interface.UPDATE)

        @instance
        def monitor_to_ijtag_interface_select():
            print("\t\tsib_mux_post({:s}): to_ijtag_interface.SELECT".format(path + "." + name),
                  to_ijtag_interface.SELECT)
            while 1:
                yield to_ijtag_interface.SELECT
                print("\t\tsib_mux_post({:s}) to_ijtag_interface.SELECT:".format(path + "." + name),
                      to_ijtag_interface.SELECT)

        @instance
        def monitor_to_ijtag_interface_reset():
            print("\t\tsib_mux_post({:s}): to_ijtag_interface.RESET".format(path + "." + name),
                  to_ijtag_interface.RESET)
            while 1:
                yield to_ijtag_interface.RESET
                print("\t\tsib_mux_post({:s}) to_ijtag_interface.RESET:".format(path + "." + name),
                      to_ijtag_interface.RESET)

        return captureFF, updateFF, Mux_post, sel, \
            monitor_si, monitor_so, monitor_from_ijtag_interface_capture, monitor_from_ijtag_interface_shift, \
            monitor_from_ijtag_interface_update, monitor_from_ijtag_interface_select, \
            monitor_from_ijtag_interface_reset, monitor_to_ijtag_interface_capture, \
            monitor_to_ijtag_interface_shift, monitor_to_ijtag_interface_update, \
            monitor_to_ijtag_interface_select, monitor_to_ijtag_interface_reset, \
            monitor_update_bit


@block
def sib_mux_post_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    so = Signal(bool(0))
    from_so = Signal(bool(0))
    to_si = Signal(bool(0))
    from_ijtag_interface = IJTAGInterface()
    to_ijtag_interface = IJTAGInterface()
    d = Signal(bool(0))
    data_in = Signal(intbv('0001010'))
    data_out = Signal(intbv('0000000'))
    si = Signal(bool(0))

    sib_inst = sib_mux_post('TOP', 'SIB0', si, from_ijtag_interface, so, to_si, to_ijtag_interface, from_so)

    @instance
    def clkgen():
        while True:
            from_ijtag_interface.CLOCK.next = not from_ijtag_interface.CLOCK
            yield delay(period // 2)

    # print simulation data to file
    file_data = open("sib_mux_post_tb.csv", 'w')  # file for saving data
    # print header to file
    print("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11}".format("si", "ce", "se", "ue", "sel", "so", "to_si",
                                                                     "from_so", "to_ce", "to_se", "to_ue", "to_sel"),
          file=file_data)

    # print data on each tap_interface.ClockDR
    @always(from_ijtag_interface.CLOCK.posedge)
    def print_data():
        """
        """
        # print in file
        # print.format is not supported in MyHDL 1.0
        print(si, ",", from_ijtag_interface.CAPTURE, ",", from_ijtag_interface.SHIFT, ",",
              from_ijtag_interface.UPDATE, ",", from_ijtag_interface.SELECT, ",", so, ",", to_si, ",",
              from_so, to_ijtag_interface.CAPTURE, ",", to_ijtag_interface.SHIFT,
              to_ijtag_interface.UPDATE, ",", to_ijtag_interface.SELECT, file=file_data)

    @always(to_ijtag_interface.CLOCK.negedge)
    def loopbackFF():
        if to_ijtag_interface.SELECT == bool(1) and to_ijtag_interface.SHIFT == bool(1):
            from_so.next = to_si
        else:
            from_so.next = bool(0)

    @instance
    def stimulus():
        """
        Not true IJTAG protocol, but used to exercise the state machine with the fewest cycles
        :return:
        """
        H = bool(1)
        L = bool(0)
        # Reset the SIB
        from_ijtag_interface.RESET.next = bool(1)
        yield delay(10)
        from_ijtag_interface.RESET.next = bool(0)
        yield delay(10)
        # Start the Capture transition operation
        # First C, S(0), U is so == bool(0)?
        print("First C, S(0), U is so == bool(0)?")
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
        si.next = L  # ########################################################### SHIFT(0)
        yield from_ijtag_interface.CLOCK.posedge
        assert (so == bool(0))
        yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        # Second C, S(1), U is so == bool(0)? to_ijtag_interface should now be enabled
        print("Second C, S(1), U is so == bool(0)? to_ijtag_interface should now be enabled")
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
        si.next = H  # ########################################################### SHIFT(1)
        yield from_ijtag_interface.CLOCK.posedge
        assert (so == bool(0))
        yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        # Third C, S(0), U is so == bool(0)? Should be value of loopbackFF
        print("Third C, S(0), U is so == bool(0)? Should be value of loopbackFF")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.UPDATE.next = L
        from_ijtag_interface.CAPTURE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        # Write Shift first bit value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        si.next = L  # loopbackFF data in  ###################################### SHIFT(0)
        yield from_ijtag_interface.CLOCK.posedge
        assert (so == bool(1))  # Value of loopbackFF
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift second bit value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        si.next = L  # SIB data in  ############################################# SHIFT(0)
        yield from_ijtag_interface.CLOCK.posedge
        assert (so == bool(0))  # Value of SIB
        yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        # Forth C, S(0), U is so == bool(1)? Should be update_bit shifting through loopbackFF
        print("Forth C, S(0), U is so == bool(1)? Should be update_bit shifting through loopbackFF")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.UPDATE.next = L
        from_ijtag_interface.CAPTURE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value of SIB
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        si.next = L  # ########################################################### SHIFT(0)
        yield from_ijtag_interface.CLOCK.posedge
        assert (so == bool(0))  # Value of SIB
        yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.negedge
        yield from_ijtag_interface.CLOCK.posedge

        raise StopSimulation()

    return sib_inst, clkgen, stimulus, loopbackFF, print_data


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    si = Signal(bool(0))
    so = Signal(bool(0))
    from_so = Signal(bool(0))
    to_si = Signal(bool(0))
    from_ijtag_interface = IJTAGInterface()
    to_ijtag_interface = IJTAGInterface()

    sib_inst = sib_mux_post('TOP', 'SIB0', si, from_ijtag_interface, so, to_si, to_ijtag_interface, from_so, monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    sib_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="sib_mux_post")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    sib_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="sib_mux_post")
    tb = sib_mux_post_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="sib_mux_post_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="sib_mux_post_tb")


def main():
    tb = sib_mux_post_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
