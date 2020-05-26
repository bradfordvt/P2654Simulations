"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
from time import sleep
from hdl.boards.gpiotest.gpiotest import GPIOTest
from hdl.ate.ate import ATE
from hdl.boards.common.BoardGPIOInterface import BoardGPIOInterface


def gpiotest_bench():
    gpio_if = BoardGPIOInterface()
    board_inst = GPIOTest()
    board_inst.configure_gpio(gpio_if)
    ate_inst = ATE(board_inst)
    ate_inst.configure_gpio(gpio_if)
    ate_inst.start_simulation()
    sleep(1)

    assert(ate_inst.write(0x00001800, 0x00000000))
    assert(ate_inst.read(0x00001800))
    assert(ate_inst.get_value() == 0x00000000)
    assert(ate_inst.write(0x00001800, 0x00000015))
    assert(ate_inst.read(0x00001800))
    assert(ate_inst.get_value() == 0x00150015)
    assert(ate_inst.write(0x00001800, 0x0000000A))
    assert(ate_inst.read(0x00001800))
    assert(ate_inst.get_value() == 0x000A000A)
    assert(ate_inst.terminate())


def main():
    gpiotest_bench()


if __name__ == '__main__':
    main()
