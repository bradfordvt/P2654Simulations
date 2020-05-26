"""
Copyright (c) 2020 Bradford G. Van Treuren
See the licence file in the top directory

IP Logic for inverter
"""
from myhdl import *
import os


class SN7404:
    def __init__(self, parent, name, _1a, _1y, _2a, _2y, _3a, _3y, _4a, _4y, _5a, _5y, _6a, _6y):
        self.parent = parent
        self.name = name
        self._1a = _1a
        self._1y = _1y
        self._2a = _2a
        self._2y = _2y
        self._3a = _3a
        self._3y = _3y
        self._4a = _4a
        self._4y = _4y
        self._5a = _5a
        self._5y = _5y
        self._6a = _6a
        self._6y = _6y

    @block
    def rtl(self):
        @always_comb
        def output_process():
            self._1y.next = not self._1a
            self._2y.next = not self._2a
            self._3y.next = not self._3a
            self._4y.next = not self._4a
            self._5y.next = not self._5a
            self._6y.next = not self._6a

        return output_process


@block
def SN7404_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    _1a = Signal(bool(0))
    _1y = Signal(bool(0))
    _2a = Signal(bool(0))
    _2y = Signal(bool(0))
    _3a = Signal(bool(0))
    _3y = Signal(bool(0))
    _4a = Signal(bool(0))
    _4y = Signal(bool(0))
    _5a = Signal(bool(0))
    _5y = Signal(bool(0))
    _6a = Signal(bool(0))
    _6y = Signal(bool(0))

    inst = SN7404("TOP", "SN74138A", _1a, _1y, _2a, _2y, _3a, _3y, _4a, _4y, _5a, _5y, _6a, _6y)

    @instance
    def stimulus():
        """
        :return:
        """
        # Test signals
        _1a.next = False
        _2a.next = False
        _3a.next = False
        _4a.next = False
        _5a.next = False
        _6a.next = False
        yield delay(1)
        assert(_1y == True)
        assert(_2y == True)
        assert(_3y == True)
        assert(_4y == True)
        assert(_5y == True)
        assert(_6y == True)

        # Test signals
        _1a.next = True
        _2a.next = False
        _3a.next = False
        _4a.next = False
        _5a.next = False
        _6a.next = False
        yield delay(1)
        assert(_1y == False)
        assert(_2y == True)
        assert(_3y == True)
        assert(_4y == True)
        assert(_5y == True)
        assert(_6y == True)

        # Test signals
        _1a.next = False
        _2a.next = True
        _3a.next = False
        _4a.next = False
        _5a.next = False
        _6a.next = False
        yield delay(1)
        assert(_1y == True)
        assert(_2y == False)
        assert(_3y == True)
        assert(_4y == True)
        assert(_5y == True)
        assert(_6y == True)

        # Test signals
        _1a.next = False
        _2a.next = False
        _3a.next = True
        _4a.next = False
        _5a.next = False
        _6a.next = False
        yield delay(1)
        assert(_1y == True)
        assert(_2y == True)
        assert(_3y == False)
        assert(_4y == True)
        assert(_5y == True)
        assert(_6y == True)

        # Test signals
        _1a.next = False
        _2a.next = False
        _3a.next = False
        _4a.next = True
        _5a.next = False
        _6a.next = False
        yield delay(1)
        assert(_1y == True)
        assert(_2y == True)
        assert(_3y == True)
        assert(_4y == False)
        assert(_5y == True)
        assert(_6y == True)

        # Test signals
        _1a.next = False
        _2a.next = False
        _3a.next = False
        _4a.next = False
        _5a.next = True
        _6a.next = False
        yield delay(1)
        assert(_1y == True)
        assert(_2y == True)
        assert(_3y == True)
        assert(_4y == True)
        assert(_5y == False)
        assert(_6y == True)

        # Test signals
        _1a.next = False
        _2a.next = False
        _3a.next = False
        _4a.next = False
        _5a.next = False
        _6a.next = True
        yield delay(1)
        assert(_1y == True)
        assert(_2y == True)
        assert(_3y == True)
        assert(_4y == True)
        assert(_5y == True)
        assert(_6y == False)

        raise StopSimulation()

    return inst.rtl(), stimulus


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    _1a = Signal(bool(0))
    _1y = Signal(bool(0))
    _2a = Signal(bool(0))
    _2y = Signal(bool(0))
    _3a = Signal(bool(0))
    _3y = Signal(bool(0))
    _4a = Signal(bool(0))
    _4y = Signal(bool(0))
    _5a = Signal(bool(0))
    _5y = Signal(bool(0))
    _6a = Signal(bool(0))
    _6y = Signal(bool(0))

    inst = SN7404("TOP", "SN7404", _1a, _1y, _2a, _2y, _3a, _3y, _4a, _4y, _5a, _5y, _6a, _6y)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    inst.rtl().convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SN7404")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    inst.rtl().convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SN7404")
    tb = SN7404_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="SN7404_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="SN7404_tb")


def main():
    tb = SN7404_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
