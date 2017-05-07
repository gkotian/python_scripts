#!/usr/bin/env python

import argparse
import re
import subprocess
import sys

from datetime import datetime, time, timedelta
from time import sleep

def seconds_until(time_str):
    try:
        target_time = time(*(map(int, time_str.split(':'))))
    except ValueError:
        return -1

    target_datetime = datetime.combine(datetime.today(), target_time)
    seconds_delta = int((target_datetime - datetime.now()).total_seconds())

    if seconds_delta < 0:
        # We're already past the target time today, so we'll countdown until the
        # given time the next day
        seconds_delta = 86400 + seconds_delta

    return seconds_delta

def seconds_in(time_str):
    # This regular expression should be improved. It currently allows erroneous
    # input like '24hf' to get through.
    regex = re.compile(
        r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')

    time_parts = regex.match(time_str)
    if not time_parts:
        return -1

    time_parts = time_parts.groupdict()

    # If time_str was initially `2h3m50s`, then time_parts will now be
    # `{'hours': '2', 'seconds': '50', 'minutes': '3'}`

    time_params = {}
    for (name, param) in time_parts.iteritems():
        if param:
            time_params[name] = int(param)
    seconds = int(timedelta(**time_params).total_seconds())

    # An erroneous input results in seconds being zero here. This should
    # probably be caught earlier (i.e. when parsing the regular expression
    # itself). Doing so will also allow us to remove the `if time_str == '0s'`
    # check at the beginning of the function.
    if seconds == 0:
        return -1

    return seconds

def calculate_seconds(time_str):
    # Plain integers are assumed to be seconds
    try: 
        seconds = int(time_str)
        return seconds
    except ValueError:
        pass

    if time_str == '0s':
        return 0

    if ':' in time_str:
        seconds = seconds_until(time_str)
    else:
        seconds = seconds_in(time_str)

    if seconds > 0:
        print "Counting down '{}' seconds until '{}'".format(seconds,
            (datetime.now() + timedelta(seconds=seconds))
            .strftime('%Y-%m-%d %H:%M:%S'))

    return seconds

# Set up command line arguments
parser = argparse.ArgumentParser(usage='%(prog)s [ARGUMENTS]',
    description='Start a countdown for the given time duration')
parser.add_argument('time',
    help='time until or time-duration for which the countdown should run')
parser.add_argument('message', nargs='?', default='Countdown complete!',
    help='message to be displayed when the countdown completes')
args = vars(parser.parse_args())

seconds = calculate_seconds(args['time'])

if seconds < 0:
    print "Unable to parse time duration '{}'".format(args['time'])
    sys.exit(1)

while seconds > 0:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    sys.stdout.write("%02d:%02d:%02d" % (h, m, s))
    sys.stdout.flush()
    sleep(1.0)
    sys.stdout.write("\r\033[K")
    seconds -= 1

print "Countdown complete!"
subprocess.call(['xmessage', args['message']])
