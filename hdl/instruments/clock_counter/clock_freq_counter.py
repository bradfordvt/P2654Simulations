"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Clock Frequency Counter
Based on the VHDL design at https://surf-vhdl.com/compute-frequency-clock/.
"""
from myhdl import *
import os
import os.path

period = 20  # clk frequency = 50 MHz


@block
def clock_freq_counter(path, name, clk, reset_n, i_clk_test, o_clock_freq, monitor=False):
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
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    # CLOCK REFERENCE signal declaration
    r1_counter_ref = Signal(modbv(0)[13:])  # 12+1 bit: extra bit used for test counter control
    r1_counter_test_ena = Signal(bool(0))
    r1_counter_test_strobe = Signal(bool(0))
    r1_counter_test_rstb = Signal(bool(0))
    # CLOCK TEST signal declaration
    r2_counter_test = Signal(modbv(0)[16:])  # clock test can be up-to 16 times clock ref
    r2_counter_test_ena = Signal(bool(0))
    r2_counter_test_strobe = Signal(bool(0))
    r2_counter_test_rstb = Signal(bool(0))

    @always(clk.posedge)
    def p_counter_ref():
        if reset_n == bool(0):
            r1_counter_ref.next = intbv(0)[13:]
            r1_counter_test_ena.next = bool(0)
            r1_counter_test_strobe.next = bool(0)
            r1_counter_test_rstb.next = bool(0)
        else:
            r1_counter_ref.next = r1_counter_ref + 1  # free running

            # use MSB to control test counter
            r1_counter_test_ena.next = not r1_counter_ref[12]

            # enable storing for 1024 clock cycle after 256 clock cycle
            if r1_counter_ref > 0x1100 and r1_counter_ref < 0x1500:
                r1_counter_test_strobe.next = bool(1)
            else:
                r1_counter_test_strobe.next = bool(0)

            # enable reset for 1024 clock cycle; after 1024 clock cycle from storing
            if r1_counter_ref > 0x1900 and r1_counter_ref < 0x1D00:
                r1_counter_test_rstb.next = bool(0)
            else:
                r1_counter_test_rstb.next = bool(1)

    @always(i_clk_test.posedge)
    def p_clk_test_resync():
        r2_counter_test_ena.next = r1_counter_test_ena
        r2_counter_test_strobe.next = r1_counter_test_strobe
        r2_counter_test_rstb.next = r1_counter_test_rstb

    @always(i_clk_test.posedge)
    def p_counter_test():
        if r2_counter_test_rstb == bool(0):
            r2_counter_test.next = intbv(0)[16:]
        else:
            if r2_counter_test_ena == bool(1):
                r2_counter_test.next = r2_counter_test + 1

    @always(i_clk_test.posedge)
    def p_counter_test_out():
        if reset_n == bool(0):
            o_clock_freq.next = intbv(0xFFFF)[16:]
        else:
            if r2_counter_test_strobe == bool(1):
                o_clock_freq.next = r2_counter_test

    if not monitor:
        return p_counter_ref, p_clk_test_resync, p_counter_test, p_counter_test_out
    else:
        @instance
        def monitor_clk():
            print("\t\tclock_freq_counter({:s}): clk".format(path + '.' + name), clk)
            while 1:
                yield clk
                print("\t\tclock_freq_counter({:s}): clk".format(path + '.' + name), clk)

        @instance
        def monitor_reset_n():
            print("\t\tclock_freq_counter({:s}): reset_n".format(path + '.' + name), reset_n)
            while 1:
                yield reset_n
                print("\t\tclock_freq_counter({:s}): reset_n".format(path + '.' + name), reset_n)

        @instance
        def monitor_i_clk_test():
            print("\t\tclock_freq_counter({:s}): i_clk_test".format(path + '.' + name), i_clk_test)
            while 1:
                yield i_clk_test
                print("\t\tclock_freq_counter({:s}): i_clk_test".format(path + '.' + name), i_clk_test)

        @instance
        def monitor_o_clock_freq():
            print("\t\tclock_freq_counter({:s}): o_clock_freq".format(path + '.' + name), o_clock_freq)
            while 1:
                yield o_clock_freq
                print("\t\tclock_freq_counter({:s}): o_clock_freq".format(path + '.' + name), o_clock_freq)

        @instance
        def monitor_r1_counter_ref():
            print("\t\tclock_freq_counter({:s}): r1_counter_ref".format(path + '.' + name), r1_counter_ref)
            while 1:
                yield r1_counter_ref
                print("\t\tclock_freq_counter({:s}): r1_counter_ref".format(path + '.' + name), r1_counter_ref)

        @instance
        def monitor_r1_counter_test_ena():
            print("\t\tclock_freq_counter({:s}): r1_counter_test_ena".format(path + '.' + name), r1_counter_test_ena)
            while 1:
                yield r1_counter_test_ena
                print("\t\tclock_freq_counter({:s}): r1_counter_test_ena".format(path + '.' + name), r1_counter_test_ena)

        @instance
        def monitor_r1_counter_test_strobe():
            print("\t\tclock_freq_counter({:s}): r1_counter_test_strobe".format(path + '.' + name), r1_counter_test_strobe)
            while 1:
                yield r1_counter_test_strobe
                print("\t\tclock_freq_counter({:s}): r1_counter_test_strobe".format(path + '.' + name), r1_counter_test_strobe)

        @instance
        def monitor_r1_counter_test_rstb():
            print("\t\tclock_freq_counter({:s}): r1_counter_test_rstb".format(path + '.' + name), r1_counter_test_rstb)
            while 1:
                yield r1_counter_test_rstb
                print("\t\tclock_freq_counter({:s}): r1_counter_test_rstb".format(path + '.' + name), r1_counter_test_rstb)

        @instance
        def monitor_r2_counter_test():
            print("\t\tclock_freq_counter({:s}): r2_counter_test".format(path + '.' + name), r2_counter_test)
            while 1:
                yield r2_counter_test
                print("\t\tclock_freq_counter({:s}): r2_counter_test".format(path + '.' + name), r2_counter_test)

        @instance
        def monitor_r2_counter_test_ena():
            print("\t\tclock_freq_counter({:s}): r2_counter_test_ena".format(path + '.' + name), r2_counter_test_ena)
            while 1:
                yield r2_counter_test_ena
                print("\t\tclock_freq_counter({:s}): r2_counter_test_ena".format(path + '.' + name), r2_counter_test_ena)

        @instance
        def monitor_r2_counter_test_strobe():
            print("\t\tclock_freq_counter({:s}): r2_counter_test_strobe".format(path + '.' + name), r2_counter_test_strobe)
            while 1:
                yield r2_counter_test_strobe
                print("\t\tclock_freq_counter({:s}): r2_counter_test_strobe".format(path + '.' + name), r2_counter_test_strobe)

        @instance
        def monitor_r2_counter_test_rstb():
            print("\t\tclock_freq_counter({:s}): r2_counter_test_rstb".format(path + '.' + name), r2_counter_test_rstb)
            while 1:
                yield r2_counter_test_rstb
                print("\t\tclock_freq_counter({:s}): r2_counter_test_rstb".format(path + '.' + name), r2_counter_test_rstb)

        return p_counter_ref, p_clk_test_resync, p_counter_test, p_counter_test_out,\
            monitor_clk, monitor_i_clk_test, monitor_o_clock_freq, monitor_r1_counter_ref,\
            monitor_r1_counter_test_ena, monitor_r1_counter_test_rstb, monitor_r1_counter_test_strobe,\
            monitor_r2_counter_test, monitor_r2_counter_test_ena, monitor_r2_counter_test_rstb,\
            monitor_r2_counter_test_strobe, monitor_reset_n


@block
def clock_freq_counter_tb(monitor=False):
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

    cfc_inst = clock_freq_counter('TOP', 'CFC0', clk, reset_n, i_clk_test, o_clock_freq, monitor=monitor)

    @instance
    def clkgen():
        while True:
            clk.next = not clk
            yield delay(period // 2)

    @instance
    def testclkgen():
        while True:
            # 5 MHz clock, 200 nsec period
            i_clk_test.next = not i_clk_test
            yield delay(100)

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
        # print("o_clock_freq = ", o_clock_freq)
        assert(o_clock_freq == 0x0199)
        # tfreq = (o_clock_freq/4096)*50
        tfreq = (o_clock_freq * 5000) >> 12
        # print("measured frequency = {:f} MHz".format(tfreq/100))
        assert(490 < tfreq and tfreq < 510)

        raise StopSimulation()

    return cfc_inst, clkgen, testclkgen, stimulus


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

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    cfc_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="clock_freq_counter")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    cfc_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="clock_freq_counter")
    tb = clock_freq_counter_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="clock_freq_counter_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="clock_freq_counter_tb")


def main():
    tb = clock_freq_counter_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
