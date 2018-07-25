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

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine tag', metavar='MAJOR', required=True)
    parser.add_argument('-d', '--description', help='the description of the release', required=False)
    parser.add_argument('-p', '--prerelease', help='this is a pre-release', action='store_true', default=False)
    parser.add_argument('-a', '--asset', help='the asset to upload', metavar='ASSET', required=False)
    args = parser.parse_args()

    tag = args.tag
    prerelease = args.prerelease
    asset = args.asset
    description = '' if args.description is None else args.description

    if asset is not None:
        asset = os.path.realpath(asset)
        asset_name = os.path.basename(asset)
        asset_mime_type = mimetypes.guess_type(asset)

        if asset_mime_type is None:
            asset_mime_type = 'application/octet-stream'
            print(str.format('could not detect mime-type: falling back to "{0}"', asset_mime_type))
        else:
            asset_mime_type = asset_mime_type[0]
            print(str.format('detected mime-type "{0}"', asset_mime_type))

    token = utils.get_github_api_accesstoken()

    if token is None:
        raise Exception('no GitHub API access token specified')

    org = 'SAP'
    repository = 'SapMachine'
    github_api = str.format('https://api.github.com/repos/{0}/{1}/releases', org, repository)
    asset_pattern = re.compile(utils.sapmachine_asset_pattern())
    request = Request(github_api)
    request.add_header('Authorization', str.format('token {0}', token))

    release_id = None
    assets_url = None
    upload_url = None

    response = json.loads(urlopen(request).read())
    for release in response:
        if release['tag_name'] == tag:
            release_id = release['id']
            assets_url = release['assets_url']
            upload_url = release['upload_url']
            break

    if release_id is None:
        data = json.dumps({ "tag_name": tag, "name": tag, "body": description, "draft": False, "prerelease": prerelease })
        request = Request(github_api, data=data)
        request.add_header('Authorization', str.format('token {0}', token))
        request.add_header('Content-Type', 'application/json')
        response = json.loads(urlopen(request).read())
        release_id = response['id']
        assets_url = response['assets_url']
        upload_url = response['upload_url']
        print(str.format('created release "{0}"', tag))

    if asset is not None:
        upload_url = str(upload_url.split('{', 1)[0] + '?name=' + quote(asset_name))

        with open(asset, 'rb') as asset_file:
            request = Request(upload_url, data=asset_file.read())

        request.add_header('Authorization', str.format('token {0}', token))
        request.add_header('Content-Type', asset_mime_type)
        print(str.format('uploading asset "{0}" ...', asset_name))
        response = json.loads(urlopen(request).read())

if __name__ == "__main__":
    sys.exit(main())
