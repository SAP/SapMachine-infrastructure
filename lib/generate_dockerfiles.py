'''
Copyright (c) 2017-2023 by SAP SE, Walldorf, Germany.
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

dockerfile_template_ubuntu = '''FROM ubuntu:22.04

RUN apt-get update \\
    && apt-get -y --no-install-recommends install ca-certificates gnupg \\
    && export GNUPGHOME="$$(mktemp -d)" \\
    && gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/sapmachine.gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys CACB9FE09150307D1D22D82962754C3B3ABCFE23 \\
    && chmod 644 /etc/apt/trusted.gpg.d/sapmachine.gpg \\
    && echo "deb http://dist.sapmachine.io/debian/$$(dpkg --print-architecture)/ ./" > /etc/apt/sources.list.d/sapmachine.list \\
    && apt-get update \\
    && apt-get -y --no-install-recommends install ${pkg_version} \\
    && apt-get remove -y --purge --autoremove ca-certificates gnupg \\
    && rm -rf "$$GNUPGHOME" /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/sapmachine-${major}

CMD ["jshell"]
'''

dockerfile_template_distroless = '''FROM gcr.io/distroless/java${distrolessvers}-debian11:${type} as distroless

FROM ubuntu as builder

RUN apt-get update && apt-get -y --no-install-recommends install ca-certificates wget

RUN dpkgArch="$$(dpkg --print-architecture)"; \\
    case "$${dpkgArch}" in \\
		'amd64') \\
			url='https://github.com/SAP/SapMachine/releases/download/sapmachine-${version_string}/sapmachine-${bundle}-${version_string}_linux-x64_bin.tar.gz'; \\
			;; \\
		'arm64') \\
			url='https://github.com/SAP/SapMachine/releases/download/sapmachine-${version_string}/sapmachine-${bundle}-${version_string}_linux-aarch64_bin.tar.gz'; \\
			;; \\
		'ppc64el') \\
			url='https://github.com/SAP/SapMachine/releases/download/sapmachine-${version_string}/sapmachine-${bundle}-${version_string}_linux-ppc64le_bin.tar.gz'; \\
			;; \\
		*) echo >&2 "error: unsupported architecture '$$dpkgArch'"; exit 1 ;; \\
	esac; \\
    wget -O sapmachine.tar.gz $$url --progress=dot:giga

COPY --from=distroless / /distroless

RUN tar xzf sapmachine.tar.gz && \\
    rm -rf /distroless/etc/java-${major}-openjdk /distroless/usr/lib/jvm/java-${major}-openjdk-amd64 && \\
    mv sapmachine-${bundle}-${version_string} /distroless/usr/lib/jvm/java-${major}-openjdk-amd64

FROM scratch
COPY --from=builder /distroless /

${debug_path}
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV LANG=C.UTF-8
ENV JAVA_VERSION=${version_string}

ENTRYPOINT [ "/usr/bin/java", "-jar" ]
'''

readmefile_template = '''
### Overview

The dockerfiles in this subdirectory define images for consuming the ${what} release ${major} (version: ${version}) of the SapMachine Java Virtual Machine (JVM).
SapMachine is an OpenJDK based JVM that is built, quality tested and long-term supported by SAP.
It is the default JVM on the [SAP Business Technology Platform](https://www.sap.com/products/technology-platform.html) and it is also supported as a [Standard JRE](https://github.com/cloudfoundry/java-buildpack/blob/master/docs/jre-sap_machine_jre.md) in the [Cloud Foundry Java Build Pack](https://github.com/cloudfoundry/java-buildpack).

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

def write_dockerfile_ubuntu(base_dir, type, major, version_string):
    dockerfile_dir = join(base_dir, type)
    os.makedirs(dockerfile_dir)
    with open(join(dockerfile_dir, 'Dockerfile'), 'w+') as dockerfile:
            dockerfile.write(Template(dockerfile_template_ubuntu).substitute(
                pkg_version=str.format('sapmachine-{0}-{1}={2}', major, type, version_string),
                major=major
            ))

def write_dockerfile_distroless(base_dir, type, major, version_string):
    dockerfile_dir = join(base_dir, 'debian11', type)
    os.makedirs(dockerfile_dir)
    with open(join(dockerfile_dir, 'Dockerfile'), 'w+') as dockerfile:
            dockerfile.write(Template(dockerfile_template_distroless).substitute(
                major=major,
                type=type,
                version_string=version_string,
                bundle='jdk' if type.startswith("debug") else 'jre',
                debug_path='ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/busybox' if type.startswith("debug") else '',
                distrolessvers=major if utils.sapmachine_is_lts(major) and utils.sapmachine_default_major() != major else '-base'
            ))

def process_release(release, infrastructure_tags, dockerfiles_dir, args):
    tag = SapMachineTag.from_string(release['name'])
    version_string = tag.get_version_string()
    major = str(tag.get_major())
    skip_tag = False
    major_dir = join(dockerfiles_dir, major)
    ubuntu_dir = join(major_dir, 'ubuntu')
    distroless_dir = join(major_dir, 'distroless')

    for infrastructure_tag in infrastructure_tags:
        if infrastructure_tag['name'] == version_string:
            print(str.format('Tag "{0}" already exists for release "{1}"', version_string, release['name']))
            if not args.force:
              skip_tag = True
              break

    if not skip_tag:
        # Write ubuntu dockerfiles
        utils.remove_if_exists(ubuntu_dir)
        os.makedirs(ubuntu_dir)
        write_dockerfile_ubuntu(ubuntu_dir, 'jre', major, version_string)
        write_dockerfile_ubuntu(ubuntu_dir, 'jre-headless', major, version_string)
        write_dockerfile_ubuntu(ubuntu_dir, 'jdk', major, version_string)
        write_dockerfile_ubuntu(ubuntu_dir, 'jdk-headless', major, version_string)

        # Write distroless dockerfiles
        utils.remove_if_exists(distroless_dir)
        os.makedirs(distroless_dir)
        write_dockerfile_distroless(distroless_dir, 'latest', major, version_string)
        write_dockerfile_distroless(distroless_dir, 'nonroot', major, version_string)
        write_dockerfile_distroless(distroless_dir, 'debug', major, version_string)
        write_dockerfile_distroless(distroless_dir, 'debug-nonroot', major, version_string)

        # Write the readme
        if utils.sapmachine_is_lts(major):
            what = 'long term support'
            docker_tag = major
        else:
            what = 'stable'
            docker_tag = 'stable'
        readme_path = join(major_dir, 'README.md')
        with open(readme_path, 'w+') as readmefile:
            readmefile.write(Template(readmefile_template).substitute(
                docker_tag=docker_tag,
                what=what,
                major=major,
                version=version_string
            ))

        utils.run_cmd(['git', 'add', '.'], cwd=major_dir)
        _, diff, _  = utils.run_cmd("git diff HEAD".split(' '), cwd=major_dir, std=True)
        if not diff.strip():
            print(str.format("No changes for {0}", version_string))
            return

        utils.git_commit(dockerfiles_dir, str.format('Update Dockerfiles for SapMachine {0}', version_string), [major_dir])
        utils.git_tag(dockerfiles_dir, version_string, force = True if args.force else False)
        if not args.dry:
            utils.git_push(dockerfiles_dir)
            utils.git_push_tag(dockerfiles_dir, version_string, force = True if args.force else False)

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', help='specify the working directory', metavar='DIR', default='docker_work', required=False)
    parser.add_argument('--force', help='upload new content even if the the release tags already exist', action='store_true', required=False)
    parser.add_argument('--dry', help='only test execution but don\'t upload any new content. Also don\'t delete the work_dir before exiting', action='store_true', required=False)
    args = parser.parse_args()

    workdir = os.path.realpath(args.workdir)

    print('Loading SapMachine Release data...')
    releases = utils.get_github_releases()
    print('Loading SapMachine-infrastructure tags...')
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

    utils.remove_if_exists(workdir)
    os.makedirs(workdir)
    utils.git_clone('github.com/SAP/SapMachine-infrastructure', 'master', workdir)

    dockerfiles_dir = join(workdir, 'dockerfiles', 'official')
    removed = []
    for f in os.listdir(dockerfiles_dir):
        if not int(f) in docker_releases:
            utils.remove_if_exists(join(dockerfiles_dir, f))
            removed.append(join(dockerfiles_dir, f))
    if removed != []:
        utils.git_commit(workdir, 'remove discontinued versions', removed)

    for release in docker_releases:
        process_release(docker_releases[release], infrastructure_tags, dockerfiles_dir, args)

    if not args.dry:
        utils.remove_if_exists(workdir)

    return 0

if __name__ == "__main__":
    sys.exit(main())
