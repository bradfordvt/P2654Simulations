"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
from asyncio import Queue as pyQueue
from hdl.common.containers import Queue as myQueue
# from hdl.buses.wishbone.wishbone_if import wishbone_if


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
        self._write = False    # write command in progress
        self._read = False     # read command in progress
        self._address = 0      # address of current/last transaction
        self._data = 0         # ??? @todo: is this used ???
        self._write_data = -1  # holds the data written
        self._read_data = -1   # holds the data read
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
            if self._write or self._read:
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

            self.wb_interface.adr.next = self._address
            self.wb_interface.dat_i.next = self._write_data
            self._read_data = self.wb_interface.dat_o

        @always(self.wb_interface.clk_i.posedge)
        def _delay():
            if not self.inprog and (self._write or self._read):
                self.inprog.next = True
                self.iswrite.next = self._write
            if self.inprog and self.wb_interface.ack:
                self.inprog.next = False
                self.iswrite.next = False

        @always_comb
        def _done():
            self.done.next = not self.inprog

        @instance
        def stimulus():
            yield delay(100)
            while 1:
                yield self.Q.get()
                cmd = self.Q.item
                if cmd[0] == "reset":
                    self.localReset.next = bool(1)
                    yield self.wb_interface.rst_i.posedge
                    self.localReset.next = bool(0)
                elif cmd[0] == "write":
                    self._write = True
                    self._read = False
                    self._address = cmd[1]
                    self._write_data = cmd[2]
                    self._read_data = False
                    to = 0
                    yield
                    while not self.done and to < self.timeout:
                        yield self.wb_interface.clk_i.posedge
                        to += 1
                    self._write = False
                    self._read = False
                    if to == self.timeout:
                        self.R.put(("ERR", "TIMEOUT"))
                    else:
                        # Return status
                        self.R.put(("OK", 0))
                elif cmd[0] == "read":
                    self._write = False
                    self._read = True
                    self._address = cmd[1]
                    self._read_data = None
                    self._write_data = False
                    to = 0
                    yield
                    while not self.done and to < self.timeout:
                        yield self.wb_interface.clk_i.posedge
                        to += 1
                    if self._read:
                        self._read_data = int(self.wb_interface.dat_o)
                    self._write = False
                    self._read = False
                    if to == self.timeout:
                        self.R.put(("ERR", "TIMEOUT"))
                    else:
                        # Return value
                        self.R.put(("VAL", self._read_data))
                elif cmd[0] == "terminate":
                    self.R.put(("DONE", 0))
                    break
            raise StopSimulation()

        return stimulus, _reset, _assign, _delay, _done

    def write(self, addr, data):
        self.Q.put(("write", addr, data))
        yield delay(100)
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
        yield delay(100)
        ret = self.R.get()
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
