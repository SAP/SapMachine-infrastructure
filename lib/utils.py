'''
Copyright (c) 2001-2017 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import shutil
import zipfile
import tarfile

from os import remove
from os.path import join
from os.path import exists
from shutil import rmtree
from shutil import move

def run_cmd(cmdline, throw=True, cwd=None, env=None, std=False, shell=False):
    import subprocess

    print str.format('calling {0}', cmdline)
    if std:
        subproc = subprocess.Popen(cmdline, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
        out, err = subproc.communicate()
    else:
        subproc = subprocess.Popen(cmdline, cwd=cwd, env=env, shell=shell)
    retcode = subproc.wait()
    if throw and retcode != 0:
        raise Exception(str.format('command failed with exit code {0}: {1}', retcode, cmdline))
    if std:
        return (retcode, out, err)
    return retcode

def extract_archive(archive, target):
    if archive.endswith('.zip'):
        with zipfile.ZipFile(archive, 'r') as zip_ref:
            print(str.format('Extracting zip archive {0} ...', archive))
            zip_ref.extractall(target)

        remove(archive)
    elif archive.endswith('tar.gz'):
        print(str.format('Extracting tar.gz archive {0} ...', archive))
        with tarfile.open(archive, 'r') as tar_ref:
            tar_ref.extractall(target)

        remove(archive)
    else:
        move(archive, target)

def download_artifact(url, target):
    import urllib

    if exists(target):
        remove(target)

    with open(target,'wb') as file:
        print(str.format('Downloading {0} ...', url))
        file.write(urllib.urlopen(url, proxies={}).read())

def make_tgz_archive(src, dest):
    if exists(dest):
        remove(dest)

    archive = tarfile.open(dest, "w:gz", compresslevel=9)
    archive.add(src)
    archive.close()

def make_zip_archive(src, dest, top_dir):
    if exists(dest):
        rmtree(top_dir)

    zip = zipfile.ZipFile(dest, 'w')

    for root, dirs, files in os.walk(src):
        for file in files:
            zip.write(join(root, file),
                      join(top_dir, os.path.relpath(join(root, file), src)),
                      zipfile.ZIP_DEFLATED)
    zip.close()

def which(file):
    for path in os.environ['PATH'].split(os.pathsep):
        if exists(join(path, file)):
                return join(path, file)

    return None
