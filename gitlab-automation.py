#!/usr/bin/env python
"""
Manages your new gitlab project like a pro

it performs the following tasks:

1. checks out the project
2. creates the build directory
3. creates the new deploy.json file
4. creates the new .gitlab-ci.yml file
5. enables the ci on the project
6. creates new variables
7. updates the jira ticket (out of scope for now)
"""
from __future__ import print_function
from __future__ import absolute_import

# modules from the standard python library
import argparse
import os
import shutil
import sys
import json
from io import StringIO

# modules from external libraries
from jinja2 import Template
from sh import openssl
from lib.base import SUCCESS, FAILED, AutomationError, DEPLOY_JSON
from lib.gitlabproject import GitlabProject
from lib.git import Git
from lib.logger import logger


def copy_build_directory(git_repo):
    """
    Copies the build directory to the working copy directory

    it also takes care of populating the deploy.json file
    """
    src = os.path.join('templates', 'build')
    dst = os.path.join(git_repo.working_copy, 'build')
    try:
        if os.path.exists(dst):
            if os.path.isfile(dst):
                msg = 'file named "build" already exists in the repository'
                raise AutomationError(msg)
            else:
                shutil.rmtree(dst)
        shutil.copytree(src, dst)
        logger.info('{0} build/ directory copied'.format(SUCCESS))
    except shutil.Error as error:
        msg = ('{0} cannot copy {1} to {2}, '
               'with error: {3}'.format(FAILED, src, dst, error))
        raise AutomationError(msg)
    git_repo.add('build')


def create_gitlab_ci_template(project, git_repo):
    """
    Created the gitlab ci template file
    """
    src_file = os.path.join('templates', 'gitlab-ci.yml.j2')
    dst_file = os.path.join(git_repo.working_copy, '.gitlab-ci.yml')
    with open(src_file, 'r') as f_in:
        template = f_in.read()
    template = Template(template)
    template.filename = src_file
    with open(dst_file, 'w') as f_out:
        f_out.write(template.render(project=project.path))
    logger.info('{0} create .gitlab-ci.yml from template'.format(SUCCESS))
    git_repo.add(dst_file)


def create_deploy_json(project, git_repo):
    """
    Created the gitlab ci template file
    """
    src_file = os.path.join('templates', DEPLOY_JSON)
    dst_file = os.path.join(git_repo.working_copy, DEPLOY_JSON)
    with open(src_file, 'r') as f_in:
        template = f_in.read()
    template = Template(template)
    template.filename = src_file
    with open(dst_file, 'w') as f_out:
        f_out.write(template.render(project=project.path()))
    logger.info('{0} create deploy.json from template'.format(SUCCESS))
    git_repo.add(dst_file)


def set_variables(project, git_repo):
    variables = {}
    deploy_json = os.path.join(git_repo.working_copy, DEPLOY_JSON)
    try:
        with open(deploy_json, 'r') as json_in:
            config = json.load(json_in)
        # TODO: import config from lib/config.py (when ready)
        for env in config:
            for item in config[env]:
                if item.endswith('_password'):
                    variables[config[env][item]] = create_random_password()

        for key in variables:
            project.set_variable(key, variables[key])

    except ValueError as error:
        msg = ('{0} decoing json file: {1}, '
               'error: {2}'.format(FAILED, deploy_json, error))
        raise AutomationError(msg)


def parse_cli():
    """
    gets the parameters from the command line
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-url', '-p', required=True,
                        help='url of the cms project to automate')
    parser.add_argument('--jira-issue', '-j', required=True,
                        help='jira issue')
    return parser.parse_args()


def create_random_password():
    buf = StringIO()
    openssl('rand', '-base64', '32', _out=buf)
    return buf.getvalue().partition('=')[0].strip()


def main():
    args = parse_cli()
    url = args.project_url
    issue = args.jira_issue
    # we work on a branch named after the jira issue
    # the next varaible is useless but it makes code more readable
    branch = issue
    try:
        # git operations
        project = GitlabProject(url)
        local_repo = Git(project.ssh_url())
        local_repo.clone()
        local_repo.switch_to_branch(issue)
        copy_build_directory(local_repo)
        create_gitlab_ci_template(project, local_repo)
        create_deploy_json(project, local_repo)
        # commit_msg
        commit_msg = "{0}: pipeline automation".format(issue)
        local_repo.commit(commit_msg)
        local_repo.push(remote='origin', branch=branch)
        # new files have been uploaded, now tell
        # gitlab we want build enabled so we can set variables
        project.enable_builds()
        set_variables(project, local_repo)
        merge_req_title = '{0}: pipeline automation'.format(issue)
        project.merge_request(source_branch=branch, title=merge_req_title)
        local_repo.destroy()
    # create pull request
    except AutomationError as error:
        logger.info(error)
        local_repo.destroy()
        logger.info('{0} to complete gitlab automation'.format(FAILED))
        sys.exit(1)


if __name__ == '__main__':
    main()
