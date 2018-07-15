#!/usr/bin/env python3

################################################################################
#
#   Description:
#   ------------
#       Generic git helper functions.
#
################################################################################

import subprocess
import sys


################################################################################
#
#   A custom git exception class
#
################################################################################

class GitException(Exception):
    pass


################################################################################
#
#   Runs a git command
#
#   Returns:
#       the stdout output of the git command if the command succeeded
#
#   Throws:
#       GitException if the git command failed. The exception will have two
#       arguments - the first is the command that failed and the second is the
#       stderr output
#
################################################################################

def run_command(*args, **kwargs):
    args = list(args)
    args.insert(0, 'git')
    kwargs['stdout'] = subprocess.PIPE
    kwargs['stderr'] = subprocess.PIPE
    proc = subprocess.Popen(args, **kwargs)
    (stdout, stderr) = proc.communicate()
    str_stdout = stdout.decode('utf-8')
    str_stderr = stderr.decode('utf-8')
    if proc.returncode != 0:
        raise GitException(" ".join(args), str_stderr)
    return str_stdout.rstrip('\n')


################################################################################
#
#   Checks whether we are in a git repository
#
#   Returns:
#       The top-level directory of the git repository if we are in one, an empty
#       string otherwise
#
################################################################################

def in_repo():
    try:
        git_top = run_command('rev-parse', '--show-toplevel')
    except GitException as e:
        return ""
    return git_top
