#!/bin/bash

set -x

UNAME=`uname`

while getopts l:h:s:j: opt
do
   case $opt in
       l) JDK_LOCATION=$OPTARG;;
       h) JT_HOME=$OPTARG;;
       s) TEST_SUITE=$OPTARG;;
   esac
done

shift $((OPTIND-1))
TEST_GROUPS=$@

if [ -z "$JDK_LOCATION" ]; then
    echo "JDK Location not specified (-l)" >&2
    exit 1
fi

if [ -z "$JT_HOME" ]; then
    echo "JavaTest Home not specified (-h)" >&2
    exit 1
fi

if [ -z "$TEST_SUITE" ]; then
    echo "Test Suite not specified (-s)" >&2
    exit 1
fi

if [ -z "$TEST_GROUPS" ]; then
    echo "Test Groups not specified" >&2
    exit 1
fi

CURRENT_DIR=$PWD
cd ${JDK_LOCATION}/build

BUILD_TYPE="$(ls)"

cd $CURRENT_DIR

TEST_JDK=${JDK_LOCATION}/build/${BUILD_TYPE}/images/jdk
TEST_NATIVE_LIB=${JDK_LOCATION}/build/${BUILD_TYPE}/images/test/${TEST_SUITE}/jtreg/native

if [[ $UNAME == Darwin ]]; then
    NUM_CPUS=`sysctl -n hw.ncpu`
elif [[ $UNAME == AIX ]]; then
    NUM_CPUS=`lparstat -m 2> /dev/null | grep -o "lcpu=[[0-9]*]*" | cut -d "=" -f 2`
else
    NUM_CPUS=`grep -c ^processor /proc/cpuinfo`
fi

# Use half number of CPUs on AIX because OSUOSL machine lacks resources for more
if [[ $UNAME == AIX ]]; then
    CONCURRENCY=`expr $NUM_CPUS / 2`
else
    #CONCURRENCY=$NUM_CPUS
    CONCURRENCY=`expr $NUM_CPUS / 2`
fi

# Use half number of CPUs for langtools suite because http://openjdk.java.net/jtreg/concurrency.html suggests this
CONCURRENCY_LANGTOOLS=`expr $NUM_CPUS / 2`

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

chmod +x ${JT_HOME}/bin/jtreg

export PATH=${TEST_JDK}:$PATH
export JT_JAVA=${TEST_JDK}
export JAVA_HOME=${TEST_JDK}

export TEST_VM_FLAGLESS=true

mkdir test_report_${TEST_SUITE}

if [ -x /opt/tinyreaper ]; then
  JTREG_CMD="/opt/tinyreaper ${JT_HOME}/bin/jtreg"
else
  JTREG_CMD="${JT_HOME}/bin/jtreg"
fi

if [ "${TEST_SUITE}" == "hotspot" ]; then
    ${JTREG_CMD} -dir:${JDK_LOCATION}/test/${TEST_SUITE}/jtreg -xml -verbose:summary -nativepath:${TEST_NATIVE_LIB} \
    -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/jtreg/ProblemList.txt \
    -conc:${CONCURRENCY} -vmoption:-Xmx384m -w:test_report_${TEST_SUITE}/JTwork -r:test_report_${TEST_SUITE}/JTreport \
    -a -ignore:quiet -timeoutFactor:5 -agentvm -javaoption:-Djava.awt.headless=true "-k:(!ignore)&(!stress)&(!headful)&(!intermittent)" "-e:ProgramFiles(x86)" -testjdk:${TEST_JDK} ${TEST_GROUPS}
fi

if [ "${TEST_SUITE}" == "jdk" ]; then
    ${JTREG_CMD} -dir:${JDK_LOCATION}/test/${TEST_SUITE} -xml -verbose:summary -nativepath:${TEST_NATIVE_LIB} \
    -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/ProblemList.txt \
    -conc:${CONCURRENCY} -vmoption:-Xmx384m -w:test_report_${TEST_SUITE}/JTwork -r:test_report_${TEST_SUITE}/JTreport \
    -a -ignore:quiet -timeoutFactor:5 -agentvm -javaoption:-Djava.awt.headless=true "-k:(!headful)&(!printer)&(!intermittent)" -testjdk:${TEST_JDK} ${TEST_GROUPS}
fi

if [ "${TEST_SUITE}" == "langtools" ]; then
    ${JTREG_CMD} -dir:${JDK_LOCATION}/test/${TEST_SUITE} -xml -verbose:summary \
    -exclude:${JDK_LOCATION}/test/${TEST_SUITE}/ProblemList.txt \
    -conc:${CONCURRENCY_LANGTOOLS} -vmoption:-Xmx768m -w:test_report_${TEST_SUITE}/JTwork -r:test_report_${TEST_SUITE}/JTreport \
    -a -ignore:quiet -timeoutFactor:5 -agentvm "-k:(!headful)&(!intermittent)" -testjdk:${TEST_JDK} ${TEST_GROUPS}
fi
