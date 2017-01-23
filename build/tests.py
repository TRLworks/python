#!/usr/bin/env python

from __future__ import print_function
from __future__ import absolute_import
import sys
import lib.docker as docker
from lib.utils import SUCCESS, FAILED
from lib.error import PipelineError


def main():
    docker.create_image()
    docker.execute_tests()


if __name__ == '__main__':
    try:
        main()
        print("{0} test completed".format(SUCCESS))
    except PipelineError as error:
        print("{0} to run tests".format(FAILED))
        print(error)
        sys.exit(1)
