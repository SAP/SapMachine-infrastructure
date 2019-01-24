'''
Copyright (c) 2001-2018 by SAP SE, Walldorf, Germany.
All rights reserved. Confidential and proprietary.
'''

import sys
import time
import subprocess

JAR        = "dacapo-9.12-MR1-bach.jar"
HEADL      = "-Djava.awt.headless=true"
PARA       = "--max-iterations=35 --variance=5 --verbose"
timeout    = 450

#
# check the argument (java path)
#

if len(sys.argv) != 2:
  print('missing java path. Syntax: python3' + str(sys.argv[0]) + ' <path to java>')
  sys.exit(-1)

JAV = sys.argv[1]
subprocess.call([ JAV , '-version'])


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
        return sys.exit(-2)

    return function_timer

	
#
# call the dacapo testsuite
#

@timerfunc
def call_dacapo():

   # provoke ERROR (with SapMachine 11):
   #result = subprocess.call([ JAV ,HEADL,'-jar',JAR,'--max-iterations=35','--variance=5','--verbose','--converge','fop','jython','avrora','eclipse','h2','luindex','lusearch','pmd','sunflow','xalan'])

   # run very short run:
   #result = subprocess.call([ JAV ,HEADL,'-jar',JAR,'--max-iterations=1','--variance=1','--verbose','--converge','fop'])

   # default run:
   result =  subprocess.call([ JAV ,HEADL,'-jar',JAR,'--max-iterations=35','--variance=5','--verbose','--converge','fop','avrora','h2','luindex','lusearch','pmd','xalan'])

   if result != 0:
     print('ERROR: Test did run in error: ', result)
     return sys.exit(-3)

	 
if __name__ == '__main__':
    call_dacapo()
     

