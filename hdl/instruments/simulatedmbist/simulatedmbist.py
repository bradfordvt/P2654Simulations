"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

MBIST Simulated Instrument
Used to simulate a real MBIST instrument for the purposes of testing the IEEE 1687 or IEEE 1149.1-2013 networks

"""
from myhdl import *
import os
import os.path

period = 20  # clk frequency = 50 MHz

t_State = enum('START', 'IDLE', 'INITIALIZE', 'INITIALIZE_DELAY', 'TEST', 'TEST_DELAY', 'ANALYZE', 'ANALYZE_DELAY')
ACTIVE_LOW = 0
IDLE_POWER = Signal(intbv(5, min=0, max=101))
START_POWER = Signal(intbv(10, min=0, max=101))
INIT_POWER = Signal(intbv(30, min=0, max=101))
TEST_POWER = Signal(intbv(100, min=0, max=101))
ANALYZE_POWER = Signal(intbv(70, min=0, max=101))

IDLE_TEMP = Signal(intbv(5, min=0, max=101))
START_TEMP = Signal(intbv(10, min=0, max=101))
INIT_TEMP = Signal(intbv(20, min=0, max=101))
TEST_TEMP = Signal(intbv(100, min=0, max=101))
ANALYZE_TEMP = Signal(intbv(70, min=0, max=101))


def int_to_list(ival):
    """
    Convert an intbv into a list of boolean values
    :param ival: intbv value
    :return: A list of boolean values of the size of the intbv
    """
    blist = []
    binary = bin(ival)[2:]
    blen = len(binary)
    for i in range(blen):
        if binary[i] == 0:
            blist.append(bool(0))
        else:
            blist.append(bool(1))
    return blist


@block
def simulatedmbist(path, name, clock, reset_n, control_register, cr_latch, status_register, power_usage_register,
                   thermal_register, initialize_delay=10, test_delay=30, analyze_delay=20, monitor=False):
    """
    Constructor to create an instance of the MBIST Simulated Instrument
    :param path: Dot path of the parent of this instance
    :param name: String containing the instance name to be printed in diagnostic messages
    :param clock: Clock signal used to change state and tick the delay times for delay states
    :param reset_n: Reset signal for state machine. 0=Reset, 1=No reset
    :param control_register[0:7]: Parallel register to control the operation of the instrument
            Bit0: 1=Start the BIST operation, 0=NOP for status scans
            Bit1: 1=Stop the BIST operation and abort, 0=Do not abort the test
            Bit2: 1=Inject error during test_delay state, 0=Do not inject error during test_delay state
            Bit3: 1=Inject error during analyze_delay state, 0=Do not inject error during analyze_delay state
            Bit4: 1=Double the initialize_delay time to use at start, 0=Use the specified initialize_delay
            Bit5: 1=Double the test_delay time to use at start, 0=Use the specified test_delay
            Bit6: 1=Double the analyze_delay time to use at start, 0=Use the specified analyze_delay
            Bit7: Reserved (Defaults to 0)
    :param cr_latch: Latch trigger to update value of control_register
    :param status_register[0:7]: Parallel register to publish the status of the instrument operation
            Bit0: 1=Test passed, 0=Test failed
            Bit1: 1=MBIST test is running, 0=MBIST test is not running
            Bit2: 1=Test aborted due to unknown error, 0=Test did not abort
            Bit3: 1=Error during test state detected, 0=No error detected during test state
            Bit4: 1=Error during analyze state detected, 0=No error detected during analyze state
            Bit5: Reserved.  Added so status_register can be capture register and control_register as update
            Bit6: Reserved.  Added so status_register can be capture register and control_register as update
            Bit7: Reserved. (Defaults to 0)
    :param power_usage_register: Signal(intbv(0, min=0, max=101)) signal representing 0 - 100% power usage
            that changes over time depending on the operation being performed.  The power monitor would
            monitor this value and report how much total power in the system is being used.
    :param thermal_register: Signal(intbv(0, min=0, max=101)) signal representing 0 - 100% thermal usage
            that changes over time depending on the operation being performed.  The temperature monitor
            would monitor this value and report the temperature the system is producing.
    :param initialize_delay: Keyword argument to specify the number of clock ticks to spin in initialize state
    :param test_delay: Keyword argument to specify the number of clock ticks to spin in the test state
    :param analyze_delay: Keyword argument to specify the number of clock ticks to spin in the analyze state
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
    state = Signal(t_State.IDLE)
    id_count = Signal(intbv(0, min=0, max=initialize_delay*2 + 1))
    td_count = Signal(intbv(0, min=0, max=test_delay*2 + 1))
    ad_count = Signal(intbv(0, min=0, max=analyze_delay*2 + 1))
    power_usage_register.next = IDLE_POWER
    thermal_register.next = IDLE_TEMP
    internal_control_register = Signal(intbv(0)[8:])

    @always_seq(clock.posedge, reset=reset_n)
    def cr_process():
        if reset_n == ACTIVE_LOW:
            internal_control_register.next = intbv(0)[8:]
        else:
            if cr_latch:
                internal_control_register.next = control_register
            elif state == t_State.ANALYZE_DELAY:
                internal_control_register.next = intbv(0)[8:]
            elif internal_control_register[1] == bool(1):
                internal_control_register.next = intbv(0)[8:]

    @always_seq(clock.posedge, reset=reset_n)
    def state_machine():
        if reset_n == ACTIVE_LOW:
            status_register.next = intbv(0)[8:]
            # internal_control_register.next = intbv(0)[8:]
            id_count.next = 0
            td_count.next = 0
            ad_count.next = 0
            state.next = t_State.IDLE
            power_usage_register.next = IDLE_POWER
            thermal_register.next = IDLE_TEMP

        else:
            if state == t_State.IDLE:
                if internal_control_register[0] == bool(1):
                    # Control bit to start BIST has been set
                    status_register.next[0] = bool(0)
                    state.next = t_State.START
                    power_usage_register.next = START_POWER
                    thermal_register.next = START_TEMP

            elif state == t_State.START:
                if internal_control_register[1] == bool(1):  # Abort
                    status_register.next = intbv('00000100')
                    state.next = t_State.IDLE
                    power_usage_register.next = IDLE_POWER
                    thermal_register.next = IDLE_TEMP
                else:
                    state.next = t_State.INITIALIZE

            elif state == t_State.INITIALIZE:
                if internal_control_register[1] == bool(1):  # Abort
                    status_register.next = intbv('00000100')
                    state.next = t_State.IDLE
                    power_usage_register.next = IDLE_POWER
                    thermal_register.next = IDLE_TEMP
                else:
                    if internal_control_register[4] == bool(1):
                        id_count.next = initialize_delay + initialize_delay
                    else:
                        id_count.next = initialize_delay
                    state.next = t_State.INITIALIZE_DELAY
                    power_usage_register.next = INIT_POWER
                    thermal_register.next = INIT_TEMP

            elif state == t_State.INITIALIZE_DELAY:
                if internal_control_register[1] == bool(1):  # Abort
                    status_register.next = intbv('00000100')
                    state.next = t_State.IDLE
                    power_usage_register.next = IDLE_POWER
                    thermal_register.next = IDLE_TEMP
                else:
                    if id_count > 0:
                        id_count.next = id_count - 1
                    else:
                        state.next = t_State.TEST

            elif state == t_State.TEST:
                if internal_control_register[1] == bool(1):  # Abort
                    status_register.next = intbv('00000100')
                    state.next = t_State.IDLE
                    power_usage_register.next = IDLE_POWER
                    thermal_register.next = IDLE_TEMP
                else:
                    if internal_control_register[5] == bool(1):
                        td_count.next = test_delay + test_delay
                    else:
                        td_count.next = test_delay
                    state.next = t_State.TEST_DELAY
                    power_usage_register.next = TEST_POWER
                    thermal_register.next = TEST_TEMP

            elif state == t_State.TEST_DELAY:
                if internal_control_register[1] == bool(1):  # Abort
                    status_register.next = intbv('00000100')
                    state.next = t_State.IDLE
                    power_usage_register.next = IDLE_POWER
                    thermal_register.next = IDLE_TEMP
                else:
                    if td_count > 0:
                        if internal_control_register[2] == bool(1):
                            if td_count == 1:
                                # Introduce error from TEST_DELAY state
                                status_register.next = intbv('00001000')
                                state.next = t_State.IDLE
                                power_usage_register.next = IDLE_POWER
                                thermal_register.next = IDLE_TEMP
                            else:
                                td_count.next = td_count - 1
                        else:
                            td_count.next = td_count - 1
                    else:
                        state.next = t_State.ANALYZE

            elif state == t_State.ANALYZE:
                if internal_control_register[1] == bool(1):  # Abort
                    status_register.next = intbv('00000100')
                    state.next = t_State.IDLE
                    power_usage_register.next = IDLE_POWER
                    thermal_register.next = IDLE_TEMP
                else:
                    if internal_control_register[6] == bool(1):
                        ad_count.next = analyze_delay + analyze_delay
                    else:
                        ad_count.next = analyze_delay
                    state.next = t_State.ANALYZE_DELAY
                    power_usage_register.next = ANALYZE_POWER
                    thermal_register.next = ANALYZE_TEMP

            elif state == t_State.ANALYZE_DELAY:
                if internal_control_register[1] == bool(1):  # Abort
                    status_register.next = intbv('00000100')

                    state.next = t_State.IDLE
                    power_usage_register.next = IDLE_POWER
                    thermal_register.next = IDLE_TEMP
                else:
                    if ad_count > 0:
                        if internal_control_register[3] == bool(1):
                            if ad_count == 1:
                                # Introduce error from TEST_DELAY state
                                status_register.next = intbv('00010000')
                                state.next = t_State.IDLE
                                power_usage_register.next = IDLE_POWER
                                thermal_register.next = IDLE_TEMP
                            else:
                                ad_count.next = ad_count - 1
                        else:
                            ad_count.next = ad_count - 1
                    else:
                        status_register.next = intbv('00000001')
                        state.next = t_State.IDLE
                        power_usage_register.next = IDLE_POWER
                        thermal_register.next = IDLE_TEMP

            else:
                raise ValueError("Undefined state")

    if not monitor:
        return state_machine, cr_process
    else:
        @instance
        def monitor_power_usage():
            print("\t\tsimulatedmbist({:s}).power_usage_register:".format(path + '.' + name), power_usage_register)
            while 1:
                yield power_usage_register
                print("\t\tsimulatedmbist({:s}).power_usage_register:".format(path + '.' + name), power_usage_register)

        @instance
        def monitor_tempurature():
            print("\t\tsimulatedmbist({:s}).thermal_register:".format(path + '.' + name), thermal_register)
            while 1:
                yield thermal_register
                print("\t\tsimulatedmbist({:s}).thermal_register:".format(path + '.' + name), thermal_register)

        @instance
        def monitor_state():
            print("\t\tsimulatedmbist({:s}).state:".format(path + '.' + name), state)
            while 1:
                yield state
                print("\t\tsimulatedmbist({:s}).state:".format(path + '.' + name), state)

        @instance
        def monitor_reset_n():
            print("\t\tsimulatedmbist({:s}).reset_n:".format(path + '.' + name), reset_n)
            while 1:
                yield reset_n
                print("\t\tsimulatedmbist({:s}).reset_n:".format(path + '.' + name), reset_n)

        @instance
        def monitor_clock():
            print("\t\tsimulatedmbist({:s}).clock:".format(path + '.' + name), clock)
            while 1:
                yield clock
                print("\t\tsimulatedmbist({:s}).clock:".format(path + '.' + name), clock)

        @instance
        def monitor_internal_control_register():
            print("\t\tsimulatedmbist({:s}).internal_control_register:".format(path + '.' + name), internal_control_register)
            while 1:
                yield internal_control_register
                print("\t\tsimulatedmbist({:s}).internal_control_register:".format(path + '.' + name), internal_control_register)

        @instance
        def monitor_status_register():
            print("\t\tsimulatedmbist({:s}).status_register:".format(path + '.' + name), status_register)
            while 1:
                yield status_register
                print("\t\tsimulatedmbist({:s}).status_register:".format(path + '.' + name), status_register)

        return state_machine, monitor_reset_n, monitor_clock, monitor_internal_control_register, monitor_status_register,\
            monitor_state, monitor_power_usage, monitor_tempurature, cr_process


@block
def simulatedmbist_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    cr = Signal(intbv(0)[8:])
    sr = Signal(intbv(0)[8:])
    cr_latch = Signal(bool(0))
    clock = Signal(bool(0))
    reset_n = ResetSignal(1, 0, True)
    power_usage = Signal(intbv(0, min=0, max=101))
    thermal = Signal(intbv(0, min=0, max=101))

    mbist_inst = simulatedmbist('TOP', 'SMBIST0', clock, reset_n, cr, cr_latch, sr, power_usage, thermal,
                                initialize_delay=10, test_delay=40,
                                analyze_delay=30,
                                monitor=monitor)

    @instance
    def clkgen():
        while True:
            clock.next = not clock
            yield delay(period // 2)

    @instance
    def stimulus():
        """
        Not true IJTAG protocol, but used to exercise the state machine with the fewest cycles
        :return:
        """
        # Reset the instrument
        reset_n.next = bool(0)
        yield delay(10)
        reset_n.next = bool(1)
        yield delay(10)
        # Start the MBIST operation
        cr.next[0] = bool(1)
        cr_latch.next = bool(1)
        yield delay(10)
        cr_latch.next = bool(0)
        yield delay(10000)
        assert (sr[0] == bool(1))
        assert (sr[1] == bool(0))
        assert (sr[2] == bool(0))
        assert (sr[3] == bool(0))
        assert (sr[4] == bool(0))

        raise StopSimulation()

    return mbist_inst, clkgen, stimulus


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    cr = Signal(intbv(0)[8:])
    sr = Signal(intbv(0)[8:])
    cr_latch = Signal(bool(0))
    clock = Signal(bool(0))
    reset_n = ResetSignal(1, 0, True)
    power_usage = Signal(intbv(0, min=0, max=101))
    thermal = Signal(intbv(0, min=0, max=101))

    mbist_inst = simulatedmbist('TOP', 'SMBIST0', clock, reset_n, cr, cr_latch, sr, power_usage, thermal,
                                initialize_delay=10, test_delay=40,
                                analyze_delay=30,
                                monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    mbist_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="simulatedmbist")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    mbist_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="simulatedmbist")
    tb = simulatedmbist_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="simulatedmbist_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="simulatedmbist_tb")


def main():
    tb = simulatedmbist_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
