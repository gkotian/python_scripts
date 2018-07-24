#!/usr/bin/env python3

import argparse
import git
import os
import re
import shutil
import subprocess
import sys
import tempfile


# Find the Dockerfile and the docker image name to use
def get_docker_details(cmdline_dockerfile):
    # If a Dockerfile was given via the command-line, then we must use it, and
    # not try to search for a suitable one.
    if cmdline_dockerfile:
        if not cmdline_dockerfile.endswith('Dockerfile'):
            sys.exit("Given Dockerfile doesn't end with 'Dockerfile'. Aborting.")

        if not os.path.isfile(cmdline_dockerfile):
            sys.exit("'{}' doesn't exist. Aborting.".format(cmdline_dockerfile))

        docker_image_name = os.path.basename(os.path.dirname(cmdline_dockerfile))

        return cmdline_dockerfile, docker_image_name

    attempted_dockerfiles = []

    print('No Dockerfile given, will look for a suitable one.')

    pwd = os.getcwd()
    pwd_name = os.path.basename(pwd)

    # First check if a Dockerfile exists in the current directory
    dockerfile = '{}/Dockerfile'.format(pwd)
    if os.path.isfile(dockerfile):
        # There's one extra case to take care of here. If there is a
        # 'docker/Dockerfile', and the script is run from within this 'docker'
        # directory, then we should use the parent of the current directory to
        # get the docker image name (this is to avoid using 'docker' as the
        # docker image name)
        if pwd_name == 'docker':
            parent_of_pwd = os.path.dirname(pwd)
            docker_image_name = os.path.basename(parent_of_pwd)
        else:
            docker_image_name = pwd_name

        return dockerfile, docker_image_name

    attempted_dockerfiles.append(dockerfile)

    # Next look for a 'docker/Dockerfile' relative to the current directory
    dockerfile = '{}/docker/Dockerfile'.format(pwd)
    if os.path.isfile(dockerfile):
        return dockerfile, pwd_name

    attempted_dockerfiles.append(dockerfile)

    # Next check for a Dockerfile based on the current directory
    dockerfile = os.path.expanduser('~/play/gautam_linux/docker/{}/Dockerfile'.format(pwd_name))
    if os.path.isfile(dockerfile):
        return dockerfile, pwd_name

    attempted_dockerfiles.append(dockerfile)

    # Finally check for a Dockerfile based on the name of the git repo (this is
    # possible only if we are in a git repo). But if we are at the top-level of
    # the git repo, then there is no point of making this check as the same
    # check is covered by the 'based on the current directory' check made above.
    git_top = git.in_repo()
    if git_top and git_top != pwd:
        repo_name = os.path.basename(git_top)
        dockerfile = os.path.expanduser('~/play/gautam_linux/docker/{}/Dockerfile'.format(repo_name))
        if os.path.isfile(dockerfile):
            return dockerfile, repo_name

        attempted_dockerfiles.append(dockerfile)
    
    print('Tried...')
    for file in attempted_dockerfiles:
        print('    {}'.format(file))
    print('...without success. Aborting.')
    sys.exit(1)


def perform_jenkins_specific_mod(docker_image_name, dockerfile):
    # Create two temporary files - one is the original Dockerfile before
    # modifications, the other is to perform the necessary modifications
    tempfile_suffix = '-' + docker_image_name + '-Dockerfile'
    dockerfile_backup = tempfile.mkstemp(suffix=tempfile_suffix)[1]
    dockerfile_new    = tempfile.mkstemp(suffix=tempfile_suffix)[1]

    shutil.copy2(dockerfile, dockerfile_backup)

    matcher_image_line  = r'^FROM sociomantic(.*)/dlang:v(.*)'
    modification_made = False

    with open(dockerfile, 'r') as in_file, open(dockerfile_new, 'w') as out_file:
        for line in in_file:
            m = re.search(matcher_image_line, line)
            if m:
                if m.group(1) != '' and m.group(1) != 'tsunami':
                    os.unlink(dockerfile_backup)
                    os.unlink(dockerfile_new)
                    sys.exit("Only 'sociomantic/dlang' and 'sociomantictsunami/dlang' images are currently supported. Aborting.")

                # Modify the line to add the 'xenial-' prefix
                line = 'FROM sociomantic{}/dlang:xenial-v{}\n'.format(m.group(1), m.group(2))
                modification_made = True

            out_file.write(line)

    if modification_made:
        # Replace the Dockerfile with the modified Dockerfile
        shutil.move(dockerfile_new, dockerfile)
    else:
        # There was no 'sociomantic/dlang' or 'sociomantictsunami/dlang' line at
        # all in the Dockerfile, which means all the work we did in this
        # function was a waste.
        os.unlink(dockerfile_backup)
        os.unlink(dockerfile_new)
        dockerfile_backup = ''

    return dockerfile_backup


def revert_jenkins_specific_mod(dockerfile_backup, dockerfile):
    if dockerfile_backup != '':
        shutil.move(dockerfile_backup, dockerfile)


parser = argparse.ArgumentParser(
    description='Script to launch a docker container')
parser.add_argument('-d', '--dockerfile', nargs='?', required=False, default='',
    help='Dockerfile to use')
parser.add_argument('-r', '--run', nargs='?', required=False, default='',
    help='Command to run (instead of running a shell) [killing the command midway is non-trivial]')
args = vars(parser.parse_args())

dockerfile, docker_image_name = get_docker_details(args['dockerfile'])
print('Docker image name: {}'.format(docker_image_name))
print('Dockerfile: {}'.format(dockerfile))

dockerfile_backup = perform_jenkins_specific_mod(docker_image_name, dockerfile)

command = ['docker', 'build', '-t']
command.append(docker_image_name)
command.append(os.path.dirname(dockerfile))
subprocess.run(command)

revert_jenkins_specific_mod(dockerfile_backup, dockerfile)

# If we're in a git repo, we mount the top-level of the git repo, or else we
# just the mount the current directory
mount_dir = git.in_repo()
if not mount_dir:
    mount_dir = os.getcwd()

command = ['docker', 'run', '-ti', '--rm', '-v']
command.append('{}:/project'.format(mount_dir))
command.append('-w')
command.append('/project')
command.append(docker_image_name)

if args['run']:
    for part in args['run'].split():
        command.append(part)
else:
    command.append('/bin/bash')

subprocess.run(command)
