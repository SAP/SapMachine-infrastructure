'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import subprocess
import os
import sys
import time

HEADL       = "-Djava.awt.headless=true"
PARA        = "--max-iterations=35 --variance=5 --verbose"
timeout     = 600

# check the argument (jar path and optional NOBUILD-Flag)
if len(sys.argv) < 2:
  print('missing path to the dacapo jar. Syntax: python ' + str(sys.argv[0]) + ' <c:\\bin\dacapo.jar>' + ' optional NOBUILD-Flag' )
  sys.exit(-2)
elif len(sys.argv) == 2:
  JAR = sys.argv[1]
  print('JAR: ', JAR)
  
  # get path to the SapMachine
  CURRENT_DIR = os.getcwd()
  os.chdir('SapMachine')
  os.chdir('build')

  PYTHON_VER = sys.version_info[0]
  if PYTHON_VER < 3:
      p1 = subprocess.Popen(['ls'], stdout=subprocess.PIPE)
      BUILD_TYPE = p1.communicate()[0]
      BUILD_TYPE = BUILD_TYPE.strip('\n')
  else:
      ARR = os.listdir()
      BUILD_TYPE  = ARR[0]
  JAV = CURRENT_DIR + "/SapMachine/build/" + BUILD_TYPE + "/images/jdk/bin/java"
  #clean up
  os.chdir(CURRENT_DIR)
else:
  JAR = sys.argv[1]
  print('JAR: ', JAR)
  JAV = "/opt/sapmachine-11-jdk/bin/java"
  
# print Java Version
subprocess.call([JAV , '-version'])

#
# call the dacapo testsuite
#

def call_dacapo():

    start   = time.time()

    # default run:
    result =  subprocess.call([ JAV ,HEADL,'-jar',JAR,'--max-iterations=35' ,'--variance=5','--verbose','--converge','fop','avrora','h2','luindex','lusearch','pmd','xalan'])

    if result != 0:
        print('ERROR: Test did run in error: ', result)
        return result

    end = time.time()
    runtime = end - start    
    diff    = timeout - runtime
    if diff < 0:
        print('ERROR: Test did run in timeout')
        return diff
    print('Testrun OK')
    return 0

if __name__ == '__main__':
    call_dacapo()


