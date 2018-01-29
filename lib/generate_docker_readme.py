'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import json
import re
import argparse

from string import Template
from urllib2 import urlopen, Request, quote
from os.path import join
from os.path import realpath

def tags_as_string(tags):
    version_map = {}
    tag_lines = []
    minor_pattern = re.compile('([0-9]+)\.([0-9]+)(-)?')
    latest = ''

    for tag in tags:
        if 'latest' not in tag:
            minor = minor_pattern.match(tag).group(2)

            if minor not in version_map:
                version_map[minor] = []

            version_map[minor].append(tag)
        else:
            latest = tag

    add_latest = True
    for minor in sorted(version_map, reverse=True):
        tag_lines.append(', '.join([version for version in version_map[minor]]))

        if add_latest:
            tag_lines[-1] += ', ' + latest
            add_latest = False

    return '\n'.join(['* ' + tag_line for tag_line in tag_lines])


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--template', help='the Readme template', metavar='FILE', required=True)
    parser.add_argument('-o', '--output', help='the Readme output', metavar='FILE', required=True)
    parser.add_argument('-i', '--image', help='the Docker image', metavar='IMAGE', required=True)
    args = parser.parse_args()

    readme_template = realpath(args.template)
    readme = realpath(args.output)
    image = args.image

    repository = 'sapmachine'
    page = 1
    docker_hub_api = 'https://hub.docker.com/v2/repositories/{0}/{1}/tags/?page={2}'
    has_next = True
    ubuntu_jdk_images = []
    ubuntu_jre_images = []
    alpine_jdk_images = []
    alpine_jre_images = []

    while has_next:
        request = Request(docker_hub_api.format(repository, image, str(page)))
        response = json.loads(urlopen(request).read())
        next_page = response['next']
        page += 1

        if next_page is None:
            has_next = False

        tags = response['results']

        for tag in tags:
            name = tag['name']

            if 'alpine' in name:
                if 'jre' in name:
                    alpine_jre_images.append(name)
                else:
                    alpine_jdk_images.append(name)
            else:
                if 'jre' in name:
                    ubuntu_jre_images.append(name)
                else:
                    ubuntu_jdk_images.append(name)

    with open(readme_template, 'r') as readme_template_file:
        with open(readme, 'w+') as readme_file:
            readme_file.write(Template(readme_template_file.read()).substitute(
                ubuntu_jdk=tags_as_string(ubuntu_jdk_images),
                ubuntu_jre=tags_as_string(ubuntu_jre_images),
                alpine_jdk=tags_as_string(alpine_jdk_images),
                alpine_jre=tags_as_string(alpine_jre_images)
            ))


if __name__ == "__main__":
    sys.exit(main())