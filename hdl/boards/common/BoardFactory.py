"""

"""
from myhdl import *

from hdl.boards.common.BoardGPIOInterface import BoardGPIOInterface
from hdl.boards.common.BoardI2CInterface import BoardI2CInterface
from hdl.boards.common.BoardSPIInterface import BoardSPIInterface
from hdl.boards.common.BoardJTAGInterface import BoardJTAGInterface
from hdl.boards.gpiotest.gpiotest import GPIOTest
from hdl.boards.i2ctest.i2ctest import I2CTest
from hdl.boards.spitest.spitest import SPITest
from hdl.boards.jtagtest.jtagtest import JTAGTest
from hdl.boards.jtagtest.jtag2test import JTAG2Test
from hdl.boards.P2654Board1.P2654Board1 import P2654Board1
from hdl.boards.P2654Board1.P2654Board1_2 import P2654Board1_2


class BoardFactory:
    def __init__(self):
        self.clk_o = Signal(bool(0))
        self.rst_o = Signal(bool(0))
        self.gpio_if = BoardGPIOInterface()
        self.i2c_if = BoardI2CInterface()
        self.spi_if = BoardSPIInterface()
        self.jtag_if = BoardJTAGInterface()
        self.jtag2_if = BoardJTAGInterface()

    def get_gpio_if(self):
        return self.gpio_if

    def get_i2c_if(self):
        return self.i2c_if

    def get_spi_if(self):
        return self.spi_if

    def get_jtag_if(self):
        return self.jtag_if

    def get_jtag2_if(self):
        return self.jtag2_if

    def get_clk_o(self):
        return self.clk_o

    def get_rst_o(self):
        return self.rst_o

    def make_board(self, board_name):
        board = None
        if board_name == "GPIOTest":
            board = GPIOTest()
            board.configure_gpio(self.gpio_if)
        elif board_name == "I2CTest":
            board = I2CTest()
            board.configure_gpio(self.gpio_if)
            board.configure_i2c(self.i2c_if)
        elif board_name == "SPITest":
            board = SPITest()
            board.configure_gpio(self.gpio_if)
            board.configure_i2c(self.i2c_if)
            board.configure_spi(self.spi_if)
            board.configure_jtag(self.jtag_if)
        elif board_name == "JTAGTest":
            board = JTAGTest()
            board.configure_gpio(self.gpio_if)
            board.configure_jtag(self.jtag_if)
        elif board_name == "JTAG2Test":
            board = JTAG2Test()
            board.configure_gpio(self.gpio_if)
            board.configure_jtag2(self.jtag2_if)
        elif board_name == "P2654Board1":
            board = P2654Board1("TOP", "P2654Board1")
            board.configure_gpio(self.gpio_if)
            board.configure_jtag(self.jtag_if)
        elif board_name == "P2654Board1_2":
            board = P2654Board1_2("TOP", "P2654Board1_2")
            board.configure_gpio(self.gpio_if)
            board.configure_jtag2(self.jtag2_if)
        else:
            board = None
        if board is not None:
            board.configure_syscon(self.clk_o, self.rst_o)
        return board
