#!/usr/bin/python

import sys
import time

first_time = True

def update_progress(text):
    global first_time

    if not first_time:
        num_lines = text.count('\n')
        for i in range(0, num_lines):
            sys.stdout.write("\r")
            sys.stdout.write("\033[K") # Clear to the end of line
            sys.stdout.write("\033[1A") # Move cursor up one line

    sys.stdout.write(text)
    sys.stdout.flush()
    first_time = False

for i in range(0, 1000):
    time.sleep(0.1)
    if i % 10 == 0:
        text = '{}\n{}\n{}\n{}'.format(i-3, i-2, i-1, i)
        update_progress(text)
