'''
Copyright (c) 2001-2021 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import json
import sys
import utils

def main(argv=None):    
    upstream_releases = utils.github_api_request(api='releases',
                                                 url=None,
                                                 owner='jvm-profiling-tools',
                                                 repository='async-profiler',
                                                 data=None,
                                                 method='GET',
                                                 per_page=100,
                                                 content_type=None,
                                                 url_parameter=[])
    sap_releases = utils.github_api_request(api='releases',
                                            url=None,
                                            owner='SAP',
                                            repository='async-profiler',
                                            data=None,
                                            method='GET',
                                            per_page=100,
                                            content_type=None,
                                            url_parameter=[])
    sap_tags = utils.github_api_request(api='tags',
                                        url=None, owner='SAP',
                                        repository='async-profiler',
                                        data=None, method='GET',
                                        per_page=100,
                                        content_type=None,
                                        url_parameter=[])

    for release in reversed(upstream_releases):
        tag = release['tag_name']
        if [x for x in sap_releases if x['tag_name'] == tag] == [] and [x for x in sap_tags if x['name'] == tag] != []:
            data = json.dumps({ "tag_name": tag, "name": release['name'], "body": release['body']})
            response = utils.github_api_request(api='releases',
                                                url=None,
                                                owner='SAP',
                                                repository='async-profiler',
                                                data=data,
                                                method='POST',
                                                content_type='application/json')
            print(tag, end='')
            return 0
    print('No new releases', end='')
    return 0

if __name__ == "__main__":
    sys.exit(main())
