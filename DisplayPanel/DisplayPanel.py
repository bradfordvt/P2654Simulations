from tkinter import Tk
from tkinter import Label, Frame
from tkinter import Variable
from time import sleep
import threading
from PIL import ImageTk, Image
import os
import os.path
from socket import *
import select
import sys

HEADER_LENGTH = 10


class DisplayPanel:
    server = socket(AF_INET, SOCK_STREAM)
    ip = 'localhost'
    server.bind((ip, 285))
    server.listen(5)
    sockets_list = [server]

    def __init__(self, title):
        self.top = None
        self.listener_thread = None
        self.title = title
        self.list_variable = None
        self.img_off = None
        self.img_on = None
        self.path_off = None
        self.path_on = None
        self.leds = {}

    def configure_display(self):
        self.top = Tk()
        self.top.title(self.title)
        self.top.geometry("600x200+10+10")
        ipath = os.path.dirname(__file__)
        self.path_off = os.path.join(ipath, "off_led.png")
        self.path_on = os.path.join(ipath, "on_led.png")
        self.img_off = ImageTk.PhotoImage(Image.open(self.path_off))
        self.img_on = ImageTk.PhotoImage(Image.open(self.path_on))

    def receive_message(self, client_socket):
        try:
            message_header = client_socket.recv(HEADER_LENGTH)
            if not len(message_header):
                return False
            message_length = int(message_header.decode('utf-8').strip())
            return {'header': message_header, 'data': client_socket.recv(message_length)}
        except:
            return False

    def listener(self):
        client, addr = self.server.accept()
        while True:
            message = self.receive_message(client)
            if message is False:
                continue
            if self.process_message(message['data']) is False:
                continue

    def process_message(self, message):
        ret = True
        try:
            command = message.split()
            if command[0] == b"NEW_LED":
                frame = Frame(self.top)
                frame.pack(side="left")
                label = Label(frame, text=command[1])
                label.pack(side="top", fill="both", expand="yes")
                panel = Label(frame, image=self.img_off)
                panel.pack(side="bottom", fill="both", expand="yes")
                inst = (frame, panel, command[1])
                self.leds[command[1]] = inst
            elif command[0] == b"QUIT":
                self.top.destroy()
                sys.exit(0)
            elif command[0] == b"LED_ON":
                f, p, n = self.leds[command[1]]
                p.configure(image=self.img_on)
                p.image = self.img_on
            elif command[0] == b"LED_OFF":
                f, p, n = self.leds[command[1]]
                p.configure(image=self.img_off)
                p.image = self.img_off
            else:
                ret = False
        except:
            ret = False
        return ret

    def create_listener(self):
        self.listener_thread = threading.Thread(target=self.listener, args=[])
        self.listener_thread.setDaemon(True)
        self.listener_thread.start()

    def start_display(self):
        self.top.mainloop()


if __name__ == "__main__":
    display = DisplayPanel("P2654Simulation Display")
    display.configure_display()
    display.create_listener()
    display.start_display()
