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
MODUS       = ""

# check the argument (jar path and optional NOBUILD-Flag)
if len(sys.argv) < 2:
  print('missing path to the dacapo jar. Syntax: python ' + str(sys.argv[0]) + ' <c:\\bin\dacapo.jar>' + ' optional NOBUILD-Flag' )
  sys.exit(-2)
# get path to dacapo.jar  
elif len(sys.argv) == 2:
  JAR = sys.argv[1]
  print('JAR: ', JAR)
  
  # evaluate path to the SapMachine
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
  # get path to dacapo.jar
  JAR = sys.argv[1]
  print('JAR: ', JAR)
  # get path to the SapMachine
  JAV = "/opt/sapmachine-11-jdk/bin/java"
  # get the modus (short, error, normal run)
  MODUS = sys.argv[2]
  print('MODUS: ', MODUS)
  
# print Java Version
subprocess.call([JAV , '-version'])

#
# call the dacapo testsuite
#

def call_dacapo():

    start   = time.time()

    if MODUS == "short":
      result =  subprocess.call([ JAV ,HEADL,'-jar',JAR,'--max-iterations=1' ,'--variance=1','--verbose','--converge','fop']) 
    elif MODUS == "error":
      result =  subprocess.call([ JAV ,HEADL,'-jar',JAR,'--max-iterations=35' ,'--variance=5','--verbose','--converge','fop','jython','avrora','eclipse','h2','luindex','lusearch',
'pmd','sunflow','xalan'])
    else:
      # default run:
      result =  subprocess.call([ JAV ,HEADL,'-jar',JAR,'--max-iterations=35' ,'--variance=5','--verbose','--converge','fop','avrora','h2','luindex','lusearch','pmd','xalan']) 

    end = time.time()
    runtime = end - start    
    diff    = timeout - runtime
    PRFX    = '<?xml version="1.0" encoding="UTF-8"?><testsuites><testsuite><testcase name="Dacapo" classname="Dacapo" time="' + str(runtime) +' sec"' 
    POFX    = '</testcase></testsuite></testsuites>'
    ERR     = PRFX + ' failures=""  tests="1" errors="1"> <error message="ERROR in dacapo">see logfile</error>' + POFX
    SUCC    = PRFX + ' failures=""  tests="1" errors="0"> successful dacapo run' + POFX
    FAL     = PRFX + ' failures="1" tests="1" errors="0"> <failure message="TIMEOUT in dacapo">see logfile</failure>' + POFX

    if result != 0:
        print('ERROR: Test did run in error: ', result)
        f = open("dacapo.xml", "w")
        f.write(ERR)
        return result

    if diff < 0:
        print('FAILURE: Test did run in timeout')
        f = open("dacapo.xml", "w")
        f.write(FAL)
        return runtime
      
    print('Testrun OK')
    f = open("dacapo.xml", "w")
    f.write(SUCC)
    return 0

if __name__ == '__main__':
    call_dacapo()


