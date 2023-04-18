'''
Copyright (c) 2023 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import requests
import tarfile
import shutil
import subprocess
import glob
import argparse
import re


def download_from_artifactory(u, dname):
    chunk_size = 16777216
    print(f"Downloading {u} to file {dname}")
    if not os.path.exists(dname):
        with requests.get(u, auth=(os.getenv("ARTIFACTORY_USER"), os.getenv("ARTIFACTORY_PWD")), stream=True) as r:
            with open(dname, 'wb') as f:
                for chunk in r.iter_content(chunk_size):
                    if chunk:
                        f.write(chunk)


def test_platform(version, urlPrefix, nameMod, platform, type, suffix):
    v = version.removeprefix("sapmachine-")
    u = f"{urlPrefix}/sapmachine-{type}_darwin{platform}64/{v}/sapmachine-{type}_darwin{platform}64-{v}{nameMod}.{suffix}"
    f = f"sapmachine-{type}_darwin{platform}64-{v}.{suffix}"
    download_from_artifactory(u, f)
    if suffix == "tar.gz":
        file = tarfile.open(f)
        shutil.rmtree("./destination")
        file.extractall('./destination')
        p = glob.glob("./destination/*/Contents/Home/bin/java")
        if p:
            err = subprocess.run([p[0], "-version"],
                                 capture_output=True, text=True).stderr
            pattern = re.compile(r'openjdk (version ")?(?P<version>[\.\d]+)')
            print("java -version output:", err.replace('\n', '\\n'))
            m = pattern.match(err)
            assert m and m.group('version'), 'could not extract version from line: '+err


parser = argparse.ArgumentParser()
parser.add_argument('--urlPrefix', '-u', help='The prefix of the url from where to download the artifacts',
                    metavar='PREFIX', default=os.getenv("BINARY_SOURCE") or "https://common.repositories.cloud.sap/artifactory/naas-deploy-releases-notarization/com/sap/sapmachine")
parser.add_argument('--versions', '-v', help='The version of sapmachine to be inspected. Should start with "sapmachine-"',
                    metavar='VERSIONS', action='append', nargs='*', default=[os.getenv("SAPMACHINE_VERSION")])
parser.add_argument('--platform', '-p', help='The platform to be tested. Could be "intel" and/or "aarch"',
                    metavar='PLATFORM', nargs='*', default=['intel', 'aarch'])
parser.add_argument('--type', '-t', help='The type of the package. Could be "jdk" and/or "jre"',
                    metavar='TYPE', nargs='*', default=['jdk', 'jre'])
parser.add_argument('--nameMod', '-n', help='The urls of the artifacts to be downloaded may have a specific suffix just before filename extension. E.g. a suffix of "-notarized" will lead to urls like "http://..sapmachine-jdk_darwinintel64-20-notarized.tar.gz"',
                    metavar='NAMEMOD', default="-notarized")
parser.add_argument('--suffix', '-s', help='The suffix of the downloaded artefacts. Could be "tar.gz" and/or "dmg"',
                    metavar='SUFFIX', nargs='*', default=['tar.gz', 'dmg'])
args = parser.parse_args()

for version in args.versions:
    for platform in args.platform:
        for type in args.type:
            for suffix in args.suffix:
                version and test_platform(version[0], args.urlPrefix, args.nameMod,
                              platform, type, suffix)
