'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import json
import re
import utils
import argparse
import mimetypes

from urllib import quote
from urllib2 import urlopen, Request, quote
from os.path import join

def create_request(path, data=None, method='GET'):
    org = 'SAP'
    repository = 'SapMachine'
    github_api = str.format('https://api.github.com/repos/{0}/{1}', org, repository)
    request_url = str.format('{0}/{1}', github_api, path)
    token = utils.get_github_api_accesstoken()

    if token is None:
        raise Exception('no GitHub API access token specified')

    request = Request(request_url, data=data)
    request.get_method = lambda: method
    request.add_header('Authorization', str.format('token {0}', token))
    return request


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine tag', metavar='MAJOR', required=True)
    parser.add_argument('-d', '--description', help='the description of the release', required=False)
    parser.add_argument('-p', '--prerelease', help='this is a pre-release', action='store_true', default=False)
    parser.add_argument('-a', '--asset', help='the asset to upload', metavar='ASSET', required=False)
    args = parser.parse_args()

    tag = args.tag
    prerelease = args.prerelease
    asset_file = args.asset
    description = '' if args.description is None else args.description

    if asset_file is not None:
        asset_file = os.path.realpath(asset_file)
        asset_name = os.path.basename(asset_file)
        asset_mime_type = mimetypes.guess_type(asset_file)

        if asset_mime_type is None:
            asset_mime_type = 'application/octet-stream'
            print(str.format('could not detect mime-type: falling back to "{0}"', asset_mime_type))
        else:
            asset_mime_type = asset_mime_type[0]
            print(str.format('detected mime-type "{0}"', asset_mime_type))

    request = create_request('releases')
    response = json.loads(urlopen(request).read())

    release_id = None
    upload_url = None

    for release in response:
        if release['tag_name'] == tag:
            release_id = release['id']
            upload_url = release['upload_url']
            break

    if release_id is None:
        data = json.dumps({ "tag_name": tag, "name": tag, "body": description, "draft": False, "prerelease": prerelease })
        request = create_request('', data=data, method='POST')
        request.add_header('Content-Type', 'application/json')
        response = json.loads(urlopen(request).read())
        release_id = response['id']
        upload_url = response['upload_url']
        print(str.format('created release "{0}"', tag))

    if asset_file is not None:
        request = create_request(str.format('releases/{0}/assets', release_id))
        response = json.loads(urlopen(request).read())

        for asset in response:
            if asset['name'] == asset_name:
                print(str.format('deleting already existing asset "{0}" ...', asset_name))
                asset_id = asset['id']
                request = create_request(str.format('releases/assets/{0}', asset_id), method='DELETE')
                urlopen(request).read()
                break

        upload_url = str(upload_url.split('{', 1)[0] + '?name=' + quote(asset_name))

        with open(asset_file, 'rb') as asset_file:
            asset_data = asset_file.read()
            asset_length = len(asset_data)

        retry = 2

        while retry > 0:
            try:
                request = Request(upload_url, data=asset_data)
                request.add_header('Authorization', str.format('token {0}', utils.get_github_api_accesstoken()))
                request.add_header('Content-Type', asset_mime_type)
                request.add_header('Content-Length', str(asset_length))
                print(str.format('uploading asset "{0}" with a length of {1} bytes ...', asset_name, str(asset_length)))
                response = json.loads(urlopen(request).read())
                break
            except IOError:
                _type, value, _traceback = sys.exc_info()
                print(str.format('Error uploading asset "{0}": {1}', asset_name, value.strerror))
                retry -= 1

if __name__ == "__main__":
    sys.exit(main())
