#!/usr/bin/python

import argparse
import os
import subprocess
import sys


cssh_config_file = os.path.expanduser('~/.clusterssh/clusters')
BROWSER_PATH = os.environ.get('BROWSER_PATH', '/usr/bin/google-chrome')


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

    # Split the line header once based on a hyphen in the hope that the first
    # two characters will be the region code
    lh_parts = line_header.split('-', 1)

    if len(lh_parts) == 1:
        # There is no hyphen in the line header, so the entire line header is
        # the app name
        region = 'NOT_PRESENT_IN_LINE'
        app = line_header
    else:
        # There is a hyphen in the line header, but we need to confirm whether
        # the first two characters are a valid region code
        if lh_parts[0] in ('ap', 'cn', 'eu', 'us'):
            region = lh_parts[0]
            app = lh_parts[1]
        else:
            region = 'NOT_PRESENT_IN_LINE'
            app = line_header

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


def csv_file_check(cssh_config_server_list):
    cssh_config_server_list = sorted(cssh_config_server_list)

    csv_file = raw_input('Enter the path of the csv file for comparison (q to quit): ')

    if csv_file == 'q':
        return

    if not os.path.isfile(csv_file):
        # Maybe the user entered only the file name instead of the full path,
        # check if the file exists in the '/tmp' directory
        csv_file = '/tmp/' + csv_file
        if not os.path.isfile(csv_file):
            print ("Couldn't find the csv file, no automatic check possible.")
            return

    csv_file_server_list = []

    with open(csv_file, 'r') as in_file:
        line_num = 0
        for line in in_file:
            line_num += 1

            # Assume that the first line is the csv header
            if line_num == 1:
                continue

            line = line.strip()

            if len(line) == 0:
                continue

            server = line.split('.')[0]

            csv_file_server_list.append(server)

    csv_file_server_list = sorted(csv_file_server_list)

    if cssh_config_server_list != csv_file_server_list:
        print("The list of servers obtained via the cssh config doesn't match the list of servers obtained via the csv file")
        list1 = [obj for obj in cssh_config_server_list if obj not in csv_file_server_list]
        list2 = [obj for obj in csv_file_server_list if obj not in cssh_config_server_list]
        print('Mismatching servers: {}'.format(list1 + list2))
    else:
        print("It's a match!")


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

    print('')

    versions_link = 'https://fm.sociomantic.com/fact_values?utf8=%E2%9C%93&search=+fact+%7E+applications%3A%3A{}%3A%3A%2F*%3A%3Aversion'.format(app)
    if region != 'ALL':
        versions_link += '+and+host+~+{}-*.sociomantic.net'.format(region)

    print('versions: {}'.format(versions_link))

    if args['launch_foreman']:
        link='https://fm.sociomantic.com/hosts?search=class+~+sociomantic%3A%3Aapplication%3A%3A{}'.format(app)

        if region != 'ALL':
            link += '+and+location+%3D+{}'.format(region)

        if not os.path.isfile(BROWSER_PATH):
            raise ValueError("Browser path '{}' doesn't exist".format(BROWSER_PATH))
        proc = subprocess.Popen([BROWSER_PATH, link],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = proc.communicate()

        print('Launched a new browser tab to get the latest info from foreman')

        # If there are more than 5 servers, then give the user the option to enter a
        # csv file for comparison
        if len(final_list) > 5:
            csv_file_check(final_list)
