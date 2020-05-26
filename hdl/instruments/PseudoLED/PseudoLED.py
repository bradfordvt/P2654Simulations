from myhdl import *


class PseudoLED:
    def __init__(self, parent, name, state, color="WHITE"):
        self.parent = parent
        self.name = name
        self.state = state
        self.color = color
        self.on = None

    @block
    def rtl(self):
        self.on = Signal(bool(0))

        @always_comb
        def display():
            if self.state:
                self.on.next = True
            else:
                self.on.next = False

        @instance
        def monitor_on():
            print("\t\tLED[{:s}]({:s}): on".format(self.parent + "." + self.name, self.color), self.on)
            while 1:
                yield self.on
                print("\t\tLED[{:s}]({:s}): on".format(self.parent + "." + self.name, self.color), self.on)

        return display, monitor_on
