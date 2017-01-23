#!/usr/bin/env python
"""
This module binds GitLab deployments and Ansible Tower jobs
"""

from __future__ import print_function
from __future__ import absolute_import
import os
import subprocess
from .error import PipelineError
from .utils import gitlab_var, project_dir, SUCCESS, FAILED
from .utils import read_json_configuration


TEST_CONFIGURATION = 'build/tests.json'
TEST_RESULT_PHP = 'phpcs-php-results.txt'
TEST_RESULT_CSS = 'phpcs-css-results.txt'
TEST_RESULT_JS = 'phpcs-js-results.txt'


def deployment_conf_dir():
    """
    Returns the deployment configuration directory: deploy/
    """
    return os.path.join(project_dir(), 'deploy')


def deployment_conf_file():
    """
    Returns the deployment configuration file: deploy/tc.config
    """
    return os.path.join(deployment_conf_dir(), 'tc.config')


def context():
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
        msg = 'Please check your configuration/GitLab keys: {0}'.format(error)
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


def default_image_name(environment=None):
    """
    Returns the docker image name to use, it creates different names if the
    deployment runs from Gitlab or localy (for testing)

    Args:
        envionment (str): name of the environment (can be None)

    Returns:
        str
    """
    project = 'local'
    stage = 'local-test'
    if 'CI_PROJECT_NAME' in os.environ:
        project = os.environ['CI_PROJECT_NAME']
    if 'CI_BUILD_STAGE' in os.environ:
        stage = os.environ['CI_BUILD_STAGE']
    if environment:
        return "experimental-{0}-{1}-{2}".format(project, stage, environment)
    else:
        return "experimental-{0}-{1}".format(project, stage)


def default_docker_file():
    """
    Returns the default Dockerfile name (<project_dir>/Dockerfile.<stage>)
    """
    docker_file = gitlab_var('DOCKERFILE', default=None)
    if docker_file is None:
        raise PipelineError('DOCKERFILE is not defined in your environment')
    return os.path.join(project_dir(), docker_file)


def create_image(image_name=None, docker_file=None):
    """
    Create a docker image (docker build).

    Args:
        image_name (str): image needed by the deployment process

    Raisese:
        PipelineError
    """
    if not image_name:
        image_name = default_image_name(environment=None)
    if not docker_file:
        docker_file = default_docker_file()
    cmd = (docker_executable(),
           'build',
           '-f', docker_file,
           '-t', image_name,
           '.')

    # docker_build = subprocess.Popen(cmd, cwd=project_dir(), stdout=subprocess.PIPE)
    docker_build = subprocess.Popen(cmd, cwd=project_dir())

    print('building docker image: {0}'.format(image_name))
    docker_build.wait()
    if docker_build.returncode != 0:
        msg = 'Failed to required docker image: {0}'.format(" ".join(cmd))
        raise PipelineError(msg)


def _base_test_cmd():
    """
    Basic phpcs test command
    """
    cmd = [docker_executable(),
           'run', '--security-opt', 'label:type:unconfined_t',
           '-u', '{0}:{1}'.format(os.getuid(), os.getuid()),
           '-v', '{0}:/opt/tests/project'.format(project_dir()),
           default_image_name(),
           'phpcs',
           '--report=summary',
           '--report-width=160']

    test_configuration = read_json_configuration(TEST_CONFIGURATION)
    for item in test_configuration['directories_to_test']:
        cmd.append(item)

    return cmd


def _php_test_command():
    """
    phpcs test command
    """
    cmd = _base_test_cmd()
    cmd.append('--extensions=php,module,inc,install,test,profile,theme')
    return cmd


def _css_test_command():
    """
    php css test command
    """
    cmd = _base_test_cmd()
    cmd.append('--extensions=css')
    return cmd


def _js_test_command():
    """
    phpjs javascript test command
    """
    cmd = _base_test_cmd()
    cmd.append('--extensions=js')
    return cmd


def execute_tests():
    """
    I execute php tests!
    """

    php_out = open(TEST_RESULT_PHP, 'w')
    css_out = open(TEST_RESULT_CSS, 'w')
    js_out = open(TEST_RESULT_JS, 'w')

    # start all the process
    php = subprocess.Popen(_php_test_command(), stdout=php_out)
    css = subprocess.Popen(_css_test_command(), stdout=css_out)
    js = subprocess.Popen(_js_test_command(), stdout=js_out)
    print('started phpcs - php tests')
    print('started phpcs - css tests')
    print('started phpcs - js tests')

    # wait for processes to complete
    php.wait()
    css.wait()
    js.wait()

    # write to file
    php_out.flush()
    css_out.flush()
    js_out.flush()

    # close output file
    php_out.close()
    css_out.close()
    js_out.close()

    print("{0} php tests".format(SUCCESS if php.returncode == 0 else FAILED))
    print("{0} css tests".format(SUCCESS if css.returncode == 0 else FAILED))
    print("{0} js tests".format(SUCCESS if js.returncode == 0 else FAILED))


def package():
    """
    This function executes the compose in a docker container
    """
    cmd = (docker_executable(),
           'run', '--security-opt', 'label:type:unconfined_t',
           '-u', '{0}:{1}'.format(os.getuid(), os.getuid()),
           '-v', '{0}:/app'.format(project_dir()),
           default_image_name())
    pkg = subprocess.Popen(cmd)
    pkg.wait()
    if pkg.returncode != 0:
        raise PipelineError("Packaging has failed!")
