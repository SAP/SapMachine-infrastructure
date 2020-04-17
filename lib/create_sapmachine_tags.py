'''
Copyright (c) 2001-2019 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''
import argparse
import os
import re
import sys
import utils

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.crumb_requester import CrumbRequester
from os.path import join
from versions import JDKTag

# Some global variables
merge_commit_pattern = re.compile('Merge pull request #\d+ from SAP/pr-jdk-')
git_target_dir = None
pull_requests = None

def run_jenkins_jobs(major, tag):
    print(str.format('starting jenkins jobs for {0}: {1}...', major, tag))

    if 'JENKINS_CREDENTIALS' not in os.environ:
        return

    jenkins_url = 'https://ci.sapmachine.io'
    jenkins_user = os.environ['JENKINS_CREDENTIALS_USR']
    jenkins_password = os.environ['JENKINS_CREDENTIALS_PSW']

    server = Jenkins(jenkins_url, username=jenkins_user, password=jenkins_password,
        requester=CrumbRequester(
            baseurl=jenkins_url,
            username=jenkins_user,
            password=jenkins_password
        )
    )

    server.use_auth_cookie()

    build_jobs = [
        str.format('build-{0}-release-linux_x86_64', major),
        str.format('build-{0}-release-linux_ppc64le', major),
        str.format('build-{0}-release-linux_ppc64', major),
        str.format('build-{0}-release-macos_x86_64', major),
        str.format('build-{0}-release-windows_x86_64', major)
    ]

    job_params = {
        'PUBLISH': 'true' ,
        'RELEASE': 'false',
        'RUN_TESTS': 'true',
        'GIT_TAG_NAME': tag
    }

    for job in build_jobs:
        print(str.format('starting jenkins job "{0}" ...', job))
        server.build_job(job, job_params)

def get_merge_commits():
    global git_target_dir
    _, commit_messages, _ = utils.run_cmd('git log --merges -n 50 --format=%s'.split(' '), cwd=git_target_dir, std=True, throw=False)
    _, commit_ids, _ = utils.run_cmd('git log --merges -n 50 --format=%H'.split(' '), cwd=git_target_dir, std=True, throw=False)

    if commit_messages and commit_ids:
        commit_messages = [commit_message for commit_message in commit_messages.split(os.linesep) if commit_message]
        commit_ids = [commit_id for commit_id in commit_ids.split(os.linesep) if commit_id]

    return list(map(lambda x,y:[x,y],commit_messages,commit_ids))

def create_sapmachine_tag(jdk_tag, commit_id):
    sapmachine_tag_str = jdk_tag.as_sapmachine_tag_string()
    print(str.format('creating tag "{0}"', sapmachine_tag_str))
    global git_target_dir
    utils.run_cmd(str.format('git checkout {0}', commit_id).split(' '), cwd=git_target_dir)
    utils.run_cmd(str.format('git tag {0}', sapmachine_tag_str).split(' '), cwd=git_target_dir)
    utils.run_cmd(str.format('git push origin {0}', sapmachine_tag_str).split(' '), cwd=git_target_dir)

def exists_tag(tag):
    _, tag_exists, _ = utils.run_cmd(str.format('git tag -l {0}', tag).split(' '), cwd=git_target_dir, std=True, throw=False)
    return bool(tag_exists)

def make_sure_last_non_ga_is_tagged(jdk_tag, commit_id):
    latest_non_ga_tag = jdk_tag.get_latest_non_ga_tag()

    if latest_non_ga_tag is not None and not exists_tag(latest_non_ga_tag.as_sapmachine_tag_string()):
        create_sapmachine_tag(latest_non_ga_tag, commit_id)
        run_jenkins_jobs(jdk_tag.get_major(), latest_non_ga_tag.as_sapmachine_tag_string())

def check_for_untagged_ga(jdk_tag, tags_of_merge_commit, merge_commit_id):
    # get the commit to which jdk_tag is pointing to
    global git_target_dir
    _, jdk_tag_commit, _ = utils.run_cmd(str.format('git rev-list -n 1 {0}', jdk_tag.as_string()).split(' '), cwd=git_target_dir, std=True, throw=False)
    if jdk_tag_commit is None:
        print(str.format('no commit found for JDK tag {0}, that should not happen', jdk_tag.as_string()))
        return

    # get all tags associated with the commit
    _, tags_of_jdk_tag_commit, _ = utils.run_cmd(str.format('git tag --contains {0}', jdk_tag_commit.rstrip()).split(' '), cwd=git_target_dir, std=True, throw=False)
    if tags_of_jdk_tag_commit is None:
        print(str.format('no tags found for commit of JDK tag {0}, that should not happen', jdk_tag.as_string()))
        return

    # search for a GA tag that matches jdk_tag's update version
    ga_tag = None
    for tag in tags_of_jdk_tag_commit.splitlines():
        ga_tag = JDKTag.from_string(tag)
        if ga_tag is not None:
            if ga_tag.is_ga() and jdk_tag.is_same_update_version(ga_tag):
                break
            else:
                ga_tag = None

    if not ga_tag is None:
        print(str.format('found GA tag for JDK tag "{0}": {1}', jdk_tag.as_string(), ga_tag.as_string()))
    else:
        print(str.format('no GA tag found for JDK tag "{0}"', jdk_tag.as_string()))
        return

    # check whether this GA tag is already one of the tags of the merge commit
    sapmachine_ga_tag_string = ga_tag.as_sapmachine_tag_string()
    if sapmachine_ga_tag_string in tags_of_merge_commit:
        print(str.format('GA tag {0} already tagged as {1}', ga_tag.as_string(), sapmachine_ga_tag_string))
        return

    # this merge commit is not contained in an existing corresponding sapmachine GA tag.
    # That's weird, but we don't change things now...
    if exists_tag(sapmachine_ga_tag_string):
        print(str.format('GA tag {0} is already tagged as {1} but does not include this merge commit. That could be a problem.',
            ga_tag.as_string(), sapmachine_ga_tag_string))
        return

    # don't create a sapmachine tag if there is already a pull request for this tag
    pull_request_title = str.format('Merge to tag {0}', ga_tag.as_string())
    pull_request_exits = False
    global pull_requests
    if pull_requests is None:
        pull_requests = utils.github_api_request('pulls', per_page=100, url_parameter=['state=all'])
    for pull_request in pull_requests:
        if pull_request['title'] == pull_request_title:
            pull_request_exits = True
            break
    if pull_request_exits:
        print(str.format('a pull request for GA tag {0} exists', ga_tag.as_string()))
        return

    # create sapmachine tag
    create_sapmachine_tag(ga_tag, merge_commit_id)

    # make sure the last tag before the GA tag has been built
    make_sure_last_non_ga_is_tagged(ga_tag, merge_commit_id)

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', help='the temporary working directory', metavar='DIR', default="tags_work", required=False)
    args = parser.parse_args()

    workdir = os.path.realpath(args.workdir)
    utils.remove_if_exists(workdir)
    os.makedirs(workdir)
    global git_target_dir
    git_target_dir = join(workdir, 'sapmachine')

    # fetch all branches
    sapmachine_branches = utils.get_active_sapmachine_branches()
    if sapmachine_branches is None or len(sapmachine_branches) == 0:
        print("No sapmachine branches found")
        return 0

    # clone the SapMachine repository to the first branch in list
    utils.git_clone('github.com/SAP/SapMachine.git', sapmachine_branches[0][0], git_target_dir)

    # go through all sapmachine branches, find the latest OpenJDK merge commit and make sure it's correctly sapmachine-tagged
    for branch in sapmachine_branches:
        # checkout branch
        utils.run_cmd(str.format('git checkout {0}', branch[0]).split(' '), cwd=git_target_dir)

        # find latest merge commit
        merge_commits = get_merge_commits()
        jdk_tag = None
        for merge_commit in merge_commits:
            if re.search(merge_commit_pattern, merge_commit[0]) is None:
                print(str.format('merge commit "{0}" is no OpenJDK merge', merge_commit[0]))
                continue

            match_jdk_tag = re.search(JDKTag.tag_pattern, merge_commit[0])
            if match_jdk_tag is None:
                print(str.format('merge commit "{0}" does not contain an OpenJDK tag pattern', merge_commit[0]))
                continue

            jdk_tag = JDKTag(match_jdk_tag)
            merge_commit_message = merge_commit[0]
            merge_commit_id = merge_commit[1]
            break

        if jdk_tag is None:
            print(str.format('No merge commits found for branch "{0}"', branch[0]))
            continue
        else:
            print(str.format('latest merge commit for branch "{0}" is {1}: "{2}"', branch[0], merge_commit_id, merge_commit_message))

        # if the merge commit is already contained in a SapMachine tag, we're done if the merge commit's JDK tag is a ga tag
        # otherwise we run some logic to make sure a corresponding JDK ga tag is not missed out
        _, tags_of_merge_commit, _ = utils.run_cmd(str.format('git tag --contains {0}', merge_commit_id).split(' '), cwd=git_target_dir, std=True, throw=False)
        if tags_of_merge_commit:
            print(str.format('Merge commit for "{0}" was already tagged.', jdk_tag.as_string()))
            if not jdk_tag.is_ga():
                check_for_untagged_ga(jdk_tag, tags_of_merge_commit.splitlines(), merge_commit_id)
            continue

        # this merge commit is not contained in a SapMachine tag but a corresponding sapmachine tag already exists pointing to somewhere else.
        # That's weird, but we don't change things now...
        if exists_tag(jdk_tag.as_sapmachine_tag_string()):
            print(str.format('"{0}" is already tagged as "{1}" but does not include this merge commit. That could be a problem.',
                jdk_tag.as_string(), jdk_tag.as_sapmachine_tag_string()))
            continue

        # create the sapmachine tag
        create_sapmachine_tag(jdk_tag, merge_commit_id)

        if jdk_tag.is_ga():
            # when the tag is a GA tag and the last non-ga tag was not yet tagged, we tag it to the same commit and build it
            make_sure_last_non_ga_is_tagged(jdk_tag, merge_commit_id)
        else:
            # build the new tag (EA release)
            run_jenkins_jobs(jdk_tag.get_major(), jdk_tag.as_sapmachine_tag_string())

    utils.remove_if_exists(workdir)
    return 0

if __name__ == "__main__":
    sys.exit(main())
