'''
Copyright (c) 2001-2020 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import re
import sys
import utils

class Tag:
    @staticmethod
    def from_string(string):
        tag = JDKTag.from_string(string)
        if tag is not None:
            return tag
        return SapMachineTag.from_string(string)

    def as_string(self):
        return self.tag

    def is_jdk_tag(self):
        return self.__class__.__name__ == 'JDKTag'

    def is_sapmachine_tag(self):
        return self.__class__.__name__ == 'SapMachineTag'

    def print_details(self, indent = ''):
        print(str.format('{0}{1}: {2}', indent, self.__class__.__name__, self.tag))
        print(str.format('{0}  version string: {1}', indent, self.get_version_string()))
        print(str.format('{0}  major         : {1}', indent, self.get_major()))
        print(str.format('{0}  update        : {1}', indent, self.get_update()))
        print(str.format('{0}  version_sap   : {1}', indent, self.get_version_sap()))
        print(str.format('{0}  build number  : {1}', indent, self.get_build_number()))
        print(str.format('{0}  ga            : {1}', indent, self.is_ga()))

    def get_version_string(self):
        return self.version_string

    def get_major(self):
        return self.version[0]

    def get_update(self):
        return self.version[2]

    def get_version_sap(self):
        if self.version[4] > 0:
            return self.version[4]
        else:
            return None

    def get_build_number(self):
        return self.build_number

    def is_ga(self):
        return self.ga

    def equals(self, other):
        return self.tag == other.tag

    def is_same_update_version(self, other):
        return self.version[:3] == other.version[:3]

    def is_greater_than(self, other):
        if self.version > other.version:
            return True
        elif self.version < other.version:
            return False

        self_build_number = self.build_number if self.build_number is not None else -1
        other_build_number = other.build_number if other.build_number is not None else -1
        if other_build_number > other_build_number:
            return True
        else:
            return False

    def get_new_tag_of_same_type(self, match):
        if self.__class__ == JDKTag:
            return JDKTag(match)
        elif self.__class__ == SapMachineTag:
            return SapMachineTag(match)
        else:
            return None

    def get_latest_non_ga_tag(self):
        if not self.is_ga():
            return self

         # fetch all tags
        tags = utils.get_github_tags()
        if tags is None:
            print(str.format("get latest non ga tag for {0}: no tags found", self.as_string()), file=sys.stderr)
            return None

        # iterate all tags
        latest_non_ga_tag = None
        for tag in tags:
            # filter for matching tags
            match = self.tag_pattern.match(tag['name'])

            if match is not None:
                # found a tag
                t = self.get_new_tag_of_same_type(match)

                if (not t.is_ga() and
                    t.is_same_update_version(self) and
                    not t.is_greater_than(self) and
                    (latest_non_ga_tag is None or t.is_greater_than(latest_non_ga_tag))):
                    latest_non_ga_tag = t

        return latest_non_ga_tag

class JDKTag(Tag):
    tag_pattern = re.compile('jdk-(\d+(\.\d+)*)(\+(\d+))?(-ga)?$')

    @staticmethod
    def from_string(string):
        match = JDKTag.tag_pattern.match(string)
        if match is not None:
            return JDKTag(match)
        return None

    def __init__(self, match):
        #for i in range(0, (len(match.groups()) + 1)):
        #    print(str.format("{0}. group: {1}", i, match.group(i)))

        self.tag = match.group(0)
        self.version_string = match.group(1)
        self.version = list(map(int, self.version_string.split('.')))
        self.version.extend([0 for i in range(5 - len(self.version))])
        self.build_number = match.group(4)
        if (self.build_number) is not None:
            self.build_number = int(self.build_number)
        self.ga = match.group(5) == '-ga'

class SapMachineTag(Tag):
    tag_pattern = re.compile('sapmachine-(\d+(\.\d+)*)(\+(\d+))?(-(\d+))?(\-(\S+))?$')

    @staticmethod
    def from_string(string):
        match = SapMachineTag.tag_pattern.match(string)
        if match is not None:
            return SapMachineTag(match)
        return None

    def __init__(self, match):
        #for i in range(0, (len(match.groups()) + 1)):
        #    print(str.format("{0}. group: {1}", i, match.group(i)))

        self.tag = match.group(0)
        self.version_string = match.group(1)
        self.version = list(map(int, self.version_string.split('.')))
        self.version.extend([0 for i in range(5 - len(self.version))])
        self.build_number = match.group(4)
        if (self.build_number) is None:
            self.ga = True
        else:
            self.build_number = int(self.build_number)
            self.ga = False

        if self.version[4] == 0 and len(match.groups()) >= 6:
            version_sap = match.group(6)
            if version_sap is not None:
                self.version[4] = int(version_sap)
