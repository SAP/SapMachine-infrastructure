'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import xml.etree.ElementTree as ET

from os.path import join

def main(argv=None):
    src_dir = os.path.realpath(argv[0])

    for root, dirs, files in os.walk(src_dir, topdown=True):
        path_elements = os.path.relpath(root, start=src_dir).split(os.path.sep)

        if len(path_elements) > 0:
            if path_elements[0] == 'jobs' and 'builds' in path_elements:
                dirs[:] = []
                files[:] = []
                continue

        for file in files:
            if file == 'config.xml':
                tree = ET.parse(join(root, file))
                root_element = tree.getroot()
                properties_element = root_element.find('properties')

                if properties_element is None:
                    properties_element = ET.Element('properties')
                    root_element.append(properties_element)

                build_discarder_property = properties_element.find('jenkins.model.BuildDiscarderProperty')

                if build_discarder_property is None:
                    build_discarder_property = ET.Element('jenkins.model.BuildDiscarderProperty')
                    properties_element.append(build_discarder_property)

                strategy_property = build_discarder_property.find('strategy')

                if strategy_property is None:
                    strategy_property = ET.Element('strategy')
                    strategy_property.set('class', 'hudson.tasks.LogRotator')
                    build_discarder_property.append(strategy_property)

                days_to_keep_property = strategy_property.find('daysToKeep')
                num_to_keep_property = strategy_property.find('numToKeep')
                artifact_days_to_keep_property = strategy_property.find('artifactDaysToKeep')
                artifact_num_to_keep_property = strategy_property.find('artifactNumToKeep')

                if days_to_keep_property is None:
                    days_to_keep_property = ET.Element('daysToKeep')
                    strategy_property.append(days_to_keep_property)

                if num_to_keep_property is None:
                    num_to_keep_property = ET.Element('numToKeep')
                    strategy_property.append(num_to_keep_property)

                if artifact_days_to_keep_property is None:
                    artifact_days_to_keep_property = ET.Element('artifactDaysToKeep')
                    strategy_property.append(artifact_days_to_keep_property)

                if artifact_num_to_keep_property is None:
                    artifact_num_to_keep_property = ET.Element('artifactNumToKeep')
                    strategy_property.append(artifact_num_to_keep_property)

                days_to_keep_property = '-1'
                num_to_keep_property.text = '10'
                artifact_days_to_keep_property = '-1'
                artifact_num_to_keep_property = '1'

                tree.write(join(root, file))

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
