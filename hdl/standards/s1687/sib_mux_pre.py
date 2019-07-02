"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import os
import os.path
from hdl.standards.s1687.IJTAGInterface import IJTAGInterface


def SA_to_String(tdo_vector):
    dlen = len(tdo_vector)
    response = ""
    for i in range(dlen):
        t = '0'
        if tdo_vector[dlen - i - 1] == bool(1):
            t = '1'
        response += t
    return response

class sib_mux_pre:
    """
    This class implements the logic from Figure F.12 in the IEEE Std 1687 standard.
    """
    def __init__(self, path, name, si, from_ijtag_interface, so, to_si, to_ijtag_interface, from_so):
        """
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
        """
        self.path = path
        self.name = name
        self.si = si
        self.from_ijtag_interface = from_ijtag_interface
        self.so = so
        self.to_ijtag_interface = to_ijtag_interface
        self.from_so = from_so
        self.to_si = to_si
        self.update_bit = Signal(bool(0))
        self.mux1_out = Signal(bool(0))
        self.mux2_out = Signal(bool(0))
        self.mux3_out = Signal(bool(0))
        self.mux4_out = Signal(bool(0))
        self.cs_out = Signal(bool(0))

    def toVHDL(self):
        """
        Converts the myHDL logic into VHDL
        :return:
        """
        vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
        if not os.path.exists(vhdl_dir):
            os.mkdir(vhdl_dir, mode=0o777)
        self.rtl(monitor=False).convert(hdl="VHDL", initial_values=True, directory=vhdl_dir)

    def toVerilog(self):
        """
        Converts the myHDL logic into Verilog
        :return:
        """
        verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
        if not os.path.exists(verilog_dir):
            os.mkdir(verilog_dir, mode=0o777)
        self.rtl(monitor=False).convert(hdl="Verilog", initial_values=True, directory=verilog_dir)

    def rtl(self, monitor=False):
        """
        Wrapper around the RTL logic to get a meaningful name during conversion
        :param monitor:
        :return:
        """
        return self.sib_mux_pre_rtl(monitor=monitor)

    @block
    def sib_mux_pre_rtl(self, monitor=False):
        """
        The logic for the SIB
        :return: The generator methods performing the logic decisions
        """
        @always_comb
        def mux1():
            if self.update_bit:
                self.mux1_out.next = self.from_so
            else:
                self.mux1_out.next = self.si

        @always_comb
        def mux2():
            if self.from_ijtag_interface.SELECT and self.from_ijtag_interface.SHIFT:
                self.mux2_out.next = self.mux1_out
            else:
                self.mux2_out.next = self.cs_out

        @always_comb
        def mux3():
            if self.from_ijtag_interface.SELECT and self.from_ijtag_interface.CAPTURE:
                self.mux3_out.next = self.update_bit
            else:
                self.mux3_out.next = self.mux2_out

        @always_comb
        def mux4():
            if self.from_ijtag_interface.SELECT and self.from_ijtag_interface.UPDATE:
                self.mux4_out.next = self.cs_out
            else:
                self.mux4_out.next = self.update_bit

        @always(self.from_ijtag_interface.CLOCK.posedge)
        def captureFF():
            # print("Entering captureFF")
            self.cs_out.next = self.mux3_out

        @always(self.from_ijtag_interface.CLOCK.negedge)
        def updateFF():
            # print("Entering updateFF")
            if self.from_ijtag_interface.RESET == bool(0):
                self.update_bit.next = bool(0)
            else:
                self.update_bit.next = self.mux4_out

        @always_comb
        def sel():
            self.so.next = self.cs_out
            self.to_si.next = self.si
            self.to_ijtag_interface.CLOCK.next = self.from_ijtag_interface.CLOCK
            self.to_ijtag_interface.RESET.next = self.from_ijtag_interface.RESET
            if self.from_ijtag_interface.SELECT:
                if self.update_bit:
                    self.to_ijtag_interface.SELECT.next = self.from_ijtag_interface.SELECT
                else:
                    self.to_ijtag_interface.SELECT.next = bool(0)
                self.to_ijtag_interface.CAPTURE.next = self.from_ijtag_interface.CAPTURE
                self.to_ijtag_interface.SHIFT.next = self.from_ijtag_interface.SHIFT
                self.to_ijtag_interface.UPDATE.next = self.from_ijtag_interface.UPDATE
            else:
                self.to_ijtag_interface.SELECT.next = bool(0)
                self.to_ijtag_interface.CAPTURE.next = bool(0)
                self.to_ijtag_interface.SHIFT.next = bool(0)
                self.to_ijtag_interface.UPDATE.next = bool(0)

        if not monitor:
            return mux1, mux2, mux3, mux4, captureFF, updateFF, sel
        else:
            @instance
            def monitor_update_bit():
                print("\t\tsib_mux_pre({:s}): update_bit".format(self.path + self.name), self.update_bit)
                while 1:
                    yield self.update_bit
                    print("\t\tsib_mux_pre({:s}): update_bit".format(self.path + self.name), self.update_bit)

            @instance
            def monitor_si():
                print("\t\tsib_mux_pre({:s}): si".format(self.path + self.name), self.si)
                while 1:
                    yield self.si
                    print("\t\tsib_mux_pre({:s}): si".format(self.path + self.name), self.si)

            @instance
            def monitor_so():
                print("\t\tsib_mux_pre({:s}): so".format(self.path + self.name), self.so)
                while 1:
                    yield self.so
                    print("\t\tsib_mux_pre({:s}) so:".format(self.path + self.name), self.so)

            @instance
            def monitor_from_so():
                print("\t\tsib_mux_pre({:s}): from_so".format(self.path + self.name), self.from_so)
                while 1:
                    yield self.from_so
                    print("\t\tsib_mux_pre({:s}): from_so".format(self.path + self.name), self.from_so)

            @instance
            def monitor_to_si():
                print("\t\tsib_mux_pre({:s}): to_si".format(self.path + self.name), self.to_si)
                while 1:
                    yield self.to_si
                    print("\t\tsib_mux_pre({:s}) to_si:".format(self.path + self.name), self.to_si)

            @instance
            def monitor_from_ijtag_interface_capture():
                print("\t\tsib_mux_pre({:s}): from_ijtag_interface.CAPTURE".format(self.path + self.name),
                      self.from_ijtag_interface.CAPTURE)
                while 1:
                    yield self.from_ijtag_interface.CAPTURE
                    print("\t\tsib_mux_pre({:s}): from_ijtag_interface.CAPTURE".format(self.path + self.name),
                          self.from_ijtag_interface.CAPTURE)

            @instance
            def monitor_from_ijtag_interface_shift():
                print("\t\tsib_mux_pre({:s}): from_ijtag_interface.SHIFT".format(self.path + self.name),
                      self.from_ijtag_interface.SHIFT)
                while 1:
                    yield self.from_ijtag_interface.SHIFT
                    print("\t\tsib_mux_pre({:s}) from_ijtag_interface.SHIFT:".format(self.path + self.name),
                          self.from_ijtag_interface.SHIFT)

            @instance
            def monitor_from_ijtag_interface_update():
                print("\t\tsib_mux_pre({:s}): from_ijtag_interface.UPDATE".format(self.path + self.name),
                      self.from_ijtag_interface.UPDATE)
                while 1:
                    yield self.from_ijtag_interface.UPDATE
                    print("\t\tsib_mux_pre({:s}): from_ijtag_interface.UPDATE".format(self.path + self.name),
                          self.from_ijtag_interface.UPDATE)

            @instance
            def monitor_from_ijtag_interface_select():
                print("\t\tsib_mux_pre({:s}): from_ijtag_interface.SELECT".format(self.path + self.name),
                      self.from_ijtag_interface.SELECT)
                while 1:
                    yield self.from_ijtag_interface.SELECT
                    print("\t\tsib_mux_pre({:s}) from_ijtag_interface.SELECT:".format(self.path + self.name),
                          self.from_ijtag_interface.SELECT)

            @instance
            def monitor_from_ijtag_interface_reset():
                print("\t\tsib_mux_pre({:s}): from_ijtag_interface.RESET".format(self.path + self.name),
                      self.from_ijtag_interface.RESET)
                while 1:
                    yield self.from_ijtag_interface.RESET
                    print("\t\tsib_mux_pre({:s}) from_ijtag_interface.RESET:".format(self.path + self.name),
                          self.from_ijtag_interface.RESET)

            @instance
            def monitor_to_ijtag_interface_capture():
                print("\t\tsib_mux_pre({:s}): to_ijtag_interface.CAPTURE".format(self.path + self.name),
                      self.to_ijtag_interface.CAPTURE)
                while 1:
                    yield self.to_ijtag_interface.CAPTURE
                    print("\t\tsib_mux_pre({:s}): to_ijtag_interface.CAPTURE".format(self.path + self.name),
                          self.to_ijtag_interface.CAPTURE)

            @instance
            def monitor_to_ijtag_interface_shift():
                print("\t\tsib_mux_pre({:s}): to_ijtag_interface.SHIFT".format(self.path + self.name),
                      self.to_ijtag_interface.SHIFT)
                while 1:
                    yield self.to_ijtag_interface.SHIFT
                    print("\t\tsib_mux_pre({:s}) to_ijtag_interface.SHIFT:".format(self.path + self.name),
                          self.to_ijtag_interface.SHIFT)

            @instance
            def monitor_to_ijtag_interface_update():
                print("\t\tsib_mux_pre({:s}): to_ijtag_interface.UPDATE".format(self.path + self.name),
                      self.to_ijtag_interface.UPDATE)
                while 1:
                    yield self.to_ijtag_interface.UPDATE
                    print("\t\tsib_mux_pre({:s}): to_ijtag_interface.UPDATE".format(self.path + self.name),
                          self.to_ijtag_interface.UPDATE)

            @instance
            def monitor_to_ijtag_interface_select():
                print("\t\tsib_mux_pre({:s}): to_ijtag_interface.SELECT".format(self.path + self.name),
                      self.to_ijtag_interface.SELECT)
                while 1:
                    yield self.to_ijtag_interface.SELECT
                    print("\t\tsib_mux_pre({:s}) to_ijtag_interface.SELECT:".format(self.path + self.name),
                          self.to_ijtag_interface.SELECT)

            @instance
            def monitor_to_ijtag_interface_reset():
                print("\t\tsib_mux_pre({:s}): to_ijtag_interface.RESET".format(self.path + self.name),
                      self.to_ijtag_interface.RESET)
                while 1:
                    yield self.to_ijtag_interface.RESET
                    print("\t\tsib_mux_pre({:s}) to_ijtag_interface.RESET:".format(self.path + self.name),
                          self.to_ijtag_interface.RESET)

            @instance
            def monitor_mux1_out():
                print("\t\tsib_mux_pre({:s}): mux1_out".format(self.path + self.name),
                      self.mux1_out)
                while 1:
                    yield self.mux1_out
                    print("\t\tsib_mux_pre({:s}) mux1_out:".format(self.path + self.name),
                          self.mux1_out)

            @instance
            def monitor_mux2_out():
                print("\t\tsib_mux_pre({:s}): mux2_out".format(self.path + self.name),
                      self.mux2_out)
                while 1:
                    yield self.mux2_out
                    print("\t\tsib_mux_pre({:s}) mux2_out:".format(self.path + self.name),
                          self.mux2_out)

            @instance
            def monitor_mux3_out():
                print("\t\tsib_mux_pre({:s}): mux3_out".format(self.path + self.name),
                      self.mux3_out)
                while 1:
                    yield self.mux3_out
                    print("\t\tsib_mux_pre({:s}) mux3_out:".format(self.path + self.name),
                          self.mux3_out)

            @instance
            def monitor_mux4_out():
                print("\t\tsib_mux_pre({:s}): mux4_out".format(self.path + self.name),
                      self.mux4_out)
                while 1:
                    yield self.mux4_out
                    print("\t\tsib_mux_pre({:s}) mux4_out:".format(self.path + self.name),
                          self.mux4_out)

            @instance
            def monitor_cs_out():
                print("\t\tsib_mux_pre({:s}): cs_out".format(self.path + self.name),
                      self.cs_out)
                while 1:
                    yield self.cs_out
                    print("\t\tsib_mux_pre({:s}) cs_out:".format(self.path + self.name),
                          self.cs_out)

            return mux1, mux2, mux3, mux4, captureFF, updateFF, sel, \
                monitor_si, monitor_so, monitor_from_ijtag_interface_capture, monitor_from_ijtag_interface_shift, \
                monitor_from_ijtag_interface_update, monitor_from_ijtag_interface_select, \
                monitor_from_ijtag_interface_reset, monitor_to_ijtag_interface_capture, \
                monitor_to_ijtag_interface_shift, monitor_to_ijtag_interface_update, \
                monitor_to_ijtag_interface_select, monitor_to_ijtag_interface_reset, \
                monitor_update_bit, monitor_mux1_out, monitor_mux2_out, monitor_mux3_out, \
                monitor_mux4_out, monitor_cs_out

    @staticmethod
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

        sib_inst = sib_mux_pre('TOP', 'SIB0', si, from_ijtag_interface, so, to_si, to_ijtag_interface, from_so)

        sib_inst.toVerilog()
        sib_inst.toVHDL()

    @staticmethod
    @block
    def testbench(monitor=False):
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

        sib_inst = sib_mux_pre('TOP', 'SIB0', si, from_ijtag_interface, so, to_si, to_ijtag_interface, from_so)

        @always(delay(10))
        def clkgen():
            from_ijtag_interface.CLOCK.next = not from_ijtag_interface.CLOCK

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
            from_ijtag_interface.RESET.next = bool(0)
            yield delay(10)
            from_ijtag_interface.RESET.next = bool(1)
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
            assert(so == bool(0))
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
            si.next = L  # SIB data in  ############################################# SHIFT(0)
            yield from_ijtag_interface.CLOCK.posedge
            assert(so == bool(1))  # Value of SIB
            yield from_ijtag_interface.CLOCK.negedge
            # Write Shift second bit value
            from_ijtag_interface.CAPTURE.next = L
            from_ijtag_interface.SHIFT.next = H
            si.next = L  # loopbackFF data in  ###################################### SHIFT(0)
            yield from_ijtag_interface.CLOCK.posedge
            assert(so == bool(0))  # Value of loopbackFF
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

        return sib_inst.sib_mux_pre_rtl(monitor=monitor), clkgen, stimulus, loopbackFF


if __name__ == '__main__':
    tb = sib_mux_pre.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    sib_mux_pre.convert()
