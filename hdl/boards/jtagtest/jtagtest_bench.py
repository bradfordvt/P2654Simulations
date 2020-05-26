"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

import binascii
from myhdl import *
from time import sleep
from hdl.boards.jtagtest.jtagtest import JTAGTest
from hdl.ate.ate import ATE
from hdl.hosts.jtaghost.JTAG_Ctrl_Master import SHIFT_DR, SHIFT_IR, RUN_TEST_IDLE
from hdl.boards.common.BoardGPIOInterface import BoardGPIOInterface
from hdl.boards.common.BoardJTAGInterface import BoardJTAGInterface


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


def jtagtest_bench():
    gpio_if = BoardGPIOInterface()
    jtag_if = BoardJTAGInterface()
    board_inst = JTAGTest()
    board_inst.configure_jtag(jtag_if)
    board_inst.configure_gpio(gpio_if)
    ate_inst = ATE(board_inst)
    ate_inst.configure_jtag(jtag_if)
    ate_inst.configure_gpio(gpio_if)
    ate_inst.start_simulation()
    sleep(1)

    # GPIO Test
    assert(ate_inst.write(0x00001800, 0x00000000))
    assert(ate_inst.read(0x00001800))
    assert(ate_inst.get_value() == 0x00000000)
    assert(ate_inst.write(0x00001800, 0x00000015))
    assert(ate_inst.read(0x00001800))
    assert(ate_inst.get_value() == 0x00150015)
    assert(ate_inst.write(0x00001800, 0x0000000A))
    assert(ate_inst.read(0x00001800))
    assert(ate_inst.get_value() == 0x000A000A)
    assert(ate_inst.write(0x00001800, 0x00000000))
    assert(ate_inst.read(0x00001800))
    assert(ate_inst.get_value() == 0x00000000)

    # JTAG Test
    assert(ate_inst.write(0x00001800, 0x00000001))  # Turn on WHITE LED to indicate scan start
    tdo = scan_ir(ate_inst, 8, '55')
    # print("tdo = ", tdo)
    assert(tdo == '55')
    assert(ate_inst.write(0x00001800, 0x00000002))  # Turn on RED LED to indicate scan start
    tdo = scan_ir(ate_inst, 12, '0A55')
    assert(tdo == 'A55')
    assert(ate_inst.write(0x00001800, 0x00000004))  # Turn on GREEN LED to indicate scan start
    tdo = scan_ir(ate_inst, 12, '5AA')
    assert(tdo == '5AA')
    assert(ate_inst.write(0x00001800, 0x00000008))  # Turn on YELLOW LED to indicate scan start
    tdo = scan_dr(ate_inst, 8, '55')
    assert(tdo == '55')
    assert(ate_inst.write(0x00001800, 0x00000010))  # Turn on BLUE LED to indicate scan start
    tdo = scan_dr(ate_inst, 12, 'AAA')
    assert(tdo == 'AAA')
    assert(ate_inst.write(0x00001800, 0x00000011))  # Turn on BLUE & WHITE LEDs to indicate scan start
    tdo = scan_dr(ate_inst, 12, 'A55')
    assert(tdo == 'A55')
    assert(ate_inst.write(0x00001800, 0x00000012))  # Turn on BLUE & RED LEDs to indicate scan start
    tdo = scan_dr(ate_inst, 12, '5AA')
    assert(tdo == '5AA')
    assert(ate_inst.write(0x00001800, 0x00000014))  # Turn on BLUE & GREEN LEDs to indicate scan start
    tdo = scan_dr(ate_inst, 16 * 4, '0123456789ABCDEF')
    assert(tdo == '0123456789ABCDEF')

    # End the simulation
    assert(ate_inst.terminate())


def main():
    jtagtest_bench()


if __name__ == '__main__':
    main()
