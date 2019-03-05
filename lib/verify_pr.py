'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import json
import re
import utils
import argparse

from urllib2 import urlopen, Request, quote
from os.path import join
from utils import github_api_request

org = 'SAP'
repository = 'SapMachine'

commit_message_pattern_sapmachine = '^SapMachine #([0-9]+):\s(.+)(([\n|\r\n].*)*)$'
commit_message_pattern_openjdk = '^([0-9]+):\s(.+)(([\n|\r\n].*)*)$'
pull_request_description_pattern = '^((.*[\n|\r\n])*)fixes #([0-9]+)\s*$'

pr_author_exception_list = [ 'SapMachine' ]

# validate an issue by issue id
def validate_issue(issue_id):
    issue = github_api_request(str.format('issues/{0}', issue_id))

    # check whether the issue exists
    if issue is None:
        raise Exception(str.format('No issue with id #{0} found.'), issue_id)

    return issue

# validate the pull request body
def validate_pull_request(body):
    if not body:
        raise Exception('The pull request description is empty.')

    pattern = re.compile(pull_request_description_pattern)
    match = pattern.match(body)

    if match is None:
        raise Exception('The pull request description has an invalid format.')

    issue_id = match.group(3)
    # check whether the given issue exists
    validate_issue(issue_id)

# validate a commit message
def validate_commit_message(message):
    is_openjdk_commit = False

    if not message:
        raise Exception('The commit message is empty.')

    # first check whether the commit message matches
    # the OpenJDK rules
    pattern = re.compile(commit_message_pattern_openjdk)
    match = pattern.match(message)

    if match is None:
        # no OpenJDK commit message
        # check whether it matches the SapMachine commit message pattern
        pattern = re.compile(commit_message_pattern_sapmachine)
        match = pattern.match(message)

        if match is None:
            raise Exception('The commit message has an invalid format.')

        issue_id = match.group(1)
        issue_title = match.group(2)

        # check whether there is an issue with this id and message
        issue = validate_issue(issue_id)

        # the commit message must contain the issue tope in the first line
        if issue['title'] != issue_title:
            raise Exception(str.format('The commit message doesn\'t contain the issue title "{0}" of #{1}.', issue['title'], issue_id))
    else:
        is_openjdk_commit = True

    return is_openjdk_commit

def create_failure_comment(pr_author, message):
    message = str.format('Hello @{0}, I\'m sorry, {1} Please have a look at {2} .', pr_author, message, 'https://github.com/SAP/SapMachine/wiki/Formal-Requirements-of-Pull-Requests')
    message = str.format('{{ "body": "{0}" }}', message.replace('"', '\\"'))
    return message

def create_success_comment(pr_author):
    message = str.format('Hello @{0}, this pull request fulfills all formal requirements.', pr_author)
    message = str.format('{{ "body": "{0}" }}', message.replace('"', '\\"'))
    return message

def create_request_for_admin_comment(pr_author):
    message = str.format('Hi @{0}. Thanks for your Pull Request. I\'m waiting for a [SapMachine Team member](https://github.com/orgs/SAP/teams/sapmachine-team) to verify that this pull request is ok to test. If it is, they should reply with `retest this please`.', pr_author)
    message = str.format('{{ "body": "{0}" }}', message.replace('"', '\\"'))
    return message

def is_pr_ok_to_test(pull_request):
    if pull_request['author_association'] == 'MEMBER' or pull_request['user']['login'] == 'SapMachine':
        # is a sapmachine-team member or user 'SapMachine'
        # it is OK to test
        return True
    else:
        # not a sapmachine-team member
        # check for a 'retest this please' comment
        # by any sapmachine-team member
        comments = github_api_request(url=pull_request['comments_url'])

        for comment in comments:
            if comment['body'] == 'retest this please' and comment['author_association'] == 'MEMBER':
                return True

    return False

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pull-request', help='the Pull Request number', metavar='NUMBER', required=True)
    args = parser.parse_args()

    pull_request_id = args.pull_request

    # request the pull request information
    pull_request = github_api_request(str.format('pulls/{0}', pull_request_id))

    comments_url = pull_request['comments_url']
    pr_author = pull_request['user']['login']
    user = github_api_request(url=pull_request['user']['url'])

    if not is_pr_ok_to_test(pull_request):
        message = create_request_for_admin_comment(pr_author)
        github_api_request(url=comments_url, data=message, method='POST')
        print(str.format('Pull Request validation failed: "{0}"', message))
        return 0

    # if the author is in the exception list, the validation is skipped
    if pr_author not in pr_author_exception_list:
        # validate the pull request body (description)
        try:
            validate_pull_request(pull_request['body'])
        except Exception as error:
            message = create_failure_comment(pr_author, str.format('this pull request doesn\'t meet the expectations. {0}', error))
            github_api_request(url=comments_url, data=message, method='POST')
            print(str.format('Pull Request validation failed: "{0}"', message))
            return 0

        # all formal requirements are met
        github_api_request(url=comments_url, data=create_success_comment(pr_author), method='POST')

    # check wether the complete validation has to run
    pull_request_files = github_api_request(str.format('pulls/{0}/files', pull_request_id))

    roots_requiring_verification = ['make', 'src', 'test', 'Makefile', 'configure']
    requires_verification = False

    for pr_file in pull_request_files:
        print(str.format('Pull Request changes file: "{0}', pr_file['filename']))
        root = next(part for part in pr_file['filename'].split(os.path.sep) if part)
        if root in roots_requiring_verification:
            requires_verification = True
            break

    if requires_verification:
        print("Pull Request requires further verification.")
        return 1
    else:
        print("Pull Request requires no further verification.")
        return 2

if __name__ == "__main__":
    sys.exit(main())
