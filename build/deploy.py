#!/usr/bin/env python
"""
This module binds GitLab deployments and Ansible Tower jobs
"""

from __future__ import print_function
from __future__ import absolute_import
import argparse
import os
import subprocess
import sys
import lib.kerberos as kerberos
from lib.utils import FAILED, read_coniguration
from lib.utils import deployment_conf_dir, project_dir
from lib.error import PipelineError


# some constants...
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_CONFIG_FILE = os.path.join(CURRENT_DIR, 'deploy.json')


def deployment_conf_file():
    """
    Returns the deployment configuration file: deploy/tc.config
    """
    return os.path.join(deployment_conf_dir(), 'tc.config')


def dockerfile_path(config):
    """
    Returns the path to the dockerfile we are using in this stage
    (defined in deploy.json)
    """
    # was: DOCKER_FILE = os.path.join(CURRENT_DIR, 'Dockerfile.deploy')
    return config['dockerfile']


def docker_context():
    """
    Returns the directory that contains the Dockerfile for deployments
    """
    return os.path.join(os.path.dirname(__file__))


def create_docker_configuration(config):
    """
    Creates the docker configuration file, we will use it to point to the right
    ansible tower instance.

    Args:
        config (dict): environment configuraiton

    Raises:
        PipelineError
    """
    # create the deployment configuration directory
    if not os.path.exists(deployment_conf_dir()):
        os.makedirs(deployment_conf_dir())

    try:
        host = config['ansible_tower_instance']
        username = os.environ[config['username']]
        password = os.environ[config['password']]
    except KeyError as error:
        msg = ("{0} Configuration error! Please check your GitLab "
               "variables: {1}".format(FAILED, error))
        raise PipelineError(msg)

    # now generate the configuration file
    conf = ["[general]",
            "host: {0}".format(host),
            "username: {0}".format(username),
            "password: {0}".format(password),
            "verify_ssl: false",
            "reckless_mode: true"]

    # write the file...
    with open(deployment_conf_file(), 'w') as conf_file:
        conf_file.write("\n".join(conf))


def docker_executable():
    """
    returns the full path to the docker executable.
    Sorry windows users, this is the only reason you cannot exeucte this job:
    getting the full path of the docker executable will make this function way
    uglier than it looks now.
    """
    for path in os.environ['PATH'].split(':'):
        docker_path = os.path.join(path, 'docker')
        if os.path.exists(docker_path):
            return docker_path


def docker_image_name(environment):
    """
    Returns the docker image name to use, it creates different names if the
    deployment runs from Gitlab or localy (for testing)

    Args:
        envionment (str): name of the environment

    Returns:
        str
    """
    project = 'local'
    if 'CI_PROJECT_NAME' in os.environ:
        project = os.environ['CI_PROJECT_NAME']
    return "{0}-deploy-{1}".format(project, environment)


def create_docker_image(image_name, dockerfile):
    """
    Create a docker image (docker build).

    Args:
        image_name (str): image needed by the deployment process

    Raisese:
        PipelineError
    """
    cmd = (docker_executable(),
           'build',
           '-f', dockerfile,
           '-t', image_name,
           '.')

    docker_build = subprocess.Popen(cmd, cwd=project_dir())
    docker_build.wait()
    if docker_build.returncode != 0:
        msg = 'Failed to required docker image: {0}'.format(" ".join(cmd))
        raise PipelineError(msg)


def excecute_deployment(config, image_name, version):
    """
    Execute the deployment using tower companion, to run a deployment we need:
        1. environment configuration (to get the environment name)
        2. image name, docker needs an image name
        3. version, we need a version to deploy, right?

    Args:
        config (dict): environment configuration
        image_name (str): name of the docker image to use
        version (str): version about to be deployed

    Raises:
        PipelineError
    """
    cmd = ['docker', 'run', '--security-opt', 'label:type:unconfined_t',
           '-u', '{0}:{1}'.format(os.getuid(), os.getuid()),
           '-v', '{0}:/deploy'.format(deployment_conf_dir()),
           image_name,
           'python', '-u', '/usr/local/bin/kick_and_monitor',
           '--template-name', '{0}'.format(config['job_name']),
           '--extra-vars', 'version: {0}'.format(version)]

    if "GITLAB_USER_EMAIL" in os.environ:
        cmd.append('--extra-vars')
        cmd.append('gitlab_user_email: {0}'.format(
            os.environ['GITLAB_USER_EMAIL']))
    # this line kicks off the deployment
    deployment = subprocess.Popen(cmd)
    # let's wait for the deployment to complete
    deployment.wait()
    # no matter what, delete the configuration file
    os.remove(deployment_conf_file())
    if deployment.returncode != 0:
        msg = 'Failed to execute requested deployment: {0}'.format(" ".join(cmd))
        raise PipelineError(msg)


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


def deploy(config_file, environment, version):
    """
    The only function you want to call from main(). A nice cozy wrapper for the
    deployment operations, nothing more, nothing less.

    Args:
        config_file (str): path to the configuration file
        environment (str): the environment you're about to deploy

    Raises:
        PipelineError: something when wrong during this deployment, please
            file a bug
    """
    config = read_coniguration(config_file=config_file, environment=environment)
    kerberos.check(config)
    image_name = docker_image_name(environment)
    create_docker_configuration(config)
    dockerfile = dockerfile_path(config)
    create_docker_image(image_name, dockerfile)
    excecute_deployment(config, image_name, version)


def main():
    """
    I am main(), I do deployments for you.
    """
    parser = argparse.ArgumentParser("cms deployment script")
    parser.add_argument('--environment', '-e', help='environment to deploy',
                        required=True)
    parser.add_argument('--version', '-v',
                        help='which version do you want to deploy?',
                        required=True)
    parser.add_argument('--config-file', '-c',
                        help='configuration file, defaults to: {0}'.format(
                            DEFAULT_CONFIG_FILE),
                        default=DEFAULT_CONFIG_FILE,
                        required=False)
    args = parser.parse_args()
    try:
        deploy(config_file=args.config_file,
               environment=args.environment,
               version=args.version)
    except PipelineError as error:
        print("{0} deployment stage failed".format(FAILED))
        print(error)
        sys.exit(1)

if __name__ == '__main__':
    main()
