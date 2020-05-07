#!/usr/bin/env python

# Written by Gregory Brancq
# Public domain software

"""
Program to square breath with different times

def protocol_basis_3():
    s.enter(1, 1, printAction, argument=("Respire",))
    s.enter(2, 1, printAction, argument=(1,))
    s.enter(3, 1, printAction, argument=(2,))
    s.enter(4, 1, printAction, argument=("Pause",))
    s.enter(5, 1, printAction, argument=(1,))
    s.enter(6, 1, printAction, argument=(2,))
    s.enter(7, 1, printAction, argument=("Expire",))
    s.enter(8, 1, printAction, argument=(1,))
    s.enter(9, 1, printAction, argument=(2,))
    s.enter(10, 1, printAction, argument=("Pause",))
    s.enter(11, 1, printAction, argument=(1,))
    s.enter(12, 1, printAction, argument=(2,))
"""
import sched

import time

n = 4

s = sched.scheduler(time.time, time.sleep)
steps = {0: "Respire", 1: "Pause", 2: "Expire", 3: "Pause"}


def printAction(txt):
    print(txt)


def square():
    for (index, step) in steps.items():
        s.enter(index * n + 1, 1, printAction, argument=(step,))
    for i in xrange(0, 4 * n, n):
        for j in xrange(1, n, 1):
            s.enter(i + j + 1, 1, printAction, argument=(j,))
    s.run()


while True:
    square()
