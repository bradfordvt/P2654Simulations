"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Simulation of an LED
"""
import os
import os.path
import queue
import threading
import time
import tkinter as tk
from PIL import ImageTk, Image
from myhdl import *
from socket import *

HEADER_LENGTH = 10


class LEDDisplay:
    display_instance = None
    client = socket(AF_INET, SOCK_STREAM)
    ip = 'localhost'
    server = (ip, 285)
    try:
        client.connect(server)
        print("Connected to server!")
    except:
        client = None

    @staticmethod
    def display_factory():
        if LEDDisplay.display_instance is None:
            LEDDisplay.display_instance = LEDDisplay()
        return LEDDisplay.display_instance

    def __init__(self):
        pass

    def send_message(self, message):
        print("Sending message: ", message)
        message = message.encode('utf-8')
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
        self.client.send(message_header + message)

    def create_led(self, name):
        try:
            if self.client is not None:
                text = "NEW_LED " + name
                print(text)
                self.send_message(text)
        except:
            pass

    def led_on(self, name):
        try:
            if self.client is not None:
                text = "LED_ON " + name
                print(text)
                self.send_message(text)
        except:
            pass

    def led_off(self, name):
        try:
            if self.client is not None:
                text = "LED_OFF " + name
                print(text)
                self.send_message(text)
        except:
            pass

    def quit(self):
        try:
            if self.client is not None:
                text = "QUIT"
                print(text)
                self.send_message(text)
                self.client.close()
        except:
            pass


class LEDThread (threading.Thread):
    def __init__(self, threadID, qlock, name, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.qlock = qlock
        self.name = name
        self.q = q
        self.display = LEDDisplay.display_factory()
        self.display.create_led(name)
        self.thread1 = None
        self.running = False

    def run(self):
        print("Starting " + self.name)
        self.display_led(self.name, self.q)
        print("Exiting " + self.name)

    def display_led(self, name, q):
        # start background thread
        self.running = True
        self.thread1 = threading.Thread(target=self.control_led)
        self.thread1.start()
        self.thread1.join()
        print("After join")

    def stop(self):
        self.running = False

    def control_led(self):
        while self.running:
            if self.q.qsize():
                try:
                    print("In control_led()")
                    self.qlock.acquire()
                    msg = self.q.get(0)
                    self.qlock.release()
                    time.sleep(1)
                    if msg == "ON":
                        self.display.led_on(self.name)
                    elif msg == "OFF":
                        self.display.led_off(self.name)
                    else:
                        print("Stop message received")
                        self.running = False
                except queue.Empty:
                    pass
        self.display.quit()
        print("After window.quit")
        print("Exiting control_led")


class LED:
    """

    """
    def __init__(self, parent, name,  di):
        """

        :param parent:
        :param name:
        :param di:
        """
        self.parent = parent
        self.name = name
        self.di = di
        self.queueLock = threading.Lock()
        self.workQueue = queue.Queue(10)
        self.threadID = 1
        self.display_thread = LEDThread(self.threadID, self.queueLock, self.parent + '.' + self.name, self.workQueue)
        self.display_thread.start()
        print("past display_thread.start")

    def stop(self):
        print("Entering stop()")
        self.queueLock.acquire()
        self.workQueue.put("STOP")
        self.queueLock.release()

    def _turn_on(self):
        """
        Turn LED on
        :return:
        """
        print("Entering _turn_on()")
        self.queueLock.acquire()
        self.workQueue.put("ON")
        self.queueLock.release()
        print("Exiting _turn_on()")

    def _turn_off(self):
        """
        Turn LED off
        :return:
        """
        print("Entering _turn_off()")
        self.queueLock.acquire()
        self.workQueue.put("OFF")
        self.queueLock.release()
        print("Exiting _turn_off()")

    @block
    def rtl(self):
        @always_comb
        def on_or_off():
            print("Entering on_or_off()")
            if self.di == bool(0):
                self._turn_off()
            else:
                self._turn_on()
            print("Exiting on_or_off()")

        return on_or_off

    @staticmethod
    @block
    def testbench(monitor=False):
        di = Signal(bool(0))
        Q = Signal(bool(1))

        led_inst = LED("DEMO", "LED0", di)

        @instance
        def stimulus():
            H = bool(1)
            L = bool(0)
            for _ in range(5):
                di.next = H
                yield delay(1)
                time.sleep(1)
                di.next = L
                yield delay(10000)
                time.sleep(1)
            # Q.next = bool(0)
            led_inst.stop()
            yield delay(1)
            # time.sleep(5)
            raise StopSimulation()

        @instance
        def _quit():
            if Q == bool(0):
                yield led_inst.stop()

        return led_inst.rtl(), stimulus  # , _quit


if __name__ == '__main__':
    tb = LED.testbench(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    print("After run_sim")
