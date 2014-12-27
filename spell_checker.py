#!/usr/bin/python


####################################################################################################
#
#   Imports
#
####################################################################################################

from enchant         import Dict, DictWithPWL
from enchant.checker import SpellChecker

import argparse
import fnmatch
import os
import re
import sys



####################################################################################################
#
#   Extracts comments from the given code text
#
#   Params:
#       text = code from which to extract comments
#
#   Returns:
#       a list containing the extracted comments
#
####################################################################################################

def extract_comments(text):
    pattern = re.compile(
        # r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        r'/\+.*?\+/|//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )

    return re.findall(pattern, text)


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

    comments_list = extract_comments(contents)

    for comment in comments_list:
        checker.set_text(comment)
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
#       whitelist = file containing words that are to be considered valid (optional)
#
#   Returns:
#       a 'Dict' object containing all valid words
#
####################################################################################################

def get_valid_words(whitelist=""):
    if whitelist:
        d = DictWithPWL("en_GB", whitelist)
    else:
        d = Dict("en_GB")

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
    supported_extensioned_file_types = [ 'c', 'cc', 'cpp', 'd', 'txt' ]

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
parser.add_argument('-s', '--suggest', action='store_true',
                    required = False, default = False,
                    help = 'Provide suggestions for possible errors')
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
    print "No supported files to process. Aborting."
    sys.exit(1)

print "Analysing " + str(total_files) + " files."
print ""

# Get the collection of all valid words
valid_words = get_valid_words(args['whitelist'])

# Make a spell checker object using all the valid words
checker = SpellChecker(valid_words)

files_done = 0

for f in files:
    update_progress(files_done / float(total_files))

    errors = set()

    errors = analyse_file(f, checker)

    files_done += 1

    if (len(errors)):
        # Get rid of the progress bar
        sys.stdout.write("\r")
        sys.stdout.write("\033[K") # Clear to the end of line
        sys.stdout.flush()

        print f + ":"
        for e in errors:
            print "    * " + e
            if args['suggest']:
                print "        ",
                print valid_words.suggest(e)
        print ""

update_progress(1.0)

print ""

