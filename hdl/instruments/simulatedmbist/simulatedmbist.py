"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

MBIST Simulated Instrument
Used to simulate a real MBIST instrument for the purposes of testing the IEEE 1687 or IEEE 1149.1-2013 networks

"""
from myhdl import *
import os
import os.path

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


class simulatedmbist:
    """
    Class structure implementing the RTL for the instrument.
    """
    def __init__(self, name, clock, reset_n, control_register, status_register, power_usage_register,
                 thermal_register, initialize_delay=10, test_delay=30, analyze_delay=20):
        """
        Constructor to create an instance of the MBIST Simulated Instrument
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
        :param status_register[0:7]: Parallel register to publish the status of the instrument operation
                Bit0: 1=Test passed, 0=Test failed
                Bit1: 1=MBIST test is running, 0=MBIST test is not running
                Bit2: 1=Test aborted due to unknown error, 0=Test did not abort
                Bit3: 1=Error during test state detected, 0=No error detected during test state
                Bit4: 1=Error during analyze state detected, 0=No error detected during analyze state
                Bit5: Reserved.  Added so status_register can be capture register and control_register as update
                Bit6: Reserved.  Added so status_register can be capture register and control_register as update
        :param power_usage_register: Signal(intbv(0, min=0, max=101)) signal representing 0 - 100% power usage
                that changes over time depending on the operation being performed.  The power monitor would
                monitor this value and report how much total power in the system is being used.
        :param thermal_register: Signal(intbv(0, min=0, max=101)) signal representing 0 - 100% thermal usage
                that changes over time depending on the operation being performed.  The temperature monitor
                would monitor this value and report the temperature the system is producing.
        :param initialize_delay: Keyword argument to specify the number of clock ticks to spin in initialize state
        :param test_delay: Keyword argument to specify the number of clock ticks to spin in the test state
        :param analyze_delay: Keyword argument to specify the number of clock ticks to spin in the analyze state
        """
        self.name = name
        self.initialize_delay = initialize_delay
        self.test_delay = test_delay
        self.analyze_delay = analyze_delay
        self.state = Signal(t_State.IDLE)
        self.reset_n = reset_n
        self.clock = clock
        self.control_register = control_register
        self.status_register = status_register
        # self.__set_status_register(intbv('00000'))
        # self.__set_control_register(intbv('000000'))
        self.power_usage_register = power_usage_register
        self.thermal_register = thermal_register
        self.id_count = Signal(intbv(0, min=0, max=self.initialize_delay + 1))
        self.td_count = Signal(intbv(0, min=0, max=self.test_delay + 1))
        self.ad_count = Signal(intbv(0, min=0, max=self.analyze_delay + 1))
        self.power_usage_register.next = IDLE_POWER
        self.thermal_register.next = IDLE_TEMP
        
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
        return self.simulatedmbist_rtl(monitor=monitor)

    @block
    def simulatedmbist_rtl(self, monitor=False):
        """
        Logic to implement the MBIST instrument
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """
        @always_seq(self.clock.posedge, reset=self.reset_n)
        def state_machine():
            if self.reset_n == ACTIVE_LOW:
                # self.__set_status_register(intbv('00000'))
                # self.__set_control_register(intbv('000000'))
                self.status_register[0].next = bool(0)
                self.status_register[1].next = bool(0)
                self.status_register[2].next = bool(0)
                self.status_register[3].next = bool(0)
                self.status_register[4].next = bool(0)
                self.status_register[5].next = bool(0)
                self.status_register[6].next = bool(0)
                self.control_register[0].next = bool(0)
                self.control_register[1].next = bool(0)
                self.control_register[2].next = bool(0)
                self.control_register[3].next = bool(0)
                self.control_register[4].next = bool(0)
                self.control_register[5].next = bool(0)
                self.control_register[6].next = bool(0)
                self.id_count.next = 0
                self.td_count.next = 0
                self.ad_count.next = 0
                self.state.next = t_State.IDLE
                self.power_usage_register.next = IDLE_POWER
                self.thermal_register.next = IDLE_TEMP

            else:
                if self.state == t_State.IDLE:
                    if self.control_register[0] == bool(1):
                        # Control bit to start BIST has been set
                        self.status_register[0].next = bool(0)
                        self.state.next = t_State.START
                        self.power_usage_register.next = START_POWER
                        self.thermal_register.next = START_TEMP

                elif self.state == t_State.START:
                    if self.control_register[1] == bool(1):  # Abort
                        # self.__set_status_register(intbv('00100'))
                        # self.__set_control_register(intbv('000000'))
                        self.status_register[0].next = bool(0)
                        self.status_register[1].next = bool(0)
                        self.status_register[2].next = bool(1)
                        self.status_register[3].next = bool(0)
                        self.status_register[4].next = bool(0)
                        self.status_register[5].next = bool(0)
                        self.status_register[6].next = bool(0)
                        self.control_register[0].next = bool(0)
                        self.control_register[1].next = bool(0)
                        self.control_register[2].next = bool(0)
                        self.control_register[3].next = bool(0)
                        self.control_register[4].next = bool(0)
                        self.control_register[5].next = bool(0)
                        self.control_register[6].next = bool(0)
                        self.state.next = t_State.IDLE
                        self.power_usage_register.next = IDLE_POWER
                        self.thermal_register.next = IDLE_TEMP
                    else:
                        self.state.next = t_State.INITIALIZE
                        # Turn off control start bit now that BIST started
                        self.control_register[0].next = bool(0)

                elif self.state == t_State.INITIALIZE:
                    if self.control_register[1] == bool(1):  # Abort
                        # self.__set_status_register(intbv('00100'))
                        # self.__set_control_register(intbv('000000'))
                        self.status_register[0].next = bool(0)
                        self.status_register[1].next = bool(0)
                        self.status_register[2].next = bool(1)
                        self.status_register[3].next = bool(0)
                        self.status_register[4].next = bool(0)
                        self.status_register[5].next = bool(0)
                        self.status_register[6].next = bool(0)
                        self.control_register[0].next = bool(0)
                        self.control_register[1].next = bool(0)
                        self.control_register[2].next = bool(0)
                        self.control_register[3].next = bool(0)
                        self.control_register[4].next = bool(0)
                        self.control_register[5].next = bool(0)
                        self.control_register[6].next = bool(0)
                        self.state.next = t_State.IDLE
                        self.power_usage_register.next = IDLE_POWER
                        self.thermal_register.next = IDLE_TEMP
                    else:
                        if self.control_register[4] == bool(1):
                            self.id_count.next = self.initialize_delay + self.initialize_delay
                        else:
                            self.id_count.next = self.initialize_delay
                        self.state.next = t_State.INITIALIZE_DELAY
                        self.power_usage_register.next = INIT_POWER
                        self.thermal_register.next = INIT_TEMP

                elif self.state == t_State.INITIALIZE_DELAY:
                    if self.control_register[1] == bool(1):  # Abort
                        # self.__set_status_register(intbv('00100'))
                        # self.__set_control_register(intbv('000000'))
                        self.status_register[0].next = bool(0)
                        self.status_register[1].next = bool(0)
                        self.status_register[2].next = bool(1)
                        self.status_register[3].next = bool(0)
                        self.status_register[4].next = bool(0)
                        self.status_register[5].next = bool(0)
                        self.status_register[6].next = bool(0)
                        self.control_register[0].next = bool(0)
                        self.control_register[1].next = bool(0)
                        self.control_register[2].next = bool(0)
                        self.control_register[3].next = bool(0)
                        self.control_register[4].next = bool(0)
                        self.control_register[5].next = bool(0)
                        self.control_register[6].next = bool(0)
                        self.state.next = t_State.IDLE
                        self.power_usage_register.next = IDLE_POWER
                        self.thermal_register.next = IDLE_TEMP
                    else:
                        if self.id_count > 0:
                            self.id_count.next = self.id_count - 1
                        else:
                            self.state.next = t_State.TEST

                elif self.state == t_State.TEST:
                    if self.control_register[1] == bool(1):  # Abort
                        # self.__set_status_register(intbv('00100'))
                        # self.__set_control_register(intbv('000000'))
                        self.status_register[0].next = bool(0)
                        self.status_register[1].next = bool(0)
                        self.status_register[2].next = bool(1)
                        self.status_register[3].next = bool(0)
                        self.status_register[4].next = bool(0)
                        self.status_register[5].next = bool(0)
                        self.status_register[6].next = bool(0)
                        self.control_register[0].next = bool(0)
                        self.control_register[1].next = bool(0)
                        self.control_register[2].next = bool(0)
                        self.control_register[3].next = bool(0)
                        self.control_register[4].next = bool(0)
                        self.control_register[5].next = bool(0)
                        self.control_register[6].next = bool(0)
                        self.state.next = t_State.IDLE
                        self.power_usage_register.next = IDLE_POWER
                        self.thermal_register.next = IDLE_TEMP
                    else:
                        if self.control_register[5] == bool(1):
                            self.td_count.next = self.test_delay + self.test_delay
                        else:
                            self.td_count.next = self.test_delay
                        self.state.next = t_State.TEST_DELAY
                        self.power_usage_register.next = TEST_POWER
                        self.thermal_register.next = TEST_TEMP

                elif self.state == t_State.TEST_DELAY:
                    if self.control_register[1] == bool(1):  # Abort
                        # self.__set_status_register(intbv('00100'))
                        # self.__set_control_register(intbv('000000'))
                        self.status_register[0].next = bool(0)
                        self.status_register[1].next = bool(0)
                        self.status_register[2].next = bool(1)
                        self.status_register[3].next = bool(0)
                        self.status_register[4].next = bool(0)
                        self.status_register[5].next = bool(0)
                        self.status_register[6].next = bool(0)
                        self.control_register[0].next = bool(0)
                        self.control_register[1].next = bool(0)
                        self.control_register[2].next = bool(0)
                        self.control_register[3].next = bool(0)
                        self.control_register[4].next = bool(0)
                        self.control_register[5].next = bool(0)
                        self.control_register[6].next = bool(0)
                        self.state.next = t_State.IDLE
                        self.power_usage_register.next = IDLE_POWER
                        self.thermal_register.next = IDLE_TEMP
                    else:
                        if self.td_count > 0:
                            if self.control_register[2] == bool(1):
                                if self.td_count == 1:
                                    # Introduce error from TEST_DELAY state
                                    # self.__set_status_register(intbv('00010'))
                                    self.status_register[0].next = bool(0)
                                    self.status_register[1].next = bool(0)
                                    self.status_register[2].next = bool(0)
                                    self.status_register[3].next = bool(1)
                                    self.status_register[4].next = bool(0)
                                    self.status_register[5].next = bool(0)
                                    self.status_register[6].next = bool(0)
                                    self.state.next = t_State.IDLE
                                    self.power_usage_register.next = IDLE_POWER
                                    self.thermal_register.next = IDLE_TEMP
                                else:
                                    self.td_count.next = self.td_count - 1
                            else:
                                self.td_count.next = self.td_count - 1
                        else:
                            self.state.next = t_State.ANALYZE

                elif self.state == t_State.ANALYZE:
                    if self.control_register[1] == bool(1):  # Abort
                        # self.__set_status_register(intbv('00100'))
                        # self.__set_control_register(intbv('000000'))
                        self.status_register[0].next = bool(0)
                        self.status_register[1].next = bool(0)
                        self.status_register[2].next = bool(1)
                        self.status_register[3].next = bool(0)
                        self.status_register[4].next = bool(0)
                        self.status_register[5].next = bool(0)
                        self.status_register[6].next = bool(0)
                        self.control_register[0].next = bool(0)
                        self.control_register[1].next = bool(0)
                        self.control_register[2].next = bool(0)
                        self.control_register[3].next = bool(0)
                        self.control_register[4].next = bool(0)
                        self.control_register[5].next = bool(0)
                        self.control_register[6].next = bool(0)
                        self.state.next = t_State.IDLE
                        self.power_usage_register.next = IDLE_POWER
                        self.thermal_register.next = IDLE_TEMP
                    else:
                        if self.control_register[6] == bool(1):
                            self.ad_count.next = self.analyze_delay + self.analyze_delay
                        else:
                            self.ad_count.next = self.analyze_delay
                        self.state.next = t_State.ANALYZE_DELAY
                        self.power_usage_register.next = ANALYZE_POWER
                        self.thermal_register.next = ANALYZE_TEMP

                elif self.state == t_State.ANALYZE_DELAY:
                    if self.control_register[1] == bool(1):  # Abort
                        # self.__set_status_register(intbv('00100'))
                        # self.__set_control_register(intbv('000000'))
                        self.status_register[0].next = bool(0)
                        self.status_register[1].next = bool(0)
                        self.status_register[2].next = bool(1)
                        self.status_register[3].next = bool(0)
                        self.status_register[4].next = bool(0)
                        self.status_register[5].next = bool(0)
                        self.status_register[6].next = bool(0)
                        self.control_register[0].next = bool(0)
                        self.control_register[1].next = bool(0)
                        self.control_register[2].next = bool(0)
                        self.control_register[3].next = bool(0)
                        self.control_register[4].next = bool(0)
                        self.control_register[5].next = bool(0)
                        self.control_register[6].next = bool(0)

                        self.state.next = t_State.IDLE
                        self.power_usage_register.next = IDLE_POWER
                        self.thermal_register.next = IDLE_TEMP
                    else:
                        if self.ad_count > 0:
                            if self.control_register[3] == bool(1):
                                if self.ad_count == 1:
                                    # Introduce error from TEST_DELAY state
                                    # self.__set_status_register(intbv('00001'))
                                    self.status_register[0].next = bool(0)
                                    self.status_register[1].next = bool(0)
                                    self.status_register[2].next = bool(0)
                                    self.status_register[3].next = bool(0)
                                    self.status_register[4].next = bool(1)
                                    self.status_register[5].next = bool(0)
                                    self.status_register[6].next = bool(0)
                                    self.state.next = t_State.IDLE
                                    self.power_usage_register.next = IDLE_POWER
                                    self.thermal_register.next = IDLE_TEMP
                                else:
                                    self.ad_count.next = self.ad_count - 1
                            else:
                                self.ad_count.next = self.ad_count - 1
                        else:
                            # self.__set_status_register(intbv('10000'))
                            # self.__set_control_register(intbv('000000'))
                            self.status_register[0].next = bool(1)
                            self.status_register[1].next = bool(0)
                            self.status_register[2].next = bool(0)
                            self.status_register[3].next = bool(0)
                            self.status_register[4].next = bool(0)
                            self.status_register[5].next = bool(0)
                            self.status_register[6].next = bool(0)
                            self.control_register[0].next = bool(0)
                            self.control_register[1].next = bool(0)
                            self.control_register[2].next = bool(0)
                            self.control_register[3].next = bool(0)
                            self.control_register[4].next = bool(0)
                            self.control_register[5].next = bool(0)
                            self.control_register[6].next = bool(0)
                            self.state.next = t_State.IDLE
                            self.power_usage_register.next = IDLE_POWER
                            self.thermal_register.next = IDLE_TEMP

                else:
                    raise ValueError("Undefined state")

        if not monitor:
            return state_machine
        else:
            @instance
            def monitor_power_usage():
                print("\t\tsimulatedmbist({:s}).power_usage_register:".format(self.name), self.power_usage_register)
                while 1:
                    yield self.power_usage_register
                    print("\t\tsimulatedmbist({:s}).power_usage_register:".format(self.name), self.power_usage_register)

            @instance
            def monitor_tempurature():
                print("\t\tsimulatedmbist({:s}).thermal_register:".format(self.name), self.thermal_register)
                while 1:
                    yield self.thermal_register
                    print("\t\tsimulatedmbist({:s}).thermal_register:".format(self.name), self.thermal_register)

            @instance
            def monitor_state():
                print("\t\tsimulatedmbist({:s}).state:".format(self.name), self.state)
                while 1:
                    yield self.state
                    print("\t\tsimulatedmbist({:s}).state:".format(self.name), self.state)

            @instance
            def monitor_reset_n():
                print("\t\tsimulatedmbist({:s}).reset_n:".format(self.name), self.reset_n)
                while 1:
                    yield self.reset_n
                    print("\t\tsimulatedmbist({:s}).reset_n:".format(self.name), self.reset_n)

            @instance
            def monitor_clock():
                print("\t\tsimulatedmbist({:s}).clock:".format(self.name), self.clock)
                while 1:
                    yield self.clock
                    print("\t\tsimulatedmbist({:s}).clock:".format(self.name), self.clock)

            @instance
            def monitor_control_register():
                print("\t\tsimulatedmbist({:s}).control_register:".format(self.name), self.control_register)
                while 1:
                    yield self.control_register
                    print("\t\tsimulatedmbist({:s}).control_register:".format(self.name), self.control_register)

            @instance
            def monitor_status_register():
                print("\t\tsimulatedmbist({:s}).status_register:".format(self.name), self.status_register)
                while 1:
                    yield self.status_register
                    print("\t\tsimulatedmbist({:s}).status_register:".format(self.name), self.status_register)

            return state_machine, monitor_reset_n, monitor_clock, monitor_control_register, monitor_status_register,\
                monitor_state, monitor_power_usage, monitor_tempurature


if __name__ == '__main__':
    cr = [Signal(bool(0)) for _ in range(6)]
    sr = [Signal(bool(0)) for _ in range(5)]
    clock = Signal(bool(0))
    reset_n = ResetSignal(1, 0, True)
    power_usage = Signal(intbv(0, min=0, max=101))
    thermal = Signal(intbv(0, min=0, max=101))

    def test():
        @always(delay(10))
        def clkgen():
            clock.next = not clock

        @instance
        def stimulus():
            # Reset the instrument
            reset_n.next = bool(0)
            yield delay(10)
            reset_n.next = bool(1)
            yield delay(10)
            # Start the MBIST operation
            cr[0].next = bool(1)
        return instances()

    mbist_inst = simulatedmbist('DEMO', clock, reset_n, cr, sr, power_usage, thermal,
                                          initialize_delay=10, test_delay=40,
                                          analyze_delay=30)
    sim = Simulation(mbist_inst.rtl(monitor=True), test())
    sim.run(10000)
    assert(sr[0] == bool(1))
    assert(sr[1] == bool(0))
    assert(sr[2] == bool(0))
    assert(sr[3] == bool(0))
    assert(sr[4] == bool(0))
    mbist_inst.toVerilog()
    mbist_inst.toVHDL()
