#!/usr/bin/python

import argparse

def die(msg):
    print(msg)
    sys.exit(1)


def isLineOfInterest(line_header, app_being_searched, region_being_searched):
    line_header = line_header.lower()

    # the line header can be either `appname` or `xx-appname` where xx is the
    # region code
    lh_parts = line_header.split('-')

    if len(lh_parts) == 1:
        region = 'NA'
        app = lh_parts[0]
    else:
        region = lh_parts[0]
        app = lh_parts[1]

    if region_being_searched == 'ALL':
        if app == app_being_searched:
            return True
    else:
        if app == app_being_searched and region == region_being_searched:
            return True

    return False


parser = argparse.ArgumentParser(usage='%(prog)s [ARGUMENTS]',
    description='blah')
parser.add_argument('app_and_region', nargs='+', help='app & region')

args = parser.parse_args()

app = args.app_and_region[0]
if len(args.app_and_region) > 2:
    die('Too many arguments. Aborting')
elif len(args.app_and_region) == 2:
    region = args.app_and_region[1].lower()
else:
    region = 'ALL'

final_list = []

cssh_config_file='/home/gautam/work/rnd/cssh/cssh_config'

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

        if isLineOfInterest(parts[0], app, region):
            final_list += parts[1:]
            if region != 'ALL':
                # when looking for a specific region, we only need to find a
                # single line
                break

if region == 'ALL':
    print("Found {} server(s) with '{}' across all regions"
        .format(len(final_list), app))
else:
    print("Found {} server(s) with '{}' in '{}'"
        .format(len(final_list), app, region))

if len(final_list) > 0:
    for server in final_list:
        print('    {}'.format(server.split('.')[0]))
