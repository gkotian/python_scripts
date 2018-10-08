#!/usr/bin/python


# Dealing with non-auto-fixed lines:
# ----------------------------------
#     1. Get the matching egrep command:
#            $> egrep -rl "^         [\*]{70}\/$" src
#     2. Open all matching files in vim:
#            $> CMD='egrep -rl "^         [\*]{70}\/$" src'
#            $> v `eval ${CMD} | ol`
#     3. Get the matching vim search command (it'll be very similar to the egrep
#        command, except that '{' & '}' would need to be escaped as well:
#            /^         [\*]\{70\}\/$
#     4. Record a suitable macro, say to @q (ensure that 'n' is the first
#        character recorded, so that the macro can be run many number of times
#        with it refusing to run if there are no more matches)
#     5. Set hidden, so that you can change buffers without saving
#            :se hidden
#     6. Run the macro many times in each buffer
#            :bufdo normal 20@q
#     7. Save all buffers
#            :wa 


####################################################################################################
#
#   Imports
#
####################################################################################################

from enchant         import Dict, DictWithPWL
from enchant.checker import SpellChecker

import argparse
import getpass
import fnmatch
import os
import re
import sys



####################################################################################################
#
#   Checks for possible spelling mistakes in the comments of a file.
#
#   Params:
#       filename = file to analyse
#       checker  = object used to check spellings
#
#   Returns:
#       a set containing all potential spelling mistakes
#
####################################################################################################

def analyse_file(filename, checker):
    f = open(filename, 'r')
    contents = f.read()

    errors = set()

    if filename.endswith(".c") or filename.endswith(".cc") or filename.endswith(".cpp"):
        pattern = re.compile(
            r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
            re.DOTALL | re.MULTILINE
        )
        text_list = re.findall(pattern, contents)
    elif filename.endswith(".d"):
        pattern = re.compile(
            r'/\+.*?\+/|//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
            re.DOTALL | re.MULTILINE
        )
        text_list = re.findall(pattern, contents)
    elif filename.endswith(".py") or filename.endswith(".sh") or filename == "Makefile":
        pattern = re.compile(r'#.*')
        text_list = re.findall(pattern, contents)
    elif filename.endswith(".vim"):
        pattern = re.compile(r'^\s*?".*?$', re.MULTILINE)
        text_list = re.findall(pattern, contents)
    elif filename.endswith(".txt") or filename.endswith(".markdown") or filename.endswith(".md") or filename.endswith(".rst"):
        text_list = contents.split()
    else:
        return errors

    for text in text_list:
        checker.set_text(text)
        for error in checker:
            errors.add(error.word)

    return errors


####################################################################################################
#
#   Displays a progress bar to indicate the status of the program.
#
#   Params:
#       progress = a floating point integer between 0 and 1 indicating how much of the program is
#                  done (0 implies nothing is done, 1 implies the program is complete)
#
#   Returns:
#       a set containing all errors (to be thought of as a set of suggestions)
#
####################################################################################################

def update_progress(progress):
    bar_len = 80 # Modify this to change the length of the progress bar

    if not isinstance(progress, float):
        return

    if progress < 0:
        progress = 0
    elif progress >= 1:
        progress = 1

    block = int(round(bar_len * progress))
    text = "Status: [{0}] {1}%".format( "="*(block-1) + ">" + " "*(bar_len-block-1), int(progress*100))

    sys.stdout.write("\r")
    sys.stdout.write("\033[K") # Clear to the end of line
    sys.stdout.write(text)
    sys.stdout.flush()


####################################################################################################
#
#   Gets all valid words.
#
#   Params:
#       dictionary = dictionary to use
#       whitelist = file containing words that are to be considered valid (optional)
#
#   Returns:
#       a 'Dict' object containing all valid words
#
####################################################################################################

def get_valid_words(dictionary, whitelist=""):
    if whitelist:
        d = DictWithPWL(dictionary, whitelist)
    else:
        d = Dict(dictionary)

    return d


####################################################################################################
#
#   Filters a list of files to get only supported files
#
#   Params:
#       all_files = list of files to be filtered
#
#   Returns:
#       a list containing only supported files
#
####################################################################################################

def filter_supported_files(all_files):
    supported_extensionless_files = [ 'Makefile' ]
    supported_extensioned_file_types = [ 'c', 'cc', 'cpp', 'd', 'markdown', 'md', 'py', 'rst', 'sh',
                                         'txt', 'vim' ]

    filtered_files = []

    for filename in all_files:
        if filename in supported_extensionless_files:
            filtered_files.append(filename)
        else:
            dummy, extension = os.path.splitext(filename)
            if extension[1:] in supported_extensioned_file_types:
                filtered_files.append(filename)

    return filtered_files


####################################################################################################
#
#    Execution starts here! [main :)]
#
####################################################################################################

parser = argparse.ArgumentParser(description='Spell Checker')
parser.add_argument('-k', '--skip-count', nargs='?',
                    required = False, default = "",
                    help = 'Number of files to skip')
parser.add_argument('-n', '--non-interactive', action='store_true',
                    required = False, default = False,
                    help = 'Run for all files without waiting for user input')
parser.add_argument('-s', '--suggest', action='store_true',
                    required = False, default = False,
                    help = 'Provide suggestions for possible errors')
parser.add_argument('-u', '--us-english', action='store_true',
                    required = False, default = False,
                    help = 'Use American English')
parser.add_argument('-w', '--whitelist', nargs='?',
                    required = False, default = "",
                    help = 'Provide a whitelist file')
args = vars(parser.parse_args())

cwd = os.getcwd()

files = []

for root, subdirs, filenames in os.walk(cwd):
    for filename in filter_supported_files(filenames):
        files.append(os.path.join(root, filename))

total_files = len(files)

if (total_files == 0):
    print("No supported files to process. Aborting.")
    sys.exit(1)

print("Files to analyse : " + str(total_files))

files_to_skip = args['skip_count']

if not files_to_skip:
    files_to_skip = 0
else:
    files_to_skip = int(files_to_skip)

print("Files to skip    : " + str(files_to_skip))
print("")

if files_to_skip > total_files:
    print("Files to skip more than total files. Aborting.")
    sys.exit(2)

# Note 'us_english' instead of 'us-english' since the hyphen is automatically converted to an
# underscore
dictionary = "en_US" if args['us_english'] else "en_GB"

# Get the collection of all valid words
valid_words = get_valid_words(dictionary, args['whitelist'])

# Make a spell checker object using all the valid words
checker = SpellChecker(valid_words)

files_analysed = 0

files_with_errors = 0

for f in files:
    update_progress(files_analysed / float(total_files))

    errors = set()

    errors = analyse_file(f, checker)

    files_analysed += 1

    if (len(errors)):
        files_with_errors += 1

        # Get rid of the progress bar
        sys.stdout.write("\r")
        sys.stdout.write("\033[K") # Clear to the end of line
        sys.stdout.flush()

        if files_to_skip >= files_with_errors:
            print(str(files_with_errors) + ". " + f + " -- skipped")
            if files_to_skip == files_with_errors:
                print("")
            continue

        print(str(files_with_errors) + ". " + f + ":")
        for e in errors:
            print("    * " + e)
            if args['suggest']:
                print("        ",)
                print(valid_words.suggest(e))
        print("")

        # Note 'non_interactive' instead of 'non-interactive' since the hyphen is automatically
        # converted to an underscore
        if not args['non_interactive']:
            dummy = getpass.getpass("")

update_progress(1.0)

print("")

