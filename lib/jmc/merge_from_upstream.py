'''
Copyright (c) 2021-2022 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''
import os
import re
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import utils

# Some global variables
pushURL = str.format('https://{0}:{1}@github.com/SAP/JMC.git', os.environ['GIT_USER'], os.environ['GIT_PASSWORD'])

def create_jmc_pr(commit, branch):
    print(str.format('Creating pull request "pr-{0}-{1}" for commit {0} from branch "{1}"', commit, branch))
    utils.run_cmd(str.format('git checkout -b pr-{0}-{1} {0}', commit, branch).split(' '))
    utils.run_cmd(str.format('git push {0} pr-{1}-{2}', pushURL, commit, branch).split(' '))
    pull_request = str.format('{{ "title": "{1}: Merge {0}", "body": "Please merge latest commit {0} from jmc upstream repo into branch {1}", "head": "pr-{0}-{1}", "base": "{1}" }}', commit, branch)
    utils.github_api_request('pulls', repository='JMC', data=pull_request, method='POST')

# This script is supposed to be run in a JMC repository directory
def main(argv=None):
    # fetch sap branches
    print("Fetching branches from JMC repository...")
    sap_branches = utils.get_active_jmc_branches()
    if sap_branches is None or len(sap_branches) == 0:
        print("No active JMC branches found")
        return 0

    # iterate sap branches
    for sap_branch in sap_branches:
        print(str.format('Processing branch "{0}" ({1})...', sap_branch[0], sap_branch[1]))

        # checkout and update branch
        utils.run_cmd(str.format('git checkout {0}', sap_branch[0]).split(' '))
        utils.run_cmd(['git', 'pull'])

        print('Checking if a new JMC commit needs to be merged...')

        # get jmc branch
        jmc_branch = "master" if sap_branch[0] == "sap" else sap_branch[0].replace("sap", "jmc")
        print(str.format('Corresponding jmc branch: {0}', jmc_branch))

        # get latest commit
        _, latest_commit_hash, _ = utils.run_cmd(str.format('git rev-parse origin/{0}', jmc_branch).split(' '), std=True, throw=False)
        latest_commit_hash = latest_commit_hash.rstrip()
        print(str.format('Latest commit: {0}', latest_commit_hash))

        # check if it is contained in current branch
        is_contained = utils.run_cmd(str.format('git merge-base --is-ancestor {0} HEAD', latest_commit_hash).split(' '), throw=False)
        if is_contained == 0:
            print(str.format('Commit "{0}" is already contained in branch "{1}"', latest_commit_hash, sap_branch[0]))
            continue

        # check if a PR branch already exists
        _, branches, _ = utils.run_cmd(str.format('git branch -a --contains {0}', latest_commit_hash).split(' '), std=True, throw=False)
        containing_branches_pattern = re.compile('pr-[a-zA-Z0-9]+-{0}'.format(sap_branch[0]))
        match = re.search(containing_branches_pattern, branches)
        if match is not None:
            print(str.format('Commit "{0}" is being merged into "{1}" via pr {2}', latest_commit_hash, sap_branch[0], match.group(0)))
            continue

        # the commit is not contained in a SAP JMC branch or a PR branch
        # create a pull request branch and a pull request.
        print('Commit isch ned drin, mer brare e pr')
        create_jmc_pr(latest_commit_hash, sap_branch[0])

    return 0

if __name__ == "__main__":
    sys.exit(main())
