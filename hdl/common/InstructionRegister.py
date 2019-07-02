"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
import logging


logger = logging.getLogger(__name__)


def sa_to_string(tdo_vector):
    dlen = len(tdo_vector)
    response = ""
    for i in range(dlen):
        t = '0'
        if tdo_vector[dlen-i-1] == bool(1):
            t = '1'
        response += t
    return response


class InstructionRegister:
    def __init__(self, path, name, si, ce, se, ue, reset, clock, so, di, do, width=9):
        """
        Generic InstructionRegister design following the Capture/Shift/Update protocol
        :param path: Dot path of the parent of this instance
        :param name: Instance name for debug logger (path instance)
        :param si: ScanIn Port
        :param ce: CaptureEnable Port
        :param se: ShiftEnable Port
        :param ue: UpdateEnable Port
        :param reset: Reset Port
        :param clock: Clock Port
        :param so: ScanOut Port
        :param di: DataIn Port
        :param do: DataOut Port
        :param width: The number of bits contained in this register
        """
        # print(__name__)
        logger.info("Constructing ScanRegister instance ({:s}).".format(path + '.' + name))
        self.path = path
        self.name = name
        self.si = si
        self.ce = ce
        self.se = se
        self.ue = ue
        self.reset = reset
        self.clock = clock
        self.so = so
        self.di = di
        self.do = do
        self.width = width
        self.isr = [Signal(bool(0)) for _ in range(width)]
        if self.di[-1] != bool(1) and self.di[-2] != bool(0):
            raise AssertionError("Value for IR does not end with a '01' value as required by IEEE Std 1149.1.")

    def rtl(self, monitor=False):
        """
        The logic for the InstructionRegister
        :return: The generator methods performing the logic decisions
        """
        logger.debug("ScanRegister({:s}).rtl()".format(self.path + '.' + self.name))
        @always(self.clock.posedge)
        def capture_ff():
            # print("Entering InstructionRegister.rtl.capture_ff()")
            logger.debug("InstructionRegister({:s}): Entering capture_ff".format(self.path + '.' + self.name))
            logger.debug("\tself.ce = {:s}".format(str(self.ce)))
            if self.ce:
                logger.debug("\tCaptureEn")
                logger.debug("\tdi = {:s}".format(sa_to_string(self.di)))
                logger.debug("\tisr = {:s}".format(sa_to_string(self.isr)))
                for i in range(self.width):
                    self.isr[i].next = self.di[i]
            elif self.se:
                logger.debug("\tShiftEn")
                logger.debug("\tsi = {:s}".format(str(self.si)))
                for i in range(self.width):
                    if i == 0:
                        self.isr[i].next = self.si
                        logger.debug("\t\tsi = {:s}".format(bin(self.si)))
                    elif i == self.width - 1:
                        logger.debug("\t\tso = {:s}".format(bin(self.isr[i])))
                        self.so.next = self.isr[i]
                        self.isr[i].next = self.isr[i-1]
                    else:
                        self.isr[i].next = self.isr[i-1]
            else:
                self.so.next = self.so

        @always(self.clock.posedge, self.reset.negedge)
        def update_ff():
            # print("Entering ScanRegister.rtl.update_ff()")
            logger.debug("InstructionRegister({:s}): Entering update_ff".format(self.path + '.' + self.name))
            logger.debug("\tself.clock is: {:s}.".format(str(self.clock)))
            logger.debug("\tself.reset is: {:s}.".format(str(self.reset)))
            if self.ue:
                logger.debug("\tUpdateEn")
                logger.debug("\tisr = {:s}".format(sa_to_string(self.isr)))
                logger.debug("\tdo = {:s}".format(sa_to_string(self.do)))
                for i in range(self.width):
                    self.do[i].next = self.isr[i]
            elif self.reset:
                for i in range(self.width):
                    self.do[i].next = self.do[i]
            elif not self.reset:
                for i in range(self.width):
                    self.do[i].next = bool(0)

        if monitor == False:
            return capture_ff, update_ff
        else:
            @instance
            def monitor_si():
                print("\t\tInstructionRegister({:s}): si".format(self.path + '.' + self.name), self.si)
                while 1:
                    yield self.si
                    print("\t\tInstructionRegister({:s}): si".format(self.path + '.' + self.name), self.si)

            @instance
            def monitor_ce():
                print("\t\tInstructionRegister({:s}): ce".format(self.path + '.' + self.name), self.ce)
                while 1:
                    yield self.ce
                    print("\t\tInstructionRegister({:s}): ce".format(self.path + '.' + self.name), self.ce)

            @instance
            def monitor_se():
                print("\t\tInstructionRegister({:s}): se".format(self.path + '.' + self.name), self.se)
                while 1:
                    yield self.se
                    print("\t\tInstructionRegister({:s}): se".format(self.path + '.' + self.name), self.se)

            @instance
            def monitor_ue():
                print("\t\tInstructionRegister({:s}): ue".format(self.path + '.' + self.name), self.ue)
                while 1:
                    yield self.ue
                    print("\t\tInstructionRegister({:s}): ue".format(self.path + '.' + self.name), self.ue)

            @instance
            def monitor_reset():
                print("\t\tInstructionRegister({:s}): reset".format(self.path + '.' + self.name), self.reset)
                while 1:
                    yield self.reset
                    print("\t\tInstructionRegister({:s}): reset".format(self.path + '.' + self.name), self.reset)

            @instance
            def monitor_clock():
                print("\t\tInstructionRegister({:s}): clock".format(self.path + '.' + self.name), self.clock)
                while 1:
                    yield self.clock
                    print("\t\tInstructionRegister({:s}): clock".format(self.path + '.' + self.name), self.clock)

            @instance
            def monitor_so():
                print("\t\tInstructionRegister({:s}): so".format(self.path + '.' + self.name), self.so)
                while 1:
                    yield self.so
                    print("\t\tInstructionRegister({:s}): so".format(self.path + '.' + self.name), self.so)

            @instance
            def monitor_isr():
                print("\t\tInstructionRegister({:s}): isr".format(self.path + '.' + self.name), self.isr)
                while 1:
                    yield self.isr
                    print("\t\tInstructionRegister({:s}): isr".format(self.path + '.' + self.name), self.isr)

            @instance
            def monitor_di():
                print("\t\tInstructionRegister({:s}): di".format(self.path + '.' + self.name), self.di)
                while 1:
                    yield self.di
                    print("\t\tInstructionRegister({:s}): di".format(self.path + '.' + self.name), self.di)

            @instance
            def monitor_do():
                print("\t\tInstructionRegister({:s}): do".format(self.path + '.' + self.name), self.do)
                while 1:
                    yield self.do
                    print("\t\tInstructionRegister({:s}): do".format(self.path + '.' + self.name), self.do)
            return monitor_si, monitor_ce, monitor_se, monitor_ue, monitor_reset,\
                monitor_clock, monitor_so, monitor_di, monitor_do, capture_ff, update_ff,\
                monitor_isr

    def get_width(self):
        return self.width
