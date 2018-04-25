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

from os.path import join
from string import Template

template_alpine ='''
FROM alpine:3.5

RUN apk update; \
    apk add ${dependencies};

WORKDIR /etc/apk/keys
RUN wget https://dist.sapmachine.io/alpine/sapmachine%40sap.com-5a673212.rsa.pub

WORKDIR /

RUN echo "http://dist.sapmachine.io/alpine/3.5" >> /etc/apk/repositories

RUN apk update; \
    apk add ${package};

${add_user}
'''

template_ubuntu = '''
FROM ubuntu:16.04

RUN rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get update \\
    && apt-get install -y --no-install-recommends ${dependencies} \\
    && rm -rf /var/lib/apt/lists/*

RUN wget -q -O - https://dist.sapmachine.io/debian/sapmachine.key | apt-key add - \\
    && echo "deb http://dist.sapmachine.io/debian/amd64/ ./" >> /etc/apt/sources.list \\
    && apt-get update \\
    && apt-get -y --no-install-recommends install ${package}

${add_user}
'''

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the GIT tag to build the image from', metavar='GIT_TAG', required=True)
    parser.add_argument('-i', '--imagetype', help='sets the image type', choices=['jdk', 'jre', 'test'], required=True)
    parser.add_argument('--alpine', help='build Alpine Linux image', action='store_true', default=False)
    parser.add_argument('--latest', help='tag image as latest', action='store_true', default=False)
    args = parser.parse_args()

    tag = args.tag
    image_type = args.imagetype
    build_alpine = args.alpine
    latest = args.latest

    version, version_part, major, build_number, sap_build_number, os_ext = utils.sapmachine_tag_components(tag)

    if version is None:
        raise Exception(str.format('Invalid tag: {0}', tag))

    dependencies = 'wget ca-certificates'

    if image_type == 'test':
        if build_alpine:
            dependencies += ' zip git unzip coreutils python binutils shadow bash'
            add_user = 'RUN groupadd -g 1002 jenkins; useradd -ms /bin/bash jenkins -u 1002 -g 1002'
        else:
            dependencies += ' zip git unzip realpath python binutils'
            add_user = 'RUN useradd -ms /bin/bash jenkins -u 1002'
    else:
        add_user = ''

    if build_alpine:
        package = str.format('sapmachine-{0}-{1}={2}.{3}.{4}-r0',
            major,
             'jdk' if image_type == 'test' else image_type,
            version_part,
            build_number,
            sap_build_number)
    else:
        package = str.format('sapmachine-{0}-{1}={2}+{3}.{4}',
            major,
            'jdk' if image_type == 'test' else image_type,
            version_part,
            build_number,
            sap_build_number)

    docker_work = join(os.getcwd(), 'docker_work')

    utils.remove_if_exists(docker_work)
    os.makedirs(docker_work)

    if build_alpine:
        template = template_alpine
    else:
        template = template_ubuntu

    with open(join(docker_work, 'Dockerfile'), 'w+') as dockerfile:
        dockerfile.write(Template(template).substitute(dependencies=dependencies, package=package, add_user=add_user))

    if 'DOCKER_USER' in os.environ and image_type != 'test':
        docker_user = os.environ['DOCKER_USER']
        docker_tag = str.format('{0}/jdk{1}:{2}.{3}.{4}{5}{6}',
            docker_user,
            major,
            version_part,
            build_number,
            sap_build_number,
            '-jre' if image_type == 'jre' else '',
            '-alpine' if build_alpine else '')

        docker_tag_latest = str.format('{0}/jdk{1}:latest{2}{3}',
            docker_user,
            major,
            '-jre' if image_type == 'jre' else '',
            '-alpine' if build_alpine else '')

        if latest:
            utils.run_cmd(['docker', 'build', '-t', docker_tag, '-t', docker_tag_latest, docker_work])
        else:
            utils.run_cmd(['docker', 'build', '-t', docker_tag, docker_work])

        if 'DOCKER_PASSWORD' in os.environ:
            docker_password = os.environ['DOCKER_PASSWORD']
            utils.run_cmd(['docker', 'login', '-u', docker_user, '-p', docker_password])
            utils.run_cmd(['docker', 'push', str.format('{0}/jdk{1}', docker_user, major)])

if __name__ == "__main__":
    sys.exit(main())