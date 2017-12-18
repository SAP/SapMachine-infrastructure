import os
import sys
import shutil
import re
import zipfile
import tarfile
import argparse

from os import remove
from os import mkdir
from os import chdir

from os.path import join
from os.path import realpath
from os.path import dirname
from os.path import basename
from os.path import exists

from shutil import rmtree
from shutil import copytree
from shutil import move
from shutil import copy

jtharness_repo = 'http://hg.openjdk.java.net/code-tools/jtharness'
jtharness_dependencies = [
    ['https://github.com/glub/secureftp/raw/master/contrib/javahelp2_0_05.zip', 'javahelp2_0_05.zip'],
    ['http://repo1.maven.org/maven2/junit/junit/4.4/junit-4.4.jar', 'junit-4.4.jar'],
    ['http://www.java2s.com/Code/JarDownload/comm/comm-2.0.jar.zip', 'comm-2.0.jar.zip'],
    ['http://www.java2s.com/Code/JarDownload/servlet/servlet-api.jar.zip', 'servlet-api.jar.zip'],
    ['http://www.java2s.com/Code/JarDownload/asm/asm-3.1.jar.zip', 'asm-3.1.jar.zip'],
    ['http://www.java2s.com/Code/JarDownload/asm/asm-commons-3.1.jar.zip', 'asm-commons-3.1.jar.zip']
]

asmtools_repo = 'http://hg.openjdk.java.net/code-tools/asmtools'

jtreg_repo = 'http://hg.openjdk.java.net/code-tools/jtreg'
jtreg_dependencies = [
    ['https://github.com/glub/secureftp/raw/master/contrib/javahelp2_0_05.zip', 'javahelp2_0_05.zip'],
    ['http://repo1.maven.org/maven2/junit/junit/4.10/junit-4.10.jar', 'junit.jar'],
    ['http://jcenter.bintray.com/org/testng/testng/6.9.5/testng-6.9.5.jar', 'testng.jar'],
    ['https://ci.adoptopenjdk.net/job/jcov/lastSuccessfulBuild/artifact/jcov-2.0-beta-1.tar.gz', 'jcov-2.0-beta-1.tar.gz'],
    ['http://repo1.maven.org/maven2/com/beust/jcommander/1.48/jcommander-1.48.jar', 'jcommander-1.48.jar']
]

def download_artifact(url, target):
    import urllib

    if exists(target):
        remove(target)

    with open(target,'wb') as file:
        print(str.format('Downloading {0} ...', url))
        file.write(urllib.urlopen(url, proxies={}).read())

def extract_archive(archive, target):
    if archive.endswith('.zip'):
        with zipfile.ZipFile(archive, 'r') as zip_ref:
            print(str.format('Extracting zip archive {0} to {1} ...', archive, target))
            zip_ref.extractall(target)

        remove(archive)
    elif archive.endswith('tar.gz'):
        print(str.format('Extracting tar.gz archive {0} to {1} ...', archive, target))
        with tarfile.open(archive, 'r') as tar_ref:
            tar_ref.extractall(target)

        remove(archive)
    else:
        move(archive, target)

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

def hg_clone(repo, tag='tip'):
    run_cmd(['hg', 'clone', repo, '-r', tag])

def hg_switch_tag(tag):
    run_cmd(cmdline = ['hg', 'up', tag])

def get_latest_hg_tag(prefix=''):
    from distutils.version import StrictVersion

    tags_ret, tags_out, tags_err = run_cmd(['hg', 'tags', '-q'], std=True)
    tags = tags_out.splitlines()

    if len(prefix) > 0:
        tags = [tag[len(prefix):] for tag in tags if prefix and tag.startswith(prefix) and re.match('[0-9]+\.[0-9]', tag[len(prefix):])]
    else:
        tags = [tag for tag in tags if re.match('[0-9]+\.[0-9]', tag)]

    latest_tag = '0.0'

    for tag in tags:
        # if StrictVersion(tag) > StrictVersion(latest_tag):
        if tag > latest_tag:
            latest_tag = tag

    return prefix+latest_tag

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

def build_jtharness(top_dir, tag=None):
    work_dir = join(top_dir, 'jtharness_work')
    hg_dir = join(work_dir, 'jtharness')
    build_dir = join(hg_dir, 'build')

    mkdir(work_dir)
    chdir(work_dir)

    # clone the jtharness mercurial repository
    hg_clone(jtharness_repo)
    chdir(hg_dir)

    if tag is None:
        # find the latest tag
        tag = get_latest_hg_tag('jt')

    hg_switch_tag(tag)
    print(str.format('Using jtharness tag {0}', tag))

    # download and extract dependencies
    for jtharness_dependecy in jtharness_dependencies:
        download_artifact(jtharness_dependecy[0], jtharness_dependecy[1])
        extract_archive(jtharness_dependecy[1], build_dir)

    move(join('build', 'jh2.0', 'javahelp', 'lib', 'jhall.jar'), build_dir)
    move(join('build', 'jh2.0', 'javahelp', 'lib', 'jh.jar'), build_dir)

    chdir(build_dir)

    # create build properties
    build_properties = 'local.properties'

    with open(build_properties, 'w') as properties:
        properties.write('jhalljar = ./build/jhall.jar\n')
        properties.write('jhjar = ./build/jh.jar\n')
        properties.write('jcommjar = ./build/comm.jar\n')
        properties.write('servletjar = ./build/servlet-api.jar\n')
        properties.write('bytecodelib = ./build/asm-3.1.jar:./build/asm-commons-3.1.jar\n')
        properties.write('junitlib = ./build/junit-4.4.jar\n')
        properties.write('BUILD_DIR = ./JTHarness-build\n')

    # run the ant build
    run_cmd(['ant', 'build', '-propertyfile', build_properties, '-Djvmargs="-Xdoclint:none"', '-debug'])

    # copy the archive
    bundles = os.listdir(join(hg_dir, 'JTHarness-build', 'bundles'))
    bundle_pattern = re.compile('jtharness-([0-9]+\.[0-9]+)\.zip')
    for bundle in bundles:
        match = bundle_pattern.match(bundle)

        if match is not None:
            jtharness_version = match.group(1)
            copy(join(hg_dir, 'JTHarness-build', 'bundles', bundle), join(top_dir, 'jtharness.zip'))

    return jtharness_version


def build_asmtools(top_dir, tag=None):
    work_dir = join(top_dir, 'asmtools_work')
    hg_dir = join(work_dir, 'asmtools')
    build_dir = join(hg_dir, 'build')

    mkdir(work_dir)
    chdir(work_dir)

    # clone the asmtools mercurial repository
    hg_clone(asmtools_repo)
    chdir(hg_dir)

    if tag is None:
        # find the latest tag
        tag = get_latest_hg_tag('')

    print(str.format('Using asmtools tag {0}', tag))
    hg_switch_tag(tag)

    chdir(build_dir)

    asmtools_version = tag

    if exists(join(build_dir, 'productinfo.properties')):
        with open('productinfo.properties', 'r') as productinfo_properties:
            lines = productinfo_properties.readlines()
            pattern = re.compile('.*PRODUCT_VERSION.*=.*([0-9]+\.[0-9])+.*')
            for line in lines:
                match = pattern.match(line)
                if match is not None:
                    asmtools_version = match.group(1)
    else:
        with open('build.properties', 'r') as build_properties:
            lines = build_properties.readlines()
            pattern = re.compile('.*BUILD_DIR.*=.*asmtools-([0-9]+\.[0-9])+-build.*')
            for line in lines:
                match = pattern.match(line)
                if match is not None:
                    asmtools_version = match.group(1)

    # run the ant build
    run_cmd(['ant', 'build'])

    # copy the build result
    asmtools_version_string = str.format('asmtools-{0}', asmtools_version)
    copytree(join(work_dir, str.format('{0}-build', asmtools_version_string), 'release'),
                    join(top_dir, 'asmtools-release'))

def build_jtreg(top_dir, jtharness_version, tag=None, build_number=None):
    work_dir = join(top_dir, 'jtreg_work')
    hg_dir = join(work_dir, 'jtreg')
    build_dir = join(hg_dir, 'build')
    dependencies_dir = join(hg_dir, 'dependencies')
    images_dir = join(hg_dir, 'build', 'images')

    mkdir(work_dir)
    chdir(work_dir)

    # clone the jtreg mercurial repository
    hg_clone(jtreg_repo)
    chdir(hg_dir)
    mkdir(dependencies_dir)

    if tag is None:
        # find the latest tag
        tag = get_latest_hg_tag('jtreg')

        if build_number is None:
            build_number = tag.split('-')[1]
    else:
        if build_number is None:
            build_number = 'b01'

    hg_switch_tag(tag)
    print(str.format('Using jtreg tag {0}', tag))

    # download and extract dependencies
    for jtreg_dependecy in jtreg_dependencies:
        download_artifact(jtreg_dependecy[0], jtreg_dependecy[1])
        extract_archive(jtreg_dependecy[1], dependencies_dir)

    # workaround for jtreg.gmk JAVAHELP_JAR rule
    with open('DUMMY.SF', 'w+') as dummy:
        dummy.write('dummy')
    with zipfile.ZipFile(join(dependencies_dir, 'jh2.0', 'javahelp', 'lib', 'jh.jar'), 'a') as java_help:
        java_help.write('DUMMY.SF', join('META-INF', 'DUMMY.SF'))

    extract_archive(join(top_dir, 'jtharness.zip'), dependencies_dir)
    copytree(join(top_dir, 'asmtools-release'), join(dependencies_dir, 'asmtools'))

    # build configuration
    javac = dirname(dirname(realpath(which('javac'))))
    ant = dirname(dirname(realpath(which('ant'))))
    make_build_env = os.environ.copy()
    make_build_env['JDK17HOME']              = javac
    make_build_env['JDK18HOME']              = javac
    make_build_env['JDKHOME']                = javac
    make_build_env['ANTHOME']                = ant
    make_build_env['ASMTOOLS_HOME']          = join(dependencies_dir, 'asmtools')
    make_build_env['JAVAHELP_HOME']          = join(dependencies_dir, 'jh2.0', 'javahelp')
    make_build_env['JTHARNESS_HOME']         = join(dependencies_dir, 'jtharness-' + jtharness_version)
    make_build_env['TESTNG_JAR']             = join(dependencies_dir, 'testng.jar')
    make_build_env['JUNIT_JAR']              = join(dependencies_dir, 'junit.jar')
    make_build_env['JCOV_JAR']               = join(dependencies_dir, 'JCOV_BUILD', 'jcov_2.0', 'jcov.jar')
    make_build_env['JCOV_NETWORK_SAVER_JAR'] = join(dependencies_dir, 'JCOV_BUILD', 'jcov_2.0', 'jcov_network_saver.jar')
    make_build_env['JCOMMANDER_JAR']         = join(dependencies_dir, 'jcommander-1.48.jar')

    # run make
    run_cmd(['make', '-C', 'make', 'BUILD_NUMBER=' + build_number], env=make_build_env)

    # add additional libraries to the archive
    # with zipfile.ZipFile(join(images_dir, 'jtreg.zip'), 'a') as jtreg_archive:
    #    jtreg_archive.write(join(dependencies_dir, 'jcommander-1.48.jar'), join('jtreg', 'lib', 'jcommander.jar'))
    #    jtreg_archive.write(join(dependencies_dir, 'testng.jar'), join('jtreg', 'lib', 'testng.jar'))

    # copy the build result
    copy(join(images_dir, 'jtreg.zip'), top_dir)

def main(argv=None):
    tag = None
    build_number=None

    parser = argparse.ArgumentParser()
    parser.add_argument('--build-tip', help='build tip instead of latest tag', action='store_true', default=False)
    parser.add_argument('--build-number', help='overrides the build number', metavar='BUILD_NUMBER', default=None)
    args = parser.parse_args()

    if args.build_tip is True:
        tag = 'tip'

    build_number = args.build_number

    cwd = os.getcwd()
    work_dir = join(cwd, 'jtreg_build')

    if exists(work_dir):
        rmtree(work_dir)

    mkdir(work_dir)

    jtharness_version = build_jtharness(work_dir, tag=tag)
    build_asmtools(work_dir, tag=tag)
    build_jtreg(work_dir, jtharness_version, tag=tag, build_number=build_number)

    if os.path.isfile(join(cwd, 'jtreg.zip')):
        remove(join(cwd, 'jtreg.zip'))

    move(join(work_dir, 'jtreg.zip'), cwd)
    #rmtree(work_dir)

if __name__ == "__main__":
    sys.exit(main())

