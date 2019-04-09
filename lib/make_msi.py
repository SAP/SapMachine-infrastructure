'''
Copyright (c) 2001-2019 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import re
import utils
import yaml
import uuid
import glob
import shutil
import argparse

from os.path import join
from string import Template

def prepare(work_dir, tag, major):
    utils.remove_if_exists(work_dir)
    os.makedirs(work_dir)
    download_jdk(work_dir, tag)
    utils.git_clone('github.com/SAP/SapMachine.git', 'sapmachine' + major, join(work_dir, 'sapmachine_git'))

def create_sapmachine_wxs(template, target, product_id, upgrade_code, version, major):
    sapmachine_wxs_content = None

    with open(template, 'r') as sapmachine_wxs_template:
        sapmachine_wxs_content = Template(sapmachine_wxs_template.read()).substitute(
            PRODUCT_ID=product_id,
            UPGRADE_CODE=upgrade_code,
            VERSION=version,
            MAJOR=major
        )

    with open(target, 'w') as sapmachine_wxs:
        sapmachine_wxs.write(sapmachine_wxs_content)

def download_jdk(target, tag):
    releases = utils.github_api_request('releases', per_page=100)

    for release in releases:
        if release['name'] == tag:
            for asset in release['assets']:
                if 'windows-x64_bin' in asset['name'] and asset['name'].endswith('.zip'):
                    utils.download_artifact(asset['browser_download_url'], join(target, 'sapmachine.zip'))
                    utils.extract_archive(join(target, 'sapmachine.zip'), target)
                    sapmachine_folder = glob.glob(join(target, 'sapmachine*'))
                    os.rename(sapmachine_folder[0], join(target, 'SourceDir'))
                    return

def write_as_rtf(source, target):
    with open(source, 'r') as fin:
        lines = fin.readlines()

        with open(target, 'w') as fout:
            fout.write('{\\rtf1\\ansi\\ansicpg1252\\deff0\\nouicompat\\deflang1033{\\fonttbl{\\f0\\fnil\\fcharset0 Consolas;}}\r\n')
            fout.write('{\\*\\SapMachine Generator}\\viewkind4\\uc1\r\n')
            fout.write('\\pard\\sl240\\slmult1\\f0\\fs16\\lang7 ')

            for line in lines:
                fout.write(line.rstrip())
                fout.write('\\par\r\n')

            fout.write('}\r\n')

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tag', help='the tag to create the msi installer from', metavar='TAG', required=True)
    parser.add_argument('-d', '--templates-directory', help='specify the templates directory', metavar='DIR', required=True)
    args = parser.parse_args()

    templates_dir = os.path.realpath(args.templates_directory)
    cwd = os.getcwd()
    work_dir = join(cwd, 'msi_work')
    tag = args.tag
    products = None
    product_id = None
    upgrade_code = None

    version, version_part, major, build_number, sap_build_number, os_ext = utils.sapmachine_tag_components(tag)
    sapmachine_version = [e for e in version_part.split('.')]

    if len(sapmachine_version) < 3:
        sapmachine_version += ['0' for sapmachine_version in range(0, 3 - len(sapmachine_version))]

    sapmachine_version = '.'.join(sapmachine_version)

    prepare(work_dir, tag, major)

    shutil.copyfile(
        join(work_dir, 'sapmachine_git', 'src', 'java.base', 'windows', 'native', 'launcher', 'icons', 'awt.ico'),
        join(work_dir, 'sapmachine.ico')
    )
    write_as_rtf(join(work_dir, 'sapmachine_git', 'LICENSE'), join(work_dir, 'license.rtf'))

    with open(join(templates_dir, 'products.yml'), 'r') as products_yml:
        products = yaml.safe_load(products_yml.read())

    if major not in products:
        product_id = str(uuid.uuid4())
        upgrade_code = str(uuid.uuid4())
        products[major] = { 'product_id': product_id, 'upgrade_code': upgrade_code }

        with open(join(templates_dir, 'products.yml'), 'w') as products_yml:
            products_yml.write(yaml.dump(products, default_flow_style=False))

        utils.git_commit(templates_dir, 'Updated product codes.', ['products.yml'])
        utils.git_push(templates_dir)
    else:
        product_id = products[major]['product_id']
        upgrade_code = products[major]['upgrade_code']

    create_sapmachine_wxs(
        join(templates_dir, 'SapMachine.wxs.template'),
        join(work_dir, 'SapMachine.wxs'),
        product_id,
        upgrade_code,
        sapmachine_version,
        major
    )
    
    shutil.copyfile(join(work_dir, 'SourceDir', 'release'), join(work_dir, 'release'))

    utils.run_cmd('heat dir SourceDir -swall -srd -gg -platform x64 -template:module -cg SapMachineGroup -out SapMachineModule.wxs'.split(' '), cwd=work_dir)

    with open(join(work_dir, 'SapMachineModule.wxs'), 'r+') as sapmachine_module:
        sapmachine_module_content = sapmachine_module.read()
        sapmachine_module_content = sapmachine_module_content.replace('PUT-MODULE-NAME-HERE', 'SapMachineModule')
        sapmachine_module_content = sapmachine_module_content.replace('PUT-COMPANY-NAME-HERE', 'SapMachine Team')
        sapmachine_module.seek(0)
        sapmachine_module.truncate()
        sapmachine_module.write(sapmachine_module_content)

    utils.run_cmd('candle -arch x64 SapMachineModule.wxs'.split(' '), cwd=work_dir)
    utils.run_cmd('light SapMachineModule.wixobj'.split(' '), cwd=work_dir)
    utils.run_cmd('candle -arch x64 SapMachine.wxs'.split(' '), cwd=work_dir)
    utils.run_cmd('light -ext WixUIExtension SapMachine.wixobj'.split(' '), cwd=work_dir)

    os.rename(join(work_dir, 'SapMachine.msi'), join(cwd, str.format('SapMachine-{0}.msi', sapmachine_version)))

    return 0

if __name__ == "__main__":
    sys.exit(main())