#!/usr/bin/python

import fnmatch
import os
import re
import sys

def gather_symbols(line):
    if (len(line) == 0):
        return []

    # Remove all spaces
    rex = re.compile(r'\s+')
    line = rex.sub('', line)

    # Get rid of the last character (',' or ';')
    line = line.rstrip(',;')

    symbols = []

    if (":" in line):
        # Selective import statement, gather all symbols after the colon
        module = line.split(':')[0];
        symbols = line.split(':')[1].split(',')
    else:
        # Regular import statement, gather a single symbols - the module name
        # We need to do an explicit 'split()' at the end to convert the single symbol to a list
        symbols = line.split('.')[-1].split()

    return symbols

def analyse_file(filename):

    imports = []
    errors = set()
    line_num = 0

    in_multiline_comment = False
    in_import_stmt = False

    symbols = []
    symbols_seen = set()

    for line in open(filename):
        line_num += 1

        line = line.strip()

        if (len(line) == 0):
            continue

        if (line.endswith("*/")):
            in_multiline_comment = False

        if ( in_multiline_comment ):
            continue

        if (line.startswith("//")):
            continue

        if (line.startswith("/*")):
            in_multiline_comment = True
            continue

        if "import" in line:
            rex = re.compile(r'\s{2,}')
            line = rex.sub(' ', line)

            # Sanity checks to see if this is indeed an import statement
            three_parts = line.split(' ', 2)

            split_count = len(three_parts)
            if (split_count == 1):
                if (three_parts[0] == "import"):
                    in_import_stmt = True
                continue
            else:
                if (three_parts[0] == "import"):
                    in_import_stmt = True
                    line = three_parts[1] if (split_count == 2) else three_parts[1] + three_parts[2]
                elif (three_parts[1] == "import"):
                    in_import_stmt = True
                    line = "" if (split_count == 2) else three_parts[2]
                    if (three_parts[0] == "private"):
                        errors.add("    * line " + str(line_num) + ": private import found")

        if (in_import_stmt):
            symbols += gather_symbols(line)
            if (len(line)):
                imports.append(line)
            if (";" in line):
                in_import_stmt = False
        else:
            for symbol in symbols:
                if symbol in line:
                    symbols_seen.add(symbol)

    for imp in imports:
        occurrence_count = imports.count(imp)
        if (occurrence_count > 1):
            errors.add("    * '" + imp + "' appears " + str(occurrence_count) + " times")

    symbols_not_seen = set(symbols) - symbols_seen
    if (len(symbols_not_seen)):
        for symbol in symbols_not_seen:
            errors.add("    * import of '" + symbol + "' could probably be removed")

    return errors

cwd = os.getcwd()

if not os.path.isdir(cwd + "/src"):
    print "'" + cwd + "/src' doesn't exist. Aborting."
    sys.exit(1)

files = []

for root, subdirs, filenames in os.walk(cwd + "/src"):
    for filename in fnmatch.filter(filenames, "*.d"):
        files.append(os.path.join(root, filename))

print "Analysing " + str(len(files)) + " D files in '" + cwd + "/src'"
print ""

for f in files:
    errors = set()

    errors = analyse_file(f)

    if (len(errors)):
        print f + ":"
        for e in errors:
            print e
        print ""

