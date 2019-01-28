'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import os
import sys
import time
import subprocess
from pathlib import Path 

JAR         = "dacapo-9.12-MR1-bach.jar"
HEADL       = "-Djava.awt.headless=true"
PARA        = "--max-iterations=35 --variance=5 --verbose"
timeout     = 450

# get path to the SapMachine
CURRENT_DIR = os.getcwd()
os.chdir('SapMachine')
os.chdir('build')
ARR = os.listdir()
BUILD_TYPE  = ARR[0]
JAV = CURRENT_DIR + "/SapMachine/build/" + BUILD_TYPE + "/images/jdk/bin/java"

# print Java Version
subprocess.call([ JAV , '-version'])

#clean up 
os.chdir(CURRENT_DIR)


#
# take and evaluate the time for the dacapo call
#

def timerfunc(func):
    def function_timer(*args, **kwargs):
        start   = time.time()
        value   = func(*args, **kwargs)
        end     = time.time()
        runtime = end - start
        msg = "The runtime for {func} took {time} seconds to complete"
        print(msg.format(func=func.__name__, time=runtime))

        diff    = timeout - runtime
        if diff > 0:
          print('Testrun OK')
          return 0
        print('ERROR: Test did run in timeout')
        return diff

    return function_timer

	
#
# call the dacapo testsuite
#

@timerfunc
def call_dacapo():

   # default run:
   result =  subprocess.call([ JAV ,HEADL,'-jar',JAR,'--max-iterations=35','--variance=5','--verbose','--converge','fop','avrora','h2','luindex','lusearch','pmd','xalan'])

   if result != 0:
     print('ERROR: Test did run in error: ', result)
     return result

	 
if __name__ == '__main__':
    call_dacapo()
     
