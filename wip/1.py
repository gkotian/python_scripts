#!/usr/bin/python

# temp files/directories creation
# mv src dst
# removing private imports

import re
import shutil
import tempfile

INPUT_FILE='tmp.txt'
TMP_FILE_TUPLE=tempfile.mkstemp()
OUTPUT_FILE=TMP_FILE_TUPLE[1]

with open(INPUT_FILE, 'r') as in_file, open(OUTPUT_FILE, 'w') as out_file:
    for line in in_file:
        if ("private" in line):
            rex = re.compile(r'private\s+')
            line = rex.sub('', line)
        out_file.write(line)

shutil.move(OUTPUT_FILE, INPUT_FILE)

