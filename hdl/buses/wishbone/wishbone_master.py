"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
from time import sleep
# from asyncio import Queue as pyQueue
from queue import Queue as pyQueue
from hdl.common.containers import Queue as myQueue
from hdl.buses.wishbone.wishbone_if import WB_ADR_WIDTH, WB_DAT_WIDTH


class WishboneMaster:
    def __init__(self, path, name, wb_interface, monitor=False):
        self.path = path
        self.name = name
        self.wb_interface = wb_interface
        self.monitor = monitor
        self.Q = myQueue()
        self.R = pyQueue()
        self.response = None
        self.localReset = Signal(bool(0))
        self.error = None
        self.value = None
        # transaction information (simulation only)
        self._write = Signal(bool(0))    # write command in progress
        self._read = Signal(bool(0))     # read command in progress
        self._address = 0      # address of current/last transaction
        self._data = 0         # ??? @todo: is this used ???
        self._write_data = 0  # holds the data written
        self._read_data = 0   # holds the data read
        # Utility signals
        self.inprog = Signal(bool(0))
        self.iswrite = Signal(bool(0))
        self.done = Signal(bool(0))
        # bus transaction timeout in clock ticks
        self.timeout = 100

    @block
    def rtl(self, monitor=False):
        @always(self.wb_interface.clk_i.posedge)
        def _reset():
            if self.localReset:
                self.wb_interface.rst_i.next = True
            else:
                self.wb_interface.rst_i.next = False

        @always_comb
        def _assign():
            # print("wb.rtl._assign0: self._address = ", hex(self._address))
            # print("wb.rtl._assign0: self._write_data = ", hex(self._write_data))
            # print("wb.rtl._assign0: self._write = ", self._write, ", self._read = ", self._read)
            # print("wb.rtl._assign0: self.inprog = ", self.inprog)
            # print("wb.rtl._assign0: self.iswrite = ", self.iswrite)
            if not self.inprog and (self._write or self._read):
                self.wb_interface.cyc.next = True
                self.wb_interface.we.next = True if self._write else False
                self.wb_interface.stb.next = True
            elif self.inprog:
                self.wb_interface.cyc.next = True
                self.wb_interface.we.next = True if self.iswrite else False
                self.wb_interface.stb.next = True
            else:
                self.wb_interface.cyc.next = False
                self.wb_interface.we.next = False
                self.wb_interface.stb.next = False

            self.wb_interface.adr.next = intbv(self._address)[WB_ADR_WIDTH:]
            self.wb_interface.dat_i.next = intbv(self._write_data)[WB_DAT_WIDTH:]
            self._read_data = int(self.wb_interface.dat_o)

        @always(self.wb_interface.clk_i.posedge)
        def _delay():
            if not self.inprog and (self._write or self._read):
                # print("wb._delay: self.inprog = ", self.inprog, ", self._write = ", self._write, ", self._read = ", self._read)
                self.inprog.next = True
                self.iswrite.next = self._write
            if self.inprog and self.wb_interface.ack:
                # print("wb._delay: self.inprog = ", self.inprog, ", self.wb_interface.ack = ", self.wb_interface.ack)
                self.inprog.next = False
                self.iswrite.next = False

        @always_comb
        def _done():
            # print("wb._done: entered")
            self.done.next = not self.inprog

        @instance
        def stimulus():
            yield delay(100)
            while 1:
                yield self.Q.get()
                cmd = self.Q.item
                # print("cmd = ", cmd)
                if cmd[0] == "reset":
                    # print("Processing Reset")
                    self.localReset.next = bool(1)
                    yield self.wb_interface.rst_i.posedge
                    self.localReset.next = bool(0)
                elif cmd[0] == "write":
                    print("Processing Write")
                    self._write.next = True
                    self._read.next = False
                    self._address = cmd[1]
                    self._write_data = cmd[2]
                    self._read_data = False
                    # yield self.wb_interface.clk_i.posedge
                    yield self.inprog.posedge
                    self._write.next = False
                    self._read.next = False
                    to = 0
                    # print("self.done = ", self.done)
                    while not self.done and to < self.timeout:
                        yield self.wb_interface.clk_i.posedge
                        to += 1
                    print("to = ", to)
                    if to == self.timeout:
                        self.R.put(("ERR", "TIMEOUT"))
                    else:
                        # Return status
                        self.R.put(("OK", 0))
                elif cmd[0] == "read":
                    print("Processing Read")
                    self._write.next = False
                    self._read.next = True
                    self._address = cmd[1]
                    self._read_data = None
                    self._write_data = False
                    # yield self.wb_interface.clk_i.posedge
                    yield self.done.negedge
                    to = 0
                    while not self.done and to < self.timeout:
                        yield self.wb_interface.clk_i.posedge
                        to += 1
                    if self._read:
                        self._read_data = int(self.wb_interface.dat_o)
                    self._write.next = False
                    self._read.next = False
                    if to == self.timeout:
                        self.R.put(("ERR", "TIMEOUT"))
                    else:
                        # Return value
                        # print("ReadQueue: value read = ", hex(self._read_data))
                        # print("self.wb_interface.adr = ", hex(self.wb_interface.adr))
                        # print("self.wb_interface.dat_o = ", hex(self.wb_interface.dat_o))
                        self.R.put(("VAL", self._read_data))
                elif cmd[0] == "terminate":
                    # print("Processing terminate")
                    self.R.put(("DONE", 0))
                    break
                else:
                    print("Invalid message sent!")
            raise StopSimulation()

        @instance
        def monitor_done():
            print("\t\tWishboneMaster({:s}): self.done".format(self.path + '.' + self.name), self.done)
            while 1:
                yield self.done
                print("\t\tWishboneMaster({:s}): self.done".format(self.path + '.' + self.name), self.done)

        return stimulus, _reset, _assign, _delay, _done
        # return stimulus, _reset, _assign, _delay, _done, \
        #         monitor_done

    def write(self, addr, data):
        self.Q.put(("write", addr, data))
        # yield delay(100)
        sleep(1)
        ret = self.R.get()
        if ret[0] == "ERR":
            self.error = ret[1]
            return False
        elif ret[0] == "OK":
            return True
        else:
            self.error = "UNKNOWN"
            return False

    def read(self, addr):
        self.Q.put(("read", addr, 0))
        # yield delay(100)
        sleep(1)
        ret = self.R.get()
        print("ret = ", ret)
        if ret[0] == "ERR":
            self.error = ret[1]
            return False
        elif ret[0] == "VAL":
            self.value = ret[1]
            return True
        else:
            self.error = "UNKNOWN"
            return False

    def terminate(self):
        self.Q.put(("terminate", 0, 0))
        ret = self.R.get()
        if ret[0] == "ERR":
            self.error = ret[1]
            return False
        elif ret[0] == "DONE":
            return True
        else:
            self.error = "UNKNOWN"
            return False

    def get_value(self):
        return self.value

    def get_error(self):
        return self.error
