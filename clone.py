#!/usr/bin/env python3

import argparse
import os
import sys
import yaml


class CloneException(Exception):
    pass


def parseRepoUrl (repo_url):
    if not repo_url.endswith('.git'):
        raise CloneException('Only git repos are currently supported')

    # Get rid of the trailing `.git`
    repo_url = repo_url[:-4]

    if repo_url.startswith('git@'):
        # It is an ssh URL
        # Get rid of the leading `git@`
        repo_url = repo_url[4:]
        vcs_provider, org_and_repo = repo_url.split(':', 1)
    elif repo_url.startswith('https://'):
        # It is an https URL
        # Get rid of the leading `https://`
        repo_url = repo_url[8:]
        vcs_provider, org_and_repo = repo_url.split('/', 1)
    else:
        raise CloneException('only SSH & HTTPS URLs are currently supported')

    if vcs_provider != 'github.com' and vcs_provider != 'gitlab.com':
        raise CloneException("only 'github.com' & 'gitlab.com' repos are currently supported")

    organization, repo_name = org_and_repo.split('/', 1)

    return organization, repo_name


def getRepoType (organization):
    if 'work' in cfg:
        all_work_orgs = []

        if 'github-orgs' in cfg['work']:
            all_work_orgs += cfg['work']['github-orgs']

        if 'gitlab-orgs' in cfg['work']:
            all_work_orgs += cfg['work']['gitlab-orgs']

        if organization in all_work_orgs:
            print('{} repos are auto-detected as WORK repos according to the config file'.format(organization))
            return 'work'

    if 'play' in cfg:
        all_play_orgs = []

        if 'github-orgs' in cfg['play']:
            all_play_orgs += cfg['play']['github-orgs']

        if 'gitlab-orgs' in cfg['play']:
            all_play_orgs += cfg['play']['gitlab-orgs']

        if organization in all_play_orgs:
            print('{} repos are auto-detected as PLAY repos according to the config file'.format(organization))
            return 'play'

    # If not found, ask the user
    response = ''
    while response not in ['p', 'w']:
        response = input('Is this a PLAY or WORK repo? [p/w] ')

    if response == 'w':
        return 'work'
    else:
        return 'play'


def getCfgValue(repo_type, key, question):
    if key in cfg[repo_type]:
        value = cfg[repo_type][key]
    else:
        value = ''
        while not value:
            value = input(question)

    return value


parser = argparse.ArgumentParser(
    usage='%(prog)s <repo-url>',
    description='Script to help clone a repo')
parser.add_argument(
    'repo_url',
    help='URL of the git repository to be cloned')
args = parser.parse_args()

config_file = os.path.expanduser('~/.config/clone.py/config.yml')
if not os.path.isfile(config_file):
    # TODO: for now, just abort if the config file doesn't exist. In future,
    # either select suitable defaults or ask for input from user for the various
    # config properties if no config file is present.
    print('Config file not found. Aborting.')
    sys.exit(1)

with open(config_file, 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

organization, repo_name = parseRepoUrl(args.repo_url)

repo_type = getRepoType(organization)
email = getCfgValue(repo_type, 'email', 'Enter the email address to be used: ')
signingkey = getCfgValue(repo_type, 'signingkey', 'Enter the signing key to be used: ')
clone_into_dir = getCfgValue(repo_type, 'clone_into_dir', 'Enter the directory in which to clone: ')

print('organization = {}'.format(organization))
print('repo_name = {}'.format(repo_name))
print('repo_type = {}'.format(repo_type))
print('email = {}'.format(email))
print('signingkey = {}'.format(signingkey))
print('clone_into_dir = {}'.format(clone_into_dir))

# TODO: actually perform the clone and set the gitconfig properties according to
# the above values
