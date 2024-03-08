'''
Copyright (c) 2018-2024 by SAP SE, Walldorf, Germany.
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

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the SapMachine tag', metavar='MAJOR', required=True)
    parser.add_argument('-d', '--description', default='', help='the description of the release', required=False)
    parser.add_argument('-p', '--prerelease', help='this is a pre-release', action='store_true', default=False)
    parser.add_argument('-a', '--asset', help='the asset to upload', metavar='ASSET', required=False)
    parser.add_argument('-g', '--github', default='https://api.github.com', help='the github api url to be used', metavar='GITHUB', required=False)
    args = parser.parse_args()

    try:
        release = utils.github_api_request(f"releases/tags/{args.tag}", github_api_url=args.github)
        release_id = release['id']
        upload_url = release['upload_url']
    except HTTPError as httpError:
        print(f"Release {args.tag} does not seem to exist: {httpError.code} ({httpError.reason})")
        release_id = upload_url = None

    if release_id is None:
        # release does not exist yet -> create it
        data = json.dumps({ "tag_name": args.tag, "name": args.tag, "body": args.description, "draft": False, "prerelease": args.prerelease })
        try:
            response = utils.github_api_request('releases', github_api_url=args.github, data=data, method='POST', content_type='application/json')
            release_id = response['id']
            upload_url = response['upload_url']
            print(f"Created release \"{args.tag}\"")
        except HTTPError as http_err:
            print(f"Error creating release \"{args.tag}\". Maybe it exists now, check...")
            try:
                release = utils.github_api_request(f"releases/tags/{args.tag}", github_api_url=args.github)
                release_id = release['id']
                upload_url = release['upload_url']
                print(f"Yes, release id: {release_id}")
            except HTTPError as httpError:
                print(f"Nope, must be something else: {httpError.code} ({httpError.reason})")
                return 1

    if args.asset is not None:
        # asset file is specified (-a)
        asset_file = os.path.realpath(args.asset)
        asset_name = os.path.basename(asset_file)
        asset_mime_type = mimetypes.guess_type(asset_file)

        if asset_mime_type is None or asset_mime_type[0] is None:
            asset_mime_type = 'application/octet-stream'
            print(f'Could not detect mime-type of {args.asset}, falling back to: {asset_mime_type}')
        else:
            asset_mime_type = asset_mime_type[0]
            print(f'Detected mime-type of {args.asset}: {asset_mime_type}')

        # first check wether the asset already exists
        for gh_asset in utils.github_api_request(f'releases/{release_id}/assets', github_api_url=args.github, per_page=50):
            if gh_asset['name'] == asset_name:
                # asset already exists -> skip
                print(f'Error: Asset "{asset_name}" already exists.')
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
                print(f'Uploading asset "{asset_name}" with a length of {str(asset_length)} bytes...')
                utils.github_api_request(url=upload_url, data=asset_data, method='POST', content_type=asset_mime_type)
                return 0
            except IOError as e:
                # _type, value, _traceback = sys.exc_info()
                # traceback.print_exception(_type, value, _traceback)
                print(f'Error uploading asset "{asset_name}": {e}')
                retry -= 1
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
