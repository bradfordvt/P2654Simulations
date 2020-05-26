"""

"""


class AbstractBoard:
    def __init__(self):
        # Default ports
        # SYSCON Signals
        self.clk_o = None
        self.rst_o = None
        # GPIO Signals
        self.i_gpio = None
        self.o_gpio = None
        # JTAG Signals
        self.tck = None
        self.tms = None
        self.trst = None
        self.tdi = None
        self.tdo = None
        self.tck2 = None
        self.tms2 = None
        self.trst2 = None
        self.tdi2 = None
        self.tdo2 = None
        # I2C Signals
        self.scl_o = None
        self.scl_i = None
        self.scl_e = None
        self.sda_o = None
        self.sda_i = None
        self.sda_e = None
        # SPI Signals
        self.sclk = None
        self.mosi = None
        self.miso = None
        self.ss = None
        # TPSP Signals
        self.tp_sck = None
        self.tp_i = None
        self.tp_o = None
        self.tp_e = None

    def configure_syscon(self, clk_o, rst_o):
        self.clk_o = clk_o
        self.rst_o = rst_o

    def configure_gpio(self, gpio_if):
        self.i_gpio = gpio_if.i_gpio
        self.o_gpio = gpio_if.o_gpio

    def configure_jtag(self, jtag_if):
        self.tdi = jtag_if.TDI
        self.tck = jtag_if.TCK
        self.tms = jtag_if.TMS
        self.trst = jtag_if.TRST
        self.tdo = jtag_if.TDO

    def configure_jtag2(self, jtag_if):
        self.tdi2 = jtag_if.TDI
        self.tck2 = jtag_if.TCK
        self.tms2 = jtag_if.TMS
        self.trst2 = jtag_if.TRST
        self.tdo2 = jtag_if.TDO

    def configure_i2c(self, i2c_if):
        self.scl_o = i2c_if.SCL_O
        self.scl_i = i2c_if.SCL_I
        self.scl_e = i2c_if.SCL_E
        self.sda_o = i2c_if.SDA_O
        self.sda_i = i2c_if.SDA_I
        self.sda_e = i2c_if.SDA_E

    def configure_spi(self, spi_if):
        self.sclk = spi_if.SCLK
        self.mosi = spi_if.MOSI
        self.miso = spi_if.MISO
        self.ss = spi_if.SS

    def configure_tpsp(self, tp_if):
        self.tp_sck = tp_if.TP_SCK
        self.tp_i = tp_if.TP_I
        self.tp_o = tp_if.TP_O
        self.tp_e = tp_if.TP_E
