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

org = 'SAP'
repository = 'SapMachine'

commit_message_pattern_sapmachine = '^SapMachine #([0-9]+):\s(.+)(([\n|\r\n].*)*)$'
commit_message_pattern_openjdk = '^([0-9]+):\s(.+)(([\n|\r\n].*)*)$'
pull_request_description_pattern = '^((.*[\n|\r\n])+)[\n|\r\n]fixes #([0-9]+)\s*$'

pr_author_exception_list = [ 'SapMachine' ]

# request to github api
def api_request(url, data=None, method='GET'):
    token = utils.get_github_api_accesstoken()
    request = Request(url, data=data)
    request.get_method = lambda: method
    
    if token is not None:
        request.add_header('Authorization', str.format('token {0}', token))

    try:
        response = json.loads(urlopen(request).read())
        return response
    except:
        return None

# validate an issue by issue id
def validate_issue(issue_id):
    issues_api = str.format('https://api.github.com/repos/{0}/{1}/issues/{2}', org, repository, issue_id)
    issue = api_request(issues_api)

    # check whether the issue exists
    if issue is None:
        raise Exception(str.format('No issue with id #{0} found.'), issue_id)

    # check whether the issue is in state "open"
    if issue['state'] != 'open':
        raise Exception(str.format('The issue #{0} is in state "{1}", but the expected state is "open".', issue_id, issue['state']))

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
    message = str.format('Hello @{0}, I\'m sorry, {1}', pr_author, message)
    message = str.format('{{ "body": "{0}" }}', message.replace('"', '\\"'))
    return message

def create_success_comment(pr_author):
    message = str.format('Hello @{0}, this pull request fulfills all formal requirements.', pr_author)
    message = str.format('{{ "body": "{0}" }}', message.replace('"', '\\"'))
    return message

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pull-request', help='the Pull Request number', metavar='NUMBER', required=True)
    args = parser.parse_args()

    pull_request_id = args.pull_request

    # request the pull request information
    pull_request_api = str.format('https://api.github.com/repos/{0}/{1}/pulls/{2}', org, repository, pull_request_id)
    pull_request = api_request(pull_request_api)
    
    comments_url = pull_request['comments_url']
    pr_author = pull_request['user']['login']

    # if the author is in the exception list, the validation is skipped
    if pr_author in pr_author_exception_list:
        return 0

    # validate the pull request body (description)
    try:
        validate_pull_request(pull_request['body'])
    except Exception as error:
        message = create_failure_comment(pr_author, str.format('this pull request doesn\'t meet the expectations. {0}', error))
        api_request(comments_url, data=message, method='POST')
        return 1

    # all formal requirements are met
    api_request(comments_url, data=create_success_comment(pr_author), method='POST')

    return 0

if __name__ == "__main__":
    sys.exit(main())
