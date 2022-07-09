'''
Copyright (c) 2018-2022 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import re
import sys
import utils

# This class represents a JMC repository tag.
# It could be both, a SapMachine or an OpenJDK JMC tag.
class JMCTag:
    # This method returns a tag instance from a string
    # Could be None, if it does not conform to the format
    @staticmethod
    def from_string(string):
        tag = JDKJMCTag.from_string(string)
        if tag is not None:
            return tag
        return SapJMCTag.from_string(string)

    # This method creates a list of 3 ints, representing the
    # JMC version from the dotted String representation
    @staticmethod
    def calc_version(version_string):
        version = list(map(int, version_string.split('.')))
        version.extend([0 for i in range(3 - len(version))])
        return version

    # the tag as string
    def as_string(self):
        return self.tag

    # true if it is a JDK tag, false otherwise
    def is_jdk_tag(self):
        return self.__class__.__name__ == 'JDKJMCTag'

    # true if it is a SapMachine tag, false otherwise
    def is_sap_tag(self):
        return self.__class__.__name__ == 'SapJMCTag'

    # returns the version as string
    def get_version_string(self):
        return self.version_string

    # returns the version as list of int
    def get_version(self):
        return self.version

    # returns the major part of the version as int, e.g. the first value.
    def get_major(self):
        return self.version[0]

    # returns the minor part of the version as int, e.g. the second value.
    def get_minor(self):
        return self.version[1]

    # returns the update part of the version as int, e.g. the third value.
    def get_update(self):
        return self.version[2]

    # True if this is a GA tag.
    def is_ga(self):
        return self.ga

    # Prints the tag details, can be used for debugging
    def print_details(self, indent = ''):
        print(str.format('{0}{1}: {2}', indent, self.__class__.__name__, self.as_string()))
        print(str.format('{0}  version string: {1}', indent, self.get_version_string()))
        print(str.format('{0}  major         : {1}', indent, self.get_major()))
        print(str.format('{0}  minor         : {1}', indent, self.get_minor()))
        print(str.format('{0}  update        : {1}', indent, self.get_update()))
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

        return False

    # Creates a new tag Object of the same type (e.g. JDK or SapMachine) from the match value.
    def get_new_tag_of_same_type(self, match):
        if self.__class__ == JDKJMCTag:
            return JDKJMCTag(match)
        elif self.__class__ == SapJMCTag:
            return SapJMCTag(match)
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

# Implementation of JDK JMC tag. Examples:
# 8.2.0-ga
# 8.2.0-rc
class JDKJMCTag(JMCTag):
    tag_pattern = re.compile('(\d+\.\d+\.\d+)(-ga|-rc)$')

    @staticmethod
    def from_string(string):
        match = JDKJMCTag.tag_pattern.match(string)
        if match is not None:
            return JDKJMCTag(match)
        return None

    def __init__(self, match):
        #for i in range(0, (len(match.groups()) + 1)):
        #    print(str.format("{0}. group: {1}", i, match.group(i)))

        self.tag = match.group(0)
        self.version_string = match.group(1)
        self.version = JMCTag.calc_version(self.version_string)
        self.ga = match.group(2) == '-ga'

    def as_sap_tag_string(self):
        return str.format('{0}{1}-sap', self.version_string, '-ga' if self.ga else '-rc')

# Implementation of SAP JMC Tag. Examples:
# 8.2.0-ga-sap
# 8.2.0-rc-sap
class SapJMCTag(JMCTag):
    tag_pattern = re.compile('(\d+\.\d+\.\d+)(-ga|-rc)-sap$')

    @staticmethod
    def from_string(string):
        match = SapJMCTag.tag_pattern.match(string)
        if match is not None:
            return SapJMCTag(match)
        return None

    def __init__(self, match):
        #for i in range(0, (len(match.groups()) + 1)):
        #    print(str.format("{0}. group: {1}", i, match.group(i)))

        self.tag = match.group(0)
        self.version_string = match.group(1)
        self.version = JMCTag.calc_version(self.version_string)
        self.ga = match.group(2) == '-ga'
