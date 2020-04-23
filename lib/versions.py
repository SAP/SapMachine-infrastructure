'''
Copyright (c) 2001-2020 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import re
import sys
import utils

# This class represents a repository tag.
# It could be both, a SapMachine or a JDK tag.
class Tag:
    # This method returns a tag instance from a string
    # Could be None, if it does not conform to the format
    @staticmethod
    def from_string(string):
        tag = JDKTag.from_string(string)
        if tag is not None:
            return tag
        return SapMachineTag.from_string(string)

    # This method creates a list of 5 ints, representing the
    # JDK version from the dotted String representation
    @staticmethod
    def calc_version(version_string):
        version = list(map(int, version_string.split('.')))
        version.extend([0 for i in range(5 - len(version))])
        return version

    # the tag as string
    def as_string(self):
        return self.tag

    # true if it is a JDK tag, false otherwise
    def is_jdk_tag(self):
        return self.__class__.__name__ == 'JDKTag'

    # true if it is a SapMachine tag, false otherwise
    def is_sapmachine_tag(self):
        return self.__class__.__name__ == 'SapMachineTag'

    # returns the version as string
    def get_version_string(self):
        return self.version_string

    # returns the version as list of int
    def get_version(self):
        return self.version

    # returns the major part of the version as int, e.g. the first value.
    def get_major(self):
        return self.version[0]

    # returns the update part of the version as int, e.g. the third value.
    def get_update(self):
        return self.version[2]

    # returns the vendor(SAP) specific part of the version, e.g. the fifth value. Could be None.
    def get_version_sap(self):
        if self.version[4] > 0:
            return self.version[4]
        else:
            return None

    # returns the build number as int.
    def get_build_number(self):
        return self.build_number

    # True if this is a GA tag.
    def is_ga(self):
        return self.ga

    # Prints the tag details, can be used for debugging
    def print_details(self, indent = ''):
        print(str.format('{0}{1}: {2}', indent, self.__class__.__name__, self.as_string()))
        print(str.format('{0}  version string: {1}', indent, self.get_version_string()))
        print(str.format('{0}  major         : {1}', indent, self.get_major()))
        print(str.format('{0}  update        : {1}', indent, self.get_update()))
        print(str.format('{0}  version_sap   : {1}', indent, self.get_version_sap()))
        print(str.format('{0}  build number  : {1}', indent, self.get_build_number()))
        print(str.format('{0}  ga            : {1}', indent, self.is_ga()))

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

    # Creates a new tag Object of the same type (e.g. JDK or SapMachine) from the match value.
    def get_new_tag_of_same_type(self, match):
        if self.__class__ == JDKTag:
            return JDKTag(match)
        elif self.__class__ == SapMachineTag:
            return SapMachineTag(match)
        else:
            return None

    # Find the latest non GA tag (if this tag is GA). It returns itself, if it isn't a GA tag.
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

# Implementation of JDK tag. Examples:
# jdk-12.0.2+8
# jdk-12.0.2-ga
# jdk-12+7
class JDKTag(Tag):
    tag_pattern = re.compile('jdk-((\d+(\.\d+)*)(\+(\d+))?)(-ga)?$')

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
        self.version_string_without_build = match.group(2)
        self.version = Tag.calc_version(self.version_string_without_build)
        self.build_number = match.group(5)
        if (self.build_number) is not None:
            self.build_number = int(self.build_number)
        self.ga = match.group(6) == '-ga'

    def as_sapmachine_tag_string(self):
        return str.format('sapmachine-{0}', self.version_string_without_build if self.ga else self.version_string)

# Implementation of SapMachine Tag. Examples:
# sapmachine-14+9
# sapmachine-14.0.1+1
# sapmachine-13.0.1
# sapmachine-11+4-0-alpine
#
# Basic pattern support for indicating the SAP version with a -nn appendix and an OS tag like -alpine
# is only kept for compatibility. It is not used any more. If we find a Sap Version of -nn, a possible
# 5th digit in the verison part takes precedence.
class SapMachineTag(Tag):
    tag_pattern = re.compile('sapmachine-((\d+(\.\d+)*)(\+(\d+))?)(-(\d+))?(\-(\S+))?$')

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
        self.version = Tag.calc_version(match.group(2))
        self.build_number = match.group(5)
        if self.build_number is None:
            self.ga = True
        else:
            self.build_number = int(self.build_number)
            self.ga = False

        # That part is to support some legacy tags.
        # We had tags where we appended the SapMachine version to the tag.
        # E.g. sapmachine-10.0.2+13-0
        # But we only use the 5th digit in the java.version scheme nowadays.
        # So self.version_string will be normalized to the new representation.
        if self.version[4] == 0 and len(match.groups()) >= 7:
            version_sap = match.group(7)
            if version_sap is not None:
                self.version[4] = int(version_sap)
                self.version_string = ".".join(list(map(str, self.version)))
                if self.build_number is not None:
                    self.version_string += "+" + str(self.build_number)
