"""
Guess what? I manage the ansible automation
"""
from __future__ import print_function
from __future__ import absolute_import

import argparse
import sys

from lib.ansible import AnsibleAutomation
from lib.base import FAILED, AutomationError
from lib.logger import logger


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


def main():
    args = parse_cli()
    url = args.project_url
    jira_issue = args.jira_issue
    # we work on a branch named after the jira issue
    # the next varaible is useless but it makes code more readable
    print(jira_issue)
    try:
        # git operations
        ansible = AnsibleAutomation(project_url=url)
        ansible.clone(branch=jira_issue)
        ansible.copy_ansible_files()
        ansible.commit()
        ansible.push()
        ansible.merge_request()
        ansible.cleanup()
    # create pull request
    except AutomationError as error:
        logger.info(error)
        ansible.cleanup()
        logger.info('{0} to complete gitlab automation'.format(FAILED))
        sys.exit(1)


if __name__ == '__main__':
    main()
