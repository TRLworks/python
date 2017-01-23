#!/usr/bin/env python

from __future__ import print_function
from __future__ import absolute_import

import os
import lib.artifactory as artifactory
import lib.docker as docker
from lib.utils import gitlab_var, create_archive, read_coniguration
from lib.utils import artifactory_urls, DEFAULT_CONFIG_FILE


def main():
    print('creating docker image')
    docker.create_image()
    print('generating final package using docker')
    docker.package()
    print('creating archive')
    archive = create_archive()
    archive = os.path.basename(archive)
    print('uploading archive {0}'.format(archive))
    config = read_coniguration(DEFAULT_CONFIG_FILE, 'artifactory')
    username = config['username']
    # deploy.json contains the NAME of the variable
    # the actual password is stored within gitlab variables
    password = config['password']
    password = gitlab_var(password, default='Not defined')
    for url in artifactory_urls():
        artifactory.upload(url=url,
                           username=username,
                           password=password,
                           file_to_upload=archive)


if __name__ == '__main__':
    main()
