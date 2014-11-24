#!/usr/bin/python

import argparse
import fnmatch
import os
import re
import shutil
import sys
import tempfile

def search_and_delete_symbol(symbol, filename):
    tmp_file_tuple = tempfile.mkstemp()
    tmp_file = tmp_file_tuple[1]

    with open(filename, 'r') as in_file, open(tmp_file, 'w') as out_file:
        skip_line = False

        for line in in_file:
            # If previous line was deleted, and current line is blank, then delete the current line as well
            if (skip_line and len(line.rstrip()) == 0):
                continue

            skip_line = False

            if ('import' in line) and (symbol in line) and (';' in line):
                if (':' in line):
                    # selective imports
                    pass
                else:
                    if (',' not in line):
                        skip_line = True
                    else:
                        begin_matcher = r'\s.*' + re.escape(symbol) + r'\s*,\s*'
                        middle_matcher = r',.*' + re.escape(symbol) + r'\s*,\s*'
                        end_matcher = r'\s*,\s*.*' + re.escape(symbol) + r'\s*'
                        if re.search(middle_matcher, line):
                            line = re.sub(middle_matcher, ', ', line)
                        elif re.search(begin_matcher, line):
                            line = re.sub(begin_matcher, ' ', line)
                        elif re.search(end_matcher, line):
                            line = re.sub(end_matcher, '', line)

            if (not skip_line):
                out_file.write(line)

    shutil.move(tmp_file, filename)

def search_and_delete_line(deletion_identifier, filename):
    tmp_file_tuple = tempfile.mkstemp()
    tmp_file = tmp_file_tuple[1]

    with open(filename, 'r') as in_file, open(tmp_file, 'w') as out_file:
        found_once = False

        for line in in_file:
            if (not found_once) and (deletion_identifier in line):
                found_once = True
            else:
                out_file.write(line);

    shutil.move(tmp_file, filename)

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
        # Regular import statement, gather a single symbol, i.e. the module name
        # We need to do an explicit 'split()' at the end to convert the single symbol to a list
        symbols = line.split('.')[-1].split()

    return symbols

def analyse_file(filename, tmp_directory):

    write_mode = False if tmp_directory is 'dummy' else True

    imports = []
    errors = set()

    in_multiline_comment = False
    in_import_stmt = False

    symbols = []
    symbols_seen = set()

    if (write_mode):
        # Make a copy of the file so that it can be reverted
        file_copy = tmp_directory + '/file_copy'
        shutil.copyfile(filename, file_copy)

    with open(filename, 'r') as in_file:
        line_num = 0
        skip_line = False

        if (write_mode):
            out_file = open(file_copy, 'w')

        for line in in_file:
            line_num += 1

            orig_line = line

            line = line.strip()

            if (len(line) == 0):
                if (write_mode):
                    out_file.write(orig_line)
                continue

            if (line.endswith("*/")):
                in_multiline_comment = False

            if ( in_multiline_comment ):
                if (write_mode):
                    out_file.write(orig_line)
                continue

            if (line.startswith("//")):
                if (write_mode):
                    out_file.write(orig_line)
                continue

            if (line.startswith("/*")):
                in_multiline_comment = True
                if (write_mode):
                    out_file.write(orig_line)
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
                    if (write_mode):
                        out_file.write(orig_line)
                    continue
                else:
                    if (three_parts[0] == "import"):
                        in_import_stmt = True
                        line = three_parts[1] if (split_count == 2) else three_parts[1] + three_parts[2]
                    elif (three_parts[1] == "import"):
                        in_import_stmt = True
                        line = "" if (split_count == 2) else three_parts[2]
                        if (three_parts[0] == "private"):
                            if (write_mode):
                                rex = re.compile(r'private\s+')
                                orig_line = rex.sub('', orig_line)
                            else:
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

            if (write_mode):
                out_file.write(orig_line)

        if (write_mode):
            out_file.close()

    imports_to_delete = set()

    for imp in imports:
        occurrence_count = imports.count(imp)
        if (occurrence_count > 1):
            if (write_mode):
                imports_to_delete.add(imp)
            else:
                errors.add("    * '" + imp + "' appears " + str(occurrence_count) + " times")

    if len(imports_to_delete):
        for imp in imports_to_delete:
            print "to delete : " + imp
            search_and_delete_line(imp, file_copy)

    symbols_not_seen = set(symbols) - symbols_seen
    if (len(symbols_not_seen)):
        for symbol in symbols_not_seen:
            if (write_mode):
                search_and_delete_symbol(symbol, file_copy)
                # pass # launch `sed -i '/symbol/d' filename`
                # the whole line with 'import.*symbol' can be deleted if it is not a selective import, or it
                # is a line with a single selective import
                # But if it is a line with multiple selective imports, it needs better handling
            else:
                errors.add("    * import of '" + symbol + "' could probably be removed")

    # if (write_mode):
    #     shutil.move(file_copy, filename)

    return errors

parser = argparse.ArgumentParser(description='Script to analyse imports in D code')
parser.add_argument('-w', '--write', action='store_true',
                    required = False, default = False,
                    help = 'Automatically make suggested changes')
args = vars(parser.parse_args())

cwd = os.getcwd()

if not os.path.isdir(cwd + "/src"):
    print "'" + cwd + "/src' doesn't exist. Aborting."
    sys.exit(1)

files = []

for root, subdirs, filenames in os.walk(cwd + "/src"):
    for filename in fnmatch.filter(filenames, "*.d"):
        files.append(os.path.join(root, filename))

if (len(files) == 0):
    print "No D files found under '" + cwd + "/src'. Aborting."
    sys.exit(2)

print "Analysing " + str(len(files)) + " D files in '" + cwd + "/src'"
print ""

if (args['write']):
    tmp_directory = tempfile.mkdtemp()
else:
    tmp_directory = 'dummy'

for f in files:
    errors = set()

    errors = analyse_file(f, tmp_directory)

    if (len(errors)):
        print f + ":"
        for e in errors:
            print e
        print ""

# TODO:
# if (tmp file exists):
#     pass # delete it!

