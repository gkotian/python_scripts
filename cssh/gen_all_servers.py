#!/usr/bin/python

import os
import sys
import tempfile

clusters_file = os.path.expanduser('~/.clusterssh/clusters')

if not os.path.isfile(clusters_file):
    print "cssh clusters file '" + clusters_file + "' not found"
    sys.exit(1)

# Collect all servers we find in the cssh clusters file
all_servers = set()
with open(clusters_file, 'r') as in_file:
    for line in in_file:
        line = line.strip()

        if (len(line) == 0):
            continue

        if (line.startswith('#')):
            continue

        elements = line.split()
        for server in elements[1:]:
            all_servers.add(server)

# Categorize all collected servers into a dictionary indexed by the regions
region_specific_servers = dict()
for server in all_servers:
    region = server.split('-')[0]
    region_specific_servers.setdefault(region, []).append(server)

# Write to the output file
preamble="""
#==============================================================================#
#                                                                              #
#   This is an automatically generated file. To re-generate this file, run:    #
#       $> /path/to/gen_all_servers.py                       #
#                                                                              #
#==============================================================================#
"""

output_file = tempfile.mkstemp()[1]

with open(output_file, 'w') as out_file:
    out_file.write(preamble[1:].strip())

    for region in sorted(region_specific_servers):
        # Get the individual server numbers (mainly to allow us to numerically
        # sort the servers)
        server_numbers = []
        for server in region_specific_servers[region]:
            server_numbers.append(server.split('-')[1])
        server_numbers = sorted(server_numbers, key=int)

        line = region.upper()
        for n in server_numbers:
            line += ' ' + region + '-' + n

        out_file.write('\n\n' + line)
        out_file.write('\n' + '# REGION=' + region.lower() + '; FORFOR_STRING=(' + ' '.join(server_numbers) + ')')

    out_file.write('\n')

print("cssh clusters file containing all servers saved to '" + output_file + "'");
