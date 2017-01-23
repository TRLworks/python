"""
This module provides basic utilities
"""

from __future__ import print_function
from __future__ import absolute_import
import hashlib
import json
import os
import tarfile
from .error import PipelineError

# some constants...
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
# colors
INFO = '\033[94m[INFO]  \033[0m'
SUCCESS = '\033[92m[OK]    \033[0m'
FAILED = '\033[91m[FAILED]\033[0m'

# default configuration file
DEFAULT_CONFIG_FILE = os.path.join(CURRENT_DIR, 'deploy.json')


def artifactory_urls(project):
    """
    Reads the configuration from deploy.json and return the artifactory
    instances urls
    for more information about the package names, please refer to the
    README.md file in this project.
    """
    config = read_coniguration(DEFAULT_CONFIG_FILE, 'artifactory')
    for artifactory in config['artifactory_instances']:
        yield "{0}/{1}/{2}".format(artifactory, project, _archive_name())


def _version():
    return "{0}.{1}".format(gitlab_var('VERSION', default='999'),
                            gitlab_var('CI_PIPELINE_ID', default='999'))


def _package_name():
    package = gitlab_var('CI_PROJECT_NAME', default='just_a_test')
    return "{0}-{1}".format(package, _version())


def _archive_name():
    return os.path.join('{0}.tar.gz'.format(_package_name()))


def _archive_path():
    return os.path.join(project_dir(), _archive_name())


def _archive_exclude(filename):
    config = read_coniguration(DEFAULT_CONFIG_FILE, 'artifactory')
    archive_exclude_directories = config['archive_exclude_directories']
    archive_exclude_extensions = config['archive_exclude_extensions']
    if filename.name.endswith('robots.txt'):
        return filename
    if os.path.split(filename.name)[1] in archive_exclude_directories:
        return None
    if filename.name.endswith(archive_exclude_extensions):
        return None
    return filename


def read_coniguration(config_file, environment):
    """
    reads the deployment configuration for a given environment

    Args:
        environment (str): environment about to be deployed

    Returns:
        (dict): deployment configuration for a given environment

    Raises:
        PipelineError
    """
    try:
        with open(config_file, 'r') as json_in:
            deploy_config = json.load(json_in)
        return deploy_config[environment]
    except IOError as error:
        msg = 'cannot read configuration file: {0}'.format(error)
        raise PipelineError(msg)
    except KeyError:
        msg = ('{0} provided environment name, {1}, does in the specified '
               'configuation file: {2}' .format(FAILED,
                                                environment, config_file))
        raise PipelineError(msg)


def read_json_configuration(json_file):
    """
    Reads a json file and returns a dictionary of its content

    Args:
        json_file (str): path to the json file

    Returns:
        dict: content of json file

    Raises:
        PipelineError
    """
    try:
        with open(json_file, 'r') as json_in:
            return json.load(json_in)
    except IOError as error:
        msg = 'cannot read configuration file: {0}'.format(error)
        raise PipelineError(msg)


def project_dir():
    """
    Returns the location of the project main directory, it is set by gitlab but
    in case we are running this locally we need to define it in other ways
    (hint is two directories up from this file)
    """
    if 'CI_PROJECT_DIR' in os.environ:
        return os.environ['CI_PROJECT_DIR']
    else:
        # trying to make it readable...
        build_dir = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
        return os.path.abspath(os.path.join(build_dir, os.pardir))


def deployment_conf_dir():
    """
    Returns the deployment configuration directory: deploy/
    """
    return os.path.join(project_dir(), 'deploy')


def gitlab_var(var_name, default):
    """

    Args:
        var_name (str): name of the variable

    Returns:
        (str): value of the variable
    """
    if var_name in os.environ:
        return os.environ[var_name]
    return default


def md5(filename, blocksize=65536):
    """
    calculate md5 hash on filename

    Args:
            filename (str):

    Returns:
            (str) md5 hash of the file
    """
    hash_ = hashlib.md5()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(blocksize), b''):
            hash_.update(block)
    return hash_.hexdigest()


def sha1(filename, blocksize=65536):
    """
    calculate sha1 hash on filename

    Args:
            filename (str):

    Returns:
            (str) sha1 hash of the file
    """
    hash_ = hashlib.sha1()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(blocksize), b''):
            hash_.update(block)
    return hash_.hexdigest()


def create_archive(archive_name=None, base_dir=None, filter_fn=_archive_exclude):
    """
    create a tar.gz archive from base_dir excluding items
    provided in exclude

    Args:
        archive_name (str): name of the archive to create

        base_dir (str): name of the directory to compress

        exclude (list, tuple): elements to exclude from the archive

    Raises:
        PipelineError
    """

    if not archive_name:
        archive_name = _archive_path()
    if not base_dir:
        base_dir = '.'

    if os.path.exists(archive_name):
        os.remove(archive_name)

    tar = tarfile.open(archive_name, "w:gz")
    tar.add(base_dir, filter=filter_fn)
    tar.close()
    return archive_name
