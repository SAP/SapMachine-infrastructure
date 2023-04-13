'''
Copyright (c) 2023 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import argparse
import os
import requests
import sys

prefix = os.getenv("DOWNLOAD_URL_PREFIX")
symbols_prefix = os.getenv("DOWNLOAD_SYMBOLS_URL_PREFIX")
version = (os.getenv("SAPMACHINE_VERSION")).removeprefix("sapmachine-")
chunk_size = 4096

def download_from_artifactory(url, filename):
    print(f"Downloading {url} to file {filename}")
    with requests.get(url, auth=(os.getenv("ARTIFACTORY_USER"), os.getenv("ARTIFACTORY_PWD")), stream=True) as r:
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size):
                if chunk:
                    f.write(chunk)

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--platform', help='The platform of the artifacts', metavar='PLATFORM')
    args = parser.parse_args()

    for type in ["jre", "jdk"]:
        for suffix in ["tar.gz", "dmg"]:
            url = f"{prefix}/sapmachine-{type}_darwin{args.platform}64/{version}/sapmachine-{type}_darwin{args.platform}64-{version}-notarized.{suffix}"
            dsuffix = "TGZ" if (suffix == "tar.gz") else "DMG"
            filename = f"{args.platform.upper()}_{type.upper()}_{dsuffix}"
            download_from_artifactory(url, filename)
    url = f"{symbols_prefix}/sapmachine-symbols_darwin{args.platform}64/{version}/sapmachine-symbols_darwin{args.platform}64-{version}.tar.gz"
    filename = f"{args.platform.upper()}_SYMBOLS"
    download_from_artifactory(url, filename)
    return 0

if __name__ == "__main__":
    sys.exit(main())
