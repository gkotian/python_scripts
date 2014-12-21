#!/usr/bin/python


####################################################################################################
#
#   Imports
#
####################################################################################################

# import argparse
# import filecmp
import fnmatch
import os
import re
# import subprocess
# import shutil
import sys
# import tempfile
# import time



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
#
#   Returns:
#       a set containing all potential spelling mistakes
#
####################################################################################################

def analyse_file(filename):
    f = open(filename, 'r')
    contents = f.read()

    comments_list = extract_comments(contents)

    words_set = set()

    for comment in comments_list:
        # Get the individual words in the comment
        words_list = []
        words_list = re.compile('[a-zA-Z]+').findall(comment)

        for word in words_list:
            words_set.add(word)

    print words_set
    # for word in words_set:
    #     if word in whitelist:
    #         continue
    return ""


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
#    Execution starts here! [main :)]
#
####################################################################################################

cwd = os.getcwd()

if not os.path.isdir(cwd + "/src"):
    print "'" + cwd + "/src' doesn't exist. Aborting."
    sys.exit(1)

files = []

for root, subdirs, filenames in os.walk(cwd + "/src"):
    for filename in fnmatch.filter(filenames, "*.d"):
        files.append(os.path.join(root, filename))

total_files = len(files)

if (total_files == 0):
    print "No D files found under '" + cwd + "/src'. Aborting."
    sys.exit(2)

print "Analysing " + str(total_files) + " D files in '" + cwd + "/src'"
print ""

files_done = 0

for f in files:
    # update_progress(files_done / float(total_files))

    errors = set()

    errors = analyse_file(f)

    files_done += 1

    # if (len(errors)):
    #     # Get rid of the progress bar
    #     sys.stdout.write("\r")
    #     sys.stdout.write("\033[K") # Clear to the end of line
    #     sys.stdout.flush()

    #     print f + ":"
    #     for e in errors:
    #         print e
    #     print ""

# update_progress(1.0)

print ""

