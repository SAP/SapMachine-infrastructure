'''
Copyright (c) 2018-2023 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import json
import mimetypes
import os
import sys
import utils

from urllib.error import HTTPError
from urllib.parse import quote

def lookup_github_release(tag, cache=True):
    for release in utils.get_github_releases(cache):
        if release['tag_name'] == tag:
            return release['id'], release['upload_url']

    return None, None

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine tag', metavar='MAJOR', required=True)
    parser.add_argument('-d', '--description', default='', help='the description of the release', required=False)
    parser.add_argument('-p', '--prerelease', help='this is a pre-release', action='store_true', default=False)
    parser.add_argument('-a', '--asset', help='the asset to upload', metavar='ASSET', required=False)
    args = parser.parse_args()

    tag = args.tag
    asset = args.asset

    if asset is not None:
        asset_file = os.path.realpath(asset)
        asset_name = os.path.basename(asset_file)
        asset_mime_type = mimetypes.guess_type(asset_file)

        if asset_mime_type is None or asset_mime_type[0] is None:
            asset_mime_type = 'application/octet-stream'
            print(str.format('Could not detect mime-type, falling back to: "{0}"', asset_mime_type))
        else:
            asset_mime_type = asset_mime_type[0]
            print(str.format('Detected mime-type: "{0}"', asset_mime_type))

    release_id, upload_url = lookup_github_release(tag)

    if release_id is None:
        # release does not exist yet -> create it
        data = json.dumps({ "tag_name": tag, "name": tag, "body": args.description, "draft": False, "prerelease": args.prerelease })
        try:
            response = utils.github_api_request('releases', data=data, method='POST', content_type='application/json')
            release_id = response['id']
            upload_url = response['upload_url']
            print(str.format('Created release "{0}"', tag))
        except HTTPError as http_err:
            print(str.format('Error creating release "{0}". Maybe it exists now already, check...', tag))
            release_id, upload_url = lookup_github_release(tag, cache=False)
            if release_id is None:
                print(str.format('Nope, must be something else. POST error: {}', http_err))
                return 1
            else:
                print(str.format('Yes, release id: {}', release_id))

    if asset is not None:
        # asset file is specified (-a)

        # first check wether the asset already exists
        for gh_asset in utils.github_api_request(str.format('releases/{0}/assets', release_id), per_page=50):
            if gh_asset['name'] == asset_name:
                # asset already exists -> skip
                print(str.format('Error: Asset "{0}" already exists.', asset_name))
                return 1

        upload_url = str(upload_url.split('{', 1)[0] + '?name=' + quote(asset_name))

        # read the contents of the asset file
        with open(asset_file, 'rb') as asset_file:
            asset_data = asset_file.read()
            asset_length = len(asset_data)

        retry = 2

        while retry > 0:
            try:
                # upload the asset file
                print(str.format('Uploading asset "{0}" with a length of {1} bytes...', asset_name, str(asset_length)))
                utils.github_api_request(url=upload_url, data=asset_data, method='POST', content_type=asset_mime_type)
                return 0
            except IOError as e:
                # _type, value, _traceback = sys.exc_info()
                # traceback.print_exception(_type, value, _traceback)
                print(str.format('Error uploading asset "{0}": {1}', asset_name, e))
                retry -= 1
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
