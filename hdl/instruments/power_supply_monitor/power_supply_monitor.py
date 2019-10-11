"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Power Supply Monitor
Simulated instrument to monitor power in the Rearick Use Case model.
"""
from myhdl import *
from hdl.instruments.noise_maker.noise_maker import MAX_STAGES, MAX_TOGGLES
import os
import os.path

period = 20  # clk frequency = 50 MHz


@block
def power_supply_monitor(path, name, reference, delta, fast_ck, over, under,
                         noise, pu_mbist1, pu_mbist2, pu_mbist3, pu_mbist4, pu_mbist5,
                         noise_flag, monitor=False):
    """
    Instrument to monitor the power supply stability over time to determine of the voltage is in range, over range,
    or under range.  Normal operating conditions is where under == 0 and over == 0.
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param reference: Reference value of what the power supply voltage should be as a Signal(intbv(0)[16:]) type.
                        This signal is to be set by the user via an instrument register.
                        Setting the reference value to zero (0) will reset the under and over signals.
    :param delta: The amount of mV variance allowed around the voltage reference as a Signal(intbv(0)[8:]) type.
                        This signal is to be set by the user via an instrument register.
    :param fast_ck: Sampling clock for when to sample the voltage value of VDD. Signal(bool(0)) type.
    :param over: Signal to indicate the monitor detected the voltage exceeded the delta setting. Signal(bool(0)) type.
    :param under: Signal to indicate the monitor detected the voltage fell below the delta setting.
                    Signal(bool(0)) type.
    :param noise: Signal input from noise_maker for clock noise injected into the power supply VDD.
                    Signal(intbv(0, min=0, max=(MAX_TOGGLES * MAX_STAGES)) type.
    :param pu_mbist1: Power Usage value coming from the mbist1 instrument. Signal(intbv(0, min=0, max=101)) type.
    :param pu_mbist2: Power Usage value coming from the mbist2 instrument. Signal(intbv(0, min=0, max=101)) type.
    :param pu_mbist3: Power Usage value coming from the mbist3 instrument. Signal(intbv(0, min=0, max=101)) type.
    :param pu_mbist4: Power Usage value coming from the mbist4 instrument. Signal(intbv(0, min=0, max=101)) type.
    :param pu_mbist5: Power Usage value coming from the mbist5 instrument. Signal(intbv(0, min=0, max=101)) type.
    :param noise_flag: 0=Disable noise influence. 1=Enable noise influence. Signal(bool(1)) type.
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: list of generators for the power_supply_monitor logic for simulation.
    """
    VDD = Signal(intbv(48000)[16:])  # voltage value in milli-volts simulating the power supply voltage being monitored
    noise_counts = Signal(intbv(0)[18:])  # Count of number of noise pulses arrived per fast_ck pulse to identify
    # load on the power supply from noise affecting delta value from reference.
    noise_reset = Signal(bool(0))  # Reset the noise counter after measuring count per fast_ck pulse
    noise_min = Signal(intbv(0)[16:])  # Intermediate value of minimum voltage detected due to noise biasing
    noise_max = Signal(intbv(0)[16:])  # Intermediate value of maximum voltage detected due to noise biasing
    noise_over = Signal(bool(0))  # Intermediate value of over voltage condition due to noise
    noise_under = Signal(bool(0))  # Intermediate value of under voltage condition due to noise
    mbist_over = Signal(bool(0))  # Intermediate value of over voltage condition due to power usage load by mbist instruments
    mbist_under = Signal(bool(0))  # Intermediate value of under voltage condition due to power usage load by mbist instruments
    rms_equal_to_dc = (707 * MAX_TOGGLES * MAX_STAGES) // 1000

    @always(fast_ck.posedge)
    def fast_ck_detect():
        if noise_reset:
            noise_max.next = 0
            noise_min.next = 0
        else:
            # Measure noise and calculate the RMS value based on noise influence
            # print("noise = ", noise, "rms_equal_to_dc = ", rms_equal_to_dc)
            if noise > rms_equal_to_dc:
                # AC RMS now over DC value, so use this to simulate an over voltage condition
                noise_max.next = VDD + noise
                noise_min.next = VDD
            else:
                noise_min.next = VDD - noise
                noise_max.next = VDD

    @always_comb
    def noise_bounds_check():
        if noise_max > VDD + (delta >> 1):
            noise_over.next = bool(1)
        else:
            noise_over.next = bool(0)
        if noise_min < VDD - (delta >> 1) and noise_min != 0:
            noise_under.next = bool(1)
        else:
            noise_under.next = bool(0)

    @always_comb
    def noise_reset_cond():
        if reference == 0:
            noise_reset.next = bool(1)
        else:
            noise_reset.next = bool(0)

    @always_comb
    def over_cond():
        if noise_over or mbist_over:
            over.next = bool(1)
        else:
            over.next = bool(0)

    @always_comb
    def under_cond():
        if noise_under or mbist_under:
            under.next = bool(1)
        else:
            under.next = bool(0)

    @always_comb
    def mbist_cond():
        # Assume 70% load on supply is optimal.
        # If greater than this value, it will cause voltage drop due to over current situation from too much load.
        if (pu_mbist1 + pu_mbist2 + pu_mbist3 + pu_mbist4 + pu_mbist5) // 5 > 70:
            mbist_under.next = bool(1)
        else:
            mbist_under.next = bool(0)

    if monitor == False:
        return fast_ck_detect, noise_bounds_check, noise_reset_cond, over_cond, under_cond, mbist_cond
    else:
        @instance
        def monitor_fast_ck():
            print("\t\tpower_supply_monitor({:s}): fast_ck".format(path + '.' + name), fast_ck)
            while 1:
                yield fast_ck
                print("\t\tpower_supply_monitor({:s}): fast_ck".format(path + '.' + name), fast_ck)

        @instance
        def monitor_over():
            print("\t\tpower_supply_monitor({:s}): over".format(path + '.' + name), over)
            while 1:
                yield over
                print("\t\tpower_supply_monitor({:s}): over".format(path + '.' + name), over)

        @instance
        def monitor_under():
            print("\t\tpower_supply_monitor({:s}): under".format(path + '.' + name), under)
            while 1:
                yield under
                print("\t\tpower_supply_monitor({:s}): under".format(path + '.' + name), under)

        @instance
        def monitor_noise_over():
            print("\t\tpower_supply_monitor({:s}): noise_over".format(path + '.' + name), noise_over)
            while 1:
                yield noise_over
                print("\t\tpower_supply_monitor({:s}): noise_over".format(path + '.' + name), noise_over)

        @instance
        def monitor_noise_under():
            print("\t\tpower_supply_monitor({:s}): noise_under".format(path + '.' + name), noise_under)
            while 1:
                yield noise_under
                print("\t\tpower_supply_monitor({:s}): noise_under".format(path + '.' + name), noise_under)

        @instance
        def monitor_mbist_under():
            print("\t\tpower_supply_monitor({:s}): mbist_under".format(path + '.' + name), mbist_under)
            while 1:
                yield mbist_under
                print("\t\tpower_supply_monitor({:s}): mbist_under".format(path + '.' + name), mbist_under)

        @instance
        def monitor_noise_reset():
            print("\t\tpower_supply_monitor({:s}): noise_reset".format(path + '.' + name), noise_reset)
            while 1:
                yield noise_reset
                print("\t\tpower_supply_monitor({:s}): noise_reset".format(path + '.' + name), noise_reset)

        @instance
        def monitor_VDD():
            print("\t\tpower_supply_monitor({:s}): VDD".format(path + '.' + name), VDD)
            while 1:
                yield VDD
                print("\t\tpower_supply_monitor({:s}): VDD".format(path + '.' + name), VDD)

        @instance
        def monitor_noise():
            print("\t\tpower_supply_monitor({:s}): noise".format(path + '.' + name), noise)
            while 1:
                yield noise
                print("\t\tpower_supply_monitor({:s}): noise".format(path + '.' + name), noise)

        @instance
        def monitor_noise_min():
            print("\t\tpower_supply_monitor({:s}): noise_min".format(path + '.' + name), noise_min)
            while 1:
                yield noise_min
                print("\t\tpower_supply_monitor({:s}): noise_min".format(path + '.' + name), noise_min)

        @instance
        def monitor_noise_max():
            print("\t\tpower_supply_monitor({:s}): noise_max".format(path + '.' + name), noise_max)
            while 1:
                yield noise_max
                print("\t\tpower_supply_monitor({:s}): noise_max".format(path + '.' + name), noise_max)

        @instance
        def monitor_reference():
            print("\t\tpower_supply_monitor({:s}): reference".format(path + '.' + name), reference)
            while 1:
                yield reference
                print("\t\tpower_supply_monitor({:s}): reference".format(path + '.' + name), reference)

        @instance
        def monitor_delta():
            print("\t\tpower_supply_monitor({:s}): delta".format(path + '.' + name), delta)
            while 1:
                yield delta
                print("\t\tpower_supply_monitor({:s}): delta".format(path + '.' + name), delta)

        @instance
        def monitor_pu_mbist1():
            print("\t\tpower_supply_monitor({:s}): pu_mbist1".format(path + '.' + name), pu_mbist1)
            while 1:
                yield pu_mbist1
                print("\t\tpower_supply_monitor({:s}): pu_mbist1".format(path + '.' + name), pu_mbist1)

        @instance
        def monitor_pu_mbist2():
            print("\t\tpower_supply_monitor({:s}): pu_mbist2".format(path + '.' + name), pu_mbist2)
            while 1:
                yield pu_mbist2
                print("\t\tpower_supply_monitor({:s}): pu_mbist2".format(path + '.' + name), pu_mbist2)

        @instance
        def monitor_pu_mbist3():
            print("\t\tpower_supply_monitor({:s}): pu_mbist3".format(path + '.' + name), pu_mbist3)
            while 1:
                yield pu_mbist3
                print("\t\tpower_supply_monitor({:s}): pu_mbist3".format(path + '.' + name), pu_mbist3)

        @instance
        def monitor_pu_mbist4():
            print("\t\tpower_supply_monitor({:s}): pu_mbist4".format(path + '.' + name), pu_mbist4)
            while 1:
                yield pu_mbist4
                print("\t\tpower_supply_monitor({:s}): pu_mbist4".format(path + '.' + name), pu_mbist4)

        @instance
        def monitor_pu_mbist5():
            print("\t\tpower_supply_monitor({:s}): pu_mbist5".format(path + '.' + name), pu_mbist5)
            while 1:
                yield pu_mbist5
                print("\t\tpower_supply_monitor({:s}): pu_mbist5".format(path + '.' + name), pu_mbist5)

        return fast_ck_detect, noise_bounds_check, noise_reset_cond, over_cond, under_cond, mbist_cond, \
               monitor_over, monitor_under, monitor_mbist_under, monitor_noise_over, \
               monitor_noise_under, monitor_noise_reset, monitor_VDD, monitor_noise_min, monitor_noise_max, \
               monitor_reference, monitor_delta, monitor_pu_mbist1, monitor_pu_mbist2, monitor_pu_mbist3, \
               monitor_pu_mbist4, monitor_pu_mbist5, \
               monitor_noise
               # monitor_fast_ck

@block
def power_supply_monitor_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    fast_ck = Signal(bool(0))
    over = Signal(bool(0))
    under = Signal(bool(0))
    noise_flag = Signal(bool(1))
    noise = Signal(intbv(0, min=0, max=(MAX_STAGES * MAX_TOGGLES)))
    pu_mbist1 = Signal(intbv(0, min=0, max=101))
    pu_mbist2 = Signal(intbv(0, min=0, max=101))
    pu_mbist3 = Signal(intbv(0, min=0, max=101))
    pu_mbist4 = Signal(intbv(0, min=0, max=101))
    pu_mbist5 = Signal(intbv(0, min=0, max=101))
    reference = Signal(intbv(48000)[16:])
    delta = Signal(intbv(0)[8:])

    psm_inst = power_supply_monitor('TOP', 'PSM00', reference, delta, fast_ck, over, under,
                                    noise, pu_mbist1, pu_mbist2, pu_mbist3, pu_mbist4, pu_mbist5,
                                    noise_flag, monitor=monitor)

    @instance
    def clkgen():
        while True:
            fast_ck.next = not fast_ck
            yield delay(period // 2)

    @instance
    def stimulus():
        """
        Perform instruction decoding for various instructions
        :return:
        """
        assert(under == bool(0))
        assert(over == bool(0))
        pu_mbist1.next = 100
        pu_mbist2.next = 100
        pu_mbist3.next = 100
        pu_mbist4.next = 100
        pu_mbist5.next = 100
        yield delay(10)
        assert(under == bool(1))
        pu_mbist1.next = 100
        pu_mbist2.next = 100
        pu_mbist3.next = 100
        pu_mbist4.next = 0
        pu_mbist5.next = 0
        yield delay(10)
        assert(under == bool(0))
        noise_flag.next = bool(1)
        for toggles in range(MAX_TOGGLES):
            for stages in range(MAX_STAGES):
                d = 10
                while d < 100:
                    noise.next = (toggles * stages)
                    delta.next = d
                    yield fast_ck.posedge
                    print("toggles = ", toggles, ", stages = ", stages, ", over = ", over, ", under = ", under)
                    d += 10

        raise StopSimulation()

    return psm_inst, clkgen, stimulus


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    fast_ck = Signal(bool(0))
    over = Signal(bool(0))
    under = Signal(bool(0))
    noise = Signal(bool(0))
    noise_flag = Signal(bool(1))
    pu_mbist1 = Signal(intbv(0, min=0, max=101))
    pu_mbist2 = Signal(intbv(0, min=0, max=101))
    pu_mbist3 = Signal(intbv(0, min=0, max=101))
    pu_mbist4 = Signal(intbv(0, min=0, max=101))
    pu_mbist5 = Signal(intbv(0, min=0, max=101))
    reference = Signal(intbv(48000)[16:])
    delta = Signal(intbv(0)[8:])

    psm_inst = power_supply_monitor('TOP', 'PSM00', reference, delta, fast_ck, over, under,
                                    noise, pu_mbist1, pu_mbist2, pu_mbist3, pu_mbist4, pu_mbist5,
                                    noise_flag, monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    psm_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="power_supply_monitor")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    psm_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="power_supply_monitor")
    tb = power_supply_monitor_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="power_supply_monitor_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="power_supply_monitor_tb")


def main():
    tb = power_supply_monitor_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
