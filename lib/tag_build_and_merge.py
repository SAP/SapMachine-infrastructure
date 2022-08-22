'''
Copyright (c) 2018-2022 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''
import os
import re
import sys
import utils

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.crumb_requester import CrumbRequester
from versions import JDKTag

# Some global variables
merge_commit_pattern = re.compile('Merge pull request #\d+ from SAP/pr-jdk-')
pull_requests = None
sapMachinePushURL = str.format('https://{0}:{1}@github.com/SAP/SapMachine.git',
    os.environ['GIT_USER'], os.environ['GIT_PASSWORD'])

def run_jenkins_jobs(major, tag):
    print(str.format('Starting jenkins jobs for {0}: {1}...', major, tag))

    if 'JENKINS_CREDENTIALS_USR' not in os.environ:
        print("JENKINS_CREDENTIALS_USR environment variable not found, can not start jenkins jobs.")
        return

    if 'JENKINS_CREDENTIALS_PSW' not in os.environ:
        print("JENKINS_CREDENTIALS_PSW environment variable not found, can not start jenkins jobs.")
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

    # strange, but with that one I got a 403: https://ci.sapmachine.io/view/Infrastructure/job/repository-tags/191/
    # server.use_auth_cookie()

    build_jobs = [
        str.format('build-{0}-release-linux_x86_64', major),
        str.format('build-{0}-release-linux_ppc64le', major),
        str.format('build-{0}-release-linux_aarch64', major),
        str.format('build-{0}-release-macos_x86_64', major),
        str.format('build-{0}-release-macos_aarch64', major),
        str.format('build-{0}-release-windows_x86_64', major)
    ]

    if major > 11:
        build_jobs.append(str.format('build-{0}-release-linux_alpine_x86_64', major))

    job_params = {
        'PUBLISH': 'true' ,
        'RELEASE': 'false',
        'GIT_REF': tag
    }

    for job in build_jobs:
        print(str.format('starting jenkins job "{0}" ...', job))
        server.build_job(job, job_params)

def get_merge_commits(numcommits = 20):
    _, commits, _ = utils.run_cmd(['git', 'log', '--merges', '-n', str(numcommits), '--format=%H %s'], std=True, throw=False)

    commit_list = []
    for commit in commits.split(os.linesep):
        if commit:
            commit_list.append(commit.split(" ", 1))

    return commit_list

def create_sapmachine_tag(jdk_tag, commit_id):
    sapmachine_tag_str = jdk_tag.as_sapmachine_tag_string()
    print(str.format('Tagging {0} as {1}...', commit_id, sapmachine_tag_str))
    env = os.environ.copy()
    env['GIT_AUTHOR_NAME'] = 'SapMachine'
    env['GIT_AUTHOR_EMAIL'] = 'sapmachine@sap.com'
    env['GIT_COMMITTER_NAME'] = env['GIT_AUTHOR_NAME']
    env['GIT_COMMITTER_EMAIL'] = env['GIT_AUTHOR_EMAIL']
    utils.run_cmd(['git', 'tag', '-a', '-m', str.format('Tag {0} as {1}', commit_id, sapmachine_tag_str), sapmachine_tag_str, commit_id], env=env)
    utils.run_cmd(str.format('git push {0} {1}', sapMachinePushURL, sapmachine_tag_str).split(' '))

def create_openjdk_pr(tag, branch):
    print(str.format('Creating pull request "pr-{0}" with base branch "{1}"', tag.as_string(), branch))
    utils.run_cmd(str.format('git checkout -b pr-{0} {0}', tag.as_string()).split(' '))
    utils.run_cmd(str.format('git push {0} pr-{1}', sapMachinePushURL, tag.as_string()).split(' '))
    pull_request = str.format('{{ "title": "Merge to tag {0}", "body": "please pull", "head": "pr-{1}", "base": "{2}" }}', tag.as_string(), tag.as_string(), branch)
    utils.github_api_request('pulls', data=pull_request, method='POST')

def exists_tag(tag):
    _, tag_exists, _ = utils.run_cmd(str.format('git tag -l {0}', tag).split(' '), std=True, throw=False)
    return bool(tag_exists)

def make_sure_last_non_ga_is_tagged(jdk_tag, commit_id):
    latest_non_ga_tag = jdk_tag.get_latest_non_ga_tag()

    if latest_non_ga_tag is not None and not exists_tag(latest_non_ga_tag.as_sapmachine_tag_string()):
        create_sapmachine_tag(latest_non_ga_tag, commit_id)
        run_jenkins_jobs(jdk_tag.get_major(), latest_non_ga_tag.as_sapmachine_tag_string())

def check_for_untagged_ga(merge_commit_id, jdk_tag, tags_of_merge_commit):
    print(str.format('Checking if OpenJDK GA tag for release {0} exists and is not SapMachine-tagged...', jdk_tag.get_version_string_without_build()))
    # get the commit the jdk_tag is pointing to
    print(str.format('Retrieving commit for OpenJDK tag {0}...', jdk_tag.as_string()))
    _, jdk_tag_commit, _ = utils.run_cmd(str.format('git rev-list -n 1 {0}', jdk_tag.as_string()).split(' '), std=True, throw=False)
    if jdk_tag_commit is None:
        print(str.format('No commit found for JDK tag {0}, that should not happen', jdk_tag.as_string()))
        return
    else:
        jdk_tag_commit = jdk_tag_commit.rstrip()
        print(str.format('JDK tag {0} points to {1}.', jdk_tag.as_string(), jdk_tag_commit))

    # get all tags associated with the commit
    print(str.format('Retrieving tags that contain commit {0}...', jdk_tag_commit))
    _, tags_of_jdk_tag_commit, _ = utils.run_cmd(str.format('git tag --contains {0}', jdk_tag_commit).split(' '), std=True, throw=False)
    if tags_of_jdk_tag_commit is None:
        print(str.format('No tags found for commit ${0}, that should not happen', jdk_tag_commit))
        return

    # search for a GA tag that matches jdk_tag's update version
    print(str.format('Checking tags for matching GA...'))
    ga_tag = None
    for tag in tags_of_jdk_tag_commit.splitlines():
        ga_tag = JDKTag.from_string(tag)
        if ga_tag is not None:
            if ga_tag.is_ga() and jdk_tag.is_same_update_version(ga_tag):
                break
            else:
                ga_tag = None

    if ga_tag is None:
        print(str.format('No GA tag found for "{0}"', jdk_tag.get_version_string_without_build()))
        return
    else:
        print(str.format('Found GA tag for "{0}": {1}', jdk_tag.get_version_string_without_build(), ga_tag.as_string()))

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

def tag_and_run_buildjob():
        print(str.format('Check if new SapMachine tag needs to be set...'))

        # get last merge commits
        numcommits = 20
        print(str.format('Retrieving last {0} merge commits...', numcommits))
        merge_commits = get_merge_commits(numcommits)

        # find latest conforming OpenJDK->SapMachine merge commit
        jdk_tag = None
        for merge_commit in merge_commits:
            if re.search(merge_commit_pattern, merge_commit[1]) is None:
                print(str.format('Merge commit {0} ("{1}") is no conforming OpenJDK->SapMachine merge', merge_commit[0], merge_commit[1]))
                continue

            match_jdk_tag = re.search(JDKTag.tag_pattern, merge_commit[1])
            if match_jdk_tag is None:
                print(str.format('Merge commit {0} ("{1}") does not mention a recognized OpenJDK tag', merge_commit[0], merge_commit[1]))
                continue

            jdk_tag = JDKTag(match_jdk_tag)
            print(str.format('Identified merge commit {0} ("{1}") as the latest conforming OpenJDK->SapMachine merge, merging "{2}"',
                merge_commit[0], merge_commit[1], jdk_tag.as_string()))
            merge_commit_id = merge_commit[0]
            break

        # log result
        if jdk_tag is None:
            print('No OpenJDK->SapMachine merge commits found')
            return

        # now check if the merge commit is already contained in a tag
        _, tags_of_merge_commit, _ = utils.run_cmd(str.format('git tag --contains {0}', merge_commit_id).split(' '), std=True, throw=False)
        if tags_of_merge_commit:
            # if the merge commit's JDK tag is not a ga tag, we need to run some logic to make sure a corresponding JDK ga tag is not missed out.
            print(str.format('Merge commit {0} is already contained in further tags.', merge_commit_id))
            if not jdk_tag.is_ga():
                check_for_untagged_ga(merge_commit_id, jdk_tag, tags_of_merge_commit.splitlines())
            # and we are done
            return

        # this merge commit is not contained in a tag but a corresponding sapmachine tag already exists pointing to somewhere else.
        # That's weird, but we don't change things now...
        if exists_tag(jdk_tag.as_sapmachine_tag_string()):
            print(str.format('"{0}" is already tagged as "{1}" but does not include this merge commit. That could be a problem.',
                jdk_tag.as_string(), jdk_tag.as_sapmachine_tag_string()))
            return

        # create the sapmachine tag
        create_sapmachine_tag(jdk_tag, merge_commit_id)

        if jdk_tag.is_ga():
            # when the tag is a GA tag and the last non-ga tag was not yet tagged, we tag it to the same commit and build it
            make_sure_last_non_ga_is_tagged(jdk_tag, merge_commit_id)
        else:
            # build the new tag (EA release)
            run_jenkins_jobs(jdk_tag.get_major(), jdk_tag.as_sapmachine_tag_string())

# This script is supposed to be run in a SapMachine repository directory
def main(argv=None):
    # fetch all branches
    sapmachine_branches = utils.get_active_sapmachine_branches()
    if sapmachine_branches is None or len(sapmachine_branches) == 0:
        print("No active sapmachine branches found")
        return 0


    # fetch all tags
    print("Fetching GitHub tags...")
    tags = utils.get_github_tags()

    # iterate all tags to find the latest jdk tag for a JDK major release
    jdk_tags = {}
    for tag in tags:
        # filter for jdk tags
        jdk_tag = JDKTag.from_string(tag['name'])
        if jdk_tag is None:
            continue

        # only remember the latest jdk tag (version comparison)
        # filter out jdk update tags with build number "0" like jdk-11.0.3+0
        if ((jdk_tag.get_major() not in jdk_tags or jdk_tag.is_greater_than(jdk_tags[jdk_tag.get_major()])) and
            not (jdk_tag.get_update() > 0 and (jdk_tag.get_build_number() if jdk_tag.get_build_number() is not None else 0) == 0)):
            jdk_tags[jdk_tag.get_major()] = jdk_tag

    print("Latest OpenJDK tag per major version:")
    for k,v in jdk_tags.items():
        print(str.format('{0}: {1}', str(k).rjust(2), v.as_string()))

    # go through all sapmachine branches
    for sapmachine_branch in sapmachine_branches:
        print(str.format('Processing branch "{0}" ({1})...', sapmachine_branch[0], sapmachine_branch[1]))

        # checkout and update branch
        utils.run_cmd(str.format('git checkout {0}', sapmachine_branch[0]).split(' '))
        utils.run_cmd(['git', 'pull'])

        # find the latest OpenJDK merge commit and make sure it's correctly sapmachine-tagged
        tag_and_run_buildjob()

        print('Checking if a new OpenJDK tag needs to be merged...')

        # get the latest jdk tag for this major version
        latest_tag = jdk_tags[sapmachine_branch[1]]
        print(str.format('Latest tag for branch "{0}" is "{1}"', sapmachine_branch[0], latest_tag.as_string()))

        # check whether the jdk tag is already contained in the sapmachine branch or a PR branch
        _, out, _ = utils.run_cmd(str.format('git branch -a --contains tags/{0}', latest_tag.as_string()).split(' '), std=True, throw=False)
        containing_branches_pattern = re.compile('{0}|pr-jdk-{1}.*'.format(sapmachine_branch[0], sapmachine_branch[1]))
        match = re.search(containing_branches_pattern, out)

        if match is None:
            # the jdk tag is not contained in a sapmachine branch
            # create a pull request branch and a pull request.
            create_openjdk_pr(latest_tag, sapmachine_branch[0])
        else:
            print(str.format('Tag "{0}" was already merged into branch "{1}" or a PR branch exists', latest_tag.as_string(), sapmachine_branch[0]))

    return 0

if __name__ == "__main__":
    sys.exit(main())
