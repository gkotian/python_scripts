#!/usr/bin/python

import argparse
import ConfigParser
import subprocess

parser = argparse.ArgumentParser(description='Script to help launch terminals')
parser.add_argument('-c', '--config-file', nargs='?', required=True, default='',
    help='Config file to control launched terminals')
parser.add_argument('-p', '--terminal-profile', nargs='?', required=False,
    default='Auto',
    help='Profile to use in the launched terminals')
args = vars(parser.parse_args())

config = ConfigParser.SafeConfigParser()
config.readfp(open(args['config_file']))

for section in config.sections():

    directory = config.get(section, "directory")
    # TODO: confirm that directory exists

    commands = config.get(section, "commands")

    # Execute the shell after all the commands, so that the terminal doesn't
    # exit immediately
    commands = commands + '; exec zsh'

    proc = subprocess.Popen(['gnome-terminal',
        '--working-directory={}'.format(directory),
        '--window-with-profile={}'.format(args['terminal_profile']),
        '-x', 'sh', '-c', commands])
