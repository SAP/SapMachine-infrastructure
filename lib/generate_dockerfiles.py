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
from utils import github_api_request

dockerfile_template = '''
FROM ubuntu:20.04

RUN apt-get update \\
    && apt-get install -y --no-install-recommends wget ca-certificates gnupg2 \\
    && rm -rf /var/lib/apt/lists/*

RUN export GNUPGHOME="$$(mktemp -d)" \\
    && wget -q -O - https://dist.sapmachine.io/debian/sapmachine.old.key | gpg --batch --import \\
    && gpg --batch --export --armor 'DA4C 00C1 BDB1 3763 8608 4E20 C7EB 4578 740A EEA2' > /etc/apt/trusted.gpg.d/sapmachine.old.gpg.asc \\
    && wget -q -O - https://dist.sapmachine.io/debian/sapmachine.key | gpg --batch --import \\
    && gpg --batch --export --armor 'CACB 9FE0 9150 307D 1D22 D829 6275 4C3B 3ABC FE23' > /etc/apt/trusted.gpg.d/sapmachine.gpg.asc \\
    && gpgconf --kill all && rm -rf "$$GNUPGHOME" \\
    && echo "deb http://dist.sapmachine.io/debian/amd64/ ./" > /etc/apt/sources.list.d/sapmachine.list \\
    && apt-get update \\
    && apt-get -y --no-install-recommends install ${version} \\
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/sapmachine-${major}

CMD ["jshell"]
'''

readmefile_template = '''
### Overview

The image in this repository contains the ${what} releases ${major} (version: ${version}) of the SapMachine Java virtual machine (JVM). SapMachine is an OpenJDK based JVM that is build, quality tested and long-term supported by SAP. It is the default JVM on the [SAP Cloud Platform](https://cloudplatform.sap.com/index.html) and it is also supported as a [Standard JRE](https://github.com/cloudfoundry/java-buildpack/blob/master/docs/jre-sap_machine_jre.md) in the [Cloud Foundry Java Build Pack](https://github.com/cloudfoundry/java-buildpack).

For more information see the [SapMachine website](https://sapmachine.io).

The SapMachine image supports the x86/64 architecture.

Java and all Java-based trademarks and logos are trademarks or registered trademarks of Oracle and/or its affiliates.

### How to use this Image

You can pull and test the image with the following commands:

```console
docker pull sapmachine:${docker_tag}
docker run -it sapmachine:${docker_tag} java -version
```

You can also use the SapMachine image as a base image to run your own jar file:

```dockerfile
FROM sapmachine:${docker_tag}
RUN mkdir /opt/myapp
COPY myapp.jar /opt/myapp
CMD ["java", "-jar", "/opt/myapp/myapp.jar"]
```

You can then build and run your own Docker image:

```console
docker build -t myapp .
docker run -it --rm myapp
```
'''

def process_release(release, tags, git_dir):
    version, version_part, major, update, version_sap, build_number, os_ext = utils.sapmachine_tag_components(release['name'])
    tag_name = version_part
    skip_tag = False
    dockerfile_dir = join(git_dir, 'dockerfiles', 'official', major)

    for tag in tags:
        if tag['name'] == tag_name:
            print(str.format('tag "{0}" already exists for release "{1}"', tag_name, release['name']))
            skip_tag = True
            break

    if not skip_tag:
        utils.remove_if_exists(dockerfile_dir)
        os.makedirs(dockerfile_dir)

        dockerfile_path = join(dockerfile_dir, 'Dockerfile')
        with open(dockerfile_path, 'w+') as dockerfile:
            dockerfile.write(Template(dockerfile_template).substitute(
                version=str.format('sapmachine-{0}-jdk={1}', major, version_part),
                major=major
            ))

        if utils.sapmachine_is_lts(major):
            what = 'long term support'
            docker_tag = major
        else:
            what = 'stable'
            docker_tag = 'stable'
        readme_path = join(dockerfile_dir, 'README.md')
        with open(readme_path, 'w+') as readmefile:
            readmefile.write(Template(readmefile_template).substitute(
                docker_tag=docker_tag,
                what=what,
                major=major,
                version=version_part
            ))

        utils.git_commit(git_dir, 'updated Dockerfile', [dockerfile_path, readme_path])
        utils.git_tag(git_dir, tag_name)
        utils.git_push(git_dir)
        utils.git_push_tag(git_dir, tag_name)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', help='specify the working directory', metavar='DIR', default='docker_work' ,required=False)
    args = parser.parse_args()

    workdir = os.path.realpath(args.workdir)
    git_dir = join(workdir, 'sapmachine-infrastructure')

    utils.remove_if_exists(workdir)
    os.makedirs(workdir)

    releases = github_api_request('releases', per_page=100)
    infrastructure_tags = utils.get_github_infrastructure_tags()
    docker_releases = {}
    stable_release = None

    for release in releases:
        if release['prerelease']:
            continue

        version, version_part, major, update, version_sap, build_number, os_ext = utils.sapmachine_tag_components(release['name'])

        if utils.sapmachine_is_lts(major):
            if major in docker_releases:
                _, _, _, lts_update, _, _, _ = utils.sapmachine_tag_components(docker_releases[major]['name'])
                if int(lts_update) < int(update):
                    docker_releases[major] = release
            else:
                docker_releases[major] = release

        if stable_release == None:
            stable_release = release
        else:
            _, _, stable_major, stable_update, _, _, _ = utils.sapmachine_tag_components(stable_release['name'])
            if int(major) > int(stable_major) or (int(major) == int(stable_major) and int(update) > int(stable_update)):
                stable_release = release

    print('Determined the following versions for processing:')
    for release in docker_releases:
        version, _, _, _, _, _, _ = utils.sapmachine_tag_components(docker_releases[release]['name'])
        print(str.format('LTS {1}: {0}', version, release))
    stable_version, _, stable_major, _, _, _, _ = utils.sapmachine_tag_components(stable_release['name'])
    print(str.format('stable: {0}', stable_version))

    if not (stable_version in docker_releases):
        docker_releases[stable_major] = stable_release

    utils.git_clone('github.com/SAP/SapMachine-infrastructure', 'master', git_dir)

    versions_dir = join(git_dir, 'dockerfiles', 'official')
    removed = []
    for f in os.listdir(versions_dir):
        if not f in docker_releases:
            utils.remove_if_exists(join(versions_dir, f))
            removed.append(join(versions_dir, f));
    if removed != []:
        utils.git_commit(git_dir, 'remove discontinued versions', removed)

    for release in docker_releases:
        process_release(docker_releases[release], infrastructure_tags, git_dir)

    utils.remove_if_exists(workdir)

    return 0

if __name__ == "__main__":
    sys.exit(main())
