import os
import sys
import shutil
import re
import zipfile
import tarfile

jtharness_repo = 'http://hg.openjdk.java.net/code-tools/jtharness'
jtharness_dependencies = [
    ['https://github.com/glub/secureftp/raw/master/contrib/javahelp2_0_05.zip', 'javahelp2_0_05.zip'],
    ['http://repo1.maven.org/maven2/junit/junit/4.4/junit-4.4.jar', 'junit-4.4.jar'],
    ['http://www.java2s.com/Code/JarDownload/comm/comm-2.0.jar.zip', 'comm-2.0.jar.zip'],
    ['http://www.java2s.com/Code/JarDownload/servlet/servlet-api.jar.zip', 'servlet-api.jar.zip'],
    ['http://www.java2s.com/Code/JarDownload/asm/asm-3.1.jar.zip', 'asm-3.1.jar.zip'],
    ['http://www.java2s.com/Code/JarDownload/asm/asm-commons-3.1.jar.zip', 'asm-commons-3.1.jar.zip']
]
jtharness_version = '5.0'

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

    if os.path.exists(target):
        os.remove(target)

    with open(target,'wb') as file:
        print(str.format('Downloading {0} ...', url))
        file.write(urllib.urlopen(url, proxies={}).read())

def extract_archive(archive, target):
    if archive.endswith('.zip'):
        with zipfile.ZipFile(archive, 'r') as zip_ref:
            print(str.format('Extracting zip archive {0} ...', archive))
            zip_ref.extractall(target)

        os.remove(archive)
    elif archive.endswith('tar.gz'):
        print(str.format('Extracting tar.gz archive {0} ...', archive))
        with tarfile.open(archive, 'r') as tar_ref:
            tar_ref.extractall(target)

        os.remove(archive)
    else:
        shutil.move(archive, target)

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
    if os.path.exists(dest):
        os.remove(dest)

    archive = tarfile.open(dest, "w:gz", compresslevel=9)
    archive.add(src)
    archive.close()

def make_zip_archive(src, dest, top_dir):
    if os.path.exists(dest):
        os.remove(dest)

    zip = zipfile.ZipFile(dest, 'w')

    for root, dirs, files in os.walk(src):
        for file in files:
            zip.write(os.path.join(root, file),
                      os.path.join(top_dir, os.path.relpath(os.path.join(root, file), src)),
                      zipfile.ZIP_DEFLATED)
    zip.close()

def build_jtharness(target):
    global jtharness_version

    if os.path.exists('jtharness'):
        shutil.rmtree('jtharness')

    # clone the jtharness mercurial repository
    hg_clone(jtharness_repo)

    os.chdir('jtharness')

    # find the latest tag
    latest_tag = get_latest_hg_tag('jt')
    print(str.format('Using jtharness tag {0}', latest_tag))
    hg_switch_tag(latest_tag)

    jtharness_version = latest_tag[2:]
    build_dir = 'build'

    # download and extract dependencies
    for jtharness_dependecy in jtharness_dependencies:
        download_artifact(jtharness_dependecy[0], jtharness_dependecy[1])
        extract_archive(jtharness_dependecy[1], build_dir)

    shutil.move(os.path.join('build', 'jh2.0', 'javahelp', 'lib', 'jhall.jar'), build_dir)
    shutil.move(os.path.join('build', 'jh2.0', 'javahelp', 'lib', 'jh.jar'), build_dir)

    cwd = os.getcwd()
    os.chdir('build')

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

    os.chdir(cwd)

    # copy the archive
    shutil.copy(os.path.join('JTHarness-build', 'bundles', str.format('jtharness-{0}.zip', jtharness_version)),
                os.path.join(target, 'jtharness.zip'))

def build_asmtools(target):
    if os.path.exists('asmtools'):
        shutil.rmtree('asmtools')

    # clone the asmtools mercurial repository
    hg_clone(asmtools_repo)

    cwd = os.getcwd()
    os.chdir('asmtools')

    # find the latest tag
    latest_tag = get_latest_hg_tag('')
    print(str.format('Using asmtools tag {0}', latest_tag))
    hg_switch_tag(latest_tag)

    os.chdir('build')

    asmtools_pseudo_version = latest_tag
    with open('build.properties', 'r') as build_properties:
        lines = build_properties.readlines()
        pattern = re.compile('.*BUILD_DIR.*=.*asmtools-([0-9]+\.[0-9])+-build.*')
        for line in lines:
            match = pattern.match(line)
            if match is not None:
                asmtools_pseudo_version = match.group(1)

    # run the ant build
    run_cmd(['ant', 'build'])

    os.chdir(cwd)
    shutil.copy(os.path.join(str.format('asmtools-{0}-build', asmtools_pseudo_version), 'binaries', 'lib', 'asmtools.jar'),
                target)

def build_jtreg(target):
    if os.path.exists('jtreg'):
        shutil.rmtree('jtreg')

    # clone the jtreg mercurial repository
    hg_clone(jtreg_repo)

    cwd = os.getcwd()

    os.chdir('jtreg')
    dependencies_dir = 'dependencies'
    os.mkdir(dependencies_dir)

    # find the latest tag
    latest_tag = get_latest_hg_tag('jtreg')
    print(str.format('Using jtreg tag {0}', latest_tag))
    hg_switch_tag(latest_tag)

    # download and extract dependencies
    for jtreg_dependecy in jtreg_dependencies:
        download_artifact(jtreg_dependecy[0], jtreg_dependecy[1])
        extract_archive(jtreg_dependecy[1], dependencies_dir)

    shutil.copy(os.path.join(dependencies_dir, 'jh2.0', 'javahelp', 'lib', 'jh.jar'), dependencies_dir)
    shutil.copy(os.path.join(dependencies_dir, 'jh2.0', 'javahelp', 'lib', 'jhall.jar'), dependencies_dir)
    extract_archive(os.path.join(cwd, 'jtharness.zip'), dependencies_dir)
    shutil.copy(os.path.join(cwd, 'asmtools.jar'), dependencies_dir)
    shutil.copytree(os.path.join(dependencies_dir, 'JCOV_BUILD', 'jcov_2.0'), os.path.join(dependencies_dir, 'jcov'))

    run_cmd(['ant', '-v', '-f', 'make/build.xml',
             '-Djunit.jar=' + os.path.join(dependencies_dir, 'junit.jar'),
             '-Dtestng.jar=' + os.path.join(dependencies_dir, 'testng.jar'),
             '-Djcommander.jar=' + os.path.join(dependencies_dir, 'jcommander.jar'),
             '-Djavatest.home=' + os.path.join(dependencies_dir,'jtharness-' + jtharness_version),
             '-Djavatest.jar=' + os.path.join(dependencies_dir, 'jtharness-' + jtharness_version, 'lib', 'javatest.jar'),
             '-Djavahelp.home=' + os.path.join(dependencies_dir, 'jh2.0'),
             '-Djhall.jar=' + os.path.join(dependencies_dir, 'jh2.0', 'javahelp', 'lib', 'jhall.jar'),
             '-Djh.jar=' + os.path.join(dependencies_dir, 'jh2.0', 'javahelp', 'lib', 'jh.jar'),
             '-Djcov.home=' + os.path.join(dependencies_dir, 'jcov')])

    # shutil.copy(os.path.join('dist', 'jtreg.zip'), target)
    shutil.copy(os.path.join(dependencies_dir, 'asmtools.jar'), os.path.join('dist', 'jtreg', 'lib'))
    shutil.copy(os.path.join(dependencies_dir, 'jcommander-1.48.jar'), os.path.join('dist', 'jtreg', 'lib'))
    make_zip_archive(os.path.join('dist', 'jtreg'), os.path.join(target, 'jtreg.zip'), 'jtreg')



def main(argv=None):
    cwd = os.getcwd()
    build_jtharness(cwd)
    os.chdir(cwd)
    build_asmtools(cwd)
    os.chdir(cwd)
    build_jtreg(cwd)

if __name__ == "__main__":
    sys.exit(main())

