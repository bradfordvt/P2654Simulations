"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory
"""

from myhdl import *
from p2654.core.utils import trigger


class Queue:
    def __init__(self):
        self.list = []
        self.sync = Signal(0)
        self.item = None

    def put(self, item):
        # non time-consuming method
        self.list.append(item)
        trigger(self.sync)

    def get(self):
        # time-consuming method
        if not self.list:
            yield self.sync
        self.item = self.list.pop(0)
