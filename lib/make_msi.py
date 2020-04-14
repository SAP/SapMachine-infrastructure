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
    parser.add_argument('-a', '--asset', help='the SapMachine asset file', metavar='ASSET', required=True)
    parser.add_argument('-j', '--jre', help='Build SapMachine JRE installer', action='store_true', default=False)
    parser.add_argument('-s', '--sapmachine-directory', help='specify the SapMachine GIT directory', metavar='DIR', required=True)
    args = parser.parse_args()

    cwd = os.getcwd()
    work_dir = join(cwd, 'msi_work')
    asset = os.path.realpath(args.asset)
    is_jre = args.jre
    sapmachine_git_dir = args.sapmachine_directory
    products = None
    product_id = None
    upgrade_code = None

    utils.remove_if_exists(work_dir)
    os.makedirs(work_dir)

    utils.extract_archive(asset, work_dir, remove_archive=False)
    sapmachine_folder = glob.glob(join(work_dir, 'sapmachine*'))
    os.rename(sapmachine_folder[0], join(work_dir, 'SourceDir'))

    _, _, version_output = utils.run_cmd([join(work_dir, 'SourceDir', 'bin', 'java.exe'), '-version'], std=True)

    version, version_part, major, version_sap, build_number = utils.sapmachine_version_components(version_output, multiline=True)
    sapmachine_version = [e for e in version_part.split('.')]

    if len(sapmachine_version) < 3:
        sapmachine_version += ['0' for sapmachine_version in range(0, 3 - len(sapmachine_version))]

    if len(sapmachine_version) == 4:
        sapmachine_version[3] = str((int(sapmachine_version[3]) < 8) & 0xFF00)

    if len(sapmachine_version) == 5:
        merged_version = str((int(sapmachine_version[3]) < 8) | (int(sapmachine_version[4]) & 0xFF))

        del sapmachine_version[4]
        sapmachine_version[3] = merged_version

    sapmachine_version = '.'.join(sapmachine_version)

    shutil.copyfile(
        join(sapmachine_git_dir, 'src', 'java.base', 'windows', 'native', 'launcher', 'icons', 'awt.ico'),
        join(work_dir, 'sapmachine.ico')
    )
    write_as_rtf(join(sapmachine_git_dir, 'LICENSE'), join(work_dir, 'license.rtf'))

    infrastructure_dir = join(work_dir, 'sapmachine_infrastructure')
    templates_dir = join(infrastructure_dir, 'wix-templates')
    utils.git_clone('github.com/SAP/SapMachine-infrastructure', 'master', infrastructure_dir)

    with open(join(templates_dir, 'products.yml'), 'r') as products_yml:
        products = yaml.safe_load(products_yml.read())

    image_type = 'jre' if is_jre else 'jdk'

    if products[image_type] is None or major not in products[image_type]:
        product_id = str(uuid.uuid4())
        upgrade_code = str(uuid.uuid4())
        if products[image_type] is None:
            products[image_type] = {}
        products[image_type][major] = { 'product_id': product_id, 'upgrade_code': upgrade_code }

        with open(join(templates_dir, 'products.yml'), 'w') as products_yml:
            products_yml.write(yaml.dump(products, default_flow_style=False))

        utils.git_commit(infrastructure_dir, 'Updated product codes.', [join('wix-templates', 'products.yml')])
        utils.git_push(infrastructure_dir)
    else:
        product_id = products[image_type][major]['product_id']
        upgrade_code = products[image_type][major]['upgrade_code']

    create_sapmachine_wxs(
        join(templates_dir, 'SapMachine.jre.wxs.template' if is_jre else 'SapMachine.jdk.wxs.template'),
        join(work_dir, 'SapMachine.wxs'),
        product_id,
        upgrade_code,
        sapmachine_version,
        major
    )

    shutil.copyfile(join(work_dir, 'SourceDir', 'release'), join(work_dir, 'release'))
    utils.remove_if_exists(join(work_dir, 'SourceDir', 'release'))

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

    msi_name = os.path.basename(asset)
    msi_name = os.path.splitext(msi_name)[0]
    os.rename(join(work_dir, 'SapMachine.msi'), join(cwd, str.format('{0}.msi', msi_name)))

    return 0

if __name__ == "__main__":
    sys.exit(main())