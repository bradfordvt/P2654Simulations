import unittest
from drivers.Python.atesim.atesim import ATE, JTAGController, I2CController, SPIController, ATETelnetClient
from time import sleep
import telnetlib


class MyTestCase(unittest.TestCase):
    def test_simservicetelnetlib001(self):
        ip = "127.0.0.1"
        port = 5023
        tn_inst = telnetlib.Telnet(ip, port)
        sleep(0.05)
        s = b"EXIT\n"
        tn_inst.write(s)
        resp = tn_inst.read_until(b"Goodbye\r\n", 30)
        sleep(0.05)
        tn_inst.close()
        sleep(0.05)
        tn_inst.open(ip, port)
        sleep(0.05)
        s = b"OK\r\n"
        resp = tn_inst.read_until(s, 30).decode("ascii")
        if len(resp) == 0:
            print("Timeout error!")
        self.assertTrue(len(resp) > 0)
        print("Before resp")
        print(resp)
        print("After resp")
        s = b"EXIT\n"
        tn_inst.write(s)
        # sleep(3)
        tn_inst.close()

    def test_simservicetelnetlib002(self):
        ip = "127.0.0.1"
        port = 5023
        tn_inst = telnetlib.Telnet(ip, port)
        sleep(0.05)
        s = b"EXIT\n"
        tn_inst.write(s)
        resp = tn_inst.read_all()
        sleep(0.05)
        tn_inst.close()
        sleep(0.05)
        tn_inst.open(ip, port)
        sleep(0.05)
        s = b"STARTSIM SPITest\n"
        tn_inst.write(s)
        s = b"STOPSIM\n"
        tn_inst.write(s)
        s = b"EXIT\n"
        tn_inst.write(s)
        resp = tn_inst.read_all()
        print(resp)
        tn_inst.close()

    def test_simservicetelnetlib003(self):
        ip = "127.0.0.1"
        port = 5023
        tn_inst = telnetlib.Telnet(ip, port)
        sleep(0.05)
        s = b"EXIT\n"
        tn_inst.write(s)
        resp = tn_inst.read_all()
        sleep(0.05)
        tn_inst.close()
        sleep(0.05)
        tn_inst.open(ip, port)
        sleep(0.05)
        s = b"STARTSIM SPITest\n"
        tn_inst.write(s)
        s = b"OK\r\n"
        resp = tn_inst.read_until(s, 10).decode("ascii")
        if len(resp) == 0:
            print("Timeout error!")
        self.assertTrue(len(resp) > 0)
        print("Before resp")
        print(resp)
        print("After resp")
        s = b"STOPSIM\n"
        tn_inst.write(s)
        s = b"OK\r\n"
        resp = tn_inst.read_until(s, 10).decode("ascii")
        if len(resp) == 0:
            print("Timeout error!")
        self.assertTrue(len(resp) > 0)
        print("Before resp")
        print(resp)
        print("After resp")
        s = b"EXIT\n"
        tn_inst.write(s)
        resp = tn_inst.read_all()
        print(resp)
        tn_inst.close()

    def test_simservicetelnetlib004(self):
        ip = "127.0.0.1"
        port = 5023
        tn_inst = telnetlib.Telnet(ip, port)
        sleep(0.05)
        s = b"EXIT\n"
        tn_inst.write(s)
        resp = tn_inst.read_all()
        sleep(0.05)
        tn_inst.close()
        sleep(0.05)
        tn_inst.open(ip, port)
        sleep(0.05)
        s = "STARTSIM SPITest\n"
        tn_inst.write(s.encode('ascii'))
        s = b"OK\r\n"
        resp = tn_inst.read_until(s, 10).decode("ascii")
        if len(resp) == 0:
            print("Timeout error!")
        self.assertTrue(len(resp) > 0)
        print("Before resp")
        print(resp)
        print("After resp")
        s = "STOPSIM\n"
        tn_inst.write(s.encode('ascii'))
        s = b"OK\r\n"
        resp = tn_inst.read_until(s, 10).decode("ascii")
        if len(resp) == 0:
            print("Timeout error!")
        self.assertTrue(len(resp) > 0)
        print("Before resp")
        print(resp)
        print("After resp")
        s = "EXIT\n"
        tn_inst.write(s.encode('ascii'))
        resp = tn_inst.read_all()
        print(resp)
        tn_inst.close()

    def test_simservicetelnetlib005(self):
        ip = "127.0.0.1"
        port = 5023
        tn_inst = telnetlib.Telnet(ip, port)
        sleep(0.05)
        s = b"EXIT\n"
        tn_inst.write(s)
        resp = tn_inst.read_all()
        sleep(0.05)
        tn_inst.close()
        sleep(0.05)
        tn_inst.open(ip, port)
        sleep(0.05)
        s = "STARTSIM SPITest\n"
        tn_inst.write(s.encode('ascii'))
        s = "OK\r\n"
        resp = tn_inst.read_until(s.encode('ascii'), 10).decode("ascii")
        if len(resp) == 0:
            print("Timeout error!")
        self.assertTrue(len(resp) > 0)
        print("Before resp")
        print(resp)
        print("After resp")
        s = "STOPSIM\n"
        tn_inst.write(s.encode('ascii'))
        s = "OK\r\n"
        resp = tn_inst.read_until(s.encode('ascii'), 10).decode("ascii")
        if len(resp) == 0:
            print("Timeout error!")
        self.assertTrue(len(resp) > 0)
        print("Before resp")
        print(resp)
        print("After resp")
        s = "EXIT\n"
        tn_inst.write(s.encode('ascii'))
        resp = tn_inst.read_all()
        print(resp)
        tn_inst.close()

    def test_simservicetelnetclient001(self):
        ip = "127.0.0.1"
        port = 5023
        tn_inst = ATETelnetClient()
        sleep(0.05)
        tn_inst.connect(ip, port)
        sleep(0.05)
        s = "STARTSIM SPITest\n"
        tn_inst.write(s)
        s = "OK\r\n"
        resp = tn_inst.read_until(s)
        if len(resp) == 0:
            print("Timeout error!")
        self.assertTrue(len(resp) > 0)
        print(resp)
        self.assertEqual("This server is running threaded.\r\nOK\r\n", resp)
        s = "STOPSIM\n"
        tn_inst.write(s)
        s = "OK\r\n"
        resp = tn_inst.read_until(s)
        if len(resp) == 0:
            print("Timeout error!")
        self.assertTrue(len(resp) > 0)
        print(resp)
        self.assertEqual("Simulation has stopped.\r\nOK\r\n", resp)
        s = "EXIT\n"
        tn_inst.write(s)
        resp = tn_inst.read_all()
        print(resp)
        self.assertEqual("Goodbye\r\n", resp)
        tn_inst.close()

    def test_simserviceATE001(self):
        ip = "127.0.0.1"
        port = 5023
        ate_inst = ATE(ip=ip, port=port)
        sleep(0.05)
        self.assertTrue(ate_inst.connect("SPITest"))
        sleep(0.05)
        self.assertTrue(ate_inst.terminate())
        ate_inst.close()

    def test_simserviceATE002(self):
        ip = "127.0.0.1"
        port = 5023
        ate_inst = ATE(ip=ip, port=port)
        sleep(0.05)
        self.assertTrue(ate_inst.connect("SPITest"))
        sleep(0.05)
        # GPIO Test
        self.assertTrue(ate_inst.write(0x00001800, 0x00000000))
        self.assertTrue(ate_inst.read(0x00001800))
        self.assertTrue(ate_inst.get_value() == 0x00000000)
        self.assertTrue(ate_inst.write(0x00001800, 0x00000015))
        self.assertTrue(ate_inst.read(0x00001800))
        self.assertTrue(ate_inst.get_value() == 0x00150015)
        self.assertTrue(ate_inst.write(0x00001800, 0x0000000A))
        self.assertTrue(ate_inst.read(0x00001800))
        self.assertTrue(ate_inst.get_value() == 0x000A000A)
        self.assertTrue(ate_inst.write(0x00001800, 0x00000000))
        self.assertTrue(ate_inst.read(0x00001800))
        self.assertTrue(ate_inst.get_value() == 0x00000000)
        sleep(0.05)
        self.assertTrue(ate_inst.terminate())
        ate_inst.close()

    def test_simserviceATE003(self):
        ip = "127.0.0.1"
        port = 5023
        ate_inst = ATE(ip=ip, port=port)
        sleep(0.05)
        self.assertTrue(ate_inst.connect("SPITest"))
        sleep(0.05)
        # JTAG Test
        jtag = JTAGController(ate_inst)
        self.assertTrue(ate_inst.write(0x00001800, 0x00000001))  # Turn on WHITE LED to indicate scan start
        tdo = jtag.scan_ir(8, '55')
        # print("tdo = ", tdo)
        self.assertTrue(tdo == '55')
        self.assertTrue(ate_inst.write(0x00001800, 0x00000002))  # Turn on RED LED to indicate scan start
        tdo = jtag.scan_ir(12, '0A55')
        self.assertTrue(tdo == 'A55')
        self.assertTrue(ate_inst.write(0x00001800, 0x00000004))  # Turn on GREEN LED to indicate scan start
        tdo = jtag.scan_ir(12, '5AA')
        self.assertTrue(tdo == '5AA')
        self.assertTrue(ate_inst.write(0x00001800, 0x00000008))  # Turn on YELLOW LED to indicate scan start
        tdo = jtag.scan_dr(8, '55')
        self.assertTrue(tdo == '55')
        self.assertTrue(ate_inst.write(0x00001800, 0x00000010))  # Turn on BLUE LED to indicate scan start
        tdo = jtag.scan_dr(12, 'AAA')
        self.assertTrue(tdo == 'AAA')
        self.assertTrue(ate_inst.write(0x00001800, 0x00000011))  # Turn on BLUE & WHITE LEDs to indicate scan start
        tdo = jtag.scan_dr(12, 'A55')
        self.assertTrue(tdo == 'A55')
        self.assertTrue(ate_inst.write(0x00001800, 0x00000012))  # Turn on BLUE & RED LEDs to indicate scan start
        tdo = jtag.scan_dr(12, '5AA')
        self.assertTrue(tdo == '5AA')
        self.assertTrue(ate_inst.write(0x00001800, 0x00000014))  # Turn on BLUE & GREEN LEDs to indicate scan start
        tdo = jtag.scan_dr(16 * 4, '0123456789ABCDEF')
        self.assertTrue(tdo == '0123456789ABCDEF')
        sleep(0.05)
        self.assertTrue(ate_inst.terminate())
        ate_inst.close()

    def test_simserviceATE004(self):
        ip = "127.0.0.1"
        port = 5023
        ate_inst = ATE(ip=ip, port=port)
        sleep(0.05)
        self.assertTrue(ate_inst.connect("SPITest"))
        sleep(0.05)
        # I2C Test
        i2c = I2CController(ate_inst)
        # I2C Test set i2c master clock scale reg PRER = (48MHz / (5 * 400KHz) ) - 1
        i2c.i2c_write_reg(0x3C, 0x01, 0xA5)
        self.assertTrue(i2c.i2c_read_reg(0x3C, 0x01) == 0xA5)

        i2c.i2c_multibyte_write(0x3C, 0, 0x89abcdef)
        self.assertTrue(i2c.i2c_multibyte_read(0x3C, 0) == 0x89abcdef)
        self.assertTrue(i2c.i2c_multibyte_read(0x3C, 4) == 0x12345678)
        sleep(0.05)
        self.assertTrue(ate_inst.terminate())
        ate_inst.close()

    def test_simserviceATE005(self):
        ip = "127.0.0.1"
        port = 5023
        ate_inst = ATE(ip=ip, port=port)
        sleep(0.05)
        self.assertTrue(ate_inst.connect("SPITest"))
        sleep(0.05)
        # SPI Test
        spi = SPIController(ate_inst)
        spi.spi_write(0x01345678)
        spi.spi_write(0x00BADEDA)
        self.assertTrue(spi.spi_read() == 0x01345678)
        spi.spi_write(0x02BEEFED)
        self.assertTrue(spi.spi_read() == 0x00BADEDA)
        spi.spi_write(0x01345678)
        self.assertTrue(spi.spi_read() == 0x02BEEFED)
        sleep(0.05)
        self.assertTrue(ate_inst.terminate())
        ate_inst.close()


if __name__ == '__main__':
    unittest.main()
