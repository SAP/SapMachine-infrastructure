'''
Copyright (c) 2023 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import requests

prefix = os.getenv("DOWNLOAD_URL_PREFIX")
symbols_prefix = os.getenv("DOWNLOAD_SYMBOLS_URL_PREFIX")
version = (os.getenv("SAPMACHINE_VERSION")).removeprefix("sapmachine-")
chunk_size = 4096

def download_from_artifactory(u, dname):
    print(f"Downloading {u} to file {dname}")
    with requests.get(u, auth=(os.getenv("ARTIFACTORY_USER"), os.getenv("ARTIFACTORY_PWD")), stream=True) as r:
        with open(dname, 'wb') as f:
            for chunk in r.iter_content(chunk_size):
                if chunk:
                    f.write(chunk)


for platform in ["aarch", "intel"]:
    for type in ["jre", "jdk"]:
        for suffix in ["tar.gz", "dmg"]:
            u = f"{prefix}/sapmachine-{type}_darwin{platform}64/{version}/sapmachine-{type}_darwin{platform}64-{version}-notarized.{suffix}"
            dsuffix = "TGZ" if (suffix == "tar.gz") else "DMG"
            f = f"{platform.upper()}_{type.upper()}_{dsuffix}"
            download_from_artifactory(u, f)
    u = f"{symbols_prefix}/sapmachine-symbols_darwin{platform}64/{version}/sapmachine-symbols_darwin{platform}64-{version}.tar.gz"
    f = f"{platform.upper()}_SYMBOLS"
    download_from_artifactory(u, f)
