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

template_ubuntu = '''
FROM ubuntu:18.04

MAINTAINER Rene Schuenemann <sapmachine@sap.com>

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
    parser.add_argument('-i', '--imagetype', help='sets the image type', choices=['jdk', 'test'], required=True)
    parser.add_argument('-p', '--publish', help='publish the image', action='store_true', default=False)
    parser.add_argument('--latest', help='tag image as latest', action='store_true', default=False)
    parser.add_argument('--workdir', help='specify the working directory', metavar='DIR', required=False)
    args = parser.parse_args()

    tag = args.tag
    image_type = args.imagetype
    publish = args.publish
    latest = args.latest
    workdir = args.workdir
    tag_is_release = utils.sapmachine_tag_is_release(tag)

    version, version_part, major, build_number, sap_build_number, os_ext = utils.sapmachine_tag_components(tag)

    if version is None:
        raise Exception(str.format('Invalid tag: {0}', tag))

    dependencies = 'wget ca-certificates'

    if image_type == 'test':
        dependencies += ' zip git unzip realpath python binutils'
        add_user = 'RUN useradd -ms /bin/bash jenkins -u 1002'
    else:
        add_user = ''


    if build_number:
        package = str.format('sapmachine-{0}-jdk={1}+{2}.{3}',
            major,
            version_part,
            build_number,
            sap_build_number if sap_build_number else '0')
    else:
        package = str.format('sapmachine-{0}-jdk={1}',
            major,
            version_part)

    if workdir is None:
        workdir = join(os.getcwd(), 'docker_work', image_type)

    utils.remove_if_exists(workdir)
    os.makedirs(workdir)

    template = template_ubuntu

    with open(join(workdir, 'Dockerfile'), 'w+') as dockerfile:
        dockerfile.write(Template(template).substitute(dependencies=dependencies, package=package, add_user=add_user))

    if 'DOCKER_USER' in os.environ and image_type != 'test':
        docker_user = os.environ['DOCKER_USER']
        sapmachine_version = [int(e) for e in version_part.split('.')]
        expand = 5  if sap_build_number else 3
        sapmachine_version += [0 for sapmachine_version in range(0, expand - len(sapmachine_version))]

        if sap_build_number:
            sapmachine_version[4] = int(sap_build_number)

        sapmachine_version_string = '.'.join([str(e) for e in sapmachine_version])

        docker_tag = str.format('{0}/jdk{1}:{2}{3}',
            docker_user,
            major,
            sapmachine_version_string,
            '.b' + build_number if build_number else '')

        docker_tag_latest = str.format('{0}/jdk{1}:latest',
            docker_user,
            major)

        if latest:
            utils.run_cmd(['docker', 'build', '-t', docker_tag, '-t', docker_tag_latest, workdir])
        else:
            utils.run_cmd(['docker', 'build', '-t', docker_tag, workdir])


        retcode, out, err = utils.run_cmd(['docker', 'run', docker_tag, 'java', '-version'], throw=False, std=True)

        if retcode != 0:
            raise Exception(str.format('Failed to run Docker image: {0}', err))

        version_2, version_part_2, major_2, build_number_2, sap_build_number_2 = utils.sapmachine_version_components(err, multiline=True)

        if version_part != version_part_2 or (build_number and (build_number != build_number_2)) or (sap_build_number and (sap_build_number != sap_build_number_2)):
           raise Exception(str.format('Invalid version found in Docker image:\n{0}', err))


        retcode, out, err = utils.run_cmd(['docker', 'run', docker_tag, 'which', 'javac'], throw=False, std=True)

        if retcode != 0 or not out:
            raise Exception('Image type is not JDK')

        if publish and 'DOCKER_PASSWORD' in os.environ:
            docker_password = os.environ['DOCKER_PASSWORD']
            utils.run_cmd(['docker', 'login', '-u', docker_user, '-p', docker_password])
            utils.run_cmd(['docker', 'push', docker_tag])

            if latest:
                utils.run_cmd(['docker', 'push', docker_tag_latest])

if __name__ == "__main__":
    sys.exit(main())
