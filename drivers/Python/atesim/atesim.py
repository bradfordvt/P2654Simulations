"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""
import threading
from subprocess import Popen, PIPE

import telnetlib
from time import sleep
from hdl.hosts.jtaghost.JTAG_Ctrl_Master import SHIFT_DR, SHIFT_IR, RUN_TEST_IDLE
from hdl.hosts.jtaghost.tapsim import *


simip = "127.0.0.1"
simport = 5023


class ATETelnetClient:
    def __init__(self):
        self.timeout = 60
        self.ip = None
        self.port = None
        self.tn_inst = None
        
    def connect(self, ip, port):
        self.tn_inst = telnetlib.Telnet(ip, port)
        sleep(0.05)
        s = b"EXIT\n"
        self.tn_inst.write(s)
        resp = self.tn_inst.read_all()
        sleep(0.05)
        self.tn_inst.close()
        sleep(0.05)
        self.tn_inst.open(ip, port)
        sleep(0.05)

    def read_until(self, s):
        """
        Helper function specialization to read data from the Simulator until a match is found with s.
        @param s: A string of characters to expect from the Simulator following a command execution.
        """
        resp = self.tn_inst.read_until(s.encode("ascii"), self.timeout).decode("ascii")
        if len(resp) == 0:
            raise TimeoutError
        return resp

    def read_all(self):
        return self.tn_inst.read_all().decode('ascii')
    
    def write(self, s):
        """
        Helper function specialization to write data to the Simulator.
        @param s: The data to be sent to the Simulator.
        """
        return self.tn_inst.write(s.encode("ascii"))
    
    def close(self):
        """
        Helper function specialization to clean up and close the connection to the Simulator.
        """
        self.tn_inst.close()


class ATE:
    def __init__(self, ip="127.0.0.1", port=5023):
        self.tn_inst = None
        self.ip = ip
        self.port = port
        self.resp = ""
        self.value = None
        self.error = None
        self.process = None
        self.stdout = None
        self.stderr = None
        self.stdin = None

    def start_simulation(self):
        x = threading.Thread(target=self.__simulator)
        x.start()
        sleep(1)

    def stop_simulation(self):
        if self.process is not None:
            self.process.stdin.write('\x03'.encode())
            self.process.stdin.flush()
            self.process.stdin.close()
            self.process.terminate()
            self.process.wait(timeout=0.2)

    def __simulator(self):
        self.process = Popen(['/home/bvt/PycharmProjects/P2654Simulations/venv/bin/python3',
                              '/home/bvt/PycharmProjects/P2654Simulations/simservice/simservice.py'],
                             stdin=PIPE,
                             stdout=PIPE,
                             stderr=PIPE,
                             universal_newlines=True,
                             bufsize=0)
        # fetch output
        for line in self.process.stdout:
            print(line),

    def connect(self, board):
        # Start up the simserver application in the background
        # Create the TelnetClient interface to the simserver
        self.tn_inst = ATETelnetClient()
        # Connect to the simserver
        self.tn_inst.connect(self.ip, self.port)
        # self.resp = self.tn_inst.read_until("P2654> ")
        # Send command to start up the simulation of the prescribed board
        self.tn_inst.write("STARTSIM {:s}\n".format(board))
        # self.resp = self.tn_inst.read_until("P2654> ")
        self.resp = self.tn_inst.read_until("OK\r\n")
        # return True if self.resp.find("OK") >= 0 else False
        return True if len(self.resp) >= 0 else False

    def write(self, adr, data):
        self.tn_inst.write("MW 0x{:X} 0x{:X}\n".format(adr, data))
        self.resp = self.tn_inst.read_until("OK\r\n")
        return True if len(self.resp) >= 0 else False

    def read(self, adr):
        self.tn_inst.write("MR 0x{:X}\n".format(adr))
        try:
            self.resp = self.tn_inst.read_until("OK\r\n")
            slist = self.resp.split()
            try:
                self.value = int(slist[0], 16)
            except ValueError as e:
                self.error = str(e)
                return False
        except TimeoutError as e:
            self.error = str(e)
            return False
        return True

    def get_value(self):
        return self.value

    def get_error(self):
        return self.error

    def terminate(self):
        self.tn_inst.write("STOPSIM\n")
        self.resp = self.tn_inst.read_until("OK\r\n")
        return True if self.resp.find("Simulation has stopped.") >= 0 else False

    def close(self):
        self.tn_inst.write("EXIT\n")
        self.resp = self.tn_inst.read_all()
        self.tn_inst.close()
        return True if self.resp.find("Goodbye") >= 0 else False

    def get_last_response(self):
        return self.resp


class AcknowledgeError(Exception):
    def __init__(self, message):
        super(AcknowledgeError, self).__init__(message)


class GPIOController:
    def __init__(self, ate_inst):
        self.ate_inst = ate_inst

    def write(self, val):
        return self.ate_inst.write(0x00001800, val)

    def read(self):
        return self.ate_inst.read(0x00001800)

    def get_value(self):
        return self.ate_inst.get_value()

    def get_error(self):
        return self.ate_inst.get_error()


class JTAGController:
    def __init__(self, ate_inst):
        self.ate_inst = ate_inst

    def __write_vector_segment(self, addr, data):
        assert (addr < 0x1000)
        wb_addr = 0x00001000 + addr
        ret = self.ate_inst.write(wb_addr, data & 0xFF)
        if not ret:
            raise AcknowledgeError("Write Error: " + self.ate_inst.get_last_response())

    def __read_vector_segment(self, addr):
        assert (addr < 0x1000)
        wb_addr = 0x00001000 + addr
        try:
            if self.ate_inst.read(wb_addr):
                return self.ate_inst.get_value()
            else:
                print(self.ate_inst.get_error())
                return None
        except ValueError as e:
            raise AcknowledgeError(e.__str__() + " " + self.ate_inst.get_last_response())

    def __set_bit_count(self, count):
        wb_addr = 0x00001000 + 0x402
        self.ate_inst.write(wb_addr, count & 0xFFFF)

    def __set_state_start(self, state):
        wb_addr = 0x00001000 + 0x400
        self.ate_inst.write(wb_addr, state & 0xF)

    def __set_state_end(self, state):
        wb_addr = 0x00001000 + 0x401
        self.ate_inst.write(wb_addr, state & 0xF)

    def __set_control_register(self, value):
        wb_addr = 0x00001000 + 0x403
        self.ate_inst.write(wb_addr, value & 0x1)

    def __get_status_register(self):
        wb_addr = 0x00001000 + 0x404
        if self.ate_inst.read(wb_addr) & 0x1:
            return self.ate_inst.get_value()
        else:
            print(self.ate_inst.get_error())
            return None

    def __scan_vector(self, tdi_vector, count, start, end):
        # Fill the JTAGCtrlMaster data buffer memory with tdi data
        data_width = 8
        addr_width = 10
        num_full_words = int(count // data_width)
        tdo_vector = bytearray((count + data_width - 1) // data_width)
        remainder = count % data_width
        addr = 0
        for i in range(num_full_words):
            data = tdi_vector[i]
            self.__write_vector_segment(addr, data)
            addr = addr + 1
        # Now write out the remaining bits that may be a partial word in size, but a full word needs to be written
        if remainder > 0:
            data = tdi_vector[num_full_words]
            self.__write_vector_segment(addr, data)
        # Now start the scan operation
        self.__set_bit_count(count)
        self.__set_state_start(start)
        self.__set_state_end(end)
        self.__set_control_register(0x1)  # Start the scan
        status = self.__get_status_register()
        while status != 0:
            status = self.__get_status_register()
        self.__set_control_register(0x0)  # Stop the scan/Reset for next scan cycle trigger
        # Scan completed, now fetch the captured data
        addr = 0
        for i in range(num_full_words):
            data = self.__read_vector_segment(addr)
            tdo_vector[i] = int(data)
            addr = addr + 1
        # Now read out the remaining bits that may be a partial word in size, but a full word needs to be read
        if remainder > 0:
            data = self.__read_vector_segment(addr)
            # print(">>tdo_vector = ", tdo_vector)
            # print(">>num_full_words = ", num_full_words)
            # print(">>data = ", data)
            tdo_vector[num_full_words] = int(data)
        return tdo_vector

    def ba_scan_ir(self, tdi_vector, count):
        """
        Scan the vector to the TAP with the IR data and capture the response in tdo_vector
        :param tdi_vector: Data to be shifted out as bytearray
        :param count: number of bits to shift
        :return: tdo_vector: Data to be captured as bytearray
        """
        start = SHIFT_IR
        end = RUN_TEST_IDLE
        return self.__scan_vector(tdi_vector, count, start, end)

    def ba_scan_dr(self, tdi_vector, count):
        """
        Scan the vector to the TAP with the DR data and capture the response in tdo_vector
        :param ate_inst:
        :param tdi_vector: Data to be shifted out as bytearray
        :param count: number of bits to shift
        :return: tdo_vector: Data to be captured as bytearray
        """
        start = SHIFT_DR
        end = RUN_TEST_IDLE
        return self.__scan_vector(tdi_vector, count, start, end)

    def scan_ir(self, count, tdi_string):
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
        tdo_vector = self.ba_scan_ir(tdi_vector, count)
        # print("tdo_vector = ", tdo_vector)
        if len(tdo_vector) > 1:
            tdo_vector.reverse()
        tdo_string = tdo_vector.hex().upper()
        # print("tdo_string = ", tdo_string)
        if len(tdo_string) * 4 > count:
            tdo_string = tdo_string[1:]
            # print("tdo_string = ", tdo_string)
        return tdo_string

    def scan_dr(self, count, tdi_string):
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
        tdo_vector = self.ba_scan_dr(tdi_vector, count)
        # print("tdo_vector = ", tdo_vector)
        if len(tdo_vector) > 1:
            tdo_vector.reverse()
        tdo_string = tdo_vector.hex().upper()
        # print("tdo_string = ", tdo_string)
        if len(tdo_string) * 4 > count:
            tdo_string = tdo_string[1:]
            # print("tdo_string = ", tdo_string)
        return tdo_string

    def runtest(self, ticks):
        start = RUN_TEST_IDLE
        end = RUN_TEST_IDLE
        blocks = ticks // 1024
        rem = ticks % 1024
        for i in range(blocks):
            self.__set_bit_count(1024)
            self.__set_state_start(start)
            self.__set_state_end(end)
            self.__set_control_register(0x1)  # Start the scan
            status = self.__get_status_register()
            while status != 0:
                status = self.__get_status_register()
            self.__set_control_register(0x0)  # Stop the scan/Reset for next scan cycle trigger
        self.__set_bit_count(rem)
        self.__set_state_start(start)
        self.__set_state_end(end)
        self.__set_control_register(0x1)  # Start the scan
        status = self.__get_status_register()
        while status != 0:
            status = self.__get_status_register()
        self.__set_control_register(0x0)  # Stop the scan/Reset for next scan cycle trigger


class JTAGController2:
    def __init__(self, ate_inst):
        self.ate_inst = ate_inst

    def __write_vector_segment(self, addr, data):
        assert (addr < 0x3000)
        wb_addr = 0x00003000 + addr
        ret = self.ate_inst.write(wb_addr, data & 0xFF)
        if not ret:
            raise AcknowledgeError("Write Error: " + self.ate_inst.get_last_response())

    def __read_vector_segment(self, addr):
        assert (addr < 0x3000)
        wb_addr = 0x00003000 + addr
        try:
            if self.ate_inst.read(wb_addr):
                return self.ate_inst.get_value()
            else:
                print(self.ate_inst.get_error())
                return None
        except ValueError as e:
            raise AcknowledgeError(e.__str__() + " " + self.ate_inst.get_last_response())

    def __set_chain_length(self, count):
        wb_addr = 0x00003000 + 0x402
        self.ate_inst.write(wb_addr, count & 0xFFFF)

    def __set_state_start(self, state):
        wb_addr = 0x00003000 + 0x400
        self.ate_inst.write(wb_addr, state & 0xF)

    def __set_state_end(self, state):
        wb_addr = 0x00003000 + 0x401
        self.ate_inst.write(wb_addr, state & 0xF)

    def __set_control_register(self, value):
        wb_addr = 0x00003000 + 0x403
        self.ate_inst.write(wb_addr, value & 0x1)

    def __get_status_register(self):
        wb_addr = 0x00003000 + 0x404
        if self.ate_inst.read(wb_addr) & 0x1:
            return self.ate_inst.get_value()
        else:
            print(self.ate_inst.get_error())
            return None

    def __set_command(self, command):
        wb_addr = 0x00003000 + 0x405
        self.ate_inst.write(wb_addr, command & 0xF)

    def __scan_vector(self, tdi_vector, count, start, end):
        # Fill the JTAGCtrlMaster data buffer memory with tdi data
        data_width = 8
        addr_width = 10
        num_full_words = int(count // data_width)
        tdo_vector = bytearray((count + data_width - 1) // data_width)
        remainder = count % data_width
        addr = 0
        for i in range(num_full_words):
            data = tdi_vector[i]
            self.__write_vector_segment(addr, data)
            addr = addr + 1
        # Now write out the remaining bits that may be a partial word in size, but a full word needs to be written
        if remainder > 0:
            data = tdi_vector[num_full_words]
            self.__write_vector_segment(addr, data)
        # Now start the scan operation
        self.__set_chain_length(count)
        self.__set_state_start(start)
        self.__set_state_end(end)
        self.__set_command(SCAN)
        self.__set_control_register(0x1)  # Start the scan
        status = self.__get_status_register()
        while status != 0:
            status = self.__get_status_register()
        self.__set_control_register(0x0)  # Stop the scan/Reset for next scan cycle trigger
        # Scan completed, now fetch the captured data
        addr = 0
        for i in range(num_full_words):
            data = self.__read_vector_segment(addr)
            tdo_vector[i] = int(data)
            addr = addr + 1
        # Now read out the remaining bits that may be a partial word in size, but a full word needs to be read
        if remainder > 0:
            data = self.__read_vector_segment(addr)
            # print(">>tdo_vector = ", tdo_vector)
            # print(">>num_full_words = ", num_full_words)
            # print(">>data = ", data)
            tdo_vector[num_full_words] = int(data)
        return tdo_vector

    def ba_scan_ir(self, tdi_vector, count):
        """
        Scan the vector to the TAP with the IR data and capture the response in tdo_vector
        :param tdi_vector: Data to be shifted out as bytearray
        :param count: number of bits to shift
        :return: tdo_vector: Data to be captured as bytearray
        """
        start = SI_SHIFT_IR
        end = SI_RUN_TEST_IDLE
        return self.__scan_vector(tdi_vector, count, start, end)

    def ba_scan_dr(self, tdi_vector, count):
        """
        Scan the vector to the TAP with the DR data and capture the response in tdo_vector
        :param ate_inst:
        :param tdi_vector: Data to be shifted out as bytearray
        :param count: number of bits to shift
        :return: tdo_vector: Data to be captured as bytearray
        """
        start = SI_SHIFT_DR
        end = SI_RUN_TEST_IDLE
        return self.__scan_vector(tdi_vector, count, start, end)

    def scan_ir(self, count, tdi_string):
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
        tdo_vector = self.ba_scan_ir(tdi_vector, count)
        # print("tdo_vector = ", tdo_vector)
        if len(tdo_vector) > 1:
            tdo_vector.reverse()
        tdo_string = tdo_vector.hex().upper()
        # print("tdo_string = ", tdo_string)
        if len(tdo_string) * 4 > count:
            tdo_string = tdo_string[1:]
            # print("tdo_string = ", tdo_string)
        return tdo_string

    def scan_dr(self, count, tdi_string):
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
        tdo_vector = self.ba_scan_dr(tdi_vector, count)
        # print("tdo_vector = ", tdo_vector)
        if len(tdo_vector) > 1:
            tdo_vector.reverse()
        tdo_string = tdo_vector.hex().upper()
        # print("tdo_string = ", tdo_string)
        if len(tdo_string) * 4 > count:
            tdo_string = tdo_string[1:]
            # print("tdo_string = ", tdo_string)
        return tdo_string

    def runtest(self, ticks):
        start = SI_RUN_TEST_IDLE
        end = SI_RUN_TEST_IDLE
        blocks = ticks // 1024
        rem = ticks % 1024
        for i in range(blocks):
            self.__set_chain_length(1024)
            self.__set_state_start(start)
            self.__set_state_end(end)
            self.__set_command(SCAN)
            self.__set_control_register(0x1)  # Start the scan
            status = self.__get_status_register()
            while status != 0:
                status = self.__get_status_register()
            self.__set_control_register(0x0)  # Stop the scan/Reset for next scan cycle trigger
        self.__set_chain_length(rem)
        self.__set_state_start(start)
        self.__set_state_end(end)
        self.__set_command(SCAN)
        self.__set_control_register(0x1)  # Start the scan
        status = self.__get_status_register()
        while status != 0:
            status = self.__get_status_register()
        self.__set_control_register(0x0)  # Stop the scan/Reset for next scan cycle trigger


class I2CController:
    def __init__(self, ate_inst):
        self.ate_inst = ate_inst

    # Read/Write registers
    def __write_transmit_register(self, value):
        wb_addr = 0x00001C00 + 0
        ret = self.ate_inst.write(wb_addr, value)
        if not ret:
            raise AcknowledgeError("Write Error: " + self.ate_inst.get_last_response())

    def __read_transmit_register(self):
        wb_addr = 0x00001C00 + 0
        try:
            if self.ate_inst.read(wb_addr):
                return self.ate_inst.get_value() & 0xFF
            else:
                print(self.ate_inst.get_error())
                return None
        except ValueError as e:
            raise AcknowledgeError(e.__str__() + " " + self.ate_inst.get_last_response())

    def __write_receive_register(self, value):
        wb_addr = 0x00001C00 + 1
        ret = self.ate_inst.write(wb_addr, value)
        if not ret:
            raise AcknowledgeError("Write Error: " + self.ate_inst.get_last_response())

    def __read_receive_register(self):
        wb_addr = 0x00001C00 + 1
        try:
            if self.ate_inst.read(wb_addr):
                return self.ate_inst.get_value() & 0xFF
            else:
                print(self.ate_inst.get_error())
                return None
        except ValueError as e:
            raise AcknowledgeError(e.__str__() + " " + self.ate_inst.get_last_response())

    def __write_control_register(self, value):
        wb_addr = 0x00001C00 + 2
        ret = self.ate_inst.write(wb_addr, value)
        if not ret:
            raise AcknowledgeError("Write Error: " + self.ate_inst.get_last_response())

    def __read_control_register(self):
        wb_addr = 0x00001C00 + 2
        try:
            if self.ate_inst.read(wb_addr):
                return self.ate_inst.get_value() & 0xFF
            else:
                print(self.ate_inst.get_error())
                return None
        except ValueError as e:
            raise AcknowledgeError(e.__str__() + " " + self.ate_inst.get_last_response())

    def __write_status_register(self, value):
        wb_addr = 0x00001C00 + 3
        ret = self.ate_inst.write(wb_addr, value)
        if not ret:
            raise AcknowledgeError("Write Error: " + self.ate_inst.get_last_response())

    def __read_status_register(self):
        wb_addr = 0x00001C00 + 3
        try:
            if self.ate_inst.read(wb_addr):
                return self.ate_inst.get_value() & 0xFF
            else:
                print(self.ate_inst.get_error())
                return None
        except ValueError as e:
            raise AcknowledgeError(e.__str__() + " " + self.ate_inst.get_last_response())

    START = 0x08
    STOP = 0x10
    MASTER_ACK = 0x04
    WRITE = 0x02
    EXECUTE = 0x01

    def i2c_write_reg(self, dev_address, reg_address, value):
        # write out device address
        self.__write_transmit_register((dev_address << 1) & 0xFE)
        self.__write_control_register(0x0B)  # START & WRITE & EXECUTE
        # write_control_register(ate_inst, 0x0A)  # START & WRITE & EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            # print("Acknowledge error detected during device address transmission.")
            raise AcknowledgeError("Acknowledge error detected during device address transmission.")
        # write out the register index
        self.__write_transmit_register(reg_address)
        self.__write_control_register(0x03)  # WRITE & EXECUTE
        # write_control_register(ate_inst, 0x02)  # WRITE & EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            # print("Acknowledge error detected during register address transmission.")
            raise AcknowledgeError("Acknowledge error detected during register address transmission.")
        # write out the data byte
        self.__write_transmit_register(value)
        self.__write_control_register(0x13)  # WRITE & EXECUTE & STOP
        # write_control_register(ate_inst, 0x12)  # WRITE & EXECUTE & STOP
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            # print("Acknowledge error detected during data transmission.")
            raise AcknowledgeError("Acknowledge error detected during data transmission.")
        # return True

    def i2c_read_reg(self, dev_address, reg_address):
        # write out device address
        self.__write_transmit_register((dev_address << 1) & 0xFE)
        self.__write_control_register(0x0B)  # START & WRITE & EXECUTE
        # write_control_register(ate_inst, 0x0A)  # START & WRITE & EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            raise AcknowledgeError("Acknowledge error detected during device address transmission for write.")
        # write out the register index
        self.__write_transmit_register(reg_address)
        self.__write_control_register(0x03)  # WRITE & EXECUTE
        # write_control_register(ate_inst, 0x02)  # WRITE & EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            raise AcknowledgeError("Acknowledge error detected during register address transmission.")
        # write out device address with read
        self.__write_transmit_register((dev_address << 1) | 1)
        self.__write_control_register(0x0B)  # START & WRITE & EXECUTE
        # write_control_register(ate_inst, 0x0A)  # START & WRITE & EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            raise AcknowledgeError("Acknowledge error detected during device address transmission for read.")
        # read byte from slave
        self.__write_control_register(0x15)  # EXECUTE & MASTER_ACK & STOP
        # write_control_register(ate_inst, 0x14)  # EXECUTE & MASTER_ACK & STOP
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:  # update_detector4, update_detector5, update_detector6, client_write, client_read

            raise AcknowledgeError("Acknowledge error detected during read transmission.")
        return self.__read_receive_register()

    def i2c_multibyte_write(self, dev_address, reg_address, data):
        print("I2C Write: At [{0:x}] = {0:x}".format(reg_address, data))
        # i2c address
        self.__write_transmit_register((dev_address << 1) & 0xFE)
        self.__write_control_register(0x0B)  # START & WRITE & EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            # print("Acknowledge error detected during device address transmission.")
            raise AcknowledgeError("Acknowledge error detected during device address transmission.")
        # write out the register index
        self.__write_transmit_register(reg_address)
        self.__write_control_register(0x03)  # WRITE & EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            # print("Acknowledge error detected during register address transmission.")
            raise AcknowledgeError("Acknowledge error detected during register address transmission.")
        # data[31:24]
        self.__write_transmit_register((data >> 24) & 0xFF)
        self.__write_control_register(0x03)  # WRITE & EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            # print("Acknowledge error detected during data transmission.")
            raise AcknowledgeError("Acknowledge error detected during data transmission 1.")
        # data[23:16]
        self.__write_transmit_register((data >> 16) & 0xFF)
        self.__write_control_register(0x03)  # WRITE & EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            # print("Acknowledge error detected during data transmission.")
            raise AcknowledgeError("Acknowledge error detected during data transmission 2.")
        # data[15:8]
        self.__write_transmit_register((data >> 8) & 0xFF)
        self.__write_control_register(0x03)  # WRITE & EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            # print("Acknowledge error detected during data transmission.")
            raise AcknowledgeError("Acknowledge error detected during data transmission 3.")
        # data[7:0]
        self.__write_transmit_register(data & 0xFF)
        self.__write_control_register(0x13)  # WRITE & EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            # print("Acknowledge error detected during data transmission.")
            raise AcknowledgeError("Acknowledge error detected during data transmission 4.")
        return True

    def i2c_multibyte_read(self, dev_address, reg_address):
        retval = 0
        # write out device address
        self.__write_transmit_register((dev_address << 1) & 0xFE)
        self.__write_control_register(0x0B)  # START & WRITE & EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            raise AcknowledgeError("Acknowledge error detected during device address transmission.")
        # write out the register index
        self.__write_transmit_register(reg_address)
        self.__write_control_register(0x03)  # WRITE & EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            raise AcknowledgeError("Acknowledge error detected during register address transmission.")
        # write out device address with read
        self.__write_transmit_register((dev_address << 1) | 1)
        self.__write_control_register(0x0B)  # START & WRITE & EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            raise AcknowledgeError("Acknowledge error detected during device address transmission for read.")
        # read byte from slave data[31:24]
        self.__write_control_register(0x01)  # EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            raise AcknowledgeError("Acknowledge error detected during data transmission 1.")
        value = self.__read_receive_register()
        retval = (value << 24) & 0xFF000000

        # read byte from slave data[23:16]
        self.__write_control_register(0x01)  # EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            raise AcknowledgeError("Acknowledge error detected during data transmission 2.")
        value = self.__read_receive_register()
        retval = retval | ((value << 16) & 0x00FF0000)
        # read byte from slave data[15:8]
        self.__write_control_register(0x01)  # EXECUTE
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            raise AcknowledgeError("Acknowledge error detected during data transmission 3.")
        value = self.__read_receive_register()
        retval = retval | ((value << 8) & 0x0000FF00)
        # read byte from slave data[7:0]
        self.__write_control_register(0x15)  # EXECUTE & MASTER_ACK & STOP
        status = self.__read_status_register()
        while status & 0x01:  # busy set
            status = self.__read_status_register()
        # check for ack error
        if status & 0x02:
            raise AcknowledgeError("Acknowledge error detected during data transmission 4.")
        value = self.__read_receive_register()
        retval = retval | (value & 0x000000FF)
        print("I2C Read: At [{0:x}] = {0:x}".format(reg_address, retval))
        return retval


class SPIController:
    def __init__(self, ate_inst):
        self.ate_inst = ate_inst

    # Read/Write registers
    def __spi_write_transmit_register(self, value):
        wb_addr = 0x00001C00 + 0x30
        ret = self.ate_inst.write(wb_addr, value)
        if not ret:
            raise AcknowledgeError("Write Error: " + self.ate_inst.get_last_response())

    def __spi_read_transmit_register(self):
        wb_addr = 0x00001C00 + 0x30
        try:
            if self.ate_inst.read(wb_addr):
                return self.ate_inst.get_value()
            else:
                print(self.ate_inst.get_error())
                return None
        except ValueError as e:
            raise AcknowledgeError(e.__str__() + " " + self.ate_inst.get_last_response())

    def __spi_write_receive_register(self, value):
        wb_addr = 0x00001C00 + 0x31
        ret = self.ate_inst.write(wb_addr, value)
        if not ret:
            raise AcknowledgeError("Write Error: " + self.ate_inst.get_last_response())

    def __spi_read_receive_register(self):
        wb_addr = 0x00001C00 + 0x31
        try:
            if self.ate_inst.read(wb_addr):
                return self.ate_inst.get_value()
            else:
                print(self.ate_inst.get_error())
                return None
        except ValueError as e:
            raise AcknowledgeError(e.__str__() + " " + self.ate_inst.get_last_response())

    def spi_write(self, value):
        """

        :param ate_inst: ATE object instance
        :param value: 32 bit value to be written to the device
        :return:
        """
        self.__spi_write_transmit_register(value)

    def spi_read(self):
        return self.__spi_read_receive_register()






