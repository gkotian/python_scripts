#!/usr/bin/python

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

def get_compile_command(submods):
    compile_command = []

    # For D1
    compile_command.append("dmd1")
    compile_command.append("-di")
    compile_command.append("-c")
    compile_command.append("-o-")
    compile_command.append("-unittest")
    compile_command.append("-version=UnitTest")
    for submod in submods:
        compile_command.append("-I" + submod + "/src")

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

    return compile_command

def compile(filename, compile_command):
    local_compile_command = compile_command[:]
    local_compile_command.append(filename)

    with open(os.devnull, 'w') as devnull:
        return_code = subprocess.call(local_compile_command, stdout=devnull, stderr=devnull)

    return return_code

def search_and_delete_symbol_import(symbol, filename):
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
                if (',' not in line):
                    skip_line = True
                else:
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

def search_and_delete_first_import(imp, skip_count, filename):
    tmp_file_tuple = tempfile.mkstemp()
    tmp_file = tmp_file_tuple[1]

    with open(filename, 'r') as in_file, open(tmp_file, 'w') as out_file:
        done = False

        for line in in_file:
            if (not done) and (imp in line):
                if (skip_count > 0):
                    skip_count -= 1
                    out_file.write(line);
                else:
                    done = True
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

def analyse_file(file_orig, compile_command, tmp_directory):

    errors = set()

    return_code = compile(file_orig, compile_command)

    if return_code != 0:
        errors.add("    ****** BUILD FAILURE!! ******")
        return errors

    in_multiline_comment = False
    in_import_stmt = False

    imports = []
    imported_symbols = []
    symbols_seen = set()

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

            if (line.endswith("*/")):
                in_multiline_comment = False

            if ( in_multiline_comment ):
                out_file.write(orig_line)
                continue

            if (line.startswith("//")):
                out_file.write(orig_line)
                continue

            if (line.startswith("/*")):
                in_multiline_comment = True
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
                            rex = re.compile(r'private\s+')
                            orig_line = rex.sub('', orig_line)
                            errors.add("    * line " + str(line_num) + ": private import found")

            if (in_import_stmt):
                imported_symbols += gather_symbols(line)
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

            out_file.write(orig_line)

    return_code = compile(file_orig, compile_command)

    if return_code != 0:
        # Revert to original file
        shutil.copyfile(file_copy, file_orig)
    else:
        # Clear all collected errors as those have been taken care of
        errors = set()

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
                search_and_delete_first_import(imp_with_count[0], num_fail, file_orig)

                return_code = compile(file_orig, compile_command)

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
            search_and_delete_symbol_import(symbol, file_orig)

            if filecmp.cmp(file_orig, file_copy):
                symbol_del_fail.add(symbol)
                continue;

            return_code = compile(file_orig, compile_command)

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

submods = []

if not os.path.isdir(cwd + "/submodules"):
    print "'" + cwd + "/submodules' doesn't exist. Assuming no submodules."
else:
    submods_dir = cwd + "/submodules"
    for item in os.listdir(submods_dir):
        full_path = os.path.join(submods_dir, item)
        if os.path.isdir(full_path):
            submods.append(full_path)

compile_command = get_compile_command(submods)

print "Analysing " + str(total_files) + " D files in '" + cwd + "/src'"
print ""

tmp_directory = tempfile.mkdtemp()

files_done = 0

for f in files:
    update_progress(files_done / float(total_files))

    errors = set()

    errors = analyse_file(f, compile_command, tmp_directory)

    files_done += 1

    if (len(errors)):
        sys.stdout.write("\r")
        sys.stdout.write("\033[K") # Clear to the end of line
        sys.stdout.flush()
        print f + ":"
        for e in errors:
            print e
        print ""

update_progress(1.0)

print ""
shutil.rmtree(tmp_directory)

