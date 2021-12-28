'''
Copyright (c) 2001-2021 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import utils

from os.path import join

def main(argv=None):
    local_repo = join(os.getcwd(), 'SapMachine')
    utils.git_clone('github.com/SAP/SapMachine.git', 'sapmachine', local_repo)
    return 0

if __name__ == "__main__":
    sys.exit(main())
