"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
#########
TPSP
#########
Address 0x00001C10 TPSP
#########
SPI
#########
Address 0x00001C08 SPI
Address 0x00001C0F SPI
#########
I2C
#########
# RW
Address 0x00001C00 I2C prer [low byte] (clock prescale register)
Address 0x00001C01 I2C prer [high byte] (clock prescale register)
Address 0x00001C02 I2C ctr (control register)
# RO
Address 0x00001C03 I2C rxr (receive register)
Address 0x00001C04 I2C sr (status register)
# WO
Address 0x00001C03 I2C txr (transmit register)
Address 0x00001C04 I2C cr (command register)
Address 0x00001C07 I2C Reserved
#########
JTAG
#########
Address 0x00001000 - 0x000013FF JTAG Vector Buffer Memory (8-bit data bus as lowest 8 bits)
Address 0x00001400 JTAG Start State Register (4-bit lowest 4 bits)
Address 0x00001401 JTAG End State Register (4-bit lowest 4 bits)
Address 0x00001402 JTAG Bit Count (16-bit lowest 16 bits)
Address 0x00001403 JTAG Control Register (bit 0: Scan start/stop: 1=start scan, 0=stop scan)
Address 0x00001404 JTAG Status Register (bit 0: 1=busy scanning, 0=done scanning)
#########
GPIO
#########
Address 0x00001800 GPIO register
"""

import binascii
from myhdl import *
from time import sleep
from hdl.boards.i2ctest.i2ctest import I2CTest
from hdl.ate.ate import ATE
from hdl.hosts.jtaghost.JTAG_Ctrl_Master import SHIFT_DR, SHIFT_IR, RUN_TEST_IDLE
from hdl.boards.spitest.spitest import SPITest
from hdl.boards.common.BoardGPIOInterface import BoardGPIOInterface
from hdl.boards.common.BoardI2CInterface import BoardI2CInterface
from hdl.boards.common.BoardSPIInterface import BoardSPIInterface


def write_vector(ate_inst, addr, data):
    """

    :param ate_inst:
    :param addr:
    :param data:
    :return:
    """
    assert(addr < 0x1000)
    wb_addr = 0x00001000 + addr
    # print("Writing ", hex(data & 0xFF), " to address ", hex(wb_addr))
    ret = ate_inst.write(wb_addr, data & 0xFF)
    if ret == False:
        print("Write Error: ", ate_inst.get_error())
    assert(ret == True)


def read_vector(ate_inst, addr):
    """

    :param ate_inst:
    :param addr:
    :return:
    """
    assert(addr < 0x1000)
    wb_addr = 0x00001000 + addr
    ret = ate_inst.read(wb_addr)
    if ret == False:
        print("Read Error: ", ate_inst.get_error())
    assert(ret == True)
    value = ate_inst.get_value() & 0xFF
    # print("Read ", hex(value), " from address ", hex(wb_addr))
    return value


def set_bit_count(ate_inst, count):
    """

    :param ate_inst:
    :param count:
    :return:
    """
    wb_addr = 0x00001000 + 0x402
    assert(ate_inst.write(wb_addr, count & 0xFFFF))


def set_state_start(ate_inst, state):
    """

    :param ate_inst:
    :param state:
    :return:
    """
    wb_addr = 0x00001000 + 0x400
    assert (ate_inst.write(wb_addr, state & 0xF))


def set_state_end(ate_inst, state):
    """

    :param ate_inst:
    :param state:
    :return:
    """
    wb_addr = 0x00001000 + 0x401
    assert (ate_inst.write(wb_addr, state & 0xF))


def set_control_register(ate_inst, value):
    """

    :param ate_inst:
    :param value:
    :return:
    """
    wb_addr = 0x00001000 + 0x403
    assert (ate_inst.write(wb_addr, value & 0x1))


def get_status_register(ate_inst):
    """

    :param ate_inst:
    :return:
    """
    wb_addr = 0x00001000 + 0x404
    assert (ate_inst.read(wb_addr))
    return ate_inst.get_value() & 0x1


def scan_vector(ate_inst, tdi_vector, count, start, end):
    """

    :param ate_inst:
    :param tdi_vector:
    :param count:
    :param start:
    :param end:
    :return:
    """
    # Fill the JTAGCtrlMaster data buffer memory with tdi data
    data_width = 8
    addr_width = 10
    num_full_words = int(count // data_width)
    tdo_vector = bytearray((count + data_width - 1) // data_width)
    remainder = count % data_width
    addr = 0
    for i in range(num_full_words):
        data = tdi_vector[i]
        write_vector(ate_inst, addr, data)
        addr = addr + 1
    # Now write out the remaining bits that may be a partial word in size, but a full word needs to be written
    if remainder > 0:
        data = tdi_vector[num_full_words]
        write_vector(ate_inst, addr, data)
    # Now start the scan operation
    set_bit_count(ate_inst, count)
    set_state_start(ate_inst, start)
    set_state_end(ate_inst, end)
    set_control_register(ate_inst, 0x1)  # Start the scan
    status = get_status_register(ate_inst)
    while status != 0:
        status = get_status_register(ate_inst)
    set_control_register(ate_inst, 0x0)  # Stop the scan/Reset for next scan cycle trigger
    # Scan completed, now fetch the captured data
    addr = 0
    for i in range(num_full_words):
        data = read_vector(ate_inst, addr)
        tdo_vector[i] = int(data)
        addr = addr + 1
    # Now read out the remaining bits that may be a partial word in size, but a full word needs to be read
    if remainder > 0:
        data = read_vector(ate_inst, addr)
        # print(">>tdo_vector = ", tdo_vector)
        # print(">>num_full_words = ", num_full_words)
        # print(">>data = ", data)
        tdo_vector[num_full_words] = int(data)
    return tdo_vector


def ba_scan_ir(ate_inst, tdi_vector, count):
    """
    Scan the vector to the TAP with the IR data and capture the response in tdo_vector
    :param ate_inst:
    :param tdi_vector: Data to be shifted out as bytearray
    :param count: number of bits to shift
    :param tdo_vector: Data to be captured as bytearray
    :return:
    """
    start = SHIFT_IR
    end = RUN_TEST_IDLE
    return scan_vector(ate_inst, tdi_vector, count, start, end)


def ba_scan_dr(ate_inst, tdi_vector, count):
    """
    Scan the vector to the TAP with the DR data and capture the response in tdo_vector
    :param ate_inst:
    :param tdi_vector: Data to be shifted out as bytearray
    :param count: number of bits to shift
    :return:
    """
    start = SHIFT_DR
    end = RUN_TEST_IDLE
    return scan_vector(ate_inst, tdi_vector, count, start, end)


def scan_ir(ate_inst, count, tdi_string):
    """

    :param ate_inst:
    :param count:
    :param tdi_string:
    :return: tdo_string
    """
    if len(tdi_string) % 2:
        tdi_string = '0' + tdi_string
    # print("tdi_string = ", tdi_string)
    tdi_vector = bytearray.fromhex(tdi_string)
    # print("tdi_vector = ", tdi_vector)
    if len(tdi_vector) > 1:
        tdi_vector.reverse()
        # print("tdi_vector = ", tdi_vector)
    tdo_vector = ba_scan_ir(ate_inst, tdi_vector, count)
    # print("tdo_vector = ", tdo_vector)
    if len(tdo_vector) > 1:
        tdo_vector.reverse()
    tdo_string = tdo_vector.hex().upper()
    # print("tdo_string = ", tdo_string)
    if len(tdo_string) * 4 > count:
        tdo_string = tdo_string[1:]
        # print("tdo_string = ", tdo_string)
    return tdo_string


def scan_dr(ate_inst, count, tdi_string):
    """

    :param ate_inst:
    :param count:
    :param tdi_string:
    :return: tdo_string
    """
    if len(tdi_string) % 2:
        tdi_string = '0' + tdi_string
    # print("tdi_string = ", tdi_string)
    tdi_vector = bytearray.fromhex(tdi_string)
    # print("tdi_vector = ", tdi_vector)
    if len(tdi_vector) > 1:
        tdi_vector.reverse()
        # print("tdi_vector = ", tdi_vector)
    tdo_vector = ba_scan_dr(ate_inst, tdi_vector, count)
    # print("tdo_vector = ", tdo_vector)
    if len(tdo_vector) > 1:
        tdo_vector.reverse()
    tdo_string = tdo_vector.hex().upper()
    # print("tdo_string = ", tdo_string)
    if len(tdo_string) * 4 > count:
        tdo_string = tdo_string[1:]
        # print("tdo_string = ", tdo_string)
    return tdo_string


# Read/Write registers
def write_transmit_register(ate_inst, value):
    wb_addr = 0x00001C00 + 0
    assert (ate_inst.write(wb_addr, value))


def read_transmit_register(ate_inst):
    wb_addr = 0x00001C00 + 0
    assert (ate_inst.read(wb_addr))
    return ate_inst.get_value() & 0xFF


def write_receive_register(ate_inst, value):
    wb_addr = 0x00001C00 + 1
    assert (ate_inst.write(wb_addr, value))


def read_receive_register(ate_inst):
    wb_addr = 0x00001C00 + 1
    assert (ate_inst.read(wb_addr))
    return ate_inst.get_value() & 0xFF


def write_control_register(ate_inst, value):
    wb_addr = 0x00001C00 + 2
    assert (ate_inst.write(wb_addr, value))


def read_control_register(ate_inst):
    wb_addr = 0x00001C00 + 2
    assert (ate_inst.read(wb_addr))
    return ate_inst.get_value() & 0xFF


def write_status_register(ate_inst, value):
    wb_addr = 0x00001C00 + 3
    assert (ate_inst.write(wb_addr, value))


def read_status_register(ate_inst):
    wb_addr = 0x00001C00 + 3
    assert (ate_inst.read(wb_addr))
    return ate_inst.get_value() & 0xFF


START = 0x08
STOP = 0x10
MASTER_ACK = 0x04
WRITE = 0x02
EXECUTE = 0x01


class AcknowledgeError(Exception):
    def __init__(self, message):
        super(AcknowledgeError, self).__init__(message)


def i2c_write_reg(ate_inst, dev_address, reg_address, value):
    # write out device address
    write_transmit_register(ate_inst, (dev_address << 1) & 0xFE)
    write_control_register(ate_inst, 0x0B)  # START & WRITE & EXECUTE
    # write_control_register(ate_inst, 0x0A)  # START & WRITE & EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        # print("Acknowledge error detected during device address transmission.")
        raise AcknowledgeError("Acknowledge error detected during device address transmission.")
    # write out the register index
    write_transmit_register(ate_inst, reg_address)
    write_control_register(ate_inst, 0x03)  # WRITE & EXECUTE
    # write_control_register(ate_inst, 0x02)  # WRITE & EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        # print("Acknowledge error detected during register address transmission.")
        raise AcknowledgeError("Acknowledge error detected during register address transmission.")
    # write out the data byte
    write_transmit_register(ate_inst, value)
    write_control_register(ate_inst, 0x13)  # WRITE & EXECUTE & STOP
    # write_control_register(ate_inst, 0x12)  # WRITE & EXECUTE & STOP
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        # print("Acknowledge error detected during data transmission.")
        raise AcknowledgeError("Acknowledge error detected during data transmission.")
    # return True


def i2c_read_reg(ate_inst, dev_address, reg_address):
    # write out device address
    write_transmit_register(ate_inst, (dev_address << 1) & 0xFE)
    write_control_register(ate_inst, 0x0B)  # START & WRITE & EXECUTE
    # write_control_register(ate_inst, 0x0A)  # START & WRITE & EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        raise AcknowledgeError("Acknowledge error detected during device address transmission for write.")
    # write out the register index
    write_transmit_register(ate_inst, reg_address)
    write_control_register(ate_inst, 0x03)  # WRITE & EXECUTE
    # write_control_register(ate_inst, 0x02)  # WRITE & EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        raise AcknowledgeError("Acknowledge error detected during register address transmission.")
    # write out device address with read
    write_transmit_register(ate_inst, (dev_address << 1) | 1)
    write_control_register(ate_inst, 0x0B)  # START & WRITE & EXECUTE
    # write_control_register(ate_inst, 0x0A)  # START & WRITE & EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        raise AcknowledgeError("Acknowledge error detected during device address transmission for read.")
    # read byte from slave
    write_control_register(ate_inst, 0x15)  # EXECUTE & MASTER_ACK & STOP
    # write_control_register(ate_inst, 0x14)  # EXECUTE & MASTER_ACK & STOP
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:               # update_detector4, update_detector5, update_detector6, client_write, client_read

        raise AcknowledgeError("Acknowledge error detected during read transmission.")
    return read_receive_register(ate_inst)


def i2c_multibyte_write(ate_inst, dev_address, reg_address, data):
    print("I2C Write: At [{0:x}] = {0:x}".format(reg_address, data))
    # i2c address
    write_transmit_register(ate_inst, (dev_address << 1) & 0xFE)
    write_control_register(ate_inst, 0x0B)  # START & WRITE & EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        # print("Acknowledge error detected during device address transmission.")
        raise AcknowledgeError("Acknowledge error detected during device address transmission.")
    # write out the register index
    write_transmit_register(ate_inst, reg_address)
    write_control_register(ate_inst, 0x03)  # WRITE & EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        # print("Acknowledge error detected during register address transmission.")
        raise AcknowledgeError("Acknowledge error detected during register address transmission.")
    # data[31:24]
    write_transmit_register(ate_inst, (data >> 24) & 0xFF)
    write_control_register(ate_inst, 0x03)  # WRITE & EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        # print("Acknowledge error detected during data transmission.")
        raise AcknowledgeError("Acknowledge error detected during data transmission 1.")
    # data[23:16]
    write_transmit_register(ate_inst, (data >> 16) & 0xFF)
    write_control_register(ate_inst, 0x03)  # WRITE & EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        # print("Acknowledge error detected during data transmission.")
        raise AcknowledgeError("Acknowledge error detected during data transmission 2.")
    # data[15:8]
    write_transmit_register(ate_inst, (data >> 8) & 0xFF)
    write_control_register(ate_inst, 0x03)  # WRITE & EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        # print("Acknowledge error detected during data transmission.")
        raise AcknowledgeError("Acknowledge error detected during data transmission 3.")
    # data[7:0]
    write_transmit_register(ate_inst, data & 0xFF)
    write_control_register(ate_inst, 0x13)  # WRITE & EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        # print("Acknowledge error detected during data transmission.")
        raise AcknowledgeError("Acknowledge error detected during data transmission 4.")
    return True


def i2c_multibyte_read(ate_inst, dev_address, reg_address):
    retval = 0
    # write out device address
    write_transmit_register(ate_inst, (dev_address << 1) & 0xFE)
    write_control_register(ate_inst, 0x0B)  # START & WRITE & EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        raise AcknowledgeError("Acknowledge error detected during device address transmission.")
    # write out the register index
    write_transmit_register(ate_inst, reg_address)
    write_control_register(ate_inst, 0x03)  # WRITE & EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        raise AcknowledgeError("Acknowledge error detected during register address transmission.")
    # write out device address with read
    write_transmit_register(ate_inst, (dev_address << 1) | 1)
    write_control_register(ate_inst, 0x0B)  # START & WRITE & EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        raise AcknowledgeError("Acknowledge error detected during device address transmission for read.")
    # read byte from slave data[31:24]
    write_control_register(ate_inst, 0x01)  # EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        raise AcknowledgeError("Acknowledge error detected during data transmission 1.")
    value = read_receive_register(ate_inst)
    retval = (value << 24) & 0xFF000000

    # read byte from slave data[23:16]
    write_control_register(ate_inst, 0x01)  # EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        raise AcknowledgeError("Acknowledge error detected during data transmission 2.")
    value = read_receive_register(ate_inst)
    retval = retval | ((value << 16) & 0x00FF0000)
    # read byte from slave data[15:8]
    write_control_register(ate_inst, 0x01)  # EXECUTE
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        raise AcknowledgeError("Acknowledge error detected during data transmission 3.")
    value = read_receive_register(ate_inst)
    retval = retval | ((value << 8) & 0x0000FF00)
    # read byte from slave data[7:0]
    write_control_register(ate_inst, 0x15)  # EXECUTE & MASTER_ACK & STOP
    status = read_status_register(ate_inst)
    while status & 0x01:  # busy set
        status = read_status_register(ate_inst)
    # check for ack error
    if status & 0x02:
        raise AcknowledgeError("Acknowledge error detected during data transmission 4.")
    value = read_receive_register(ate_inst)
    retval = retval | (value & 0x000000FF)
    print("I2C Read: At [{0:x}] = {0:x}".format(reg_address, retval))
    return retval


# Read/Write registers
def spi_write_transmit_register(ate_inst, value):
    wb_addr = 0x00001C00 + 0x30
    assert (ate_inst.write(wb_addr, value))


def spi_read_transmit_register(ate_inst):
    wb_addr = 0x00001C00 + 0x30
    assert (ate_inst.read(wb_addr))
    return ate_inst.get_value()


def spi_write_receive_register(ate_inst, value):
    wb_addr = 0x00001C00 + 0x31
    assert (ate_inst.write(wb_addr, value))


def spi_read_receive_register(ate_inst):
    wb_addr = 0x00001C00 + 0x31
    assert (ate_inst.read(wb_addr))
    return ate_inst.get_value()


def spi_write(ate_inst, value):
    """

    :param ate_inst: ATE object instance
    :param value: 32 bit value to be written to the device
    :return:
    """
    spi_write_transmit_register(ate_inst, value)


def spi_read(ate_inst):
    return spi_read_receive_register(ate_inst)


def spitest_bench():
    gpio_if = BoardGPIOInterface()
    i2c_if = BoardI2CInterface()
    spi_if = BoardSPIInterface()
    board_inst = SPITest()
    board_inst.configure_gpio(gpio_if)
    board_inst.configure_i2c(i2c_if)
    board_inst.configure_spi(spi_if)
    ate_inst = ATE(board_inst)
    ate_inst.configure_gpio(gpio_if)
    ate_inst.configure_i2c(i2c_if)
    ate_inst.configure_spi(spi_if)
    ate_inst.start_simulation()
    sleep(1)

    # # GPIO Test
    # assert(ate_inst.write(0x00001800, 0x00000000))
    # assert(ate_inst.read(0x00001800))
    # assert(ate_inst.get_value() == 0x00000000)
    # assert(ate_inst.write(0x00001800, 0x00000015))
    # assert(ate_inst.read(0x00001800))
    # assert(ate_inst.get_value() == 0x00150015)
    # assert(ate_inst.write(0x00001800, 0x0000000A))
    # assert(ate_inst.read(0x00001800))
    # assert(ate_inst.get_value() == 0x000A000A)
    # assert(ate_inst.write(0x00001800, 0x00000000))
    # assert(ate_inst.read(0x00001800))
    # assert(ate_inst.get_value() == 0x00000000)
    #
    # # JTAG Test
    # assert(ate_inst.write(0x00001800, 0x00000001))  # Turn on WHITE LED to indicate scan start
    # tdo = scan_ir(ate_inst, 8, '55')
    # # print("tdo = ", tdo)
    # assert(tdo == '55')
    # assert(ate_inst.write(0x00001800, 0x00000002))  # Turn on RED LED to indicate scan start
    # tdo = scan_ir(ate_inst, 12, '0A55')
    # assert(tdo == 'A55')
    # assert(ate_inst.write(0x00001800, 0x00000004))  # Turn on GREEN LED to indicate scan start
    # tdo = scan_ir(ate_inst, 12, '5AA')
    # assert(tdo == '5AA')
    # assert(ate_inst.write(0x00001800, 0x00000008))  # Turn on YELLOW LED to indicate scan start
    # tdo = scan_dr(ate_inst, 8, '55')
    # assert(tdo == '55')
    # assert(ate_inst.write(0x00001800, 0x00000010))  # Turn on BLUE LED to indicate scan start
    # tdo = scan_dr(ate_inst, 12, 'AAA')
    # assert(tdo == 'AAA')
    # assert(ate_inst.write(0x00001800, 0x00000011))  # Turn on BLUE & WHITE LEDs to indicate scan start
    # tdo = scan_dr(ate_inst, 12, 'A55')
    # assert(tdo == 'A55')
    # assert(ate_inst.write(0x00001800, 0x00000012))  # Turn on BLUE & RED LEDs to indicate scan start
    # tdo = scan_dr(ate_inst, 12, '5AA')
    # assert(tdo == '5AA')
    # assert(ate_inst.write(0x00001800, 0x00000014))  # Turn on BLUE & GREEN LEDs to indicate scan start
    # tdo = scan_dr(ate_inst, 16 * 4, '0123456789ABCDEF')
    # assert(tdo == '0123456789ABCDEF')

    # # I2C Test set i2c master clock scale reg PRER = (48MHz / (5 * 400KHz) ) - 1
    # print("Testing register read/write")
    # i2c_write_reg(ate_inst, 0x3C, 0x01, 0xA5)
    # assert(i2c_read_reg(ate_inst, 0x3C, 0x01) == 0xA5)
    #
    # i2c_multibyte_write(ate_inst, 0x3C, 0, 0x89abcdef)
    # assert(i2c_multibyte_read(ate_inst, 0x3C, 0) == 0x89abcdef)
    # assert(i2c_multibyte_read(ate_inst, 0x3C, 4) == 0x12345678)
    #
    sleep(1)
    spi_write(ate_inst, 0x01345678)
    spi_write(ate_inst, 0x00BADEDA)
    assert(spi_read(ate_inst) == 0x01345678)
    spi_write(ate_inst, 0x02BEEFED)
    assert(spi_read(ate_inst) == 0x00BADEDA)
    spi_write(ate_inst, 0x01345678)
    assert(spi_read(ate_inst) == 0x02BEEFED)

    # End the simulation
    assert(ate_inst.terminate())
    print("Test complete!")


def main():
    spitest_bench()


if __name__ == '__main__':
    main()
