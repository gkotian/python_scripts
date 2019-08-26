#!/usr/bin/env python3

# Pre-requisites:
#     a config file at '${HOME}/.config/clone.py/config.yml' in the format:
#     ```
#     work:
#         email: email-address@work.com
#         signingkey: CAFEBABE007
#         clone_into_dir: /path/to/work/directory
#         github:
#             username: work-github-username
#             orgs:
#                 - a-work-org-in-github
#                 - another-work-org-in-github
#         gitlab:
#             username: work-gitlab-username
#             orgs:
#                 - a-work-org-in-gitlab
#
#     play:
#         <same format as above>
#     ```

import argparse
import os
import sys
import yaml


class CloneException(Exception):
    pass


def parseRepoUrl (repo_url):
    if repo_url.endswith('.git'):
        # Get rid of the trailing `.git`
        repo_url = repo_url[:-4]

    if repo_url.startswith('git@'):
        # It is an ssh URL
        # Get rid of the leading `git@`
        repo_url = repo_url[4:]
        (vcs_provider, org_and_repo) = repo_url.split(':', 1)
    elif repo_url.startswith('https://'):
        # It is an https URL
        # Get rid of the leading `https://`
        repo_url = repo_url[8:]
        (vcs_provider, org_and_repo) = repo_url.split('/', 1)
    else:
        raise CloneException('only SSH & HTTPS URLs are currently supported')

    if vcs_provider != 'github.com' and vcs_provider != 'gitlab.com':
        raise CloneException("only 'github.com' & 'gitlab.com' repos are currently supported")

    # Get rid of the trailing `.com` from the VCS provider
    vcs_provider = vcs_provider[:-4]

    (organization, repo_name) = org_and_repo.split('/', 1)

    return (vcs_provider, organization, repo_name)


def getRepoType (organization):
    all_work_orgs = []

    try:
        orgs = cfg['work']['github']['orgs']
        for org in orgs:
            all_work_orgs.append(org)
    except KeyError:
        pass

    try:
        orgs = cfg['work']['gitlab']['orgs']
        for org in orgs:
            all_work_orgs.append(org)
    except KeyError:
        pass

    if organization in all_work_orgs:
        print("'{}' repos are auto-detected as WORK repos according to the config file".format(organization))
        return 'work'

    all_play_orgs = []

    try:
        orgs = cfg['play']['github']['orgs']
        for org in orgs:
            all_play_orgs.append(org)
    except KeyError:
        pass

    try:
        orgs = cfg['play']['gitlab']['orgs']
        for org in orgs:
            all_play_orgs.append(org)
    except KeyError:
        pass

    if organization in all_play_orgs:
        print("'{}' repos are auto-detected as PLAY repos according to the config file".format(organization))
        return 'play'

    # If not found, ask the user
    response = ''
    while response not in ['p', 'w']:
        response = input('Is this a PLAY or WORK repo? [p/w] ')

    if response == 'w':
        return 'work'
    else:
        return 'play'


def getCfgValue(question, *args):
    # params:
    #     question = question to ask if not found in config
    #     args = keys that lead to the desired value

    args = list(args)

    value = None
    cfg_to_query = cfg

    for arg in args:
        try:
            value = cfg_to_query[arg]
        except KeyError:
            value = None
            break
        else:
            cfg_to_query = value

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

(vcs_provider, organization, repo_name) = parseRepoUrl(args.repo_url)

repo_type = getRepoType(organization)
email = getCfgValue('Enter the email address to be used: ', repo_type, 'email')
signingkey = getCfgValue('Enter the signing key to be used: ', repo_type, 'signingkey')
clone_into_dir = getCfgValue('Enter the directory in which to clone: ', repo_type, 'clone_into_dir')
username = getCfgValue('Enter the username to be used: ', repo_type, vcs_provider, 'username')

ssh_host = '{}-{}'.format(vcs_provider, repo_type.upper())
clone_url = 'git@{}:{}/{}.git'.format(ssh_host, organization, repo_name);
fork_url = 'git@{}:{}/{}.git'.format(ssh_host, username, repo_name);

print('organization = {}'.format(organization))
print('repo_name = {}'.format(repo_name))
print('repo_type = {}'.format(repo_type))
print('email = {}'.format(email))
print('signingkey = {}'.format(signingkey))
print('clone_into_dir = {}'.format(clone_into_dir))
print('clone_url = {}'.format(clone_url))
print('fork_url = {}'.format(fork_url))
print('')

# TODO: actually perform the clone and set the gitconfig properties according to
# the above values
print(f'git clone {clone_url} {clone_into_dir}/{repo_name} && cd {clone_into_dir}/{repo_name} && git remote rename origin upstream && git remote add fork {fork_url} && git config user.email "{email}" && git config user.signingkey "{signingkey}" && cd -')
