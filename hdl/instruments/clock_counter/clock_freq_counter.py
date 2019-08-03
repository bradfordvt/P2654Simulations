"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Clock Frequency Counter
Based on the VHDL design at https://surf-vhdl.com/compute-frequency-clock/.
"""
from myhdl import *
import os
import os.path


class clock_freq_counter:
    def __init__(self, path, name, clk, reset_n, i_clk_test, o_clock_freq):
        """
        Clock Frequency Counter
        Variables and processes with prefix r1_ are with clk reference domain
        Variables and processes with prefix r2_ are with i_clk_test domain
        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logger (path instance)
        :param clk: Reference Clock
        :param reset_n: Reset signal to reset the logic
        :param i_clk_test: The clock to be tested
        :param o_clock_freq: Signal(intbv(0)[16:]) The count of ticks on i_clk_test
        """
        self.path = path
        self.name = name
        self.clk = clk
        self.reset_n = reset_n
        self.i_clk_test = i_clk_test
        self.o_clock_freq = o_clock_freq
        # CLOCK REFERENCE signal declaration
        self.r1_counter_ref = Signal(modbv(0)[13:])  # 12+1 bit: extra bit used for test counter control
        self.r1_counter_test_ena = Signal(bool(0))
        self.r1_counter_test_strobe = Signal(bool(0))
        self.r1_counter_test_rstb = Signal(bool(0))
        # CLOCK TEST signal declaration
        self.r2_counter_test = Signal(modbv(0)[16:])  # clock test can be up-to 16 times clock ref
        self.r2_counter_test_ena = Signal(bool(0))
        self.r2_counter_test_strobe = Signal(bool(0))
        self.r2_counter_test_rstb = Signal(bool(0))

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
        return self.clock_freq_counter_rtl(monitor=monitor)

    @block
    def clock_freq_counter_rtl(self, monitor=False):
        """
        The logic for the Clock Frequency Counter
        :return: The generator methods performing the logic decisions
        """
        @always(self.clk.posedge)
        def p_counter_ref():
            if self.reset_n == bool(0):
                self.r1_counter_ref.next = intbv(0)[13:]
                self.r1_counter_test_ena.next = bool(0)
                self.r1_counter_test_strobe.next = bool(0)
                self.r1_counter_test_rstb.next = bool(0)
            else:
                self.r1_counter_ref.next = self.r1_counter_ref + 1  # free running

                # use MSB to control test counter
                self.r1_counter_test_ena.next = not self.r1_counter_ref[12]

                # enable storing for 1024 clock cycle after 256 clock cycle
                if self.r1_counter_ref > 0x1100 and self.r1_counter_ref < 0x1500:
                    self.r1_counter_test_strobe.next = bool(1)
                else:
                    self.r1_counter_test_strobe.next = bool(0)

                # enable reset for 1024 clock cycle; after 1024 clock cycle from storing
                if self.r1_counter_ref > 0x1900 and self.r1_counter_ref < 0x1D00:
                    self.r1_counter_test_rstb.next = bool(0)
                else:
                    self.r1_counter_test_rstb.next = bool(1)

        @always(self.i_clk_test.posedge)
        def p_clk_test_resync():
            self.r2_counter_test_ena.next = self.r1_counter_test_ena
            self.r2_counter_test_strobe.next = self.r1_counter_test_strobe
            self.r2_counter_test_rstb.next = self.r1_counter_test_rstb

        @always(self.i_clk_test.posedge)
        def p_counter_test():
            if self.r2_counter_test_rstb == bool(0):
                self.r2_counter_test.next = intbv(0)[16:]
            else:
                if self.r2_counter_test_ena == bool(1):
                    self.r2_counter_test.next = self.r2_counter_test + 1

        @always(self.i_clk_test.posedge)
        def p_counter_test_out():
            if self.reset_n == bool(0):
                self.o_clock_freq.next = intbv(0xFFFF)[16:]
            else:
                if self.r2_counter_test_strobe == bool(1):
                    self.o_clock_freq.next = self.r2_counter_test

        if not monitor:
            return p_counter_ref, p_clk_test_resync, p_counter_test, p_counter_test_out
        else:
            @instance
            def monitor_clk():
                print("\t\tclock_freq_counter({:s}): clk".format(self.path + '.' + self.name), self.clk)
                while 1:
                    yield self.clk
                    print("\t\tclock_freq_counter({:s}): clk".format(self.path + '.' + self.name), self.clk)

            @instance
            def monitor_reset_n():
                print("\t\tclock_freq_counter({:s}): reset_n".format(self.path + '.' + self.name), self.reset_n)
                while 1:
                    yield self.reset_n
                    print("\t\tclock_freq_counter({:s}): reset_n".format(self.path + '.' + self.name), self.reset_n)

            @instance
            def monitor_i_clk_test():
                print("\t\tclock_freq_counter({:s}): i_clk_test".format(self.path + '.' + self.name), self.i_clk_test)
                while 1:
                    yield self.i_clk_test
                    print("\t\tclock_freq_counter({:s}): i_clk_test".format(self.path + '.' + self.name), self.i_clk_test)

            @instance
            def monitor_o_clock_freq():
                print("\t\tclock_freq_counter({:s}): o_clock_freq".format(self.path + '.' + self.name), self.o_clock_freq)
                while 1:
                    yield self.o_clock_freq
                    print("\t\tclock_freq_counter({:s}): o_clock_freq".format(self.path + '.' + self.name), self.o_clock_freq)

            @instance
            def monitor_r1_counter_ref():
                print("\t\tclock_freq_counter({:s}): r1_counter_ref".format(self.path + '.' + self.name), self.r1_counter_ref)
                while 1:
                    yield self.r1_counter_ref
                    print("\t\tclock_freq_counter({:s}): r1_counter_ref".format(self.path + '.' + self.name), self.r1_counter_ref)

            @instance
            def monitor_r1_counter_test_ena():
                print("\t\tclock_freq_counter({:s}): r1_counter_test_ena".format(self.path + '.' + self.name), self.r1_counter_test_ena)
                while 1:
                    yield self.r1_counter_test_ena
                    print("\t\tclock_freq_counter({:s}): r1_counter_test_ena".format(self.path + '.' + self.name), self.r1_counter_test_ena)

            @instance
            def monitor_r1_counter_test_strobe():
                print("\t\tclock_freq_counter({:s}): r1_counter_test_strobe".format(self.path + '.' + self.name), self.r1_counter_test_strobe)
                while 1:
                    yield self.r1_counter_test_strobe
                    print("\t\tclock_freq_counter({:s}): r1_counter_test_strobe".format(self.path + '.' + self.name), self.r1_counter_test_strobe)

            @instance
            def monitor_r1_counter_test_rstb():
                print("\t\tclock_freq_counter({:s}): r1_counter_test_rstb".format(self.path + '.' + self.name), self.r1_counter_test_rstb)
                while 1:
                    yield self.r1_counter_test_rstb
                    print("\t\tclock_freq_counter({:s}): r1_counter_test_rstb".format(self.path + '.' + self.name), self.r1_counter_test_rstb)

            @instance
            def monitor_r2_counter_test():
                print("\t\tclock_freq_counter({:s}): r2_counter_test".format(self.path + '.' + self.name), self.r2_counter_test)
                while 1:
                    yield self.r2_counter_test
                    print("\t\tclock_freq_counter({:s}): r2_counter_test".format(self.path + '.' + self.name), self.r2_counter_test)

            @instance
            def monitor_r2_counter_test_ena():
                print("\t\tclock_freq_counter({:s}): r2_counter_test_ena".format(self.path + '.' + self.name), self.r2_counter_test_ena)
                while 1:
                    yield self.r2_counter_test_ena
                    print("\t\tclock_freq_counter({:s}): r2_counter_test_ena".format(self.path + '.' + self.name), self.r2_counter_test_ena)

            @instance
            def monitor_r2_counter_test_strobe():
                print("\t\tclock_freq_counter({:s}): r2_counter_test_strobe".format(self.path + '.' + self.name), self.r2_counter_test_strobe)
                while 1:
                    yield self.r2_counter_test_strobe
                    print("\t\tclock_freq_counter({:s}): r2_counter_test_strobe".format(self.path + '.' + self.name), self.r2_counter_test_strobe)

            @instance
            def monitor_r2_counter_test_rstb():
                print("\t\tclock_freq_counter({:s}): r2_counter_test_rstb".format(self.path + '.' + self.name), self.r2_counter_test_rstb)
                while 1:
                    yield self.r2_counter_test_rstb
                    print("\t\tclock_freq_counter({:s}): r2_counter_test_rstb".format(self.path + '.' + self.name), self.r2_counter_test_rstb)

            return p_counter_ref, p_clk_test_resync, p_counter_test, p_counter_test_out,\
                monitor_clk, monitor_i_clk_test, monitor_o_clock_freq, monitor_r1_counter_ref,\
                monitor_r1_counter_test_ena, monitor_r1_counter_test_rstb, monitor_r1_counter_test_strobe,\
                monitor_r2_counter_test, monitor_r2_counter_test_ena, monitor_r2_counter_test_rstb,\
                monitor_r2_counter_test_strobe, monitor_reset_n

    @staticmethod
    def convert():
        """
        Convert the myHDL design into VHDL and Verilog
        :return:
        """
        clk = Signal(bool(0))
        reset_n = Signal(bool(1))
        o_clock_freq = Signal(modbv(0)[16:])
        i_clk_test = Signal(bool(0))

        cfc_inst = clock_freq_counter('TOP', 'CFC0', clk, reset_n, i_clk_test, o_clock_freq)

        cfc_inst.toVerilog()
        cfc_inst.toVHDL()

    @staticmethod
    @block
    def testbench(monitor=False):
        """
        Test bench interface for a quick test of the operation of the design
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """
        H = bool(1)
        L = bool(0)
        clk = Signal(bool(0))
        reset_n = Signal(bool(1))
        o_clock_freq = Signal(modbv(0)[16:])
        i_clk_test = Signal(bool(0))

        cfc_inst = clock_freq_counter('TOP', 'CFC0', clk, reset_n, i_clk_test, o_clock_freq)

        @always(delay(10))
        def clkgen():
            # 50 MHz clock, 20 nsec period
            clk.next = not clk

        @always(delay(100))
        def testclkgen():
            # 5 MHz clock, 200 nsec period
            i_clk_test.next = not i_clk_test

        @instance
        def stimulus():
            """
            Perform instruction decoding for various instructions
            :return:
            """
            # Reset the Clock Frequency Counter
            reset_n.next = bool(0)
            yield delay(10)
            reset_n.next = bool(1)
            yield delay(100000)
            print("o_clock_freq = ", o_clock_freq)
            assert(o_clock_freq == 0x019a)
            tfreq = (o_clock_freq/4096)*50
            print("measured frequency = {:f} MHz".format(tfreq))
            assert(int(tfreq) == 5)

            raise StopSimulation()

        return cfc_inst.clock_freq_counter_rtl(monitor=monitor), clkgen, testclkgen, stimulus


if __name__ == '__main__':
    tb = clock_freq_counter.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    clock_freq_counter.convert()
