"""

"""
import os
from platform import system, node
import sys

if sys.version_info > (3, 0):
    import socketserver
    from telnetsrv.threaded import TelnetHandler
    from telnetsrv.telnetsrvlib import command
else:
    import SocketServer
    from telnetsrv.threaded import TelnetHandler
    from telnetsrv.telnetsrvlib import command

import threading
import string

if sys.version_info > (3, 0):
    import queue
else:
    import Queue

TELNET_IP_BINDING = ""  # all
TELNET_PORT_BINDING = 5023
SERVERPROTOCOL = 'telnet'
SERVERTYPE = 'threaded'

# The SocketServer needs *all IPs* to be 0.0.0.0
if not TELNET_IP_BINDING:
    TELNET_IP_BINDING = '127.0.0.1'

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class SimulatorHandler(TelnetHandler):
    # -- Override items to customize the server --
    if sys.version_info > (3, 0):
        WELCOME = 'You have connected to the P2654Simulation server.'
        PROMPT = "P2654> "
    else:
        WELCOME = 'You have connected to the P2654Simulation test server.'
        PROMPT = "P2654> "
    # authNeedUser = True
    # authNeedPass = True
    # parseState = {'START': 0, 'PSTART': 1, 'PIPE': 2, 'CSTART': 3, 'CARRIER': 4, 'BSTART': 5, 'BW': 6, 'CSTOP': 7,
    #               'PSTOP': 8}
    # ttParseState = {'START': 0, 'KSTART': 1, 'KEY': 2, 'VSTART': 3, 'VALUE': 4, 'VSTOP': 5, 'KSTOP': 6}
    # tupleParseState = {'START': 0, 'QSTART': 1, 'PARAM': 2, 'QSTOP': 3, 'SEPARATOR': 4, 'STOP': 5}
    # parseListState = {'START': 0, 'LSTART': 1, 'PARAM': 2, 'SEPERATOR': 3, 'STOP': 4}
    # parseIntListState = {'START': 0, 'LSTART': 1, 'PARAM': 2, 'SEPERATOR': 3, 'STOP': 4}

    def __init__(self, request, client_address, server):
        TelnetHandler.__init__(self, request, client_address, server)

    def __mw(self, adr, data):
        print("MW(", adr, ", ", data, ")")

    def __mr(self, adr):
        print("MR(", adr, ")")
        return "42"

    def __mrmw(self, adr, data):
        print("MRMW(", adr, ", ", data, ")")
        return "43"

    def __mmw(self, adr, cnt, data):
        print("MMW(", adr, ", ", cnt, end="")
        for s in data:
            print(", ", s, end="")
        print(")")

    def __mmwi(self, adr, cnt, data):
        print("MMWI(", adr, ", ", cnt, end="")
        for s in data:
            print(", ", s, end="")
        print(")")

    def __mmr(self, adr, cnt):
        print("MMR(", adr, ", ", cnt, ")")
        return "42 43"

    def __mmri(self, adr, cnt):
        print("MMRI(", adr, ", ", cnt, ")")
        return "42 43"

    def setterm(self, term):
        """
        # Override the default behavior
        Set the curses structures for this terminal
        """
        print("Entering SimulatorHandler.setterm().")
        TelnetHandler.setterm(self, term)
        if system() == 'Windows':
            # Override the missing codes for Windows and set to a default for ansi/vt100
            self.CODES['DEOL'] = '\033[K'
            # self.CODES['DEL'] = '\033[3~'
            self.CODES['DEL'] = ' \033[D'
            self.CODES['INS'] = '\033[2~'
            self.CODES['CSRLEFT'] = '\033[D'
            self.CODES['CSRRIGHT'] = '\033[C'

    # def authCallback(self, username, password):
    #     '''Called to validate the username/password.'''
    #     # Note that this method will be ignored if the SSH server is invoked.
    #     # We accept everyone here, as long as any name is given!
    #     #print "In authCallback({:s}, {:s})".format(username, password)
    #
    #     if not username:
    #         # complain by raising any exception
    #         raise ValueError("username is not specified.")
    #     if username != 'root':
    #         raise ValueError("Incorrect username given.")
    #     if password != 'sarokal':
    #         raise ValueError("Incorrect password given.")

    def session_start(self):
        """Called after the user successfully logs in."""
        self.writeline('This server is running %s.' % SERVERTYPE)

    def session_end(self):
        """Called after the user logs off."""
        print("Session ending.")

    # pass

    # -- Custom Commands --
    @command('*IDN?')
    def command_IDNquery(self, params):
        '''
        Report P2654Simulation identification.
        Report back the identification information about the
        P2654Simulation.
        P2654Simulation <version>
        '''
        response = "P2654Simulation v0.1"
        self.writeresponse(response)

    ############################################################################################
    # Single Cycle Commands
    ############################################################################################
    @command('MW')
    def command_MW(self, params):
        """
        <32-bit hex address> <32-bit hex data word>
        Writes the data word to address on Wishbone bus for one cycle.
        Writes the data word to address on Wishbone bus for one cycle.
        MW 0x00001800 0x00010001
        """
        if len(params) == 0:
            # No argument given, so respond with help message
            return self.cmdHELP(['MW'])
        try:
            if len(params) == 2:
                self.__mw(int(params[0], 16), int(params[1], 16))
            else:
                self.writeerror('Invalid number of arguments received.')
        except:
            self.writeerror('Invalid argument received.')

    @command('MR')
    def command_MR(self, params):
        """
        <32-bit hex address>
        Reads from the address on Wishbone bus for one cycle and returns the value.
        Reads from the address on Wishbone bus for one cycle and returns the value.
        MR 0x00001800
        """
        if len(params) == 0:
            # No argument given, so respond with help message
            return self.cmdHELP(['MR'])
        try:
            if len(params) == 1:
                response = self.__mr(int(params[0], 16))
                self.writeresponse(response)
            else:
                self.writeerror('Invalid number of arguments received.')
        except:
            self.writeerror('Invalid argument received.')

    @command('MRMW')
    def command_MRMW(self, params):
        """
        <32-bit hex address> <32-bit hex data word>
        Reads from address then writes the data word to address on Wishbone bus.
        Reads from address then writes the data word to address on Wishbone bus.
        MRMW 0x00001800 0x00010001
        """
        if len(params) == 0:
            # No argument given, so respond with help message
            return self.cmdHELP(['MRMW'])
        try:
            if len(params) == 2:
                response = self.__mrmw(int(params[0], 16), int(params[1], 16))
                self.writeresponse(response)
            else:
                self.writeerror('Invalid number of arguments received.')
        except:
            self.writeerror('Invalid argument received.')

    ############################################################################################
    # Block Cycle Commands
    ############################################################################################
    @command('MMW')
    def command_MMW(self, params):
        """
        <32-bit hex address> <number of words> <32-bit hex data word> [<32-bit hex data word> ...]
        Writes the data word to address on Wishbone bus for multiple cycles.
        Writes the data word to address on Wishbone bus for multiple cycles.
        MMW 0x00001800 2 0x00010001 0x00010000
        """
        if len(params) == 0:
            # No argument given, so respond with help message
            return self.cmdHELP(['MMW'])
        try:
            ndata = len(params) - 2
            if ndata != int(params[1]):
                self.writeerror('Invalid argument received.')
            else:
                self.__mmw(int(params[0], 16), int(params[1]), params[2:])
        except:
            self.writeerror('Invalid argument received.')

    @command('MMWI')
    def command_MMWI(self, params):
        """
        <32-bit hex address> <number of words> <32-bit hex data word> [<32-bit hex data word> ...]
        Writes the data word to incrementing address on Wishbone bus for multiple cycles.
        Writes the data word to incrementing address on Wishbone bus for multiple cycles.
        MMW 0x00001800 2 0x00010001 0x00010000
        """
        if len(params) == 0:
            # No argument given, so respond with help message
            return self.cmdHELP(['MMWI'])
        try:
            ndata = len(params) - 2
            if ndata != int(params[1]):
                self.writeerror('Invalid argument received.')
            else:
                self.__mmwi(int(params[0], 16), int(params[1]), params[2:])
        except:
            self.writeerror('Invalid argument received.')

    @command('MMR')
    def command_MMR(self, params):
        """
        <32-bit hex address> <number of words>
        Reads from the address on Wishbone bus for multiple cycles and returns the values.
        Reads from the address on Wishbone bus for multiple cycles and returns the values.
        MR 0x00001800 2
        """
        if len(params) == 0:
            # No argument given, so respond with help message
            return self.cmdHELP(['MMR'])
        try:
            if len(params) == 2:
                response = self.__mmr(int(params[0], 16), int(params[1]))
                self.writeresponse(response)
            else:
                self.writeerror('Invalid number of arguments received.')
        except:
            self.writeerror('Invalid argument received.')

    @command('MMRI')
    def command_MMRI(self, params):
        """
        <32-bit hex address> <number of words>
        Reads from the incrementing address on Wishbone bus for multiple cycles and returns the values.
        Reads from the incrementing address on Wishbone bus for multiple cycles and returns the values.
        MMRI 0x00001800 2
        """
        if len(params) == 0:
            # No argument given, so respond with help message
            return self.cmdHELP(['MMRI'])
        try:
            if len(params) == 2:
                response = self.__mmri(int(params[0], 16), int(params[1]))
                self.writeresponse(response)
            else:
                self.writeerror('Invalid number of arguments received.')
        except:
            self.writeerror('Invalid argument received.')


class SimulatorServer(object):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.server = None
        self.status = False
        self.thread = None
        self.__is_shut_down = threading.Event()

    def start(self):

        Handler = SimulatorHandler

        # Single threaded server - only one session at a time
        if sys.version_info > (3, 0):
            class TelnetServer(socketserver.TCPServer):
                allow_reuse_address = True
        else:
            class TelnetServer(SocketServer.TCPServer):
                allow_reuse_address = True

        # server = TelnetServer((TELNET_IP_BINDING, TELNET_PORT_BINDING), Handler)
        self.server = TelnetServer((self.ip, self.port), Handler)

        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True  # Daemonize thread
        self.__is_shut_down.clear()
        self.status = True
        self.thread.start()  # Start the execution
        print("TelnetServer running in thread " + self.thread.name + ".")

    # time.sleep(2.0)

    def run(self):
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("Server shut down.")
        self.status = False
        self.__is_shut_down.set()
        print("run() self.status is now set to False.")

    def stop(self):
        self.server.shutdown()
        self.__is_shut_down.wait()
        print("Server is now stopped!")

    def close(self):
        print("Closing Server.")
        self.server.server_close()

    def wait(self):
        self.thread.join()

    def getStatus(self):
        return self.status


class SimulatorService(object):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.server = None
        self.shutdown_request = False
        self.__is_shut_down = threading.Event()
        self.service = None
        self.thread = None
        self.status = False

    def start(self):
        self.service = SimulatorServer(self.ip, self.port)

        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True  # Daemonize thread
        self.__is_shut_down.clear()
        self.status = True
        self.thread.start()  # Start the execution
        print("Server running in thread " + self.thread.name + ".")

    def run(self):
        print("Starting SimulatorServer.")
        self.service.start()
        while not self.shutdown_request and self.service.getStatus():
            if self.shutdown_request == True:
                self.service.stop()
        print("SimulatorServer Stopped.")
        self.__is_shut_down.set()

    def shutdown(self):
        print("Waiting to shutdown SimulatorServer.")
        self.service.stop()
        if self.service.getStatus():
            self.shutdown_request = True
            self.__is_shut_down.wait()
        self.service.close()


if __name__ == '__main__':
    Handler = SimulatorHandler

    # Single threaded server - only one session at a time
    if sys.version_info > (3, 0):
        class TelnetServer(socketserver.TCPServer):
            allow_reuse_address = True
    else:
        class TelnetServer(SocketServer.TCPServer):
            allow_reuse_address = True

    # server = TelnetServer((TELNET_IP_BINDING, TELNET_PORT_BINDING), Handler)
    server = TelnetServer(('127.0.0.1', 5023), Handler)
    server.serve_forever()
