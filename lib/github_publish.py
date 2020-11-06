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

from urllib.parse import quote
from urllib.error import URLError
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
    asset_file = args.asset
    description = '' if args.description is None else args.description

    if asset_file is not None:
        asset_file = os.path.realpath(asset_file)
        asset_name = os.path.basename(asset_file)
        asset_mime_type = mimetypes.guess_type(asset_file)

        if asset_mime_type is None or asset_mime_type[0] is None:
            asset_mime_type = 'application/octet-stream'
            print(str.format('could not detect mime-type: falling back to "{0}"', asset_mime_type))
        else:
            if asset_mime_type[0] == "application/x-redhat-package-manager":
              asset_mime_type = 'application/octet-stream'
              print(str.format('using mime-type "{0}" instead of detected pplication/x-redhat-package-manager', asset_mime_type))
            else:
              asset_mime_type = asset_mime_type[0]
              print(str.format('detected mime-type "{0}"', asset_mime_type))

    releases = utils.get_github_releases()

    release_id = None
    upload_url = None

    for release in releases:
        if release['tag_name'] == tag:
            release_id = release['id']
            upload_url = release['upload_url']
            break

    if release_id is None:
        '''
        release does not exist yet -> create it
        '''
        data = json.dumps({ "tag_name": tag, "name": tag, "body": description, "draft": False, "prerelease": prerelease })
        response = utils.github_api_request('releases', data=data, method='POST', content_type='application/json')
        release_id = response['id']
        upload_url = response['upload_url']
        print(str.format('created release "{0}"', tag))

    if asset_file is not None:
        '''
        asset file is specified (-a)
        first check wether the asset already exists
        '''
        assets = utils.github_api_request(str.format('releases/{0}/assets', release_id), per_page=50)

        for asset in assets:
            if asset['name'] == asset_name:
                '''
                asset already exists -> skip
                '''
                print(str.format('error: asset "{0}" already exists ...', asset_name))
                return 1

        upload_url = str(upload_url.split('{', 1)[0] + '?name=' + quote(asset_name))

        '''
        read the contents of the asset file
        '''
        with open(asset_file, 'rb') as asset_file:
            asset_data = asset_file.read()
            asset_length = len(asset_data)

        retry = 2
        rc = -1

        while retry > 0:
            try:
                '''
                upload the asset file
                '''
                print(str.format('uploading asset "{0}" with a length of {1} bytes ...', asset_name, str(asset_length)))
                utils.github_api_request(url=upload_url, data=asset_data, method='POST', content_type=asset_mime_type)
                rc = 0
                break
            except IOError:
                _type, value, _traceback = sys.exc_info()
                print(str.format('Error uploading asset "{0}": {1}', asset_name, value.strerror))
                retry -= 1
            except URLError:
                _type, value, _traceback = sys.exc_info()
                print(str.format('Error uploading asset "{0}"', asset_name))
                retry -= 1

    return rc

if __name__ == "__main__":
    sys.exit(main())
