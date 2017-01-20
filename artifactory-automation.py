#!/usr/bin/env python

from __future__ import absolute_import

import sys
import argparse

from lib.base import AutomationError
from lib.artifactory import Artifactory
from lib.logger import logger
from lib.gitlabproject import GitlabProject
from lib.config import ArtifactoryConfig


def parse_cli():
    """
    gets the parameters from the command line
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-url', '-p', required=True,
                        help='url of the cms project to automate')
    return parser.parse_args()


def main():
    args = parse_cli()
    project_url = args.project_url
    try:
        project = GitlabProject(project_url)
        repository = project.path()
        deploy_json = project.deploy_json(branch=None)
        artifactory_config = ArtifactoryConfig(deploy_json)
        username = artifactory_config.username()
        password = artifactory_config.password()
        # congratulation we just got the name of the variable in which gitlab
        # stores the artifactory password, let's ask gitlab for its real value
        password = project.get_variable(password).value
        for artifactory_url in artifactory_config.instances():
            artifactory = Artifactory(artifactory_url)
            artifactory.create_repository(repository)
            artifactory.create_or_replace_user(username, password)
            artifactory.grant_permission(repository=repository,
                                         username=username,
                                         permissions='w')
    except AutomationError as error:
        logger.error(error)
        sys.exit(1)

if __name__ == '__main__':
    main()
