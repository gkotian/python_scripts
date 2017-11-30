#!/usr/bin/python

import argparse
import subprocess
import sys


cssh_config_file='/home/gautam/work/rnd/cssh/cssh_config'
browser='/usr/bin/google-chrome'


def die(msg):
    print(msg)
    sys.exit(1)


def filterServersByRegion(all_servers, region):
    filtered_servers = []

    for s in all_servers:
        if s.split('-')[0] == region:
            filtered_servers.append(s)

    return filtered_servers


def getInterestLevelOfLine(line_header, app_being_searched, region_being_searched):
    line_header = line_header.lower()

    # the line header can be either `appname` or `xx-appname` where xx is the
    # region code
    lh_parts = line_header.split('-')

    if len(lh_parts) == 1:
        region = 'NOT_PRESENT_IN_LINE'
        app = lh_parts[0]
    else:
        region = lh_parts[0]
        app = lh_parts[1]

    if region_being_searched == 'ALL':
        if app == app_being_searched:
            return 'FULL'
    else:
        if app == app_being_searched:
            if region == region_being_searched:
                return 'FULL'
            elif region == 'NOT_PRESENT_IN_LINE':
                return 'PARTIAL'

    return 'UNINTERESTING'


parser = argparse.ArgumentParser(usage='%(prog)s app region [-f]',
    description='blah')
parser.add_argument('app_and_region', nargs='+', help='app & region')
parser.add_argument('--launch-foreman', '-f', action='store_true',
    required = False, default = False,
    help = 'Launch foreman at the end (to confirm the output)')

# Make a dictionary of the arguments for convenient indexing
args = vars(parser.parse_args())


app = args['app_and_region'][0]
if len(args['app_and_region']) > 2:
    die('Too many arguments. Aborting')
elif len(args['app_and_region']) == 2:
    region = args['app_and_region'][1].lower()
else:
    region = 'ALL'

final_list = []

with open(cssh_config_file, 'r') as in_file:
    line_num = 0
    for line in in_file:
        line_num += 1
        line = line.strip()

        if len(line) == 0:
            continue

        if line.startswith('#'):
            continue

        parts = line.split()

        interest_level = getInterestLevelOfLine(parts[0], app, region)

        if interest_level == 'FULL':
            final_list += parts[1:]
            if region != 'ALL':
                # When looking for a specific region, we only need to find the
                # first matching line.
                break
        elif interest_level == 'PARTIAL':
            final_list += filterServersByRegion(parts[1:], region)
            if region != 'ALL':
                # When looking for a specific region, we only need to find the
                # first matching line.
                break
        else:
            # The current line is not of interest, so nothing to do.
            # This empty `else` block has been left here deliberately to
            # discourage someone from trying to move the `if region != 'ALL':`
            # checks in the previous two blocks outside.
            pass

if region == 'ALL':
    print("Found {} server(s) with '{}' across all regions"
        .format(len(final_list), app))
else:
    print("Found {} server(s) with '{}' in '{}'"
        .format(len(final_list), app, region))

if len(final_list) > 0:
    for server in final_list:
        print('    {}'.format(server.split('.')[0]))

if args['launch_foreman']:
    link='https://fm.sociomantic.com/hosts?search=class+~+sociomantic%3A%3Aapplication%3A%3A{}'.format(app)

    if region != 'ALL':
        link += '+and+location+%3D+{}'.format(region)

    proc = subprocess.Popen([browser, link],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()

    print('Launched a new browser tab to get the latest info from foreman')
