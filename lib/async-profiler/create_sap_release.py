'''
Copyright (c) 2024 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import utils

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the release tag', metavar='TAG', required=True)
    parser.add_argument('--tgt-github', default='https://api.github.com', help='the target github api url',
                        metavar='TGT_GITHUB', required=False)
    parser.add_argument('--tgt-github-org', default='SAP', help='the target github org',
                        metavar='TGT_GITHUB_ORG', required=False)
    parser.add_argument('--tgt-github-token', help='the target github security token', metavar='TGT_GITHUB_TOKEN',
                        required=False)
    args = parser.parse_args()

    # upstream release must exist
    upstream_release = utils.github_api_request(api=f'releases/tags/{args.tag}', github_org='async-profiler', repository='async-profiler', raiseError=False)
    if upstream_release is None:
        print(f'Upstream release {args.tag} not found.')
        return -1

    # if sap release exists, all is good.
    sap_release = utils.github_api_request(api=f'releases/tags/{args.tag}', github_api_url=args.tgt_github, github_org=args.tgt_github_org, repository='async-profiler', token=args.tgt_github_token, raiseError=False)
    if sap_release is not None:
        print(f'SAP release {args.tag} already exists.')
        return 0

    # a tag must exist in SAP repository
    sap_tags = utils.github_api_request(api='tags', github_api_url=args.tgt_github, github_org=args.tgt_github_org, repository='async-profiler', token=args.tgt_github_token, per_page=100)
    sap_tag_exists = False
    for x in sap_tags:
        if x['name'] == args.tag:
            sap_tag_exists = True

    if sap_tag_exists is False:
        print(f'Tag {args.tag} not found in SAP repository.')
        return -1

    data = json.dumps({"tag_name": args.tag, "name": upstream_release['name'], "body": upstream_release['body']})
    utils.github_api_request(api='releases', github_api_url=args.tgt_github, github_org=args.tgt_github_org, repository='async-profiler', token=args.tgt_github_token, data=data, method='POST', add_headers={"Content-Type": "application/json"})

    return 0

if __name__ == "__main__":
    sys.exit(main())
