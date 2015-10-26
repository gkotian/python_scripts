#!/usr/bin/python


####################################################################################################
#
#   Imports
#
####################################################################################################

import argparse
import filecmp
import fnmatch
import getpass
import os
import re
import subprocess
import shutil
import sys
import tempfile
import time



####################################################################################################
#
#   Function to inspect a big comment marker line (either start or end of the comment marker).
#
#   Params:
#       line = line containing the comment marker
#       indent = the expected indent of the comment marker
#
####################################################################################################

def inspect_big_comment_marker(line, indent):
    # Remove only the newline
    line = line.rstrip('\n')

    errors = []

    num_leading_spaces = len(line) - len(line.lstrip(' '))
    if num_leading_spaces != indent:
        errors.append('incorrect number of leading spaces (expected ' + str(indent) + ', found ' +
            str(num_leading_spaces) + ')')

    if line.endswith(' '):
        errors.append('trailing space(s) present')

    if len(line) != 80:
        errors.append('line length is not 80' + ' (' + str(len(line)) + ')')

    return errors


####################################################################################################
#
#   Function to automatically fix certain lines in the given file.
#
#   Params:
#       file_orig = the file on which to perform the automatic fixes
#       lines_to_fix = set containing the numbers of the lines to be fixed
#       fixed_line = the replacement line (i.e. the correct line)
#
####################################################################################################

def performAutomaticFixes(file_orig, lines_to_fix, fixed_line):
    # Make a copy of the file
    file_copy = tmp_directory + '/file_copy'
    shutil.copyfile(file_orig, file_copy)

    with open(file_copy, 'r') as in_file, open(file_orig, 'w') as out_file:
        line_num = 0
        for line in in_file:
            line_num += 1
            if line_num in lines_to_fix:
                line = fixed_line + '\n'
            out_file.write(line)


####################################################################################################
#
#   Function to analyse a file to determine which imports may not be necessary.
#   It also acts upon the determined suggestions and makes changes to the file as necessary (the
#   file is compiled after every edit and if the compilation fails, it is rolled back to its most
#   recent compilable state).
#
#   Params:
#       file_orig = the file to be analysed
#       compile_command = the command to be used for compiling the file
#       tmp_directory = directory in which to create temporary files whenever needed
#
#   Returns:
#       a set containing all errors
#       (if the set is not made up of a single element pointing to an outright compilation error,
#       then it should be thought of as a set of suggestions which could not be automatically
#       applied)
#
####################################################################################################

def analyseFile(filename):
    lines_with_errors = {}

    with open(filename, 'r') as in_file:
        indent = 0
        line_num = 0

        matcher_comment_marker_start = r'^\/\*+$'
        matcher_comment_marker_end   = r'^\*+\/$'

        for line in in_file:
            line_num += 1

            orig_line = line

            line = line.strip()

            if line == '{':
                indent += 4
                continue
            elif line == '}':
                indent -= 4
                continue

            is_big_comment_marker = False

            m1 = re.search(matcher_comment_marker_start, line)
            if m1:
                is_big_comment_marker = True
            else:
                m2 = re.search(matcher_comment_marker_end, line)
                if m2:
                    is_big_comment_marker = True

            if is_big_comment_marker:
                # print 'inspecting line ' + str(line_num) + ' (indent = ' + str(indent) + ')'
                errors_in_line = []
                errors_in_line = inspect_big_comment_marker(orig_line, indent)

                if errors_in_line:
                    lines_with_errors[line_num] = errors_in_line

    return lines_with_errors


####################################################################################################
#
#   Function to display a progress bar to indicate the status of the program.
#
#   Params:
#       progress = a floating point integer between 0 and 1 indicating how much of the program is
#                  done (0 implies nothing is done, 1 implies the program is complete)
#
#   Returns:
#       a set containing all errors (to be thought of as a set of suggestions)
#
####################################################################################################

def updateProgress(progress):
    bar_len = 80 # Modify this to change the length of the progress bar

    if not isinstance(progress, float):
        return

    if progress < 0:
        progress = 0
    elif progress >= 1:
        progress = 1

    block = int(round(bar_len * progress))
    text = "Status: [{0}] {1}%".format( "="*(block-1) + ">" + " "*(bar_len-block-1), int(progress*100))

    removeProgressBar()

    sys.stdout.write(text)
    sys.stdout.flush()


####################################################################################################
#
#   Function to remove the progress bar.
#
####################################################################################################

def removeProgressBar():
    sys.stdout.write("\r")
    sys.stdout.write("\033[K") # Clear to the end of line
    sys.stdout.flush()


####################################################################################################
#
#   Function to get a set of filenames present in the given file.
#
#   Params:
#       cwd = the current working directory
#       filename = file containing the locations of other files
#
#   Returns:
#       a set containing the absolute paths of all files found
#
####################################################################################################

def getFiles(cwd, filename):
    files = set()

    file_to_parse = cwd + "/" + filename

    if not os.path.isfile(file_to_parse):
        return files

    with open(file_to_parse, 'r') as in_file:
        line_num = 0
        for line in in_file:
            line_num += 1
            line = line.strip()
            if not os.path.isfile(line):
                print ("File '" + line + "' (line " + str(line_num) + " in " + filename +
                    ") doesn't exist. Will ignore.")
            else:
                if not os.path.isabs(line):
                    line = cwd + "/" + line
                files.add(line)

    return files


####################################################################################################
#
#    Execution starts here! [main :)]
#
####################################################################################################

parser = argparse.ArgumentParser(usage='%(prog)s [ARGUMENTS]', description='Comments Formatter')
parser.add_argument('-n', '--non-interactive', action='store_true',
                    required = False, default = False,
                    help = 'Run for all files without waiting for user input')
args = vars(parser.parse_args())

cwd = os.getcwd()

files = set()

if os.path.isfile(cwd + "/restrictlist.txt"):
    files = getFiles(cwd, "restrictlist.txt")
    print "Files to restrict   : " + str(len(files))
else:
    for root, subdirs, filenames in os.walk(cwd):
        for filename in fnmatch.filter(filenames, "*.d"):
            files.add(os.path.join(root, filename))
    print "Total D files found : " + str(len(files))

files_to_skip = getFiles(cwd, "skiplist.txt")
print "Files to skip       : " + str(len(files_to_skip))
files -= files_to_skip

if not files:
    print "No D files to analyse. Aborting."
    sys.exit(2)

total_files = len(files)

print "Files to analyse    : " + str(total_files)
print ""

tmp_directory = tempfile.mkdtemp()

files_done = 0
files_with_errors = 0
lines_auto_fixed = 0
files_with_auto_fixed_lines = 0

for f in files:
    updateProgress(files_done / float(total_files))

    lines_with_errors = analyseFile(f)

    files_done += 1

    if lines_with_errors:
        files_with_errors += 1
        lines_to_fix = set()

        removeProgressBar()
        print f + ':'

        for line in sorted(lines_with_errors):
            print "    * line " + str(line)
            for error in lines_with_errors[line]:
                if error == 'incorrect number of leading spaces (expected 4, found 5)':
                    lines_to_fix.add(line)
                    print "        - <auto fixed>"
                else:
                    print "        - " + error

        print ''

        if lines_to_fix:
            lines_auto_fixed += len(lines_to_fix)
            files_with_auto_fixed_lines += 1
            fixed_line = '    ***************************************************************************/'
            performAutomaticFixes(f, lines_to_fix, fixed_line)

        # Note 'non_interactive' instead of 'non-interactive' since the hyphen is automatically
        # converted to an underscore
        if not args['non_interactive']:
            updateProgress(files_done / float(total_files))
            sys.stdout.write('\r')
            sys.stdout.write('\033[1A')
            dummy = getpass.getpass("")

removeProgressBar()

print 'Number of files analysed: ' + str(total_files)
print 'Files with errors: ' + str(files_with_errors)
if lines_auto_fixed > 0:
    print ('Lines automatically fixed: ' + str(lines_auto_fixed) + ' (in ' +
        str(files_with_auto_fixed_lines) + ' files)')

shutil.rmtree(tmp_directory)

