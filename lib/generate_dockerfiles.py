'''
Copyright (c) 2017-2022 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import os
import sys
import utils

from os.path import join
from string import Template
from utils import github_api_request
from versions import SapMachineTag

dockerfile_template = '''
FROM ubuntu:20.04

RUN apt-get update \\
    && apt-get install -y --no-install-recommends ca-certificates gnupg2 \\
    && rm -rf /var/lib/apt/lists/*

RUN export GNUPGHOME="$$(mktemp -d)" \\
    && gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys CACB9FE09150307D1D22D82962754C3B3ABCFE23 \\
    && gpg --batch --export --armor 'CACB 9FE0 9150 307D 1D22 D829 6275 4C3B 3ABC FE23' > /etc/apt/trusted.gpg.d/sapmachine.gpg.asc \\
    && gpgconf --kill all && rm -rf "$$GNUPGHOME" \\
    && echo "deb http://dist.sapmachine.io/debian/${architecture}/ ./" > /etc/apt/sources.list.d/sapmachine.list \\
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

The SapMachine image supports the x86/64, aarch64 and ppc64le architectures.

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

architectures = ["amd64", "arm64", "ppc64el"]

def process_release(release, infrastructure_tags, git_dir, args):
    tag = SapMachineTag.from_string(release['name'])
    version_string = tag.get_version_string()
    major = str(tag.get_major())
    skip_tag = False
    dockerfile_base_dir = join(git_dir, 'dockerfiles', 'official', major)

    for infrastructure_tag in infrastructure_tags:
        if infrastructure_tag['name'] == version_string:
            print(str.format('tag "{0}" already exists for release "{1}"', version_string, release['name']))
            if not args.force:
              skip_tag = True
              break

    if not skip_tag:
        utils.remove_if_exists(dockerfile_base_dir)
        os.makedirs(dockerfile_base_dir)

        for architecture in architectures:
            os.makedirs(join(dockerfile_base_dir, architecture))
            dockerfile_path = join(dockerfile_base_dir, architecture, 'Dockerfile')
            with open(dockerfile_path, 'w+') as dockerfile:
                dockerfile.write(Template(dockerfile_template).substitute(
                    architecture=architecture,
                    version=str.format('sapmachine-{0}-jdk={1}', major, version_string),
                    major=major
                ))

            if utils.sapmachine_is_lts(major):
                what = 'long term support'
                docker_tag = major
            else:
                what = 'stable'
                docker_tag = 'stable'
            readme_path = join(dockerfile_base_dir, architecture, 'README.md')
            with open(readme_path, 'w+') as readmefile:
                readmefile.write(Template(readmefile_template).substitute(
                    docker_tag=docker_tag,
                    what=what,
                    major=major,
                    version=version_string
                ))

        utils.git_commit(git_dir, 'updated Dockerfile', [dockerfile_path, readme_path])
        if not args.dry:
            utils.git_tag(git_dir, version_string)
            utils.git_push(git_dir)
            utils.git_push_tag(git_dir, version_string)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', help='specify the working directory', metavar='DIR', default='docker_work', required=False)
    parser.add_argument('--force', help='upload new content even if the the release tags already exist', action='store_true', required=False)
    parser.add_argument('--dry', help='only test execution but don\'t upload any new content. Also don\'t delete the work_dir before exiting', action='store_true', required=False)
    args = parser.parse_args()

    workdir = os.path.realpath(args.workdir)
    git_dir = join(workdir, 'sapmachine-infrastructure')

    utils.remove_if_exists(workdir)
    os.makedirs(workdir)

    releases = github_api_request('releases', per_page=100)
    infrastructure_tags = utils.get_github_tags(repository='SapMachine-infrastructure')
    docker_releases = {}
    stable_release = None

    for release in releases:
        if release['prerelease']:
            continue

        tag = SapMachineTag.from_string(release['name'])
        if tag is None:
            print(str.format("{0} is no SapMachine release, dropping", release['name']))
            continue

        major = tag.get_major()
        update = tag.get_update()

        if utils.sapmachine_is_lts(major):
            if major in docker_releases:
                if SapMachineTag.from_string(docker_releases[major]['name']).get_update() < update:
                    docker_releases[major] = release
            else:
                docker_releases[major] = release

        if stable_release == None:
            stable_release = release
        else:
            stable_tag = SapMachineTag.from_string(stable_release['name'])
            if major > stable_tag.get_major() or (major == stable_tag.get_major() and update > stable_tag.get_update()):
                stable_release = release

    print('Determined the following versions for processing:')
    for release in docker_releases:
        print(str.format('LTS {1}: {0}', SapMachineTag.from_string(docker_releases[release]['name']).get_version_string(), release))
    stable_tag = SapMachineTag.from_string(stable_release['name'])
    print(str.format('STABLE: {0}', stable_tag.get_version_string()))

    stable_major = stable_tag.get_major()
    if not (stable_major in docker_releases):
        print("Adding stable release to docker_releases")
        docker_releases[stable_major] = stable_release

    utils.git_clone('github.com/SAP/SapMachine-infrastructure', 'master', git_dir)

    versions_dir = join(git_dir, 'dockerfiles', 'official')
    removed = []
    for f in os.listdir(versions_dir):
        if not int(f) in docker_releases:
            utils.remove_if_exists(join(versions_dir, f))
            removed.append(join(versions_dir, f))
    if removed != []:
        utils.git_commit(git_dir, 'remove discontinued versions', removed)

    for release in docker_releases:
        process_release(docker_releases[release], infrastructure_tags, git_dir, args)

    if not args.dry:
        utils.remove_if_exists(workdir)

    return 0

if __name__ == "__main__":
    sys.exit(main())
