"""
Artifatory module
"""

from __future__ import print_function
from __future__ import absolute_import
import os
from mimetypes import MimeTypes
try:
    from urlparse import urlparse
except ImportError:
    # python 3
    from urllib.parse import urlparse
import requests
from .utils import SUCCESS, FAILED, md5, sha1
from .error import PipelineError


def upload(url, username, password, file_to_upload):
    """
    Uploads a given file to url.

    Args:
        url (str): destination url

        username (str): upload user

        password (str): upload password

        file_to_upload (str): path to the file to upload
    """
    md5_ = md5(file_to_upload)
    sha1_ = sha1(file_to_upload)
    short_url = urlparse(url).netloc
    mimetype = MimeTypes()
    file_len = str(os.path.getsize(file_to_upload))
    headers = {"Content-Type": mimetype.guess_type(file_to_upload)[0],
               "Content-Length": file_len,
               "X-Checksum-Md5": md5_,
               "X-Checksum-Sha1": sha1_}

    with open(file_to_upload, 'rb') as upload_me:
        try:
            response = requests.put(url, auth=(username, password),
                                    headers=headers, data=upload_me)
            if response.status_code != 201:
                print('{0} {1}'.format(FAILED, url))
            else:
                print('{0} {1}'.format(SUCCESS, url))
        except requests.ConnectionError as error:
            print('{0} to upload {1} to {2}'.format(FAILED, file_to_upload, short_url))
            print('       please check: {0}'.format(url))
            print('       error: {0}'.format(error))
            raise PipelineError('upload step failed')
