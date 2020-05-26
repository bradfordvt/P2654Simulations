"""
Copyright (c) 2020 Bradford G. Van Treuren
See the licence file in the top directory

IP Logic for decoder
"""
from myhdl import *
import os


class SN74138A:
    def __init__(self, parent, name, en1, en2, e3, an0, an1, an2, on0, on1, on2, on3, on4, on5, on6, on7):
        self.parent = parent
        self.name = name
        self.en1 = en1
        self.en2 = en2
        self.e3 = e3
        self.an0 = an0
        self.an1 = an1
        self.an2 = an2
        self.on0 = on0
        self.on1 = on1
        self.on2 = on2
        self.on3 = on3
        self.on4 = on4
        self.on5 = on5
        self.on6 = on6
        self.on7 = on7

    @block
    def rtl(self):
        enable = Signal(bool(0))

        @always_comb
        def enable_process():
            if not self.en1 and not self.en2 and self.e3:
                enable.next = True
            else:
                enable.next = False

        @always_comb
        def output_process():
            if not self.an0 and not self.an1 and not self.an2 and enable:
                self.on0.next = False
            else:
                self.on0.next = True
            if self.an0 and not self.an1 and not self.an2 and enable:
                self.on1.next = False
            else:
                self.on1.next = True
            if not self.an0 and self.an1 and not self.an2 and enable:
                self.on2.next = False
            else:
                self.on2.next = True
            if self.an0 and self.an1 and not self.an2 and enable:
                self.on3.next = False
            else:
                self.on3.next = True
            if not self.an0 and not self.an1 and self.an2 and enable:
                self.on4.next = False
            else:
                self.on4.next = True
            if self.an0 and not self.an1 and self.an2 and enable:
                self.on5.next = False
            else:
                self.on5.next = True
            if not self.an0 and self.an1 and self.an2 and enable:
                self.on6.next = False
            else:
                self.on6.next = True
            if self.an0 and self.an1 and self.an2 and enable:
                self.on7.next = False
            else:
                self.on7.next = True

        return enable_process, output_process


@block
def SN74138A_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    en1 = Signal(bool(0))
    en2 = Signal(bool(0))
    e3 = Signal(bool(0))
    an0 = Signal(bool(0))
    an1 = Signal(bool(0))
    an2 = Signal(bool(0))
    on0 = Signal(bool(0))
    on1 = Signal(bool(0))
    on2 = Signal(bool(0))
    on3 = Signal(bool(0))
    on4 = Signal(bool(0))
    on5 = Signal(bool(0))
    on6 = Signal(bool(0))
    on7 = Signal(bool(0))

    inst = SN74138A("TOP", "SN74138A", en1, en2, e3, an0, an1, an2, on0, on1, on2, on3, on4, on5, on6, on7)

    @instance
    def stimulus():
        """
        :return:
        """
        # Test on0 signals
        en1.next = False
        en2.next = False
        e3.next = True
        an0.next = False
        an1.next = False
        an2.next = False
        yield delay(1)
        assert(on0 == False)
        assert(on1 == True)
        assert(on2 == True)
        assert(on3 == True)
        assert(on4 == True)
        assert(on5 == True)
        assert(on6 == True)
        assert(on7 == True)

        # Test on1 signals
        en1.next = False
        en2.next = False
        e3.next = True
        an0.next = True
        an1.next = False
        an2.next = False
        yield delay(1)
        assert(on0 == True)
        assert(on1 == False)
        assert(on2 == True)
        assert(on3 == True)
        assert(on4 == True)
        assert(on5 == True)
        assert(on6 == True)
        assert(on7 == True)

        # Test on2 signals
        en1.next = False
        en2.next = False
        e3.next = True
        an0.next = False
        an1.next = True
        an2.next = False
        yield delay(1)
        assert(on0 == True)
        assert(on1 == True)
        assert(on2 == False)
        assert(on3 == True)
        assert(on4 == True)
        assert(on5 == True)
        assert(on6 == True)
        assert(on7 == True)

        # Test on3 signals
        en1.next = False
        en2.next = False
        e3.next = True
        an0.next = True
        an1.next = True
        an2.next = False
        yield delay(1)
        assert(on0 == True)
        assert(on1 == True)
        assert(on2 == True)
        assert(on3 == False)
        assert(on4 == True)
        assert(on5 == True)
        assert(on6 == True)
        assert(on7 == True)

        # Test on4 signals
        en1.next = False
        en2.next = False
        e3.next = True
        an0.next = False
        an1.next = False
        an2.next = True
        yield delay(1)
        assert(on0 == True)
        assert(on1 == True)
        assert(on2 == True)
        assert(on3 == True)
        assert(on4 == False)
        assert(on5 == True)
        assert(on6 == True)
        assert(on7 == True)

        # Test on5 signals
        en1.next = False
        en2.next = False
        e3.next = True
        an0.next = True
        an1.next = False
        an2.next = True
        yield delay(1)
        assert(on0 == True)
        assert(on1 == True)
        assert(on2 == True)
        assert(on3 == True)
        assert(on4 == True)
        assert(on5 == False)
        assert(on6 == True)
        assert(on7 == True)

        # Test on6 signals
        en1.next = False
        en2.next = False
        e3.next = True
        an0.next = False
        an1.next = True
        an2.next = True
        yield delay(1)
        assert(on0 == True)
        assert(on1 == True)
        assert(on2 == True)
        assert(on3 == True)
        assert(on4 == True)
        assert(on5 == True)
        assert(on6 == False)
        assert(on7 == True)

        # Test on7 signals
        en1.next = False
        en2.next = False
        e3.next = True
        an0.next = True
        an1.next = True
        an2.next = True
        yield delay(1)
        assert(on0 == True)
        assert(on1 == True)
        assert(on2 == True)
        assert(on3 == True)
        assert(on4 == True)
        assert(on5 == True)
        assert(on6 == True)
        assert(on7 == False)

        raise StopSimulation()

    return inst.rtl(), stimulus


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    en1 = Signal(bool(0))
    en2 = Signal(bool(0))
    e3 = Signal(bool(0))
    an0 = Signal(bool(0))
    an1 = Signal(bool(0))
    an2 = Signal(bool(0))
    on0 = Signal(bool(0))
    on1 = Signal(bool(0))
    on2 = Signal(bool(0))
    on3 = Signal(bool(0))
    on4 = Signal(bool(0))
    on5 = Signal(bool(0))
    on6 = Signal(bool(0))
    on7 = Signal(bool(0))

    inst = SN74138A("TOP", "SN74138A", en1, en2, e3, an0, an1, an2, on0, on1, on2, on3, on4, on5, on6, on7)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    inst.rtl().convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SN74138A")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    inst.rtl().convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SN74138A")
    tb = SN74138A_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SN74138A_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SN74138A_tb")


def main():
    tb = SN74138A_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
