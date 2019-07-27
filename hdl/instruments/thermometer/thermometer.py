"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Simulation of a thermometer
"""
from myhdl import *
import os
import os.path

MBIST1_TEMP_MAX = 120
MBIST2_TEMP_MAX = 120
MBIST3_TEMP_MAX = 120
MBIST4_TEMP_MAX = 120
MBIST5_TEMP_MAX = 120
AMBIENT = 70
OVERTEMP = 451
HEAT_EXCHANGE = 150


class thermometer:
    """
    Class structure implementing the RTL for the instrument.
    """
    def __init__(self, parent, name, clock, reset_n, temperature,
                 thermal_register1, thermal_register2, thermal_register3,
                 thermal_register4, thermal_register5):
        """

        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logger (path instance)
        :param clock: Clock signal used to change state
        :param reset_n: Reset signal for state machine. 0=Reset, 1=No reset
        :param temperature: Register where output value of temperature
        :param thermal_register1: Proportion of total temperature of MBIST1
        :param thermal_register2: Proportion of total temperature of MBIST2
        :param thermal_register3: Proportion of total temperature of MBIST3
        :param thermal_register4: Proportion of total temperature of MBIST4
        :param thermal_register5: Proportion of total temperature of MBIST5
        """
        self.parent = parent
        self.name = name
        self.clock = clock
        self.reset_n = reset_n
        self.temperature = temperature
        self.thermal_register1 = thermal_register1
        self.thermal_register2 = thermal_register2
        self.thermal_register3 = thermal_register3
        self.thermal_register4 = thermal_register4
        self.thermal_register5 = thermal_register5

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
        return self.thermometer_rtl(monitor=monitor)

    @block
    def thermometer_rtl(self, monitor=False):
        """
        The logic for the thermometer
        :return: The generator methods performing the logic decisions
        """
        @always(self.clock.posedge)
        def calc_temp():
            if self.reset_n == bool(0):
                self.temperature.next = AMBIENT
            else:
                mbist1_temp = (((MBIST1_TEMP_MAX - AMBIENT) * self.thermal_register1) // 100) + AMBIENT
                mbist2_temp = (((MBIST2_TEMP_MAX - AMBIENT) * self.thermal_register2) // 100) + AMBIENT
                mbist3_temp = (((MBIST3_TEMP_MAX - AMBIENT) * self.thermal_register3) // 100) + AMBIENT
                mbist4_temp = (((MBIST4_TEMP_MAX - AMBIENT) * self.thermal_register4) // 100) + AMBIENT
                mbist5_temp = (((MBIST5_TEMP_MAX - AMBIENT) * self.thermal_register5) // 100) + AMBIENT
                hot = (mbist1_temp + mbist2_temp + mbist3_temp + mbist4_temp + mbist5_temp) - HEAT_EXCHANGE
                # print("mbist1_temp = ", mbist1_temp)
                # print("mbist2_temp = ", mbist2_temp)
                # print("mbist3_temp = ", mbist3_temp)
                # print("mbist4_temp = ", mbist4_temp)
                # print("mbist5_temp = ", mbist5_temp)
                # print("hot = ", hot)
                self.temperature.next = hot

        if not monitor:
            return calc_temp
        else:
            @instance
            def monitor_temperature():
                print("\t\tthermometer({:s}): temperature".format(self.parent + '.' + self.name), self.temperature)
                while 1:
                    yield self.temperature
                    print("\t\tthermometer({:s}): temperature".format(self.parent + '.' + self.name), self.temperature)

            @instance
            def monitor_thermal_register1():
                print("\t\tthermometer({:s}): thermal_register1".format(self.parent + '.' + self.name), self.thermal_register1)
                while 1:
                    yield self.thermal_register1
                    print("\t\tthermometer({:s}): thermal_register1".format(self.parent + '.' + self.name), self.thermal_register1)

            @instance
            def monitor_thermal_register2():
                print("\t\tthermometer({:s}): thermal_register2".format(self.parent + '.' + self.name), self.thermal_register2)
                while 1:
                    yield self.thermal_register2
                    print("\t\tthermometer({:s}): thermal_register2".format(self.parent + '.' + self.name), self.thermal_register2)

            @instance
            def monitor_thermal_register3():
                print("\t\tthermometer({:s}): thermal_register1".format(self.parent + '.' + self.name), self.thermal_register3)
                while 1:
                    yield self.thermal_register3
                    print("\t\tthermometer({:s}): thermal_register3".format(self.parent + '.' + self.name), self.thermal_register3)

            @instance
            def monitor_thermal_register4():
                print("\t\tthermometer({:s}): thermal_register1".format(self.parent + '.' + self.name), self.thermal_register4)
                while 1:
                    yield self.thermal_register4
                    print("\t\tthermometer({:s}): thermal_register4".format(self.parent + '.' + self.name), self.thermal_register4)

            @instance
            def monitor_thermal_register5():
                print("\t\tthermometer({:s}): thermal_register1".format(self.parent + '.' + self.name), self.thermal_register5)
                while 1:
                    yield self.thermal_register5
                    print("\t\tthermometer({:s}): thermal_register5".format(self.parent + '.' + self.name), self.thermal_register5)

            return calc_temp, monitor_temperature, monitor_thermal_register1, monitor_thermal_register2, \
                monitor_thermal_register3, monitor_thermal_register4, monitor_thermal_register5

    @staticmethod
    def convert():
        """
        Convert the myHDL design into VHDL and Verilog
        :return:
        """
        clock = Signal(bool(0))
        reset_n = Signal(bool(1))
        temperature = Signal(intbv(AMBIENT, min=0, max=OVERTEMP))
        thermal_register1 = Signal(intbv(0, min=0, max=101))
        thermal_register2 = Signal(intbv(0, min=0, max=101))
        thermal_register3 = Signal(intbv(0, min=0, max=101))
        thermal_register4 = Signal(intbv(0, min=0, max=101))
        thermal_register5 = Signal(intbv(0, min=0, max=101))

        temp_inst = thermometer('TOP', 'TEMP0', clock, reset_n, temperature,
                                thermal_register1, thermal_register2, thermal_register3,
                                thermal_register4, thermal_register5)

        temp_inst.toVerilog()
        temp_inst.toVHDL()

    @staticmethod
    @block
    def testbench(monitor=False):
        """
        Test bench interface for a quick test of the operation of the design
        :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
        :return: A list of generators for this logic
        """
        clock = Signal(bool(0))
        reset_n = Signal(bool(1))
        temperature = Signal(intbv(AMBIENT, min=0, max=OVERTEMP))
        thermal_register1 = Signal(intbv(0, min=0, max=101))
        thermal_register2 = Signal(intbv(0, min=0, max=101))
        thermal_register3 = Signal(intbv(0, min=0, max=101))
        thermal_register4 = Signal(intbv(0, min=0, max=101))
        thermal_register5 = Signal(intbv(0, min=0, max=101))

        temp_inst = thermometer('TOP', 'TEMP0', clock, reset_n, temperature,
                                thermal_register1, thermal_register2, thermal_register3,
                                thermal_register4, thermal_register5)

        @always(delay(1))
        def clkgen():
            clock.next = not clock

        @instance
        def stimulus():
            """
            Perform simulated temperature measurements
            :return:
            """
            # Reset the thermometer
            reset_n.next = bool(0)
            yield delay(1)
            assert(temperature == AMBIENT)
            reset_n.next = bool(1)
            yield delay(10)

            ####################################################
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 210)
            thermal_register1.next = 10
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 213)
            thermal_register1.next = 30
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 223)
            thermal_register1.next = 100
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 258)
            thermal_register1.next = 70
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 243)

            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 210)
            thermal_register1.next = 5
            thermal_register2.next = 10
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 213)
            thermal_register1.next = 5
            thermal_register2.next = 30
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 223)
            thermal_register1.next = 5
            thermal_register2.next = 100
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 258)
            thermal_register1.next = 5
            thermal_register2.next = 70
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 243)

            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 210)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 10
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 213)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 30
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 223)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 100
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 258)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 70
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 243)

            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 210)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 10
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 213)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 30
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 223)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 100
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 258)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 70
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 243)

            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 5
            yield delay(10)
            assert(temperature == 210)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 213)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 223)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 258)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 243)

            ####################################################
            thermal_register1.next = 10
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 216)
            thermal_register1.next = 30
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 226)
            thermal_register1.next = 100
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 261)
            thermal_register1.next = 70
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 246)

            thermal_register1.next = 5
            thermal_register2.next = 10
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 216)
            thermal_register1.next = 5
            thermal_register2.next = 30
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 226)
            thermal_register1.next = 5
            thermal_register2.next = 100
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 261)
            thermal_register1.next = 5
            thermal_register2.next = 70
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 246)

            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 10
            thermal_register4.next = 5
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 216)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 30
            thermal_register4.next = 5
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 226)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 100
            thermal_register4.next = 5
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 261)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 70
            thermal_register4.next = 5
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 246)

            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 10
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 216)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 30
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 226)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 70
            thermal_register5.next = 10
            yield delay(10)
            assert(temperature == 246)

            ####################################################
            thermal_register1.next = 10
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 226)
            thermal_register1.next = 30
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 236)
            thermal_register1.next = 100
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 271)
            thermal_register1.next = 70
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 256)

            thermal_register1.next = 5
            thermal_register2.next = 10
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 226)
            thermal_register1.next = 5
            thermal_register2.next = 30
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 236)
            thermal_register1.next = 5
            thermal_register2.next = 100
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 271)
            thermal_register1.next = 5
            thermal_register2.next = 70
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 256)

            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 10
            thermal_register4.next = 5
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 226)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 30
            thermal_register4.next = 5
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 236)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 100
            thermal_register4.next = 5
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 271)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 70
            thermal_register4.next = 5
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 256)

            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 10
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 226)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 30
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 236)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 100
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 271)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 70
            thermal_register5.next = 30
            yield delay(10)
            assert(temperature == 256)

            ####################################################
            thermal_register1.next = 10
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 261)
            thermal_register1.next = 30
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 271)
            thermal_register1.next = 100
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 306)
            thermal_register1.next = 70
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 291)

            thermal_register1.next = 5
            thermal_register2.next = 10
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 261)
            thermal_register1.next = 5
            thermal_register2.next = 30
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 271)
            thermal_register1.next = 5
            thermal_register2.next = 100
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 306)
            thermal_register1.next = 5
            thermal_register2.next = 70
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 291)

            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 10
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 261)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 30
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 271)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 100
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 306)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 70
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 291)

            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 10
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 261)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 30
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 271)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 100
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 306)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 70
            thermal_register5.next = 100
            yield delay(10)
            assert(temperature == 291)

            ####################################################
            thermal_register1.next = 10
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 246)
            thermal_register1.next = 30
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 256)
            thermal_register1.next = 100
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 291)
            thermal_register1.next = 70
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 276)

            thermal_register1.next = 5
            thermal_register2.next = 10
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 246)
            thermal_register1.next = 5
            thermal_register2.next = 30
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 256)
            thermal_register1.next = 5
            thermal_register2.next = 100
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 291)
            thermal_register1.next = 5
            thermal_register2.next = 70
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 276)

            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 10
            thermal_register4.next = 5
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 246)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 30
            thermal_register4.next = 5
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 256)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 100
            thermal_register4.next = 5
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 291)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 70
            thermal_register4.next = 5
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 276)

            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 10
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 246)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 30
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 256)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 100
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 291)
            thermal_register1.next = 5
            thermal_register2.next = 5
            thermal_register3.next = 5
            thermal_register4.next = 70
            thermal_register5.next = 70
            yield delay(10)
            assert(temperature == 276)

            # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
            ####################################################
            thermal_register1.next = 10
            thermal_register2.next = 10
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert (temperature == 264)
            thermal_register1.next = 30
            thermal_register2.next = 30
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert (temperature == 284)
            thermal_register1.next = 100
            thermal_register2.next = 100
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert (temperature == 354)
            thermal_register1.next = 70
            thermal_register2.next = 70
            thermal_register3.next = 5
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert (temperature == 324)

            thermal_register1.next = 10
            thermal_register2.next = 10
            thermal_register3.next = 10
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert (temperature == 267)
            thermal_register1.next = 30
            thermal_register2.next = 30
            thermal_register3.next = 30
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert (temperature == 297)
            thermal_register1.next = 100
            thermal_register2.next = 100
            thermal_register3.next = 100
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert (temperature == 402)
            thermal_register1.next = 70
            thermal_register2.next = 70
            thermal_register3.next = 70
            thermal_register4.next = 5
            thermal_register5.next = 100
            yield delay(10)
            assert (temperature == 357)

            thermal_register1.next = 10
            thermal_register2.next = 10
            thermal_register3.next = 10
            thermal_register4.next = 10
            thermal_register5.next = 100
            yield delay(10)
            assert (temperature == 270)
            thermal_register1.next = 30
            thermal_register2.next = 30
            thermal_register3.next = 30
            thermal_register4.next = 30
            thermal_register5.next = 100
            yield delay(10)
            assert (temperature == 310)
            thermal_register1.next = 100
            thermal_register2.next = 100
            thermal_register3.next = 100
            thermal_register4.next = 100
            thermal_register5.next = 100
            yield delay(10)
            assert (temperature == 450)
            thermal_register1.next = 70
            thermal_register2.next = 70
            thermal_register3.next = 70
            thermal_register4.next = 70
            thermal_register5.next = 100
            yield delay(10)
            assert (temperature == 390)

            raise StopSimulation()

        return temp_inst.thermometer_rtl(monitor=monitor), clkgen, stimulus


if __name__ == '__main__':
    tb = thermometer.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    thermometer.convert()
