'''
Copyright (c) 2021-2022 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import utils

from jmc_versions import JMCTag

def main(argv=None):
    # fetch all tags
    print("Fetching GitHub tags from JMC repository...")
    tags = utils.get_github_tags(repository='JMC')
    print(str.format('Found {0} tags.', len(tags)))

    # iterate all tags to find the latest JMC tag for a JMC major release
    jmc_tags = {}
    for tag in tags:
        # filter for jmc tags
        jmc_tag = JMCTag.from_string(tag['name'])
        if jmc_tag is None:
            continue

        # print(str.format('Found Tag object...'))
        # jmc_tag.print_details()

        # only remember the latest jmc tag (version comparison)
        if (jmc_tag.get_major() not in jmc_tags or jmc_tag.is_greater_than(jmc_tags[jmc_tag.get_major()]) or
            (jmc_tag.is_same_update_version(jmc_tags[jmc_tag.get_major()]) and jmc_tag.is_ga())):
            jmc_tags[jmc_tag.get_major()] = jmc_tag

    print("Latest JMC tag per major version:")
    for k,v in jmc_tags.items():
        print(str.format('{0}: {1}', str(k).rjust(2), v.as_string()))

if __name__ == "__main__":
    sys.exit(main())
