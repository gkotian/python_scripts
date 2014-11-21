#!/usr/bin/python

# non-selective imports

import re
import shutil
import tempfile

INPUT_FILE='tmp.txt'
TMP_FILE_TUPLE=tempfile.mkstemp()
OUTPUT_FILE=TMP_FILE_TUPLE[1]
SYMBOL='ModuleX'

with open(INPUT_FILE, 'r') as in_file, open(OUTPUT_FILE, 'w') as out_file:
    skip_line=False

    for line in in_file:
        # If previous line was deleted, and current line is blank, then delete the current line as well
        if (skip_line and len(line.rstrip()) == 0):
            continue

        skip_line=False

        if ('import' in line and
            SYMBOL in line and
            ';' in line):
            if (':' in line):
                # selective imports
                pass
            else:
                if (',' not in line):
                    skip_line=True
                else:
                    begin_matcher = r'\s.*' + re.escape(SYMBOL) + r'\s*,\s*'
                    middle_matcher = r',.*' + re.escape(SYMBOL) + r'\s*,\s*'
                    end_matcher = r'\s*,\s*.*' + re.escape(SYMBOL) + r'\s*'
                    if re.search(middle_matcher, line):
                        line = re.sub(middle_matcher, ', ', line)
                    elif re.search(begin_matcher, line):
                        line = re.sub(begin_matcher, ' ', line)
                    elif re.search(end_matcher, line):
                        line = re.sub(end_matcher, '', line)
        if (not skip_line):
            out_file.write(line)

shutil.move(OUTPUT_FILE, INPUT_FILE)

