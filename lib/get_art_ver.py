'''
Copyright (c) 2023 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys

from versions import SapMachineTag

def main(argv=None):
    tag = SapMachineTag.from_string(os.environ['SAPMACHINE_VERSION'])
    f = open("art_vers.txt", "w")
    f.write(tag.get_version_string())
    f.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
