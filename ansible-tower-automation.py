#!/usr/bin/env python

from __future__ import absolute_import

import sys
import argparse

from lib.base import AutomationError
from lib.config import TowerConfig
from lib.gitlabproject import GitlabProject
from lib.logger import logger
from lib.tower import AnsibleTower


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
        tower_config = TowerConfig(deploy_json)
        msgreen = tower_config['mic-tst-itass01.msgreen.dom']
        print(msgreen)
        # congratulation we just got the name of the variable in which gitlab
        # stores the artifactory password, let's ask gitlab for its real value
    except AutomationError as error:
        logger.error(error)
        sys.exit(1)

if __name__ == '__main__':
    main()
