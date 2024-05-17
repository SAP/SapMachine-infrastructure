'''
Copyright (c) 2024 by SAP SE, Walldorf, Germany.
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
    parser.add_argument('--src-github', default='https://api.github.com', help='the source github api url',
                        metavar='SRC_GITHUB', required=False)
    parser.add_argument('--src-github-org', default='SAP', help='the source github org', metavar='SRC_GITHUB_ORG',
                        required=False)
    parser.add_argument('--src-repository', default='SapMachine', help='the source github repository name',
                        metavar='SRC_GITHUB_REPO', required=False)
    parser.add_argument('--src-github-token', help='the source github security token',
                        metavar='SRC_GITHUB_TOKEN', required=False)
    parser.add_argument('--tgt-github', default='https://api.github.com', help='the target github api url',
                        metavar='TGT_GITHUB', required=False)
    parser.add_argument('--tgt-github-org', default='SAP', help='the target github org',
                        metavar='TGT_GITHUB_ORG', required=False)
    parser.add_argument('--tgt-repository', default='SapMachine', help='the target github repository name',
                        metavar='TGT_GITHUB_REPO', required=False)
    parser.add_argument('--tgt-github-token', help='the target github security token', metavar='TGT_GITHUB_TOKEN',
                        required=False)
    args = parser.parse_args()

    src_assets, src_release_id, _, _ = github_get_release(github=args.src_github, github_org=args.src_github_org,
                                                       tag=args.tag, repository=args.src_repository,
                                                       token=args.src_github_token)
    tgt_asset_names, tgt_release_id, tgt_upload_url, tgt_html_url = github_create_release(github=args.tgt_github,
                                                                            github_org=args.tgt_github_org,
                                                                            tag=args.tag,
                                                                            description=args.description,
                                                                            prerelease=args.prerelease,
                                                                            repository=args.tgt_repository,
                                                                            token=args.tgt_github_token)

    for f, u in src_assets.items():
        if f not in tgt_asset_names:
            github_copy_asset(asset_name=f, asset_url=u, src_token=args.src_github_token,
                              tgt_token=args.tgt_github_token, upload_url=tgt_upload_url)
        else:
            print(f"Skipping file {f} because it already exists in {tgt_html_url}")


def github_get_release(github, github_org, tag, repository='SapMachine', token=None):
    assets = {}
    try:
        release = utils.github_api_request(f"releases/tags/{tag}", github_api_url=github, github_org=github_org,
                                           repository=repository, token=token)
        release_id = release['id']
        upload_url = release['upload_url']
        html_url = release['html_url']
        for asset in release['assets']:
            assets[asset['name']] = asset['url']
    except HTTPError as httpError:
        print(f"Release {tag} does not seem to exist: {httpError.code} ({httpError.reason})")
        release_id = upload_url = html_url = None
    return assets, release_id, upload_url, html_url


def github_create_release(tag, github, github_org, description, prerelease, repository='SapMachine', token=None):
    upload_url = None
    asset_names, release_id, upload_url, html_url = github_get_release(github, github_org, tag, repository=repository,
                                                                       token=token)

    if release_id is None:
        # release does not exist yet -> create it
        data = json.dumps({"tag_name": tag, "name": tag, "body": description, "draft": False, "prerelease": prerelease})
        try:
            response = utils.github_api_request('releases', github_api_url=github, github_org=github_org, data=data,
                                                method='POST', repository=repository, token=token,
                                                add_headers={"Content-Type": "application/json", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
            release_id = response['id']
            upload_url = response['upload_url']
            html_url = response['html_url']
            print(f"Created release \"{tag}\"")
        except HTTPError:
            print(f"Error creating release \"{tag}\". Maybe it exists now, check...")
            try:
                release = utils.github_api_request(f"releases/tags/{tag}", github_api_url=github,
                                                   github_org=github_org, repository=repository, token=token)
                release_id = release['id']
                upload_url = release['upload_url']
                html_url = release['html_url']
            except HTTPError as httpError:
                print(f"Nope, must be something else: {httpError.code} ({httpError.reason})")
                return 1
    return asset_names, release_id, upload_url, html_url


def github_copy_asset(asset_name, asset_url, upload_url, src_token=None, tgt_token=None):
    if asset_name is not None:
        # asset file is specified (-a)
        utils.download_file(url=asset_url, target=asset_name, token=src_token,
                            headers={'Accept': 'application/octet-stream'})
        asset_file = os.path.realpath(asset_name)
        asset_mime_type = mimetypes.guess_type(asset_file)

        if asset_mime_type is None or asset_mime_type[0] is None:
            asset_mime_type = 'application/octet-stream'
            print(f'Could not detect mime-type of {asset_name}, falling back to: {asset_mime_type}')
        else:
            asset_mime_type = asset_mime_type[0]
            print(f'Detected mime-type of {asset_name}: {asset_mime_type}')

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
                utils.github_api_request(url=upload_url, data=asset_data, method='POST', add_headers={"Content-Type": asset_mime_type},
                                         token=tgt_token)
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
