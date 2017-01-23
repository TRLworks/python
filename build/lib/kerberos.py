#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Κέρβερος is the guardian of deployments

Κέρβερος decides if your deployment can be applied to the next environment
based on the prerequisite variable in .gitlab-ci.yml and authorizations set in
the deploy.json file

Κέρβερος it's a strange name but it also ensures we're using utf-8 encoding

Κέρβερος, has a weird tendency of speaking about iteslf in 3rd person.
"""
from __future__ import print_function
from __future__ import absolute_import

import logging
import os
import requests
from lib.utils import SUCCESS, FAILED, INFO
from lib.error import PipelineError

# how many results for page?
RESULTS_PER_PAGE = 40
# requests is printing out annoying ssl-warnings
# https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
# this line disables them
logging.captureWarnings(True)


# we need to iterate through the deployment pages following this order:
# 1. page 0
# 2. last page
# 3. last page - 1
# and so on until we get to page 1
class Pages(object):
    """
    Manage API pagination
    """
    def __init__(self):
        self.last = 0

    def __iter__(self):
        return self

    def next(self):
        """
        next page
        """
        self.last = self.last - 1
        if self.last < 1:
            raise StopIteration
        return self.last


def api_url():
    """
    gitlab API url

    Returns:
        (str): gitlab API url
    """
    return "https://gitlab.ph.esl-asia.com/api/v3/"


def deployments_url():
    """
    API deployments endpoint for current project

    Returns:
        (str): API deployments endpoint
    """
    return "{0}/projects/{1}/deployments".format(api_url(), project_id())


def pipeline_url():
    """
    current pipeline data from API

    Returns:
        (str): current pipeline data from API
    """
    return "{0}/projects/{1}/pipelines/{2}".format(api_url(), project_id(),
                                                   pipeline_id())


def project_id():
    """
    returns current project ID as set in the environment variables

    Returns:
        (int): project ID

    Raises:
        KeyError
    """
    return int(os.environ['CI_PROJECT_ID'])


def pipeline_id():
    """
    returns current pipeline ID as set in the environment variables

    Returns:
        (int): pipline ID

    Raises:
        KeyError
    """
    return int(os.environ['CI_PIPELINE_ID'])


def api_token():
    """
    returns current api token as set in the environment variables

    Returns:
        (str): api token

    Raises:
        KeyError
    """
    return os.environ['PRIVATE_TOKEN']


def prerequisite(config):
    """
    returns the name of the prerequistite for this step
    (must be defined as variable in .gitlab-ci.yml)

    Returns:
        (str): api token

    Raises:
        KeyError
    """
    return config['prerequisite']


def meets_requirements(requirement):
    """
    Checks if current deployment statisfies requirements

    Returns:
        (bool) checks if requested deployment can be performed
    """
    # step 1.
    # get page 0, this will tell us how many pages in total there are
    # the number of pages depends on `per_page` size so don't the value of
    # RESULTS_PER_PAGE during the run
    url = deployments_url()
    headers = {"PRIVATE-TOKEN": api_token()}
    params = {'per_page': RESULTS_PER_PAGE, 'page': 0}
    res = requests.get(url, headers=headers, verify=False, params=params)
    # if we're lucky the result is already in the first page, but...
    if is_deployable(res.json(), requirement):
        return True

    # in case it's not, we need to iterate to the deployment results starting
    # from the last page, our custom class, Pages will do this for us
    pages = Pages()
    pages.last = int(res.headers['X-Total-Pages']) + 1
    for page in pages:
        params = {'per_page': RESULTS_PER_PAGE, 'page': page}
        res = requests.get(url, headers=headers, verify=False, params=params)
        if is_deployable(res.json(), requirement):
            return True
    return False


def is_deployable(deployments, requirement):
    """
    Parses deployments and returns true if we can proceed with the deployment

    Args:
        deployments (dict): json as returned from the api call

    Returns:
        bool
    """
    pipeline = pipeline_id()
    for deployment in deployments:
        current_pipeline = int(deployment['deployable']['pipeline']['id'])
        state = deployment['deployable']['status']
        name = deployment['deployable']['name']

        if current_pipeline == pipeline:
            if name == requirement and state == 'success':
                return True
    return False


def current_user_email():
    """
    Returns the current user email (lower case)
    """
    return os.environ['GITLAB_USER_EMAIL'].lower()


def authorized_users(config):
    """
    Returns a tuple of the authorized users for this step
    (as defined in deploy.json)
    """
    return (user.lower() for user in config['authorized_users'])


def authorized(config):
    valid_users = authorized_users(config)
    if "any" in valid_users:
        msg = ("{0} Κέρβερος says: this steps can be performed by "
               "anyone, be ready for the next quest".format(SUCCESS))
        print(msg)
        return True

    user = current_user_email()
    if user not in authorized_users(config):
        msg = ("{0} Κέρβερος says: you're not authorized to trigger "
               "this step".format(FAILED, user))
        raise PipelineError(msg)

    msg = ("{0} Κέρβερος says: you're authorized to trigger "
           "this step, be ready for the next quest".format(SUCCESS, user))
    print(msg)


def pre_requirements(config):
    prereq = prerequisite(config)
    if prereq == 'any':
        msg = ("{0}  Κέρβερος this step do not depend on any previous "
               "stage".format(SUCCESS))
        print(msg)
        return True
    if not meets_requirements(prereq):
        msg = ("{0} Κέρβερος does not allow you to proceed any further "
               "requirements are not met: {1} "
               "did not complete successfully".format(FAILED, prereq))
        raise PipelineError(msg)
    msg = ("{0} Κέρβερος says: all the requirements are met, let's "
           "start".format(SUCCESS))
    print(msg)
    return True


def check(config):
    # no blockers for this environment
    print('{0} Κέρβερος sniffs'.format(INFO))
    authorized(config)
    pre_requirements(config)
