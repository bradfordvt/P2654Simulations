"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
from hdl.boards.gpiotest.gpiotest import GPIOTest
from hdl.ate.ate import ATE


def gpiotest_bench():
    board_inst = GPIOTest()
    ate_inst = ATE(board_inst)
    ate_inst.start_simulation()

    assert(ate_inst.write(0x00001800, 0x00000000))
    assert(ate_inst.terminate())


def main():
    gpiotest_bench()


if __name__ == '__main__':
    main()
