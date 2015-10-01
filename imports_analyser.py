#!/usr/bin/python


####################################################################################################
#
#   Imports
#
####################################################################################################

import argparse
import filecmp
import fnmatch
import os
import re
import subprocess
import shutil
import sys
import tempfile
import time



####################################################################################################
#
#   Function to form the command used for compilation.
#
#   Params:
#       cwd = the current working directory
#
#   Returns:
#       the compilation command to be used (does not contain the filename)
#
####################################################################################################

def getCompileCommand(cwd):
    submods = []

    if not os.path.isdir(cwd + "/submodules"):
        print "'" + cwd + "/submodules' doesn't exist. Assuming no submodules."
    else:
        submods_dir = cwd + "/submodules"
        for item in os.listdir(submods_dir):
            full_path = os.path.join(submods_dir, item)
            if os.path.isdir(full_path):
                submods.append(full_path)

    compile_command = []

    # For D1
    compile_command.append("dmd1")
    compile_command.append("-di")
    compile_command.append("-c")
    compile_command.append("-o-")
    compile_command.append("-unittest")
    compile_command.append("-version=UnitTest")

    # # For a test D2 file
    # compile_command.append("gdc")
    # compile_command.append("-c")
    # compile_command.append("-o")
    # compile_command.append("/dev/null")

    # # For vibe.d
    # compile_command.append("gdc")
    # compile_command.append("-I/home/gautam/play/vibe.d/source")
    # compile_command.append("-c")
    # compile_command.append("-o")
    # compile_command.append("/dev/null")

    compile_command.append("-I" + cwd + "/src")

    compile_command.append("-I" + cwd + "/build/devel/include")

    for submod in submods:
        compile_command.append("-I" + submod + "/src")

    return compile_command


####################################################################################################
#
#   Function to compile a file.
#
#   Params:
#       filename = the file to be compiled
#       compile_command = command to be used for the compilation
#       debug_flags = set of additional debug flags present in the file
#       save_stderr = whether to save stderr output or not
#
#   Returns:
#       the return code of the result of compilation
#
####################################################################################################

def compileFile(filename, compile_command, debug_flags, save_stderr=False):
    local_compile_command = compile_command[:]

    for flag in debug_flags:
        local_compile_command.append("-debug=" + flag)

    local_compile_command.append(filename)

    with open(os.devnull, 'w') as devnull:
        stderr_file = open(tmp_directory + "/stderr.txt", 'w') if save_stderr else devnull
        return_code = subprocess.call(local_compile_command, stdout=devnull, stderr=stderr_file)

    return return_code


####################################################################################################
#
#   Function used to search for and delete the statement importing the given symbol.
#
#   Params:
#       symbol = symbol whose import statement is to be deleted
#       filename = file in which to search
#
####################################################################################################

def searchAndDeleteSymbolImport(symbol, filename):
    tmp_file_tuple = tempfile.mkstemp()
    tmp_file = tmp_file_tuple[1]

    with open(filename, 'r') as in_file, open(tmp_file, 'w') as out_file:
        skip_line = False

        for line in in_file:
            skip_line = False

            if ('import' in line) and (symbol in line) and (';' in line):
                if (',' not in line):
                    # This is the only symbol imported in this line, so this whole line can be
                    # deleted
                    skip_line = True
                else:
                    # There are other symbols also imported in this line, so we must delete only the
                    # symbol we're looking for
                    if (':' in line):
                        begin_matcher = r'\s' + re.escape(symbol) + r'\s*,\s*'
                        middle_matcher = r',\s*' + re.escape(symbol) + r'\s*,\s*'
                        end_matcher = r'\s*,\s*' + re.escape(symbol) + r'\s*'
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


####################################################################################################
#
#   Function to search for and delete the first occurrence of the given import statement. This
#   function is used only when an import statement occurs multiple times in a file.
#
#   Params:
#       imp = the import statement to be deleted
#       skip_count = the number of times the given import statement should be skipped (i.e. retained
#                    as is and not treated as a match)
#       filename = file in which to search
#
####################################################################################################

def searchAndDeleteFirstImport(imp, skip_count, filename):
    tmp_file_tuple = tempfile.mkstemp()
    tmp_file = tmp_file_tuple[1]

    with open(filename, 'r') as in_file, open(tmp_file, 'w') as out_file:
        done = False

        for line in in_file:
            if (not done) and ("import" in line) and (imp in line):
                if (skip_count > 0):
                    skip_count -= 1
                    out_file.write(line);
                else:
                    # The current line is not written to the output file (effectively deleting it).

                    # Set the done flag so that all remaining lines in the file are blindly written
                    # to the output file.
                    done = True
            else:
                out_file.write(line);

    shutil.move(tmp_file, filename)


####################################################################################################
#
#   Function to gather all symbols of interest in the given line.
#
#   Params:
#       line = the line from which to gather symbols
#
#   Returns:
#       a list containing all the gathered symbols
#
####################################################################################################

def gatherSymbols(line):
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

def analyseFile(file_orig, compile_command, tmp_directory):

    errors = set()

    return_code = compileFile(file_orig, compile_command, [])

    if return_code != 0:
        # If compilation fails at this stage, it means that some modification made to another file
        # previously has caused a problem in this file. This is reason enough to abort and call for
        # manual intervention.
        errors.add("BUILD FAILURE")
        return errors

    in_import_stmt = False

    imports = []
    imported_symbols = []
    symbols_seen = set()
    debug_flags = set()

    # Make a copy of the file
    file_copy = tmp_directory + '/file_copy'
    shutil.copyfile(file_orig, file_copy)

    with open(file_copy, 'r') as in_file, open(file_orig, 'w') as out_file:
        line_num = 0
        skip_line = False

        for line in in_file:
            line_num += 1

            orig_line = line

            line = line.strip()

            if (len(line) == 0):
                out_file.write(orig_line)
                continue

            if (line.startswith("//")):
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
                        # 'import' is the only word in the line - assume it is a valid import
                        # statement
                        in_import_stmt = True
                    out_file.write(orig_line)
                    continue
                else:
                    if (three_parts[0] == "import"):
                        # 'import' is the first word in the line - assume it is a valid import
                        # statement
                        in_import_stmt = True
                        line = three_parts[1] if (split_count == 2) else three_parts[1] + three_parts[2]
                    elif (three_parts[1] == "import"):
                        # 'import' is the second word in the line - but we'll take it as a valid
                        # import statement only if it preceded by 'private' or 'public'
                        line = "" if (split_count == 2) else three_parts[2]
                        if (three_parts[0] == "private"):
                            # It's a 'private import' - valid import statement, but the 'private'
                            # keyword is redundant, so remove it.
                            in_import_stmt = True
                            rex = re.compile(r'private\s+')
                            orig_line = rex.sub('', orig_line)
                        elif (three_parts[0] == "public"):
                            # It's a 'public import' - also valid import statement.
                            in_import_stmt = True

            if (in_import_stmt):
                imported_symbols += gatherSymbols(line)
                if (";" in line):
                    in_import_stmt = False
                if (len(line)):
                    # Get rid of the last character (',' or ';')
                    line = line.rstrip(',;')
                    imports.append(line)
            else:
                for symbol in imported_symbols:
                    if symbol in line:
                        symbols_seen.add(symbol)

            if "debug" in line:
                # Remove all spaces
                rex = re.compile(r'\s+')
                line = rex.sub('', line)

                # Get the word in the parentheses after debug (matching inside the parentheses is
                # done in a non-greedy manner using '?')
                m = re.search(r'debug\((.*?)\)', line)
                if m:
                    debug_flags.add(m.group(1))

            out_file.write(orig_line)

    return_code = compileFile(file_orig, compile_command, debug_flags)

    if return_code != 0:
        # Revert to original file
        shutil.copyfile(file_copy, file_orig)
    else:
        # Update the file copy with the modified version
        shutil.copyfile(file_orig, file_copy)

    imports_to_delete = []

    imports_set = set(imports)

    for imp in imports_set:
        occurrence_count = imports.count(imp)
        if (occurrence_count > 1):
            imports_to_delete.append([imp, occurrence_count-1])

    if len(imports_to_delete):
        for imp_with_count in imports_to_delete:
            del_count = 0
            num_fail = 0

            while del_count < imp_with_count[1]:
                searchAndDeleteFirstImport(imp_with_count[0], num_fail, file_orig)

                return_code = compileFile(file_orig, compile_command, debug_flags)

                if return_code != 0:
                    num_fail += 1
                    # Revert
                    shutil.copyfile(file_copy, file_orig)
                else:
                    shutil.copyfile(file_orig, file_copy)

                del_count += 1

            if num_fail != 0:
                errors.add("    * '" + imp_with_count[0] + "' appears " + str(num_fail + 1) + " times")

    shutil.copyfile(file_orig, file_copy)

    symbols_not_seen = set(imported_symbols) - symbols_seen
    if (len(symbols_not_seen)):
        symbol_del_fail = set()

        for symbol in symbols_not_seen:
            searchAndDeleteSymbolImport(symbol, file_orig)

            if filecmp.cmp(file_orig, file_copy):
                symbol_del_fail.add(symbol)
                continue;

            return_code = compileFile(file_orig, compile_command, debug_flags)

            if return_code != 0:
                # Revert
                shutil.copyfile(file_copy, file_orig)
                symbol_del_fail.add(symbol)
            else:
                shutil.copyfile(file_orig, file_copy)

        if len(symbol_del_fail):
            for symbol in symbol_del_fail:
                errors.add("    * '" + symbol + "' imported but unused (selective imports possible?)")

    return errors


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
#   Function to make a first-pass check on the given files using the given compile command.
#
#   Params:
#       files = list of all files to be compiled
#       compile_command = command to be used for the compilation
#
#   Returns:
#       string containing the first file that failed to compile, an empty string if all files
#       compiled successfully
#
####################################################################################################

def makeFirstPassCheck(files, compile_command):
    failed_file = ""
    files_done = 0
    total_files = len(files)

    for f in files:
        updateProgress(files_done / float(total_files))
        return_code = compileFile(f, compile_command, [])
        if return_code != 0:
            failed_file = f
            break
        files_done += 1

    removeProgressBar()
    return failed_file


####################################################################################################
#
#    Execution starts here! [main :)]
#
####################################################################################################

cwd = os.getcwd()

if not os.path.isdir(cwd + "/src"):
    print "'" + cwd + "/src' doesn't exist. Aborting."
    sys.exit(1)

files_to_skip = set()

if os.path.isfile(cwd + "/skiplist.txt"):
    with open(cwd + "/skiplist.txt", 'r') as in_file:
        for line in in_file:
            line = line.strip()
            if not os.path.isfile(line):
                print "Skiplist file '" + line + "' not found. Will ignore."
            else:
                if not os.path.isabs(line):
                    line = cwd + "/" + line
                files_to_skip.add(line)

files = []

for root, subdirs, filenames in os.walk(cwd + "/src"):
    for filename in fnmatch.filter(filenames, "*.d"):
        full_file_path = os.path.join(root, filename)
        if not full_file_path in files_to_skip:
            files.append(os.path.join(root, filename))

if (len(files) == 0):
    print "No D files to analyse. Aborting."
    sys.exit(2)

total_files = len(files) + len(files_to_skip)

print "Total D files found : " + str(total_files)
print "Files to skip       : " + str(len(files_to_skip))
print "Files to analyse    : " + str(len(files))
print ""

compile_command = getCompileCommand(cwd)

print "Making a first-pass check to see if all files compile ..."

failed_file = makeFirstPassCheck(files, compile_command);
sys.stdout.write("\033[1A") # Go up one line

if not failed_file:
    print "Making a first-pass check to see if all files compile ... DONE"
    print "Starting imports analysis now..."
    print ""
else:
    print "Making a first-pass check to see if all files compile ... FAILED"
    print ""
    print "File '" + failed_file + "' failed to compile."
    print "Please fix this manually before attempting again."
    print "Build command used:"
    for p in compile_command: print p,
    print failed_file
    print ""
    print "Aborting."
    sys.exit(3)

tmp_directory = tempfile.mkdtemp()

files_done = 0
files_modified = 0
files_with_suggestions = 0

for f in files:
    updateProgress(files_done / float(total_files))

    errors = set()

    # Make a temporary copy of the file
    tmp_file = tmp_directory + '/tmp_file'
    shutil.copyfile(f, tmp_file)

    errors = analyseFile(f, compile_command, tmp_directory)

    files_done += 1

    if not filecmp.cmp(f, tmp_file):
        files_modified += 1

    if (len(errors)):
        removeProgressBar()

        if "BUILD FAILURE" in errors:
            print ("One or more changes made in one of the " + str(files_modified) +
                   " modified files has caused a build failure in:")
            print "    " + f
            print ("Please identify this change(s), revert only the relevant change(s), and add " +
                   "that file to the skiplist.")
            print "This will prevent the same modification(s) from being performed in the next run."
            print ""
            print "Aborting."
            sys.exit(4)

        files_with_suggestions += 1

        print f + ":"
        for e in errors:
            print e
        print ""

removeProgressBar()

print ""
print "Number of files analysed: " + str(total_files)
print "Number of files automatically modified: " + str(files_modified)
print "Number of files with suggestions: " + str(files_with_suggestions)

shutil.rmtree(tmp_directory)

