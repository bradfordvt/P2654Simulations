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


class LEDThread (threading.Thread):
    def __init__(self, threadID, qlock, name, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.qlock = qlock
        self.name = name
        self.q = q
        self.window = None
        ipath = os.path.dirname(__file__)
        self.path_off = os.path.join(ipath, "off_led.png")
        self.path_on = os.path.join(ipath, "on_led.png")
        # Creates a Tkinter-compatible photo image, which can be used everywhere Tkinter expects an image object.
        self.img_off = None
        self.img_on = None
        self.panel = None
        self.thread1 = None
        self.thread2 = None
        self.running = None
        self.label = None

    def run(self):
        print("Starting " + self.name)
        self.display_led(self.name, self.q)
        print("Exiting " + self.name)

    def display_led(self, name, q):
        # start background thread
        self.running = True
        self.thread1 = threading.Thread(target=self.control_led)
        self.thread1.start()
        self.thread2 = threading.Thread(target=self.display_window)
        self.thread2.start()
        # Start the GUI
        # self.window.mainloop()
        print("After thread2.start")
        # self.thread1.stop()
        # self.stop()
        self.thread1.join()
        print("After join")
        self.thread2.join()
        print("After thread2.join")

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
                        self.panel.configure(image=self.img_on)
                        self.panel.image = self.img_on
                    elif msg == "OFF":
                        self.panel.configure(image=self.img_off)
                        self.panel.image = self.img_off
                    else:
                        print("Stop message received")
                        self.running = False
                except queue.Empty:
                    pass
        self.window.quit()
        print("After window.quit")
        print("Exiting control_led")

    def display_window(self):
        self.window = tk.Tk()
        self.window.title(self.name)
        # self.window.geometry("300x300")
        self.window.geometry("150x150")
        self.window.configure(background='grey')
        self.img_off = ImageTk.PhotoImage(Image.open(self.path_off))
        self.img_on = ImageTk.PhotoImage(Image.open(self.path_on))
        self.label = tk.Label(self.window, text=self.name)
        self.label.pack(side="top", fill="both", expand="yes")
        # The Label widget is a standard Tkinter widget used to display a text or image on the screen.
        self.panel = tk.Label(self.window, image=self.img_off)
        # The Pack geometry manager packs widgets in rows or columns.
        self.panel.pack(side="bottom", fill="both", expand="yes")
        # Start the GUI
        print("Entering display_window")
        self.window.mainloop()
        print("Exiting display_window")


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
